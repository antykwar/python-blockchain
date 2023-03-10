from collections import OrderedDict


class Transaction:
    def __init__(self, sender, recipient, amount, signature):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = signature

    def __repr__(self):
        return str(self.__dict__)

    def get_savable_version(self):
        return self.__dict__.copy()

    def to_ordered_dict(self):
        return OrderedDict([
            ('sender', self.sender),
            ('recipient', self.recipient),
            ('amount', self.amount),
            ('signature', self.signature)
        ])
