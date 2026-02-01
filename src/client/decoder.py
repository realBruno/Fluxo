def iterate(contents: str, index, caller='b'):
    if caller == 'i':
        index += 1
    number = ''
    while contents[index].isdigit():
        number += contents[index]
        index += 1
    number = int(number)
    return number, index + 1

def read(path: str):
    path = path.replace('\"', '')
    try:
        with open(path, "rb") as file:
            return file.read()
    except (OSError, UnicodeDecodeError) as e:
        raise ValueError("File invalid or inaccessible") from e

def parse(contents: str, index: int):
    try:
        if contents[index] == 'd':
            index += 1
            d = dict()
            while contents[index] != 'e':
                key = parse(contents, index)
                value = parse(contents, key[1])
                d[key[0]] = value[0]
                index = value[1]
            return d, index + 1

        elif contents[index] == 'l':
            index += 1
            l = list()
            while contents[index] != 'e':
                value = parse(contents, index)
                l.append(value[0])
                index = value[1]
            return l, index + 1

        elif contents[index] == 'i':
            return iterate(contents, index, 'i')

        elif contents[index].isdigit():
            length, index = iterate(contents, index)
            string = contents[index: index + length]
            return string, index + length

    except Exception as e:
        raise ValueError("Invalid torrent file") from e

def decode(path: str):
    contents = read(path).decode("latin-1")
    decoded = parse(contents, 0)[0]
    return decoded