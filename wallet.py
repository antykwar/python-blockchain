import json
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import Crypto.Random
import binascii
from configuration import Configuration


class Wallet:
    def __init__(self, network_id=None):
        self.private_key = None
        self.public_key = None
        self.network_id = network_id if network_id is not None else ''

    def create_keys(self):
        private_key, public_key = self.generate_keys()
        self.private_key = private_key
        self.public_key = public_key

    def load_keys(self):
        try:
            with open(Configuration.WALLET_FILE + str(self.network_id), mode='r') as datastore:
                file_content = datastore.readlines()
                raw_wallet_data = json.loads(file_content[0])
                self.private_key = raw_wallet_data['private_key']
                self.public_key = raw_wallet_data['public_key']
            return True
        except (IOError, IndexError):
            print('Error while reading wallet data, assuming wallet not set!')
            return False

    def save_keys(self):
        if self.private_key is None or self.public_key is None:
            print('Trying to save empty wallet data!')
            return
        try:
            with open(Configuration.WALLET_FILE + str(self.network_id), mode='w') as datastore:
                datastore.write(json.dumps({'public_key': self.public_key, 'private_key': self.private_key}))
            return True
        except IOError:
            print('Error while saving wallet data!')
            return False

    @staticmethod
    def generate_keys():
        private_key = RSA.generate(1024, Crypto.Random.new().read)
        public_key = private_key.publickey()
        return (
            binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
            binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
        )

    def sign_transaction(self, sender, recipient, amount):
        signer = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.private_key)))
        hash_to_sign = SHA256.new((str(sender) + str(recipient) + str(amount)).encode('utf8'))
        signature = signer.sign(hash_to_sign)
        return binascii.hexlify(signature).decode('ascii')

    @staticmethod
    def verify_transaction(transaction):
        public_key = RSA.importKey(binascii.unhexlify(transaction.sender))
        verifier = PKCS1_v1_5.new(public_key)
        hash_to_check = \
            SHA256.new((str(transaction.sender) + str(transaction.recipient) + str(transaction.amount)).encode('utf8'))
        return verifier.verify(hash_to_check, binascii.unhexlify(transaction.signature))

