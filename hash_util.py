import hashlib as hl
import json


class HashUtil:
    @classmethod
    def hash_block(cls, block):
        block_data = block.get_savable_version()
        return cls.hash_string_256(json.dumps(block_data, sort_keys=True).encode())

    @staticmethod
    def hash_string_256(string):
        return hl.sha256(string).hexdigest()
