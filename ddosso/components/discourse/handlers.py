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

import base64

from ddosso import discourse

import firenado.tornadoweb
from firenado import service

import hashlib
import hmac

import tornado.escape
from tornado.web import MissingArgumentError

import urllib.parse


class DiscourseSSOHandler(firenado.tornadoweb.TornadoHandler):

    def get(self):
        payload = self.get_argument("sso", strip=False)
        signature = self.get_argument("sig")
        secret = self.component.conf['discourse']['sso']['secret']

        if None in [payload, signature]:
            raise MissingArgumentError("No SSO payload or signature. Please "
                                       "contact support if this problem "
                                       "persists.")
        try:
            assert discourse.sso_has_nounce(payload)
        except AssertionError:
            return MissingArgumentError("Invalid payload. Please contact "
                                        "support if this problem persists.")

        if not discourse.sso_validate(payload, signature, secret):
            raise MissingArgumentError("Invalid payload. Please contact "
                                       "support if this problem persists.")
        self.session.clear()
        self.session.set("payload", payload)
        self.session.set("signature", signature)
        self.session.set("goto", "discourse")
        #self.print(tornado.escape.url_unescape(sso_data['return_sso_url']))
        self.redirect("login")


class DiscourseLoginHandler(firenado.tornadoweb.TornadoHandler):


    def get(self):
        errors = {}
        if self.session.has('login_errors'):
            errors = self.session.get('login_errors')

        ddosso_logo = self.component.conf['logo']
        #print(self.session.get("payload"))
        #print(self.session.get("signature"))

        self.render("login.html", ddosso_conf=self.component.conf,
                    ddosso_logo=ddosso_logo, errors=errors)

    @service.served_by("ddosso.services.LoginService")
    @service.served_by("ddosso.services.UserService")
    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        errors = {}

        if username == "":
            errors['username'] = "Please inform the username"
        if password == "":
            errors['password'] = "Please inform the password"

        self.session.delete('login_errors')
        user = None
        if not errors:
            user = self.login_service.is_valid(username, password)
            if not user:
                errors['fail'] = "Invalid login"

        if errors:
            self.session.set('login_errors', errors)
            self.redirect("login")
            return
        else:
            # Getting real ip from the nginx
            x_real_ip = self.request.headers.get("X-Real-IP")
            remote_ip = x_real_ip or self.request.remote_ip
            #self.user_service.set_user_seem(user, remote_ip)

        sso_data = discourse.get_sso_data(self.session.get("payload"))
        params = {
            'nonce': sso_data['nonce'],
            'email': user['email'],
            'external_id': user['guid'],
            'username': user['username'],
            'name': user['name'],
            'avatar_url': user['avatar']
        }

        secret = self.component.conf['discourse']['sso']['secret']
        return_sso_url = tornado.escape.url_unescape(
            sso_data['return_sso_url'])
        return_payload = base64.encodebytes(
            urllib.parse.urlencode(params).encode())
        h = hmac.new(secret.encode(), return_payload, digestmod=hashlib.sha256)
        query_string = urllib.parse.urlencode(
            {'sso': return_payload, 'sig': h.hexdigest()})
        return_path = '%s?%s' % (return_sso_url, query_string)
        self.redirect(return_path)