from stack import Stack

MAX_PRINTABLE = 127 # maximum possible decimal value for a printable char in the ASCII table

class BencodeParser:
    stack = Stack()
    main_list = []
    main_dictionary = {}

    @staticmethod
    def byte_string(file_content, index):
        length = ""
        while (char := file_content[index]).isnumeric():
            length += char
            index += 1

        length = int(length)

        index += 1 # so it skips :

        string = ""
        while length > 0:
            string += file_content[index]
            length -= 1
            index += 1
        return [string, index]

    @staticmethod
    def integer(file_content, index):
        index += 1
        integer = ""
        while (char := file_content[index]).isnumeric():
            integer += char
            index += 1
        return [int(integer), index]

    @staticmethod
    def structure(file_content, index):
        print("Structure")
        """To use with lists or dictionaries"""
        index += 1
        match file_content[index]:
            case 'd', 'l': return BencodeParser.structure(file_content, index)
            case 'i': return BencodeParser.integer(file_content, index)
            case '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9':
                return BencodeParser.byte_string(file_content, index)
        return []

    @staticmethod
    def decode(filename):
        with open(filename, "rb") as file: # test_file.torrent
            file_content = ""

            for line in file.read():
                if line > MAX_PRINTABLE:
                    break
                file_content += chr(line)

            returned_value = BencodeParser.structure(file_content, 0)

            print(returned_value)

BencodeParser.decode(input())