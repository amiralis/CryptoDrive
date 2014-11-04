__author__ = 'amirali'

from distutils.core import setup

setup(name='cryptobox',
      version='1.0',
      description='Crypto Box: a Virtual Encrypted Filesystem',
      author='Amirali Sanatinia',
      author_email='amirali@ccs.neu.edu',
      url='https://github.com/amiralis/CryptoBox',
      packages=['cryptography', 'fusepy'],
     )
