from hash_util import hash_string_256, hash_block


class Verification:
    @classmethod
    def valid_proof(cls, transactions, last_hash, proof):
        guess = (str([tx.to_ordered_dict() for tx in transactions]) + str(last_hash) + str(proof)).encode()
        guess_hash = hash_string_256(guess)
        return guess_hash.startswith('00')

    @classmethod
    def verify_chain(cls, blockchain):
        for index, block in enumerate(blockchain):
            if index == 0:
                continue
            if block.previous_hash != hash_block(blockchain[index - 1]):
                return False
            if not cls.valid_proof(block.transactions[:-1], block.previous_hash, block.proof):
                return False
        return True

    @classmethod
    def verify_transaction(cls, transaction, get_balance_callback):
        sender_balance = get_balance_callback(transaction.sender)
        return sender_balance >= transaction.amount

    @classmethod
    def verify_transactions(cls, open_transactions, get_balance_callback):
        return all([cls.verify_transaction(tx, get_balance_callback) for tx in open_transactions])
