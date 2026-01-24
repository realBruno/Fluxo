class BencodeParser:
    main_dictionary: dict = {}
    is_key: bool = True # checks if entry is key or value in dictionary
    key = None
    MAX_PRINTABLE: int = 127  # maximum possible decimal value for a printable char in the ASCII table

    @staticmethod
    def byte_string(file_content : str, index : int) -> list:
        length = ""
        while (char := file_content[index]).isnumeric():
            length += char
            index += 1
        index += 1 # skips :

        length = int(length)

        string = ""
        to_hex = False
        for i in range(length):
            string += file_content[index]
            if ord(file_content[index]) > 127:
                to_hex = True
            index += 1

        if to_hex:
            string = ' '.join(f'{b:02x}' for b in string.encode("latin-1"))

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
            return_value = dict()

            while file_content[index] != 'e':
                key = BencodeParser.decider(file_content, index)
                value = BencodeParser.decider(file_content, key[1])
                return_value[key[0]] = value[0]
                index = value[1]

            index += 1

            return [return_value, index]

        elif file_content[index] == 'l':
            index += 1
            local_list = []

            while file_content[index] != 'e':
                returned_value = BencodeParser.decider(file_content, index)
                local_list.append(returned_value[0])
                index = returned_value[1]

            index += 1
            return [local_list, index]

        elif file_content[index] == 'i':
            returned_value = BencodeParser.integer(file_content, index) # -> [integer, i]
            return returned_value

        else:
            returned_value = BencodeParser.byte_string(file_content, index) # -> ["string", i]
            return returned_value

    @staticmethod
    def decode(filename : str):
        try:
            with (open(filename, "rb") as file):
                file_content = ""

                for line in file.read():
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
                        BencodeParser.main_dictionary[BencodeParser.key] = returned_value[0]
                        BencodeParser.is_key = True

                    index = int(returned_value[1])
        except (OSError, UnicodeDecodeError) as e:
            raise ValueError("File invalid or inaccessible") from e

        return BencodeParser.main_dictionary