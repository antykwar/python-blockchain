from uuid import uuid4

from verification import Verification
from blockchain import Blockchain


class Node:
    def __init__(self):
        self.user_choice = None
        # self.id = str(uuid4())
        self.id = 'STUB'
        self.blockchain = Blockchain(self.id)

    @staticmethod
    def read_user_choice():
        return input('Your choice: ')

    @staticmethod
    def print_input_prompt():
        print('Please, choose')
        print('1: Add new transaction')
        print('2: Mine a new block')
        print('3: Show the blockchain blocks')
        print('4: Check transactions validity')
        print('q: Quit')

    def main_loop(self):
        while True:
            self.print_input_prompt()
            self.user_choice = self.read_user_choice()

            if self.user_choice == '1':
                recipient, amount = self.read_transaction_value()
                if self.blockchain.add_transaction(recipient, self.id, amount=amount):
                    print('Successfully added transaction!')
                else:
                    print('Error while adding transaction!')
            elif self.user_choice == '2':
                self.blockchain.mine_block()
            elif self.user_choice == '3':
                self.print_blockchain_elements()
            elif self.user_choice == '4':
                if Verification.verify_transactions(self.blockchain.open_transactions, self.blockchain.get_balance):
                    print('All transactions are valid')
                else:
                    print('There are invalid transactions')
            elif self.user_choice == 'q':
                break
            else:
                print('Invalid input! Please, provide value from the list.')

            if not Verification.verify_chain(self.blockchain.chain):
                print('Corrupted blockchain!')
                self.print_blockchain_elements()
                break

            print(f'Balance of {self.id}: {self.blockchain.get_balance():6.2f}')

        print('Done!')

    @staticmethod
    def read_transaction_value():
        recipient = input('Provide recipient, please: ')
        amount = float(input('Provide transaction sum, please: '))
        return recipient, amount

    def print_blockchain_elements(self):
        if len(self.blockchain.chain) == 0:
            print('Blockchain is empty')
            return
        for index, block in enumerate(self.blockchain.chain):
            if index <= 0:
                continue
            print(f'Outputting block #{index}:')
            print(block)


if __name__ == "__main__":
    node = Node()
    node.main_loop()
