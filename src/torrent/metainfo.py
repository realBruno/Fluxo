import hashlib
import random
import binascii

from src.torrent import bencode


def get_file_info(path: str) -> tuple[dict, str, bool]:
    decoded = bencode.decode(path)
    info_hash = hashlib.sha1(bencode.encode(decoded[b"info"])).digest().hex()
    is_single = b"files" not in decoded[b"info"]
    return decoded, info_hash, is_single


def tracker_payload(info_hash: str) -> dict:
    id_version = "PY0001"
    rand_int = ''.join(str(random.randint(0, 9)) for _ in range(12))
    return {
        "info_hash": binascii.unhexlify(info_hash),
        "peer_id": '-' + '-'.join((id_version, rand_int)),
        "port": 6881,
        "uploaded": 0,
        "downloaded": 0,
        "compact": 1,
        "event": "started"
    }