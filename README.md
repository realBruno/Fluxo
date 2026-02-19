# Fluxo 🌊

A BitTorrent client built from scratch in Python, implementing the core BitTorrent protocol without relying on existing torrent libraries.

## Overview

Fluxo is a educational BitTorrent client that demonstrates how peer-to-peer file sharing works at a fundamental level. It handles parsing .torrent files, communicating with trackers, coordinating with multiple peers simultaneously, and reconstructing files from distributed pieces.

## Features

✅ **Complete BitTorrent Protocol Implementation**
- Bencode encoding/decoding for .torrent files
- Tracker communication (HTTP/HTTPS)
- Peer handshakes and message protocol
- Piece validation via SHA1 hashing

✅ **Asynchronous Architecture**
- Concurrent connections to 30+ peers
- Non-blocking I/O with asyncio
- Efficient coordination with locks and semaphores

✅ **Robust Download Management**
- Automatic piece selection and distribution
- Block-level downloads (16KB chunks)
- Corruption detection and retry logic
- Progress tracking with bitfields

✅ **Single-File Mode**
- Download individual files
- Automatic file creation and positioning
- Last piece handling for variable sizes

## Project Structure
```
fluxo/
├── client/
│   └── client.py           # Client configuration
├── peer/
│   ├── connections.py      # Peer connection management
│   ├── messages.py         # BitTorrent message types
│   ├── peer.py            # Peer state tracking
│   └── protocol.py        # Protocol implementation
├── torrent/
│   ├── bencode.py         # Bencode parser
│   ├── download.py        # Download state management
│   ├── metainfo.py        # Torrent metadata
│   └── modes/
│       └── single_file.py # Single-file download logic
└── tracker/
    └── endpoints.py       # Tracker communication
```

## Technical Stack

- **Python 3.14+**
- **asyncio** - Asynchronous I/O
- **numpy** - Efficient bitfield operations
- **struct** - Binary data manipulation
- **hashlib** - SHA1 validation
- **colorama** - Terminal colors

## How It Works

### 1. Parse Torrent File
```python
# Decode .torrent file (Bencode format)
decoded = bencode.decode(torrent_file)
metainfo = extract_metadata(decoded)
```

### 2. Contact Tracker
```python
# Get list of peers from tracker
response = tracker.announce(info_hash, peer_id)
peers = extract_peer_addresses(response)
```

### 3. Connect to Peers
```python
# Establish connections asynchronously
for peer in peers:
    - Send handshake
    - Exchange bitfields
    - Send interested message
```

### 4. Download Pieces
```python
# Coordinate parallel downloads
while not complete:
    - Select next piece
    - Request blocks (16KB each)
    - Validate SHA1 hash
    - Write to disk
```

### 5. Reconstruct File
```python
# Assemble pieces in correct order
for piece_index in range(total_pieces):
    position = piece_index * piece_length
    write_to_file(position, piece_data)
```

## Core Components

### Peer Protocol

The `PeerProtocol` class handles all BitTorrent peer wire protocol messages:

- **Handshake**: Initial connection establishment
- **Interested/Not Interested**: Signal willingness to download
- **Choke/Unchoke**: Flow control mechanism
- **Have**: Announce piece availability
- **Bitfield**: Share complete piece inventory
- **Request**: Ask for specific blocks
- **Piece**: Deliver requested data

### Message Format

All messages follow this structure:
```
[4 bytes: length] [1 byte: message_id] [variable: payload]
```

Example - Request message:
```
[13] [6] [piece_index] [begin_offset] [block_length]
```

## Installation
```bash
# Clone repository
git clone https://github.com/realBruno/fluxo.git
cd fluxo

# Install dependencies
pip install -r requirements.txt

# Run
python main.py path/to/file.torrent
```

## Usage
```python
from client.connections import contact_peer

# Load torrent file
decoded = bencode.decode("example.torrent")

# Get tracker response
tracker_response = tracker.announce(...)

# Start download
contact_peer(decoded, tracker_response, tracker_payload)
```

## Implementation Details

### Bitfield Operations

Efficient piece tracking using NumPy:
```python
# Check if piece is available
if peer.bitfield[piece_index]:
    ...

# Mark piece as downloaded
download.downloaded[piece_index] = True

# Find missing pieces
missing = np.where(~download.downloaded)[0]
```

### Asynchronous Coordination

Multiple peers download different pieces simultaneously:
```python
async with download.lock:
    # Atomic operation: select next piece
    for piece_index in range(total_pieces):
        if available and not downloaded and not downloading:
            download.downloading[piece_index] = True
            break
```

### SHA1 Validation

Every piece is validated before saving:
```python
expected_hash = pieces[index * 20:(index + 1) * 20]
actual_hash = hashlib.sha1(piece_data).digest()

if expected_hash != actual_hash:
    discard_piece()  # Retry from different peer
else:
    save_to_disk()
```

### Keep-Alive Mechanism

Maintains connections with periodic messages:
```python
async def keep_alive_loop(interval=60):
    while True:
        await asyncio.sleep(interval)
        if time.since_last_message >= interval:
            send_keep_alive()
```

## Limitations

⚠️ **Current Limitations:**
- Single-file mode only (no multi-file torrents)
- HTTP/HTTPS trackers only (no UDP support)
- Download only (no seeding/uploading)
- No DHT support
- No magnet links
- No encryption

## Roadmap

🔮 **Planned Features:**
- [ ] Multi-file torrent support
- [ ] UDP tracker protocol
- [ ] DHT (Distributed Hash Table)
- [ ] Upload/seeding capability
- [ ] Magnet link support
- [ ] Resume interrupted downloads
- [ ] Piece selection optimization (rarest first)
- [ ] Protocol encryption
- [ ] Web UI for monitoring

## Architecture Decisions

### Why asyncio?

BitTorrent clients spend most time waiting for network I/O. Asyncio allows handling dozens of peer connections efficiently without threads.

### Why NumPy for bitfields?

NumPy provides:
- Compact memory representation (1 bit per piece)
- Fast bitwise operations
- Easy conversion to/from bytes for protocol messages

### Why separate Download state?

Shared state ensures:
- No duplicate downloads across peers
- Thread-safe coordination with locks
- Easy progress tracking

## Performance Considerations

- **Connection limit**: 30 concurrent peers (configurable)
- **Block size**: 16KB (standard)
- **Timeout**: 10s for connections, 60s for messages
- **Keep-alive**: Every 60 seconds

## Troubleshooting

**"Peer did not respond"**
- Peer may be offline or firewalled
- Increase connection timeout

**"Invalid block" / "Hash mismatch"**
- Peer sent corrupted data
- Piece will be re-requested from different peer

**"Connection refused"**
- Port may be blocked
- Try different peers from tracker

**Download stalls**
- Not enough active peers
- Request more peers from tracker

## License

MIT License - See LICENSE file for details

## Author

Bruno Fernandes  
[GitHub](https://github.com/realBruno) | [LinkedIn](https://linkedin.com/in/your-profile)

---

**Note**: This is a learning project. For production use, consider established clients like qBittorrent, Transmission, or Deluge.