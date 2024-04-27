# 使用.env中的AES_KEY进行加密解密，写一个类
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import dotenv
from os import getenv
from os import urandom
import base64

class CryptoUtils:
    KEY_SIZE = 32  # 256 bits
    IV_SIZE = 16   # 128 bits

    def __init__(self):
        base64_encoded = dotenv.get_key('.env', 'AES_BASE64_KEY')
        self.secret_key, self.iv = self.extract_key_and_iv(base64_encoded)

    def encrypt(self, plain_text):
        cipher = Cipher(algorithms.AES(self.secret_key), modes.CBC(self.iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padded_text = CryptoUtils._pad(plain_text.encode('utf-8'))
        encrypted = encryptor.update(padded_text) + encryptor.finalize()
        return base64.b64encode(encrypted).decode('utf-8')

    def decrypt(self, encrypted_text):
        encrypted = base64.b64decode(encrypted_text)
        cipher = Cipher(algorithms.AES(self.secret_key), modes.CBC(self.iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(encrypted) + decryptor.finalize()
        return CryptoUtils._unpad(decrypted_padded).decode('utf-8')

    @staticmethod
    def _pad(data):
        padding_len = 16 - len(data) % 16
        padding = bytes([padding_len] * padding_len)
        return data + padding

    @staticmethod
    def _unpad(data):
        padding_len = data[-1]
        if data[-padding_len:] != bytes([padding_len] * padding_len):
            raise ValueError("Invalid padding")
        return data[:-padding_len]

    def extract_key_and_iv(self, base64_encoded):
        combined = base64.b64decode(base64_encoded)
        key = combined[:self.KEY_SIZE]
        iv = combined[self.KEY_SIZE:self.KEY_SIZE + self.IV_SIZE]
        return key, iv
    