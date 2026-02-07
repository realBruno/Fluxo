import requests
from requests import Response

from src.client.request import support_request

def submit(decoded: dict, hashed: str, queries: dict, announce: str) -> Response:
    for i in range(9): # make 9 attempts to connect before giving up
        queries["port"] += i
        response = requests.get(announce, params=support_request.payload(decoded, hashed))
        if response.status_code == 200:
            return response
    raise ConnectionError("Could not establish connection with server")

def torrent(decoded: dict, hashed: str):
    announce = (decoded[b"announce"]).decode("utf-8")
    queries = support_request.payload(decoded, hashed)

    # adjust query params
    queries["left"] = decoded[b"info"][b"length"]

    submit(decoded, hashed, queries, announce)