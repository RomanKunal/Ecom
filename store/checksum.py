import base64
import string
import random
import hashlib
from Crypto.Cipher import AES
import binascii

IV = '@@@@&&&&####$$$$'
BLOCK_SIZE = 16

def generate_checksum(params, merchant_key):
    params = {k: str(v) for k, v in sorted(params.items())}
    data = '|'.join(params.values())
    return __encode__(generate_salt() + data, merchant_key)

def verify_checksum(params, checksum, merchant_key):
    params = {k: str(v) for k, v in sorted(params.items())}
    data = '|'.join(params.values())
    return __verify__(checksum, generate_salt() + data, merchant_key)

def generate_salt(length=4):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def __encode__(data, key):
    key = hashlib.sha256(key.encode()).digest()
    cipher = AES.new(key, AES.MODE_CBC, IV.encode())
    return base64.b64encode(cipher.encrypt(pad(data).encode())).decode()

def __verify__(checksum, data, key):
    return checksum == __encode__(data, key)

def pad(data):
    pad_len = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
    return data + (chr(pad_len) * pad_len)
