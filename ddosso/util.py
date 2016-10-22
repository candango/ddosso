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

def captcha_data(handler, name):
    from captcha.image import ImageCaptcha
    from PIL import Image
    from firenado.util import random_string
    image = ImageCaptcha(fonts=[
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/liberation/LiberationSerif-Regular.ttf"]
    )
    string = random_string(5).lower()
    anti_cache = random_string(22)
    handler.session.set("captcha_string_%s" % name, string)
    data = image.generate(string)
    return data.getvalue()


def rooted_path(root, path):
    if root[-1] != "/":
        root = "%s/" % root
    rooted_path = "".join([root, path.lstrip("/")])
    if rooted_path == "/":
        return rooted_path
    return rooted_path.rstrip("/")

# TODO: Private key methods belong to podship_platform project
def generate_private_key():
    """ FROM pyraspora: pyaspora.user.models
            Generate a 4096-bit RSA key. The key will be stored in the User
            object. The private key will be protected with password <passphrase>,
            which is usually the user password.
            """
    # TODO: I don't know if this is the way diaspora is handling the key
    # Let's keep this way by now
    # TODO: looks like this method is candidate to be part of some security
    # toolkit
    from Crypto.PublicKey import RSA

    RSAkey = RSA.generate(4096)

    return RSAkey.exportKey(
        format='PEM',
        pkcs=1
    ).decode("ascii")


def load_private_key(private_key_data):
    from Crypto.PublicKey import RSA
    return RSA.importKey(private_key_data)

def generate_public_key(private_key_data):
    RSAkey = load_private_key(private_key_data)
    return RSAkey.publickey().exportKey(
        format='PEM',
        pkcs=1
    ).decode("ascii")

