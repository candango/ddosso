import ujson
import urllib.parse
import base64
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2

unpad = lambda s: s[:-ord(s[len(s)-1:])]

# As seen in https://gist.github.com/wbills/3a83338508ded263e701

class RailsCookieDecryptor(object):
    def __init__(self, secret_key_base, salt="encrypted cookie",
                 keylen=64, iterations=1000):
        self.secret = PBKDF2(secret_key_base.encode(), salt.encode(), keylen,
                             iterations)

    def get_cookie_data(self, cookie):
        cookie = base64.b64decode(urllib.parse.unquote(cookie).split('--')[0])
        encrypted_data, iv = map(base64.b64decode, cookie.decode().split('--'))
        cipher = AES.new(self.secret[:32], AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(encrypted_data))
        return ujson.loads(plaintext)
