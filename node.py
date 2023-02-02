from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from wallet import Wallet
from blockchain import Blockchain

app = Flask(__name__)
CORS(app)

wallet = Wallet()
blockchain = Blockchain(wallet.public_key)


@app.route('/', methods=['GET'])
def get_ui():
    return send_from_directory('ui', 'node.html')


@app.route('/transaction', methods=['POST'])
def add_transaction():
    if wallet.public_key is None:
        response = {
            'success': False,
            'message': 'No wallet set up!',
            'wallet_set_up': False
        }
        return jsonify(response), 400
    if not request.is_json or not request.get_json():
        response = {
            'success': False,
            'message': 'No input data!'
        }
        return jsonify(response), 400
    user_data = request.get_json()
    required_fields = ['recipient', 'amount']
    if not all(field in user_data for field in required_fields):
        response = {
            'success': False,
            'message': 'Required data is missing!'
        }
        return jsonify(response), 400
    signature = wallet.sign_transaction(
        wallet.public_key,
        user_data['recipient'],
        user_data['amount']
    )
    success = blockchain.add_transaction(
        user_data['recipient'],
        wallet.public_key,
        user_data['amount'],
        signature
    )
    if success:
        response = {
            'success': True,
            'message': 'Transaction successfully created!',
            'transaction': {
                'sender': wallet.public_key,
                'recipient': user_data['recipient'],
                'amount': user_data['amount'],
                'signature': signature
            },
            'balance': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'success': False,
            'message': 'Creating a transaction failed!'
        }
        return jsonify(response), 500


@app.route('/wallet', methods=['POST'])
def create_keys():
    wallet.create_keys()
    if wallet.save_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key)
        response = {
            'success': True,
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'balance': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'success': False,
            'message': 'Error while saving wallet data!'
        }
        return jsonify(response), 500


@app.route('/wallet', methods=['GET'])
def load_keys():
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key)
        response = {
            'success': True,
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'balance': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'success': False,
            'message': 'Error while loading wallet data!'
        }
        return jsonify(response), 500


@app.route('/balance', methods=['GET'])
def get_balance():
    balance = blockchain.get_balance()
    if balance is not None:
        response = {
            'success': True,
            'balance': balance
        }
        return jsonify(response), 200
    else:
        response = {
            'success': False,
            'message': 'Loading balance failed!',
            'wallet_set_up': wallet.public_key is not None
        }
        return jsonify(response), 500


@app.route('/mine', methods=['POST'])
def mine():
    block = blockchain.mine_block()
    if block is not None:
        response = {
            'success': True,
            'message': 'Block successfully added!',
            'block': block.get_savable_version(),
            'balance': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'success': False,
            'message': 'Adding a block failed!',
            'wallet_set_up': wallet.public_key is not None
        }
        return jsonify(response), 500


@app.route('/chain', methods=['GET'])
def get_chain():
    chain = blockchain.chain
    response = {
        'success': True,
        'chain': [block.get_savable_version() for block in chain]
    }
    return jsonify(response), 200


@app.route('/transactions', methods=['GET'])
def get_open_transactions():
    transactions = [tx.to_ordered_dict() for tx in blockchain.open_transactions]
    response = {
        'success': True,
        'transactions': transactions
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
