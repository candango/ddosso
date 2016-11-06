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

from ddosso.handlers import RootedHandlerMixin

import firenado.conf
import firenado.tornadoweb
from firenado import service

from tornado.auth import GoogleOAuth2Mixin
import tornado.escape
from tornado import gen


class GoogleHandlerMixin:

    SESSION_KEY = 'google_user'

    def get_current_user(self):
        user_json = self.session.get(self.SESSION_KEY)
        if not user_json:
            return None
        return tornado.escape.json_decode(user_json)


class GoogleSignupHandler(GoogleHandlerMixin,
                          firenado.tornadoweb.TornadoHandler):

    @firenado.security.authenticated("google")
    @service.served_by("ddosso.services.UserService")
    def get(self):
        errors = {}
        google_user = self.current_user
        if self.user_service.by_email(google_user['email']):
            self.session.delete(self.SESSION_KEY)
            errors['signup'] = ("Este email já está cadastrado no pod. Faça o "
                                "login e associe sua conta os seu perfil do "
                                "Google.")
            self.session.set("errors", errors)
            self.redirect("%s" % self.component.conf['root'])
        else:
            self.redirect(self.session.get("next_url"))


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
            self.session.set("GOOGLE_ACCESS", tornado.escape.json_encode(
                access))

            self.redirect(
                self.get_argument('next',
                                  self.get_rooted_path("google/oauth2")))
        else:
            yield self.authorize_redirect(
                redirect_uri=my_redirect_url,
                client_id=self.component.conf['social']['google']['key'],
                client_secret=self.component.conf['social']['google']['secret'],
                scope=['profile', 'email'],
                response_type='code',
                extra_params={'approval_prompt': 'auto'})
                #extra_params={'approval_prompt': 'force'})
