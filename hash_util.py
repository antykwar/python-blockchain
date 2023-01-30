import hashlib as hl
import json


def hash_block(block):
    block_data = block.get_savable_version()
    return hash_string_256(json.dumps(block_data, sort_keys=True).encode())


def hash_string_256(string):
    return hl.sha256(string).hexdigest()
