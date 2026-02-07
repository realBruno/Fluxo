import sys

from client.request.mode import single
from client.bencode import decoder
from client.request import peer
from client.request import support

def make_request(path: str):
    decoded, info_hash, is_single = support.get_file_info(path)
    announce = decoded[b"announce"]
    if is_single:
        payload = single.torrent(decoded, info_hash)
        response = single.submit(announce, payload)
        response = decoder.parse(response, 0)[0]
        peer.handshake(response)
    else:
        raise TypeError("Multi-file mode is under development")

def get_path():
    if len(sys.argv) == 2:
        path = sys.argv[1]
    elif len(sys.argv) == 1:
        path = input()
    else:
        raise TypeError(f"Takes exactly 1 argument. {len(sys.argv) - 1} given.")

    make_request(path)