import json
from functools import reduce
import requests

from utilities.hash_util import HashUtil
from utilities.verification import Verification
from block import Block
from transaction import Transaction
from configuration import Configuration
from wallet import Wallet


class Blockchain:
    def __init__(self, hosting_node_id, network_id=None):
        self.hosting_node = hosting_node_id
        self.resolve_conflicts = False
        self.network_id = network_id if network_id is not None else ''
        self.chain = [Block(
            index=0,
            previous_hash='',
            transactions=[],
            proof=0,
            block_time=0
        )]
        self.open_transactions = []
        self.__peer_nodes = set()
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
            with open(Configuration.BLOCKCHAIN_FILE + str(self.network_id), mode='r') as datastore:
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
                raw_open_transactions_data = json.loads(file_content[1][:-1])
                self.__open_transactions = [
                    Transaction(tx['sender'], tx['recipient'], tx['amount'], tx['signature'])
                    for tx in raw_open_transactions_data
                ]
                self.__peer_nodes = set(json.loads(file_content[2]))
        except (IOError, IndexError):
            print('Error while reading blockchain data, assuming empty chain!')

    def save_data(self):
        try:
            with open(Configuration.BLOCKCHAIN_FILE + str(self.network_id), mode='w') as datastore:
                savable_blockchain = [block.get_savable_version() for block in self.__chain]
                datastore.write(json.dumps(savable_blockchain))
                datastore.write('\n')
                savable_transactions = [transaction.get_savable_version() for transaction in self.__open_transactions]
                datastore.write(json.dumps(savable_transactions))
                datastore.write('\n')
                datastore.write(json.dumps(list(self.__peer_nodes)))
        except IOError:
            print('Saving failed!')

    def proof_of_work(self):
        last_block = self.__chain[-1]
        last_hash = HashUtil.hash_block(last_block)
        proof = 0
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def get_balance(self, sender=None):
        if sender is None:
            if self.hosting_node is None:
                return None
            participant = self.hosting_node
        else:
            participant = sender
        total_sent = self.calculate_balance(participant) + self.calculate_open_transactions(participant)
        total_received = self.calculate_balance(participant, tx_type='recipient')
        return total_received - total_sent

    def calculate_balance(self, participant, tx_type='sender'):
        known_type = None
        if tx_type in ('sender', 'recipient'):
            known_type = tx_type
        if known_type is None:
            return 0
        transactions_sums = [[tx.amount for tx in block.transactions if getattr(tx, known_type) == participant]
                             for block in self.__chain]
        return reduce(lambda total_sum, current: total_sum + sum(current), transactions_sums, 0)

    def calculate_open_transactions(self, participant, tx_type='sender'):
        known_type = None
        if tx_type in ('sender', 'recipient'):
            known_type = tx_type
        if known_type is None:
            return 0
        return sum([tx.amount for tx in self.__open_transactions if getattr(tx, known_type) == participant])

    def get_last_blockchain_value(self):
        try:
            return self.__chain[-1]
        except IndexError:
            return None

    def mine_block(self):
        if self.hosting_node is None:
            return None
        last_block = self.__chain[-1]
        proof = self.proof_of_work()
        reward_transaction = Transaction(Configuration.MINING_SENDER, self.hosting_node, Configuration.MINING_REWARD,
                                         '')
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
        if not self.notify_peer_nodes_about_block(block):
            pass
        return block

    def add_transaction(self, recipient, sender, amount, signature, is_receiving=False):
        transaction = Transaction(sender, recipient, amount, signature)
        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data()
            if not is_receiving:
                if not self.notify_peer_nodes_about_transaction(transaction):
                    return False
            return True
        return False

    def notify_peer_nodes_about_transaction(self, transaction):
        for node in self.__peer_nodes:
            url = f'http://{node}/broadcast-transaction'
            try:
                response = requests.post(url, json={'transaction': transaction.to_ordered_dict()})
                if response.status_code in [400, 500]:
                    print('Transaction declined, needs resolving')
                    return False
            except requests.exceptions.ConnectionError:
                continue
        return True

    def add_block(self, block):
        transactions = [Transaction(tx['sender'], tx['recipient'], tx['amount'], tx['signature'])
                        for tx in block['transactions']]
        proof_is_valid = Verification.valid_proof(transactions[:-1], block['previous_hash'], block['proof'])
        hashes_match = HashUtil.hash_block(self.chain[-1]) == block['previous_hash']
        if not (proof_is_valid and hashes_match):
            return False
        new_block = Block(
            index=block['index'],
            previous_hash=block['previous_hash'],
            transactions=transactions,
            proof=block['proof'],
            block_time=block['timestamp']
        )
        self.__chain.append(new_block)
        self.clear_open_peer_transactions(block)
        self.save_data()
        return True

    def notify_peer_nodes_about_block(self, block):
        for node in self.__peer_nodes:
            url = f'http://{node}/broadcast-block'
            try:
                response = requests.post(url, json={'block': block.get_savable_version()})
                if response.status_code in [400, 500]:
                    print('Block declined, needs resolving')
                if response.status_code in [409]:
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue
        return True

    def clear_open_peer_transactions(self, block):
        stored_transactions = self.__open_transactions[:]
        for incoming_transaction in block['transactions']:
            for open_transaction in stored_transactions:
                if open_transaction.sender == incoming_transaction['sender'] \
                        and open_transaction.recipient == incoming_transaction['recipient'] \
                        and open_transaction.signature == incoming_transaction['signature']:
                    try:
                        self.__open_transactions.remove(open_transaction)
                    except ValueError:
                        print('Item already removed!')

    def resolve(self):
        winner_chain = self.chain
        replace = False
        for node in self.__peer_nodes:
            url = f'http://{node}/chain'
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [Block(
                    block['index'],
                    block['previous_hash'],
                    [Transaction(tx['sender'], tx['recipient'], tx['amount'], tx['signature'])
                     for tx in block['transactions']],
                    block['proof'],
                    block['timestamp']
                ) for block in node_chain['chain']]
                node_chain_length = len(node_chain)
                local_chain_length = len(winner_chain)
                if node_chain_length > local_chain_length and Verification.verify_chain(node_chain):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue
        self.resolve_conflicts = False
        self.chain = winner_chain
        if replace:
            self.__open_transactions = []
        self.save_data()
        return replace

    def add_peer_node(self, node):
        self.__peer_nodes.add(node)
        self.save_data()

    def remove_peer_node(self, node):
        self.__peer_nodes.discard(node)
        self.save_data()

    def get_peer_nodes(self):
        return list(self.__peer_nodes)
