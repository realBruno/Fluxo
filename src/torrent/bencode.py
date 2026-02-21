# DECODE FUNCTIONS
def decode(path: str | bytes):
    contents = read(path) if type(path) is str else path
    decoded = parse(contents, 0)[0]
    return decoded


def iterate(contents: bytes, index, caller='b'):
    negative = 1
    if caller == 'i':
        index += 1
        if contents[index] == 45:
            negative = -1
            index += 1
    number = bytearray()
    while 48 <= contents[index] <= 57:
        number.append(contents[index])
        index += 1
    number = int(number) * negative
    return number, index + 1


def read(path: str):
    path = path.replace('\"', '')
    try:
        with open(path, "rb") as file:
            return file.read()
    except (OSError, UnicodeDecodeError) as e:
        raise ValueError("File invalid or inaccessible") from e


def parse(contents: bytes, index: int):
    try:
        if contents[index] == ord('d'):
            index += 1
            d = dict()
            while contents[index] != ord('e'):
                key = parse(contents, index)
                value = parse(contents, key[1])
                d[key[0]] = value[0]
                index = value[1]
            return d, index + 1
        elif contents[index] == ord('l'):
            index += 1
            l = list()
            while contents[index] != ord('e'):
                value = parse(contents, index)
                l.append(value[0])
                index = value[1]
            return l, index + 1
        elif contents[index] == ord('i'):
            return iterate(contents, index, 'i')
        elif 48 <= contents[index] <= 57:
            length, index = iterate(contents, index)
            string = contents[index: index + length]
            return string, index + length
    except Exception as e:
        raise ValueError("Invalid torrent file") from e


# ENCODE FUNCTIONS
def encode(parsed: dict):
    if type(parsed) != dict:
        raise ValueError("Data is not a dictionary")
    bencoded = b'd'
    for k, v in parsed.items():
        bencoded += str(len(k)).encode() + b':' + k
        bencoded += data(v)
    bencoded += b'e'
    return bencoded


def data(v: list | dict | bytes | int):
    content = b''
    match v:
        case list():
            content += b'l'
            for item in v:
                content += data(item)
            content += b'e'
        case dict():
            content += b'd'
            for key, val in v.items():
                content += data(key)
                content += data(val)
            content += b'e'
        case int():
            content += b'i' + str(v).encode() + b'e'
        case bytes():
            content += str(len(v)).encode() + b':' + v
    return content
