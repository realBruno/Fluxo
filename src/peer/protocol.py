import hashlib
import math
import time
from dataclasses import dataclass
import asyncio
import struct

from typing import Any

import numpy as np
from colorama import Fore

from peer.messages import Message
from peer.peer import Peer
from torrent.download import Download


@dataclass
class PeerProtocol:
    writer: asyncio.StreamWriter
    reader: asyncio.StreamReader
    last_sent: float = None

    def __post_init__(self):
        self.last_sent = time.monotonic()

    async def send(self, data: bytes):
        self.writer.write(data)
        await self.writer.drain()
        self.last_sent = time.monotonic()

    async def send_handshake(self, handshake: bytes) -> bytes | None:
        """Sends first ever message to peer.

        :param handshake: Handshake message
        :returns: The peer's handshake bytes if valid, otherwise None
        """
        await self.send(handshake)
        return await self.read_handshake(handshake)

    async def read_handshake(self, handshake: bytes) -> bytes | None:
        """ Reads and validates peer's handshake.

        Each handshake should be 68 bytes long. The info_hash
        of the response, which is 20 bytes long and is located at
        positions 28 to 48, should equal the client's info_hash.

        :param handshake: Handshake message.
        :returns: The peer's handshake bytes if valid, otherwise None.
        """
        response = await asyncio.wait_for(
            self.reader.readexactly(68), timeout=10
        )
        if response[28:48] == handshake[28:48]:
            return response
        return None

    async def send_interested(self, peer: Peer) -> None:
        """ Informs peer that the client is interested in pieces they own.

            Peer's responds with one of the values in the "Message" dataclass.
        """
        peer.am_choking = False
        peer.am_interested = True

        message = struct.pack("!IB", msg_len := 1, Message.interested)
        await self.send(message)

    async def send_not_interested(self, peer: Peer) -> None:
        peer.am_choking = True
        peer.am_interested = False

        message = struct.pack("!IB", msg_len := 1, Message.not_interested)
        await self.send(message)

    async def send_keep_alive(self) -> None:
        print(f"{Fore.CYAN}KEEP-ALIVE:{Fore.RESET} client has avoided timeout")
        message = struct.pack("!I", msg_len := 0)
        # TODO IMPLEMENT COUNTER
        await self.send(message)

    async def keep_alive_loop(self, interval=60):
        try:
            while True:
                await asyncio.sleep(interval)
                if time.monotonic() - self.last_sent >= interval:
                    await self.send_keep_alive()
        except asyncio.CancelledError:
            pass

    # TODO
    # async def handle_interested(self):
    #     ...

    # TODO
    # async def handle_not_interested(self):
    #     ...

    async def handle_have(self, peer: Peer):
        index = await self.reader.readexactly(4)
        index = struct.unpack("!I", index)[0]
        peer.bitfield[index] = True

    @staticmethod
    async def handle_bitfield(total_pieces, payload):
        """
            rounded_size takes total_pieces and "rounds"
            it to the nearest integer divisible by 8,
            in order to stop the client from dropping
            connection with peers mistakenly.
        """
        bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8)).astype(bool)

        rounded_size = total_pieces + 8 - (total_pieces % 8)
        if bits.size > rounded_size:
            print(f"{Fore.RED}ERROR:{Fore.RESET} bitfield larger than expected")
            return None
        return bits[:total_pieces]

    @staticmethod
    async def handle_piece(peer: Peer, download: Download, payload):
        index = struct.unpack("!I", payload[0:4])[0]
        begin = struct.unpack("!I", payload[4:8])[0]
        block = payload[8:]

        full_piece = None

        async with download.lock:
            if index not in download.piece_blocks:
                download.piece_blocks[index] = {}

            if begin in download.piece_blocks[index]:
                return

            download.piece_blocks[index][begin] = block

            if len(download.piece_blocks[index]) == download.total_blocks:
                blocks = download.piece_blocks.pop(index)
                full_piece = b''.join(blocks[offset] for offset in sorted(blocks))

        if full_piece is None:
            return

        expected_hash = download.pieces[index * 20: (index + 1) * 20]
        hash_obtained = hashlib.sha1(full_piece).digest()

        if expected_hash != hash_obtained:
            print(f"{Fore.RED}ERROR:{Fore.RESET}: peer has sent invalid block")
            return

        print(f"{Fore.GREEN}SUCCESS:{Fore.RESET} piece number {index} has been downloaded")

        async with download.lock:
            download.downloaded[index] = True
            download.downloading[index] = False

        position = index * download.piece_length

        if index == download.total_pieces - 1:
            expected_size = download.file_size - position
            full_piece = full_piece[:expected_size]

        with open(download.filename, "r+b") as f:
            f.seek(position)
            f.write(full_piece)

    async def handle_cancel(self):
        ...

    async def send_request(self, peer: Peer, download: Download):

        async with download.lock:
            next_piece = None
            for piece_index in range(download.total_pieces):
                if (
                        peer.bitfield[piece_index]
                        and not download.downloaded[piece_index]
                        and not download.downloading[piece_index]
                ):
                    next_piece = piece_index
                    download.downloading[piece_index] = True
                    break

            if next_piece is None:
                return 0

        if next_piece == download.total_pieces - 1:
            piece_size = download.file_size - next_piece * download.piece_length
        else:
            piece_size = download.piece_length

        block_size = download.block_size
        total_blocks = math.ceil(piece_size / block_size)

        print(f"{Fore.YELLOW}REQUEST:{Fore.RESET} piece number {next_piece}")

        for block in range(total_blocks):
            begin = block * block_size
            length = min(block_size, piece_size - begin)

            message = struct.pack(
                "!IBIII",
                13,
                Message.request,
                next_piece,
                begin,
                length,
            )
            await self.send(message)

        return 1

    async def handle_port(self):
        ...

    async def read_response(self) -> tuple[int, Any, Any]:
        """Reads response from peer.

        The response from a peer may vary in length:
        If length is 0, peer is sending a "keep-alive" message.
        If 1, it sent requests of (un)choke or (not) interested.
        Otherwise, peer has sent data on the files requested.

        :return: A tuple with length, and message_id and payload or None
        """
        length = await self.reader.readexactly(4)
        length = struct.unpack("!I", length)[0]
        if length == 0:
            return length, None, None

        message_id = await self.reader.readexactly(1)
        message_id = struct.unpack("!B", message_id)[0]
        if length == 1:
            return length, message_id, None

        payload = await self.reader.readexactly(length - 1)
        return length, message_id, payload