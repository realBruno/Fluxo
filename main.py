"""
    Torrent client program.
    Author: Bruno Fernandes (github.com/realBruno)
    Date: 24/jan/2026
"""
import sys

from torrent import metainfo
from torrent.modes.single_file import single_file
from peer.connections import contact_peer

def make_request(path: str):
    print("Parsing torrent file metadata")
    decoded, info_hash, is_single = metainfo.get_file_info(path)
    if is_single:
        print("Building tracker payload and making request")
        t_payload, t_response = single_file(decoded, info_hash)
        print("Establishing connection with peers")
        contact_peer(decoded, t_response, t_payload)
    else:
        raise TypeError("Multi-file mode is under development")


def get_path():
    if len(sys.argv) == 2:
        return sys.argv[1]
    elif len(sys.argv) == 1:
        return input("Path to file: ")
    else:
        raise TypeError(f"Takes exactly 1 argument. {len(sys.argv) - 1} given.")


file_loc = get_path()
make_request(file_loc)