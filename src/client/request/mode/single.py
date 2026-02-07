import requests
from requests import Response

from src.client.request import support

def submit(announce: str, payload: dict) -> bytes:
    for i in range(9): # make 9 attempts to connect before giving up
        payload["port"] += i
        response = requests.get(announce, params=payload)
        if response.status_code == 200:
            return response.content

    raise ConnectionError("Could not establish connection with server")

def torrent(decoded: dict, info_hash: str):
    announce = (decoded[b"announce"]).decode("utf-8")
    payload = support.payload(info_hash)

    # adjust query params
    payload["left"] = decoded[b"info"][b"length"]

    return payload