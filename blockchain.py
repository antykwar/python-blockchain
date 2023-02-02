import json
from functools import reduce

from utilities.hash_util import HashUtil
from utilities.verification import Verification
from block import Block
from transaction import Transaction
from configuration import Configuration
from wallet import Wallet


class Blockchain:
    def __init__(self, hosting_node_id):
        self.hosting_node = hosting_node_id
        self.chain = [Block(
            index=0,
            previous_hash='',
            transactions=[],
            proof=0
        )]
        self.open_transactions = []
        self.load_data()

    @property
    def chain(self):
        return self.__chain[:]

    @chain.setter
    def chain(self, value):
        self.__chain = value

    @property
    def open_transactions(self):
        return self.__open_transactions[:]

    @open_transactions.setter
    def open_transactions(self, value):
        self.__open_transactions = value

    def load_data(self):
        try:
            with open(Configuration.BLOCKCHAIN_FILE, mode='r') as datastore:
                file_content = datastore.readlines()
                raw_blockchain_data = json.loads(file_content[0][:-1])
                self.__chain = [Block(
                    index=block['index'],
                    previous_hash=block['previous_hash'],
                    transactions=[
                        Transaction(tx['sender'], tx['recipient'], tx['amount'], tx['signature'])
                        for tx in block['transactions']
                    ],
                    proof=block['proof'],
                    block_time=block['timestamp']
                ) for block in raw_blockchain_data]
                raw_open_transactions_data = json.loads(file_content[1])
                self.__open_transactions = [
                    Transaction(tx['sender'], tx['recipient'], tx['amount'], tx['signature'])
                    for tx in raw_open_transactions_data
                ]
        except (IOError, IndexError):
            print('Error while reading blockchain data, assuming empty chain!')

    def save_data(self):
        try:
            with open(Configuration.BLOCKCHAIN_FILE, mode='w') as datastore:
                savable_blockchain = [block.get_savable_version() for block in self.__chain]
                datastore.write(json.dumps(savable_blockchain))
                datastore.write('\n')
                savable_transactions = [transaction.get_savable_version() for transaction in self.__open_transactions]
                datastore.write(json.dumps(savable_transactions))
        except IOError:
            print('Saving failed!')

    def proof_of_work(self):
        last_block = self.__chain[-1]
        last_hash = HashUtil.hash_block(last_block)
        proof = 0
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def get_balance(self):
        if self.hosting_node is None:
            return None
        total_sent = self.calculate_balance() + self.calculate_open_transactions()
        total_received = self.calculate_balance('recipient')
        return total_received - total_sent

    def calculate_balance(self, tx_type='sender'):
        known_type = None
        if tx_type in ('sender', 'recipient'):
            known_type = tx_type
        if known_type is None:
            return 0
        transactions_sums = [[tx.amount for tx in block.transactions if getattr(tx, known_type) == self.hosting_node]
                             for block in self.__chain]
        return reduce(lambda total_sum, current: total_sum + sum(current), transactions_sums, 0)

    def calculate_open_transactions(self, tx_type='sender'):
        known_type = None
        if tx_type in ('sender', 'recipient'):
            known_type = tx_type
        if known_type is None:
            return 0
        return sum([tx.amount for tx in self.__open_transactions if getattr(tx, known_type) == self.hosting_node])

    def get_last_blockchain_value(self):
        try:
            return self.__chain[-1]
        except IndexError:
            return None

    def add_transaction(self, recipient, sender, amount, signature):
        if self.hosting_node is None:
            return False
        transaction = Transaction(sender, recipient, amount, signature)
        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data()
            return True
        return False

    def mine_block(self):
        if self.hosting_node is None:
            return None
        last_block = self.__chain[-1]
        proof = self.proof_of_work()
        reward_transaction = Transaction(Configuration.MINING_SENDER, self.hosting_node, Configuration.MINING_REWARD, '')
        copied_transactions = self.__open_transactions[:]
        for tx in copied_transactions:
            if not Wallet.verify_transaction(tx):
                return None
        copied_transactions.append(reward_transaction)
        block = Block(
            index=len(self.__chain),
            previous_hash=HashUtil.hash_block(last_block),
            transactions=copied_transactions,
            proof=proof
        )
        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()
        return block
