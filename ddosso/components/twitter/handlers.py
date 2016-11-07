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

from ddosso.handlers import DdossoHandlerMixin

import firenado.conf
import firenado.tornadoweb
from firenado import service

from tornado.auth import TwitterMixin
from tornado.escape import json_encode, json_decode
from tornado import gen


class TwitterHandlerMixin:

    SESSION_KEY = 'twitter_user'

    def get_current_user(self):
        user_json = self.session.get(self.SESSION_KEY)
        if not user_json:
            return None
        return json_decode(user_json)

    def is_signin_next(self):
        sign_in_url = self.get_rooted_path("sign_in")
        return sign_in_url in self.session.get("next_url")


class TwitterOauthHandler(TwitterHandlerMixin,
                          firenado.tornadoweb.TornadoHandler,
                          DdossoHandlerMixin):

    @firenado.security.authenticated("twitter")
    @service.served_by("ddosso.services.SocialLinkService")
    def get(self):

        sign_in_url = self.get_rooted_path("sign_in")
        print(sign_in_url)

        print(self.session.get("next_url"))
        errors = {}
        twitter_user = self.current_user
        if self.social_link_service.by_handler("Oauth:Twitter",
                                               twitter_user['username']):
            self.session.delete(self.SESSION_KEY)
            errors['signup'] = ("Este email já está cadastrado no pod. Faça o "
                                "login e associe sua conta ao seu perfil do "
                                "Twitter.")
            self.session.set("errors", errors)
            self.redirect("%s" % self.component.conf['root'])
        else:
            self.redirect(self.session.get("next_url"))


class TwitterOauthCallbackHandler(TwitterHandlerMixin,
                                  firenado.tornadoweb.TornadoHandler, TwitterMixin,
                                  DdossoHandlerMixin):
    @gen.coroutine
    @service.served_by("ddosso.services.SocialLinkService")
    def get(self):
        self.settings['twitter_consumer_key'] = self.component.conf[
            'social']['twitter']['key']
        self.settings['twitter_consumer_secret'] = self.component.conf[
            'social']['twitter']['secret']
        twitter_url_login = firenado.conf.app['login']['urls']['twitter']
        my_redirect_url = "%s://%s%s" % (self.request.protocol,
                                         self.request.host, twitter_url_login)


        if self.get_argument('oauth_token', False):
            user = yield self.get_authenticated_user()
            del user['description']
            del user['follow_request_sent']
            del user['status']
            del user['profile_link_color']
            del user['profile_text_color']
            del user['profile_sidebar_fill_color']
            del user['profile_sidebar_border_color']
            del user['profile_background_color']
            del user['statuses_count']
            user['oauth_token'] = self.get_argument('oauth_token')
            user['oauth_verifier'] = self.get_argument('oauth_verifier')
            # Save the user and access token with
            # e.g. set_secure_cookie.
            self.session.set(self.SESSION_KEY, json_encode(user))
            self.redirect(self.get_argument('next',
                                            self.get_rooted_path(
                                                "twitter/oauth")))
        else:
            yield self.authorize_redirect(callback_uri=my_redirect_url)
                #extra_params={'approval_prompt': 'force'})
