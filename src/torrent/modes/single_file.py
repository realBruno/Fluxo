import requests

from src.torrent import metainfo, bencode


def submit(announce: bytes, payload: dict) -> dict:
    response = None
    for i in range(9):
        payload["port"] += i
        response = requests.get(announce, params=payload)
        decoded_response = bencode.decode(response.content)

        if b"failure reason" in decoded_response:
            print(f"FAILURE: {decoded_response[b"failure reason"]}")
            continue
        if b"warning message" in decoded_response:
            print(f"WARNING: {decoded_response[b"warning message"]}")
        if response.status_code == 200:
            return decoded_response
    raise ConnectionError(f"{[response.status_code]}: {response.reason}")


def single_file(decoded: dict, info_hash: str):
    payload = metainfo.tracker_payload(info_hash)
    payload["left"] = decoded[b"info"][b"length"]

    announce = decoded[b"announce"]
    response = submit(announce, payload)

    return payload, response