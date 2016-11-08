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

from tornado.auth import FacebookGraphMixin
from tornado.escape import json_encode, json_decode, url_escape
import tornado.web


class FacebookHandlerMixin:

    SESSION_KEY = 'facebook_user'

    def get_current_user(self):
        user_json = self.session.get(self.SESSION_KEY)
        if not user_json:
            return None
        return json_decode(user_json)

#to get avatar https://developers.facebook.com/docs/graph-api/reference/user/picture/
class FacebookRouterHandler(FacebookHandlerMixin,
                          firenado.tornadoweb.TornadoHandler,
                          DdossoHandlerMixin):

    @firenado.security.authenticated("facebook")
    @service.served_by("ddosso.services.SocialLinkService")
    def get(self):

        sign_in_url = self.get_rooted_path("sign_in")
        print(sign_in_url)

        print(self.session.get("next_url"))
        errors = {}
        if False:
            facebook_user = self.current_user
            print(facebook_user)
            if self.social_link_service.by_handler("Graph:Facebook",
                                                   facebook_user['username']):
                self.session.delete(self.SESSION_KEY)
                errors['signup'] = ("Este email já está cadastrado no pod. Faça o "
                                    "login e associe sua conta ao seu perfil do "
                                    "Twitter.")
                self.session.set("errors", errors)
                self.redirect("%s" % self.component.conf['root'])
            else:
                self.redirect(self.session.get("next_url"))


class FacebookGraphAuthHandler(FacebookHandlerMixin,
                               firenado.tornadoweb.TornadoHandler,
                               FacebookGraphMixin, DdossoHandlerMixin):
    @tornado.web.asynchronous
    def get(self):
        self.settings['facebook_api_key'] = self.component.conf[
            'social']['facebook']['key']
        self.settings['facebook_secret'] = self.component.conf[
            'social']['facebook']['secret']

        fb_url = firenado.conf.app['login']['urls']['facebook']

        my_url = "%s://%s%s?next=%s" % (self.request.protocol,
                                        self.request.host, fb_url,
                                        url_escape(self.get_argument("next",
                                                                     "/")))

        if self.get_argument("code", False):
            self.get_authenticated_user(
                redirect_uri=my_url,
                client_id=self.settings["facebook_api_key"],
                client_secret=self.settings["facebook_secret"],
                code=self.get_argument("code"),
                callback=self._on_auth)
            return
        self.authorize_redirect(redirect_uri=my_url,
                                client_id=self.settings["facebook_api_key"],
                                extra_params={"scope": "user_posts"})

    @tornado.web.asynchronous
    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Facebook auth failed")
        self.session.set(self.SESSION_KEY, json_encode(user))

        self.redirect(self.get_rooted_path("/facebook/get_avatar"))


class FacebookAvatarHandler(FacebookHandlerMixin,
                            firenado.tornadoweb.TornadoHandler,
                            FacebookGraphMixin, DdossoHandlerMixin):
    @tornado.web.asynchronous
    def get(self):
        self.facebook_request("/v2.8/%s/picture" % self.current_user["id"],
                              self._on_stream,
                              access_token=self.current_user["access_token"])

    def _on_stream(self, stream):
        if stream is None:
            # Session may have expired
            self.redirect("/auth/login")
            return
        print(stream.encode())

        #self.redirect(self.get_argument("next", self.get_rooted_path("/facebook/authorize")))