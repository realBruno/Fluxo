from dataclasses import dataclass

@dataclass
class Client:
    peer_id: bytes
    keep_alive: int