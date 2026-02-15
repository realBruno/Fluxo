import struct
import socket
from colorama import Fore

def get_ips(response: dict):
    ips = []
    peers = response[b"peers"]

    if type(peers) == dict:
        return ips

    for i in range(0, len(peers) - 6, 6):
        chunk = peers[i: i + 6]
        ip = '.'.join(str(b) for b in chunk[0:4])
        if ip != "127.0.0.1":
            port = struct.unpack("!H", chunk[4: 6])[0]
            ips.append((ip, port))

    return ips


def build_handshake(info_hash, peer_id):
    pstr = b"BitTorrent protocol"
    pstrlen = len(pstr).to_bytes(1, byteorder="big")
    reserved = bytes(8)
    info_hash = info_hash
    peer_id = peer_id.encode()

    return pstrlen + pstr + reserved + info_hash + peer_id


def connect_to_peer(endpoints, info_hash, peer_id):
    for endpoint in endpoints:
        print(f"Connecting to peer at {endpoint[0]} via {endpoint[1]}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            sock.connect(endpoint)
            sock.send(build_handshake(info_hash, peer_id))
            response = sock.recv(68)
            if len(response) < 68:
                print(Fore.YELLOW +
                      "Peer responded with malformed answer." + Fore.RESET)
            else:
                print(Fore.GREEN + "Peer responded successfully." + Fore.RESET)
        except socket.error:
            print(Fore.RED + "Peer did not respond in time" + Fore.RESET)
            continue
        finally:
            sock.close()


def contact_peer(response: dict, info_hash, peer_id):
    ips = get_ips(response)
    connect_to_peer(ips, info_hash, peer_id)
    return ips