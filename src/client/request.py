import requests
import random
import hashlib
import binascii
from urllib.parse import quote_from_bytes

from client.bencode.decoder import decode
from client.bencode.encoder import encode

def get_file_info(path: str) -> tuple[dict, str]:
    decoded = decode(path)
    return decoded, hashlib.sha1(encode(decoded[b"info"])).digest().hex()

def payload(decoded: dict, hashed: str) -> dict:
    """Returns query params"""
    client_id = "PY"
    client_version = "0001"

    print(decoded)

    query = {
        "info_hash": binascii.unhexlify(hashed),
        "peer_id": '-' + client_id +  client_version + '-' +
                   ''.join(str(random.randint(0, 9)) for _ in range(12)),
        "port": 6881, #[port for port in range(6881, 6890)],
        "uploaded": 0,
        "downloaded": 0,
        "left": 4733116416,
        "compact": 1,
        #"no_peer_id": 0, # ignored if compact is available
        # "event": "started",
        # "ip": "",
        # "numwant": "",
        # "key": "",
        # "trackerid": "",
    }

    return query

def torrent(decoded: dict, hashed: str):
    announce = (decoded[b"announce"]).decode("utf-8")
    queries = payload(decoded, hashed)

    response = requests.get(announce, params=payload(decoded, hashed))
    print(response.url)
    print(response.text)