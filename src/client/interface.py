import sys
from client.bencode import decode

def interface():
    if len(sys.argv) == 2:
        path = sys.argv[1]
        parsed = decode(path)
    elif len(sys.argv) == 1:
        path = input()
        parsed = decode(path)
    else:
        raise TypeError(f"Takes exactly 1 argument. {len(sys.argv) - 1} given.")

    return parsed

if __name__ == '__main__':
    ...