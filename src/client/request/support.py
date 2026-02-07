""" Auxiliary functions for both single and multiple file modes"""
import hashlib
import random
import binascii

from client.bencode.decoder import decode
from client.bencode.encoder import encode

def get_file_info(path: str) -> tuple[dict, str, int]:
    decoded = decode(path)
    info_hash = hashlib.sha1(encode(decoded[b"info"])).digest().hex()
    single_file = b"files" not in decoded[b"info"]

    return decoded, info_hash, single_file

def payload(info_hash: str) -> dict:
    client_id = "PY"
    client_version = "0001"
    query = {
        "info_hash": binascii.unhexlify(info_hash),
        "peer_id": '-' + client_id + client_version + '-' + ''.join(str(random.randint(0, 9)) for _ in range(12)),
        "port": 6881,
        "uploaded": 0,
        "downloaded": 0,
        "left": 0,
        "compact": 1,
        "no_peer_id": 0, # ignored if compact is available
        "event": "started",
    }

    return query