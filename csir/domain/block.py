from csir.utils import clean_timestamp


class Block():
    def __init__(self, data):
        self.height = int(data['block_meta']['header']['height'])
        self.timestamp = clean_timestamp(data['block_meta']['header']['time'])
