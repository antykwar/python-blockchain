from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from argparse import ArgumentParser

from wallet import Wallet
from blockchain import Blockchain

app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET'])
def get_ui():
    return send_from_directory('ui', 'node.html')


@app.route('/network', methods=['GET'])
def get_network_ui():
    return send_from_directory('ui', 'network.html')


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
        blockchain = Blockchain(wallet.public_key, network_id=port)
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
        blockchain = Blockchain(wallet.public_key, network_id=port)
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


@app.route('/node', methods=['POST'])
def add_node():
    if not request.is_json or not request.get_json():
        response = {
            'success': False,
            'message': 'No input data!'
        }
        return jsonify(response), 400
    data = request.get_json()
    if 'node' not in data:
        response = {
            'success': False,
            'message': 'Required data is missing!'
        }
        return jsonify(response), 400
    node = data['node']
    blockchain.add_peer_node(node)
    response = {
        'success': True,
        'message': 'Node added successfully!',
        'nodes': blockchain.get_peer_nodes()
    }
    return jsonify(response), 200


@app.route('/node/<node_url>', methods=['DELETE'])
def remove_node(node_url):
    if not node_url:
        response = {
            'success': False,
            'message': 'No node found!'
        }
        return jsonify(response), 400
    blockchain.remove_peer_node(node_url)
    response = {
        'success': True,
        'message': 'Node removed successfully!',
        'nodes': blockchain.get_peer_nodes()
    }
    return jsonify(response), 200


@app.route('/nodes', methods=['GET'])
def get_nodes():
    response = {
        'success': True,
        'nodes': blockchain.get_peer_nodes()
    }
    return jsonify(response), 200


@app.route('/broadcast-transaction', methods=['POST'])
def broadcast_transaction():
    data = request.get_json()
    if not data:
        response = {
            'success': False,
            'message': 'No data found!'
        }
        return jsonify(response), 400
    if 'transaction' not in data:
        response = {
            'success': False,
            'message': 'Missing transaction data!'
        }
        return jsonify(response), 400
    transaction = data['transaction']
    success = blockchain.add_transaction(
        transaction['recipient'],
        transaction['sender'],
        transaction['amount'],
        transaction['signature'],
        is_receiving=True
    )
    if success:
        response = {
            'success': True,
            'message': 'Transaction successfully added!',
            'transaction': {
                'sender': transaction['sender'],
                'recipient': transaction['recipient'],
                'amount': transaction['amount'],
                'signature': transaction['signature']
            },
        }
        return jsonify(response), 201
    else:
        response = {
            'success': False,
            'message': 'Adding a transaction failed!'
        }
        return jsonify(response), 500


@app.route('/broadcast-block', methods=['POST'])
def broadcast_block():
    data = request.get_json()
    if not data:
        response = {
            'success': False,
            'message': 'No data found!'
        }
        return jsonify(response), 400
    if 'block' not in data:
        response = {
            'success': False,
            'message': 'Missing transaction data!'
        }
        return jsonify(response), 400
    block = data['block']
    if block['index'] == blockchain.chain[-1].index + 1:
        if blockchain.add_block(block):
            response = {
                'success': True,
                'message': 'Block successfully added!'
            }
            return jsonify(response), 201
        else:
            response = {
                'success': False,
                'message': 'Block seems invalid!'
            }
            return jsonify(response), 500
    elif block['index'] > blockchain.chain[-1].index:
        pass
    else:
        response = {
            'success': False,
            'message': 'Your blockchain is shorter than expected, block not added!'
        }
        return jsonify(response), 409


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=5000)
    args = parser.parse_args()
    port = args.port
    wallet = Wallet(network_id=port)
    blockchain = Blockchain(wallet.public_key, network_id=port)
    app.run(host='0.0.0.0', port=port)
