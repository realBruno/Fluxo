from stack import Stack



class BencodeParser:
    stack = Stack()
    main_dictionary = {}
    is_key = True # checks if entry is key or value in dictionary
    key = ""
    FINAL_STRUCTURE = []
    MAX_PRINTABLE = 127  # maximum possible decimal value for a printable char in the ASCII table
    MAX_INDEX = 0 # stores length of bencode string

    @staticmethod
    def byte_string(file_content : str, index : int):
        length = ""
        while (char := file_content[index]).isnumeric():
            length += char
            index += 1

        length = int(length)

        index += 1 # skips ':'

        string = ""
        while length > 0:
            string += file_content[index]
            length -= 1
            index += 1
        return [string, index]

    @staticmethod
    def integer(file_content : str, index : int):
        index += 1
        integer = ""
        while (char := file_content[index]).isnumeric():
            integer += char
            index += 1
        return [int(integer), index]

    @staticmethod
    def structure(file_content : str, index : int):
        match file_content[index]:
            case 'd', 'l':
                index += 1
                return BencodeParser.structure(file_content, index)
            case 'i':
                return BencodeParser.integer(file_content, index)
            case '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9':
                return BencodeParser.byte_string(file_content, index)

    @staticmethod
    def decode(filename):
        with open(filename, "rb") as file: # test_file.torrent
            file_content = ""

            for line in file.read(): # reads characters of torrent until it finds a non-printable character
                if line > BencodeParser.MAX_PRINTABLE:
                    break
                file_content += chr(line)
                BencodeParser.MAX_INDEX += 1

            index = 1
            BencodeParser.stack.push(file_content[0])

            while BencodeParser.stack.peek(): # peek method returns None if empty
                match BencodeParser.stack.peek():
                    case 'd': # dictionary
                        returned_value = BencodeParser.structure(file_content, index)
                        if BencodeParser.is_key:
                            BencodeParser.key = returned_value[0]
                            BencodeParser.is_key = False
                        else:
                            BencodeParser.is_key = True
                            BencodeParser.main_dictionary[BencodeParser.key] = returned_value[0]
                    case 'l': # list
                        BencodeParser.structure(file_content, index)
                    case 'i': # integer
                        BencodeParser.integer(file_content, index)
                    case '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9': # byte string
                        returned_value = BencodeParser.byte_string(file_content, index)
                        index = returned_value[1] + 1

                if file_content[index] == 'e':
                    BencodeParser.stack.pop()
                else:
                    BencodeParser.stack.push(file_content[index])


BencodeParser.decode(input())