import asyncio
import math
from dataclasses import dataclass

import numpy as np


@dataclass
class Download:
    """Keeps track of information on the download."""
    file_size: int
    filename: str
    piece_length: int
    total_pieces: int
    # bitfield_size: int
    block_size = 16384
    pieces: bytes
    total_blocks: int

    interval: int
    complete: int
    incomplete: int

    downloading: np.ndarray
    downloaded: np.ndarray
    piece_blocks = dict()

    lock = asyncio.Lock()

def build_download(decoded: dict, tracker_response: dict) -> Download:
    info = decoded[b"info"]

    t_pieces = len(info[b"pieces"]) // 20

    d_complete = 0
    if b"complete" in tracker_response:
        d_complete = tracker_response[b"complete"]

    d_incomplete = 0
    if b"incomplete" in tracker_response:
        d_incomplete = tracker_response[b"incomplete"]

    piece_length = info[b"piece length"]
    block_size = 16384

    return Download(
        file_size = info[b"length"],
        filename = info[b"name"].decode(),
        piece_length = piece_length,
        total_pieces = t_pieces,
        interval = tracker_response[b"interval"],
        complete = d_complete,
        incomplete = d_incomplete,
        # bitfield_size = math.ceil(t_pieces / 8),
        downloaded = np.zeros(t_pieces, dtype=bool),
        downloading = np.zeros(t_pieces, dtype=bool),
        pieces = info[b"pieces"],
        total_blocks = (piece_length + block_size - 1) // block_size
    )