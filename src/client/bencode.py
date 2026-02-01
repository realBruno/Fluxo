class Bencode:
    @staticmethod
    def iterator(contents: str, index, caller='b'):
        if caller == 'i':
            index += 1
        number = ''
        while contents[index].isdigit():
            number += contents[index]
            index += 1
        number = int(number)
        return number, index + 1

    @staticmethod
    def read(path: str):
        path = path.replace('\"', '')
        try:
            with open(path, "rb") as file:
                return file.read()
        except (OSError, UnicodeDecodeError) as e:
            raise ValueError("File invalid or inaccessible") from e

    @classmethod
    def parser(cls, contents: str, index: int):
        try:
            if contents[index] == 'd':
                index += 1
                d = dict()
                while contents[index] != 'e':
                    key = cls.parser(contents, index)
                    value = cls.parser(contents, key[1])
                    d[key[0]] = value[0]
                    index = value[1]
                return d, index + 1
            elif contents[index] == 'l':
                index += 1
                l = list()
                while contents[index] != 'e':
                    value = cls.parser(contents, index)
                    l.append(value[0])
                    index = value[1]
                return l, index + 1
            elif contents[index] == 'i':
                return cls.iterator(contents, index, 'i')
            elif contents[index].isdigit():
                length, index = cls.iterator(contents, index)
                string = contents[index: index + length]
                return string, index + length
        except Exception as e:
            raise ValueError("Invalid torrent file") from e

    @classmethod
    def decode(cls, path):
        contents = cls.read(path).decode("latin-1")
        decoded = cls.parser(contents, 0)[0]
        return decoded