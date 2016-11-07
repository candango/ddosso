#!/usr/bin/env python
#
# Copyright 2016 Flavio Garcia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import urllib.parse
import base64
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto import Random
from hashlib import sha1, md5
import hmac

BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s: s[:-ord(s[len(s)-1:])]

# Solved the digest mistery!!!
# https://gist.github.com/tonytonyjan/d71f040fe1085dfcf1d4


class RailsCookie(object):

    def __init__(self, secret_key_base, salt="encrypted cookie",
                 encrypted_salt='signed encrypted cookie', keylen=64,
                 iterations=1000):
        self.secret_key = secret_key_base.encode("ascii")


        self.secret = PBKDF2(self.secret_key, salt.encode("ascii"), keylen,
                             iterations)
        self.secret_encrypted = PBKDF2(self.secret_key,
                                       encrypted_salt.encode("ascii"),
                                       keylen, iterations)

    def gen_cookie_id(self):
        m = md5()
        m.update(Random.new().read(32))
        return m.hexdigest()

    def is_valid(self, cookie):
        unquoted_cookie = urllib.parse.unquote(cookie)
        their_signature = unquoted_cookie.split("--")[1].encode()
        my_signature = self.sign(unquoted_cookie.split("--")[0].encode())
        return hmac.compare_digest(their_signature, my_signature)

    def sign(self, data):
        return hmac.new(self.secret_encrypted, data,
                        digestmod=sha1).hexdigest().encode()

    def decrypt(self, cookie):
        first = urllib.parse.unquote(cookie)
        second = first.split("--")[0]
        cookie = base64.b64decode(second)
        encrypted_data, iv = map(base64.b64decode, cookie.decode().split('--'))
        cipher = AES.new(self.secret[:32], AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(encrypted_data))
        return plaintext

    def encrypt(self, raw):
        import html
        raw = pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.secret[:32], AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(raw)
        encoded_encrypted_message = base64.b64encode(encrypted)
        iv_base64 = base64.b64encode(iv)
        separator = "--".encode('ascii')
        encoded_cookie = base64.b64encode(
            html.escape(encoded_encrypted_message.decode()).encode() +
            separator + iv_base64)
        hexdigest = self.sign(encoded_cookie)
        return urllib.parse.quote_from_bytes(encoded_cookie + separator +
                                             hexdigest).encode()
