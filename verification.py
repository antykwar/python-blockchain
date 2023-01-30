class Verification:
    def verify_chain():
        for index, block in enumerate(blockchain):
            if index == 0:
                continue
            if block.previous_hash != hash_block(blockchain[index - 1]):
                return False
            if not valid_proof(block.transactions[:-1], block.previous_hash, block.proof):
                return False
        return True
