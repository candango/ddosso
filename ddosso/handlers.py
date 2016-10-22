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

# See: http://bit.ly/2cj7IRS

from . import discourse
from .forms import SignupForm
from .util import captcha_data, rooted_path
import base64

import firenado.conf
import firenado.tornadoweb
import firenado.security
from firenado import service

import functools

import hashlib
import hmac

from tornado.auth import GoogleOAuth2Mixin
import tornado.escape
from tornado.web import MissingArgumentError
from tornado import gen

import urllib.parse


def only_ajax(method):

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if "X-Requested-With" in self.request.headers:
            if self.request.headers['X-Requested-With'] == "XMLHttpRequest":
                return method(self, *args, **kwargs)

        else:
            self.set_status(403)
            self.write("This is an XMLHttpRequest request only.")

    return wrapper


class RootedHandlerMixin:

    def get_rooted_path(self, path):
        root = self.component.conf['root']
        return rooted_path(root, path)

class GoogleHandlerMixin:
    SESSION_KEY = 'google_user'

    def get_current_user(self):
        user_json = self.session.get(self.SESSION_KEY)
        if not user_json:
            return None
        return tornado.escape.json_decode(user_json)


class IndexHandler(firenado.tornadoweb.TornadoHandler, RootedHandlerMixin):

    def get(self):
        self.redirect(self.get_rooted_path("/sign_in"), permanent=True)


class SgninHandler(firenado.tornadoweb.TornadoHandler):

    def get(self):
        errors = None
        if self.session.has('errors'):
            errors = self.session.get('errors')
            self.session.delete('errors')
        ddosso_logo = self.component.conf['logo']
        self.render("sign_in.html", ddosso_conf=self.component.conf,
                    ddosso_logo=ddosso_logo, errors=errors)


class SignupHandler(firenado.tornadoweb.TornadoHandler, RootedHandlerMixin):

    def get(self):
        errors = None
        if self.session.has('errors'):
            errors = self.session.get('errors')
            self.session.delete('errors')
        ddosso_logo = self.component.conf['logo']
        self.render("sign_up.html", ddosso_conf=self.component.conf,
                    ddosso_logo=ddosso_logo, errors=errors)

    def post(self):
        error_data = {'errors': {}}
        form = SignupForm(self.request.arguments, handler=self)
        if form.validate():
            self.set_status(200)
            data = {'id': "abcd1234",
                    'next_url': self.get_rooted_path("profile")}
            self.write(data)
        else:
            self.set_status(403)
            error_data['errors'].update(form.errors)
            self.write(error_data)


class GoogleSignupHandler(GoogleHandlerMixin,
                          firenado.tornadoweb.TornadoHandler):

    @firenado.security.authenticated("google")
    @service.served_by("ddosso.services.UserService")
    def get(self):
        errors = {}
        google_user = self.current_user
        if self.user_service.by_email('podmin@therealtalk.org'):
            self.session.delete(self.SESSION_KEY)
            errors['signup'] = ("Este email já está cadastrado no pod. Faça o "
                                "login e associe sua conta os seu perfil do "
                                "Google.")
            self.session.set("errors", errors)
            self.redirect("%s" % self.component.conf['root'])
        ddosso_logo = self.component.conf['logo']
        self.render("google_signup.html", ddosso_conf=self.component.conf,
                    ddosso_logo=ddosso_logo, errors=errors,
                    google_user=self.current_user)
        print(self.current_user)


class GoogleLoginHandler(GoogleHandlerMixin,
                         firenado.tornadoweb.TornadoHandler, GoogleOAuth2Mixin,
                         RootedHandlerMixin):
    @gen.coroutine
    def get(self):
        self.settings['google_oauth'] = {}
        self.settings[
            'google_oauth']['key'] = self.component.conf[
            'social']['google']['key']
        self.settings[
            'google_oauth']['secret'] = self.component.conf[
            'social']['google']['secret']

        google_url_login = firenado.conf.app['login']['urls']['google']
        my_redirect_url = "%s://%s%s" % (self.request.protocol,
                                         self.request.host, google_url_login)
        if self.get_argument('code', False):
            access = yield self.get_authenticated_user(
                redirect_uri=my_redirect_url,
                code=self.get_argument('code'))
            user = yield self.oauth2_request(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                access_token=access["access_token"])
            # Save the user and access token with
            # e.g. set_secure_cookie.
            self.session.set(self.SESSION_KEY, tornado.escape.json_encode(
                user))

            self.redirect(self.get_argument('next', self.get_rooted_path(
                "google/sign_up")))
        else:
            print(self.session.get('next_url'))
            yield self.authorize_redirect(
                redirect_uri=my_redirect_url,
                client_id=self.component.conf['social']['google']['key'],
                client_secret=self.component.conf['social']['google']['secret'],
                scope=['profile', 'email'],
                response_type='code',
                extra_params={'approval_prompt': 'force'})


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


class LoginHandler(firenado.tornadoweb.TornadoHandler):


    def get(self):
        errors = {}
        if self.session.has('login_errors'):
            errors = self.session.get('login_errors')

        ddosso_logo = self.component.conf['logo']
        #print(self.session.get("payload"))
        #print(self.session.get("signature"))

        self.render("discourse/login.html", ddosso_conf=self.component.conf,
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


class CaptchaHandler(firenado.tornadoweb.TornadoHandler):

    @only_ajax
    def get(self, name):
        import base64
        data = {
            "id": name,
            "captcha": "data:image/png;base64,%s" %
                       base64.b64encode(captcha_data(self, name)).decode()
        }
        self.write(data)
