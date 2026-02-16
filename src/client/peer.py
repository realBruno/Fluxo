from dataclasses import dataclass
import struct
import hashlib
import asyncio
from colorama import Fore
from enum import Enum

HANDSHAKE_SIZE = 68


@dataclass
class ClientSate:
    interested: bool
    owned_pieces: set[int]
    path: str


def build_client_state(is_interested: bool, pieces: set[int], specified_path: str):
    return ClientSate (
        interested = is_interested,
        owned_pieces = pieces,
        path = specified_path
    )


@dataclass
class DownloadState:
    downloaded: set[int]
    downloading: set[int]
    piece_blocks: dict[int, set]
    lock: asyncio.Lock = None

    def __post_init__(self):
        if self.lock is None:
            self.lock = asyncio.Lock()


def build_download_state(loaded: set[int], loading: set[int], temp_var):
    return DownloadState (
        downloaded = loaded,
        downloading = loading,
        piece_blocks= temp_var
    )


@dataclass
class MetadataState:
    file_name: str
    length: int # total to be downloaded
    pieces_length: int # length of each piece
    pieces: bytes # pieces (bytes)


def build_metadata_state(decoded):
    return MetadataState(
        file_name = decoded[b"info"][b"name"].decode(),
        length = decoded[b"info"][b"length"],
        pieces_length = decoded[b"info"][b"piece length"],
        pieces = decoded[b"info"][b"pieces"]
    )


@dataclass
class PeerState:
    choking: bool


def build_peer_state(is_choking: bool):
    return PeerState (
        choking = is_choking
    )


class STATE(Enum):
    """Indexes for all states listed abot"""
    CLIENT = 0
    DOWNLOAD = 1
    METADATA = 2


class MESSAGE(Enum):
    CHOKE = 0
    UNCHOKE = 1
    INTERESTED = 2
    NOT_INTERESTED = 3
    HAVE = 4
    BITFIELD = 5
    REQUEST = 6
    PIECE = 7
    CANCEL = 8
    PORT = 9


def get_ips(response: dict):
    ips = []
    peers = response[b"peers"]

    if type(peers) == dict: return ips

    for i in range(0, len(peers) - 6, 6):
        chunk = peers[i: i + 6]
        ip = '.'.join(str(b) for b in chunk[0:4])
        if ip != "127.0.0.1":
            port = struct.unpack("!H", chunk[4: 6])[0]
            ips.append((ip, port))
    return ips


def build_handshake(info_hash, peer_id):
    pstr = b"BitTorrent protocol"
    pstrlen = len(pstr).to_bytes(1, byteorder="big")
    reserved = bytes(8)
    info_hash = info_hash
    peer_id = peer_id.encode()
    return pstrlen + pstr + reserved + info_hash + peer_id


def validate_handshake(response, info_hash):
    if len(response) < HANDSHAKE_SIZE or response[28:48] != info_hash:
        print(Fore.YELLOW + "Peer responded with malformed answer." + Fore.RESET)
        return 0
    print(Fore.GREEN + "Peer responded successfully." + Fore.RESET)
    return 1


async def send_handshake(handshake, writer, reader, info_hash):
    writer.write(handshake)
    await writer.drain()

    response = await asyncio.wait_for(
        reader.read(HANDSHAKE_SIZE), timeout=10
    )

    valid = validate_handshake(response, info_hash)

    return response if valid else None


async def send_interested(writer):
    message = struct.pack("!IB", 1, MESSAGE.INTERESTED.value)
    writer.write(message)
    await writer.drain()


async def receive_message(reader):
    size = await reader.readexactly(4)
    size = struct.unpack("!I", size)[0]

    if size == 0:
        return 0, None, b''

    message_type = await reader.readexactly(1)
    message_type = struct.unpack("!B", message_type)[0]

    payload = await reader.readexactly(size - 1) if size - 1 > 0 else b''
    return size, message_type, payload


def process_bitfield(payload):
    piece_index = 0
    indexes = set()
    for byte in payload:
        for bit_position in range(7, -1, -1):
            if byte & (1 << bit_position):
                indexes.add(piece_index)
            piece_index += 1
    return indexes


async def send_request(writer, index, begin, length):
    message = struct.pack("!IBIII", 13, MESSAGE.REQUEST.value, index, begin, length)
    writer.write(message)
    await writer.drain()


async def answer_to_unchoke(states, bitfield, writer, block_info):
    block_size, piece_length, total_blocks = block_info
    async with states[STATE.DOWNLOAD.value].lock:
        next_piece = None
        total_pieces = states[STATE.METADATA.value].length // 20
        for piece_i in range(total_pieces):
            if (piece_i in bitfield and
                    piece_i not in states[STATE.DOWNLOAD.value].downloaded and
                    piece_i not in states[STATE.DOWNLOAD.value].downloading):
                next_piece = piece_i
                states[STATE.DOWNLOAD.value].downloading.add(piece_i)
                break

        if next_piece is None:
            return 1

        current_piece_i = next_piece

    for block_num in range(total_blocks):
        begin = block_num * block_size
        length = min(block_size, piece_length - begin)
        await send_request(writer, current_piece_i, begin, length)
    return 0


async def answer_to_piece(payload, states, block_info):
    block_size, piece_length, total_blocks = block_info

    index = struct.unpack("!I", payload[0:4])[0]
    begin = struct.unpack("!I", payload[4:8])[0]
    data = payload[8:]

    async with states[STATE.DOWNLOAD.value].lock:
        if index not in states[STATE.DOWNLOAD.value].piece_blocks:
            states[STATE.DOWNLOAD.value].piece_blocks[index] = {}

        states[STATE.DOWNLOAD.value].piece_blocks[index][begin] = data

        if len(states[STATE.DOWNLOAD.value].piece_blocks[index]) == total_blocks:
            entire_piece = b''
            for offset in sorted(states[STATE.DOWNLOAD.value].piece_blocks[index].keys()):
                entire_piece += states[STATE.DOWNLOAD.value].piece_blocks[index][offset]

            expected_hash = states[STATE.METADATA.value].pieces[index * 20: (index + 1) * 20]
            actual_hash = hashlib.sha1(entire_piece).digest()

            if expected_hash == actual_hash:
                states[STATE.DOWNLOAD.value].downloaded.add(index)
                states[STATE.DOWNLOAD.value].downloading.discard(index)
                file_name = states[STATE.CLIENT.value].path + "\\"
                file_name += states[STATE.METADATA.value].file_name
                position = index * piece_length
                total_size = states[STATE.METADATA.value].length

                total_pieces = len(states[STATE.METADATA.value].pieces) // 20

                if index == total_pieces - 1:
                    expected_size = total_size - position
                    entire_piece = entire_piece[:expected_size]

                with open(file_name, "r+b") as f:
                    f.seek(position)
                    f.write(entire_piece)

                print(f"{Fore.GREEN} Piece {index} downloaded and saved at {position} {Fore.RESET}")

                del states[STATE.DOWNLOAD.value].piece_blocks[index]
            else:
                print(f"{Fore.RED} Piece {index} corrupted and therefore discarded {Fore.RESET}")


async def connect_to_peer(block_info, states, endpoint, handshake, info_hash, semaphore):
    ip, port = endpoint
    writer = None
    async with semaphore:
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=10)
            response = await send_handshake(handshake, writer, reader, info_hash)

            if response is None: raise Exception

            await send_interested(writer)

            peer_state = build_peer_state(is_choking=False)
            bitfield = set()

            while True:
                size, message_type, payload = await receive_message(reader)

                if message_type == MESSAGE.CHOKE.value:     # 0
                    peer_state.choking = True
                elif message_type == MESSAGE.UNCHOKE.value: # 1
                    peer_state.choking = False
                    if await answer_to_unchoke(states, bitfield, writer, block_info):
                        break
                elif message_type == MESSAGE.HAVE.value:    # 4
                    ...
                elif message_type == MESSAGE.BITFIELD.value:
                    bitfield = process_bitfield(payload)
                elif message_type == MESSAGE.REQUEST.value: # 6
                    ...
                elif message_type == MESSAGE.PIECE.value:   # 7
                    await answer_to_piece(payload, states, block_info)
                elif message_type == MESSAGE.CANCEL.value:  # 8
                    ...
                elif message_type == MESSAGE.PORT.value:    # 9
                    ...
        except asyncio.TimeoutError:
            print(Fore.RED + f"Peer did not respond" + Fore.RESET)
        except ConnectionError as c:
            print(Fore.RED + f"Connection error: {c}" + Fore.RESET)
        except Exception as e:
            print(Fore.RED + f"Unexpected error: {e}" + Fore.RESET)
        finally:
            if writer:
                writer.close()
                try:
                    await asyncio.wait_for(writer.wait_closed(), timeout=2)
                except (asyncio.TimeoutError, ConnectionResetError, OSError):
                    pass


async def connect_to_peers(block_info, states, endpoints, handshake, info_hash):
    MAX_CONNECTIONS = 30
    semaphore = asyncio.Semaphore(MAX_CONNECTIONS)
    tasks = [
        asyncio.create_task(
            connect_to_peer(block_info, states, endpoint, handshake, info_hash, semaphore)
        )
        for endpoint in endpoints
    ]
    await asyncio.gather(*tasks)


def contact_peer(decoded, response: dict, info_hash, peer_id):
    ips = get_ips(response)
    handshake = build_handshake(info_hash, peer_id)

    client_state = build_client_state(True, set(), r"C:\Users\soubr\OneDrive\Desktop")
    download_state = build_download_state(set(), set(), dict())
    metadata_state = build_metadata_state(decoded)

    states = [client_state, download_state, metadata_state]

    block_size = 16384
    piece_length = states[STATE.METADATA.value].pieces_length
    total_blocks = (piece_length + block_size - 1) // block_size

    block_info = [block_size, piece_length, total_blocks]

    file_name = states[STATE.CLIENT.value].path + "\\"
    file_name += states[STATE.METADATA.value].file_name
    file_length = states[STATE.METADATA.value].length
    with open(file_name, 'wb') as f:
        f.seek(file_length - 1)
        f.write(b'\0')

    asyncio.run(connect_to_peers(block_info, states, ips, handshake, info_hash))