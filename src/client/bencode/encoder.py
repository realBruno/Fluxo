def value(v: list | dict | bytes | int):
    content = b''
    match v:
        case list():
            content += b'l'
            for item in v:
                content += value(item)
            content += b'e'
        case dict():
            content += b'd'
            for key, val in v.items():
                content += value(key)
                content += value(val)
            content += b'e'
        case int():
            content += b'i' + str(v).encode() + b'e'
        case bytes():
            content += str(len(v)).encode() + b':' + v

    return content

def encode(parsed: dict):
    if type(parsed) != dict:
        raise ValueError("Data is not a dictionary")

    bencoded = b'd'
    for k, v in parsed.items():
        bencoded += str(len(k)).encode() + b':' + k
        bencoded += value(v)
    bencoded += b'e'
    return bencoded