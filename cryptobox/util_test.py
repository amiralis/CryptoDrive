__author__ = 'amirali'

import util
import base64
import os


def test_enc_dec_file_data():
    """ Test encrypt/decrypt file content """

    key = base64.urlsafe_b64encode(os.urandom(32))

    with open('test_file') as f:
        data = f.read()

    c = util.encrypt(key, data)
    d = util.decrypt(key, c)

    assert d == data


test_enc_dec_file_data()