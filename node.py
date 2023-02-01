from utilities.verification import Verification
from blockchain import Blockchain
from wallet import Wallet


class Node:
    def __init__(self):
        self.user_choice = None
        self.wallet = Wallet()
        if self.wallet.load_keys():
            self.blockchain = Blockchain(self.wallet.public_key)
        else:
            self.blockchain = Blockchain(None)

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
        print('5: Create wallet')
        print('6: Load wallet')
        print('q: Quit')

    def main_loop(self):
        while True:
            self.print_input_prompt()
            self.user_choice = self.read_user_choice()

            if self.user_choice == '1':
                recipient, amount = self.read_transaction_value()
                signature = self.wallet.sign_transaction(self.wallet.public_key, recipient, amount)
                if self.blockchain.add_transaction(recipient, self.wallet.public_key, amount, signature):
                    print('Successfully added transaction!')
                else:
                    print('Error while adding transaction! Missing wallet?')
            elif self.user_choice == '2':
                if not self.blockchain.mine_block():
                    print('Mining error! Missing wallet?')
            elif self.user_choice == '3':
                self.print_blockchain_elements()
            elif self.user_choice == '4':
                if Verification.verify_transactions(self.blockchain.open_transactions, self.blockchain.get_balance):
                    print('All transactions are valid')
                else:
                    print('There are invalid transactions')
            elif self.user_choice == '5':
                self.wallet.create_keys()
                self.wallet.save_keys()
                self.blockchain = Blockchain(self.wallet.public_key)
            elif self.user_choice == '6':
                self.wallet.load_keys()
                self.blockchain = Blockchain(self.wallet.public_key)
            elif self.user_choice == 'q':
                break
            else:
                print('Invalid input! Please, provide value from the list.')

            if not Verification.verify_chain(self.blockchain.chain):
                print('Corrupted blockchain!')
                self.print_blockchain_elements()
                break

            print(f'Balance of {self.wallet.public_key}: {self.blockchain.get_balance():6.2f}')

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
