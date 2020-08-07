from csir.utils import clean_timestamp


class Block():
    def __init__(self, data):
        self.__data = data
        self.height = int(self.header()['height'])
        self.timestamp = clean_timestamp(self.header()['time'])

    def header(self):
        if 'block_meta' in self.__data:
            return self.__data['block_meta']['header']
        else:
            return self.__data['block']['header']
