from stack import Stack

class BencodeParser:
    """
        Byte string and integer methods are like base cases;
        List and dictionary methods are like recursive steps
    """

    stack = Stack()
    main_list = []
    main_dictionary = {}
    is_key = True
    key = ""

    @staticmethod
    def byte_string(file_content, index):
        index += 1
        length = ""
        while (char := file_content[index]).isnumeric():
            length += char
            index += 1

        length = int(length)
        index += 1  # so it skips character ':'

        string = ""
        while length > 0:
            string += file_content[index]
            length -= 1
            index += 1
        return [string, index + 1]

    @staticmethod
    def integer(file_content, index):
        index += 1
        integer = ""
        while (char := file_content[index]).isnumeric():
            integer += char
            index += 1
        return [int(integer), index + 1]

    @staticmethod
    def dictionary_or_list(file_content, index):
        index += 1
        match file_content[index]:
            case 'd', 'l': return BencodeParser.dictionary_or_list(file_content, index)
            case 'i': return BencodeParser.integer(file_content, index)
            case '1', '2', '3', '4', '5', '6', '7', '8', '9':
                return BencodeParser.byte_string(file_content, index)
        return []

    @staticmethod
    def decode(filename):
        with open(filename, "rb") as file: # test_file.torrent
            file_content = str(file.read())
            i = 0
            BencodeParser.stack.push(file_content[0])
            while (char := file_content[i]) != 'e':
                # match BencodeParser.stack.peek():
                #     case 'd': # create a new dictionary
                returned_value = BencodeParser.dictionary_or_list(file_content[i:], i)

                if BencodeParser.is_key:
                    BencodeParser.key = returned_value[0]
                    BencodeParser.is_key = False
                else:
                    BencodeParser.is_key = True
                    BencodeParser.main_dictionary[BencodeParser.key] = returned_value[0]

                i = returned_value[1]
            else:
                BencodeParser.stack.pop()