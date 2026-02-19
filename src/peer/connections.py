import asyncio
import math
import struct

import numpy as np
from colorama import Fore

from  peer.peer import Peer
from peer.protocol import PeerProtocol
from torrent.download import Download, build_download
from tracker.endpoints import sock_addr
from peer.messages import Message


def build_handshake(info_hash: bytes, peer_id: str) -> bytes:
    pstr = b"BitTorrent protocol"
    pstrlen = len(pstr).to_bytes(1, byteorder="big")
    reserved = bytes(8)
    info_hash = info_hash
    peer_id = peer_id.encode()
    return pstrlen + pstr + reserved + info_hash + peer_id


async def close_writer(writer: asyncio.StreamWriter):
    if not writer:
        return
    writer.close()
    try:
        await asyncio.wait_for(writer.wait_closed(), timeout=2)
    except (asyncio.TimeoutError, ConnectionResetError, OSError):
        pass


async def handle_peer(endpoint, handshake, download, semaphore):

    ip, port = endpoint
    writer = None
    keep_alive_task = None
    async with semaphore:
        # noinspection PyBroadException
        try:
            connection = asyncio.open_connection(ip, port)
            reader, writer = await asyncio.wait_for(connection, timeout=10)

            peer = Peer(np.zeros(download.total_pieces, dtype=np.uint8))
            peer_protocol = PeerProtocol(writer, reader)

            keep_alive_task = asyncio.create_task(
                peer_protocol.keep_alive_loop()
            )

            peer_handshake = await peer_protocol.send_handshake(handshake)
            if peer_handshake is None: raise # drops connection with peer

            while True:
                length, message_id, payload = await peer_protocol.read_response()
                if message_id is not None:
                    match message_id:
                        case Message.choke:
                            peer.peer_choking = True
                        case Message.unchoke:
                            peer.peer_choking = False
                            await peer_protocol.send_request(peer, download)
                        # case Message.interested:
                        #     await peer_protocol.handle_interested()
                        # case Message.not_interested:
                        #     await peer_protocol.handle_not_interested()
                        case Message.have:
                            await peer_protocol.handle_have(peer)
                        case Message.bitfield:
                            peer.bitfield = await peer_protocol.handle_bitfield(download.total_pieces, payload)
                            if peer.bitfield is None:
                                return # drops connection with peer
                            wanted = np.any(peer.bitfield & ~download.downloaded)
                            if not wanted:
                                await peer_protocol.send_not_interested(peer)
                            else:
                                await peer_protocol.send_interested(peer)
                        case Message.piece:
                            await peer_protocol.handle_piece(peer, download, payload)
                        # case Message.cancel:
                        #     await peer_protocol.handle_cancel()
                        # case Message.port:
                        #     await peer_protocol.handle_port()
        except asyncio.TimeoutError:
            print(f"{Fore.RED}ERROR:{Fore.RESET} Peer did not respond")
        except ConnectionError as c:
            print(f"{Fore.RED}ERROR:{Fore.RESET} Connection: {c}")
        except Exception as e:
            print(f"{Fore.RED}ERROR:{Fore.RESET} {e}")
        finally:
            if keep_alive_task:
                keep_alive_task.cancel()
            await close_writer(writer)


async def handle_peers(endpoints, handshake, download):
    semaphore = asyncio.Semaphore(30)
    tasks = [
        asyncio.create_task(
            handle_peer(endpoint, handshake, download, semaphore)
        )
        for endpoint in endpoints
    ]
    await asyncio.gather(*tasks)


def contact_peer(decoded, t_response: dict, tracker_payload: dict):
    # t_response = tracker_response
    endpoints = sock_addr(t_response)

    # BUILDING HANDSHAKE
    info_hash = tracker_payload["info_hash"]
    peer_id = tracker_payload["peer_id"]
    handshake = build_handshake(info_hash, peer_id)

    download = build_download(decoded, t_response)

    with open(download.filename, "wb") as f:
        f.seek(download.file_size - 1)
        f.write(b'\0')

    asyncio.run(handle_peers(endpoints, handshake, download))