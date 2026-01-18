from copy import deepcopy
from stack import Stack

class BencodeParser:
    stack = Stack()
    main_dictionary = {}
    template_list = []
    is_key = True # checks if entry is key or value in dictionary
    key = ""
    MAX_PRINTABLE = 127  # maximum possible decimal value for a printable char in the ASCII table

    @staticmethod
    def byte_string(file_content : str, index : int) -> list:
        length = ""
        while (char := file_content[index]).isnumeric():
            length += char
            index += 1
        index += 1 # skips :
        length = int(length)

        string = ""
        for i in range(length):
            string += file_content[index]
            index += 1
        return [string, index]

    @staticmethod
    def integer(file_content : str, index : int) -> list:
        index += 1
        integer = ""
        while (char := file_content[index]) != 'e':
            integer += char
            index += 1
        index += 1 # skips 'e'
        return [int(integer), index]

    @staticmethod
    def decider(file_content : str, index : int):
        if file_content[index] == 'd':
            index += 1

            key = BencodeParser.decider(file_content, index)
            index = key[1]

            value = BencodeParser.decider(file_content, index)
            index = value[1]

            return_value = {
                key[0] : value[0]
            }

            return [return_value, index]

        elif file_content[index] == 'l':
            index += 1

            while file_content[index] != 'e':
                return_value = BencodeParser.decider(file_content, index)
                index = return_value[1]
                BencodeParser.template_list.append(return_value[0])
            index += 1

            aux = deepcopy(BencodeParser.template_list)
            BencodeParser.template_list.clear()

            return [aux, index] # -> [[], i]

        elif file_content[index] == 'i':
            returned_value = BencodeParser.integer(file_content, index) # -> [integer, i]
            index = returned_value[1]
            return returned_value

        elif file_content[index].isnumeric():
            returned_value = BencodeParser.byte_string(file_content, index) # -> ["bencode", i]
            index = returned_value[1]
            return returned_value

    @staticmethod
    def decode(filename : str) -> dict:
        with open(filename, "rb") as file: # test_file.torrent
            file_content = ""

            for line in file.read(): # reads characters of torrent until it finds a non-printable character
                if line > BencodeParser.MAX_PRINTABLE:
                    break
                file_content += chr(line)

            if file_content[0] != 'd':
                raise TypeError("Not a torrent file.")

            index = 1
            while file_content[index] != 'e':
                returned_value = BencodeParser.decider(file_content, index)
                if BencodeParser.is_key:
                    BencodeParser.key = returned_value[0]
                    BencodeParser.is_key = False
                else:
                    BencodeParser.is_key = True
                    BencodeParser.main_dictionary[BencodeParser.key] = returned_value[0]

                index = int(returned_value[1])

        return BencodeParser.main_dictionary

BencodeParser.decode(input())
print(BencodeParser.main_dictionary)