from distutils.core import setup

import cryptodrive


def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='cryptobox',
      version=cryptodrive.__version__,
      description='Crypto Box: a Virtual Encrypted Filesystem',
      long_description=readme(),
      author='Amirali Sanatinia',
      author_email='amirali@ccs.neu.edu',
      url='https://github.com/amiralis/CryptoBox',
      packages=['cryptodrive'],
      license='Apache 2',
      classifiers=['License :: OSI Approved :: Apache Software License',
                   'Programming Language :: Python :: 2.7'],
      install_requires=['fusepy', 'cryptography'],
      include_package_data=True)