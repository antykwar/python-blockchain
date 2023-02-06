"""Verification methods for blockchain elements."""

from utilities.hash_util import HashUtil
from wallet import Wallet


class Verification:
    @staticmethod
    def valid_proof(transactions, last_hash, proof):
        guess = (str([tx.to_ordered_dict() for tx in transactions]) + str(last_hash) + str(proof)).encode()
        guess_hash = HashUtil.hash_string_256(guess)
        return guess_hash.startswith('00')

    @classmethod
    def verify_chain(cls, blockchain):
        for index, block in enumerate(blockchain):
            if index == 0:
                continue
            if block.previous_hash != HashUtil.hash_block(blockchain[index - 1]):
                return False
            if not cls.valid_proof(block.transactions[:-1], block.previous_hash, block.proof):
                return False
        return True

    @staticmethod
    def verify_transaction(transaction, get_balance_callback, check_funds=True):
        if check_funds:
            sender_balance = get_balance_callback(transaction.sender)
            return sender_balance >= transaction.amount and Wallet.verify_transaction(transaction)
        return Wallet.verify_transaction(transaction)

    @classmethod
    def verify_transactions(cls, open_transactions, get_balance_callback):
        return all([cls.verify_transaction(tx, get_balance_callback, check_funds=False) for tx in open_transactions])
