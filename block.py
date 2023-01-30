from time import time


class Block:
    def __init__(self, index, previous_hash, transactions, proof, block_time=None):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = time() if block_time is None else block_time
        self.transactions = transactions
        self.proof = proof

    def __repr__(self):
        return f'Index: {self.index}, ' \
               f'Previous Hash: {self.previous_hash}, ' \
               f'Proof: {self.proof}, ' \
               f'Transactions: {self.transactions}'

    def get_savable_version(self):
        block_data = self.__dict__.copy()
        block_data['transactions'] = [tx.to_ordered_dict() for tx in block_data['transactions']]
        return block_data
