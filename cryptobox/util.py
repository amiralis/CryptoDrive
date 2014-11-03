__author__ = 'amirali'

import base64
from cryptography.fernet import Fernet


def encrypt(key, data):
    f = Fernet(key)
    cipher = f.encrypt(bytes(data))
    return base64.urlsafe_b64decode(cipher)


def decrypt(key, cipher):
    f = Fernet(key)
    data = f.decrypt(base64.urlsafe_b64encode(cipher))
    return data


