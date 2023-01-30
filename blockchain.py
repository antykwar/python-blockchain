import json
from functools import reduce


from hash_util import hash_string_256, hash_block
from block import Block
from transaction import Transaction

MINING_REWARD = 10
MINING_SENDER = 'ABYSS'
BLOCKCHAIN_FILE = 'blockchain.dat'

owner = 'Max'
blockchain = []
open_transactions = []


def save_data():
    try:
        with open(BLOCKCHAIN_FILE, mode='w') as datastore:
            savable_blockchain = [block.get_savable_version() for block in blockchain]
            datastore.write(json.dumps(savable_blockchain))
            datastore.write('\n')
            savable_transactions = [transaction.get_savable_version() for transaction in open_transactions]
            datastore.write(json.dumps(savable_transactions))
    except IOError:
        print('Saving failed!')


def load_data():
    global blockchain
    global open_transactions
    try:
        with open(BLOCKCHAIN_FILE, mode='r') as datastore:
            file_content = datastore.readlines()
            blockchain = json.loads(file_content[0][:-1])
            blockchain = [Block(
                index=block['index'],
                previous_hash=block['previous_hash'],
                transactions=[
                    Transaction(tx['sender'], tx['recipient'], tx['amount'])
                    for tx in block['transactions']
                ],
                proof=block['proof'],
                block_time=block['timestamp']
            ) for block in blockchain]
            open_transactions = json.loads(file_content[1])
            open_transactions = [
                Transaction(tx['sender'], tx['recipient'], tx['amount'])
                for tx in open_transactions
            ]
    except (IOError, IndexError):
        blockchain = [Block(
            index=0,
            previous_hash='',
            transactions=[],
            proof=0
        )]
        open_transactions = []


def valid_proof(transactions, last_hash, proof):
    guess = (str([tx.to_ordered_dict() for tx in transactions]) + str(last_hash) + str(proof)).encode()
    guess_hash = hash_string_256(guess)
    return guess_hash.startswith('00')


def proof_of_work():
    last_block = blockchain[-1]
    last_hash = hash_block(last_block)
    proof = 0
    while not valid_proof(open_transactions, last_hash, proof):
        proof += 1
    return proof


def verify_transaction(transaction):
    sender_balance = get_balance(transaction.sender)
    return sender_balance >= transaction.amount


def add_transaction(recipient, sender=owner, amount=1.0):
    transaction = Transaction(sender, recipient, amount)
    if verify_transaction(transaction):
        open_transactions.append(transaction)
        save_data()
        return True
    return False


def calculate_balance(participant, tx_type='sender'):
    known_type = None
    if tx_type in ('sender', 'recipient'):
        known_type = tx_type
    if known_type is None:
        return 0

    transactions_sums = [[tx.amount for tx in block.transactions if getattr(tx, known_type) == participant] for block in
                         blockchain]
    return reduce(lambda total_sum, current: total_sum + sum(current), transactions_sums, 0)


def calculate_open_transactions(participant, tx_type='sender'):
    known_type = None
    if tx_type in ('sender', 'recipient'):
        known_type = tx_type
    if known_type is None:
        return 0

    return sum([tx.amount for tx in open_transactions if getattr(tx, known_type) == participant])


def get_balance(participant):
    total_sent = calculate_balance(participant) + calculate_open_transactions(participant)
    total_received = calculate_balance(participant, 'recipient')
    return total_received - total_sent


def mine_block():
    last_block = blockchain[-1]
    proof = proof_of_work()
    reward_transaction = Transaction(MINING_SENDER, owner, MINING_REWARD)
    copied_transactions = open_transactions[:]
    copied_transactions.append(reward_transaction)
    block = Block(
        index=len(blockchain),
        previous_hash=hash_block(last_block),
        transactions=copied_transactions,
        proof=proof
    )
    blockchain.append(block)
    save_data()
    return True


def get_last_blockchain_value():
    try:
        return blockchain[-1]
    except IndexError:
        return None


def verify_chain():
    for index, block in enumerate(blockchain):
        if index == 0:
            continue
        if block.previous_hash != hash_block(blockchain[index - 1]):
            return False
        if not valid_proof(block.transactions[:-1], block.previous_hash, block.proof):
            return False

    return True


def read_transaction_value():
    recipient = input('Provide recipient, please: ')
    amount = float(input('Provide transaction sum, please: '))
    return recipient, amount


def read_user_choice():
    return input('Your choice: ')


def print_input_prompt():
    print('Please, choose')
    print('1: Add new transaction')
    print('2: Mine a new block')
    print('3: Show the blockchain blocks')
    print('4: Check transactions validity')
    print('q: Quit')


def print_blockchain_elements():
    if len(blockchain) == 0:
        print('Blockchain is empty')
        return
    for index, block in enumerate(blockchain):
        if index <= 0:
            continue
        print(f'Outputting block #{index}:')
        print(block)


def verify_transactions():
    return all([verify_transaction(tx) for tx in open_transactions])


# -------------
load_data()

while True:
    print_input_prompt()
    user_choice = read_user_choice()

    if user_choice == '1':
        recipient, amount = read_transaction_value()
        if add_transaction(recipient, amount=amount):
            print('Successfully added transaction!')
        else:
            print('Error while adding transaction!')
    elif user_choice == '2':
        if mine_block():
            open_transactions = []
            save_data()
    elif user_choice == '3':
        print_blockchain_elements()
    elif user_choice == '4':
        if verify_transactions():
            print('All transactions are valid')
        else:
            print('There are invalid transactions')
    elif user_choice == 'q':
        break
    else:
        print('Invalid input! Please, provide value from the list.')

    if not verify_chain():
        print('Corrupted blockchain!')
        break

    print(f'Balance of {owner}: {get_balance(owner):6.2f}')

print('Done!')
