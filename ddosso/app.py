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

from . import handlers
from . import uimodules
from .util import rooted_path
import firenado.tornadoweb


class DDOSSOComponent(firenado.tornadoweb.TornadoComponent):

    def get_handlers(self):
        self.conf['social']['enabled'] = False
        if (self.conf['social']['facebook']['enabled'] or
                self.conf['social']['google']['enabled'] or
                self.conf['social']['twitter']['enabled']):
            self.conf['social']['enabled'] = True
        root = self.conf['root']
        return [
            (r"%s" % rooted_path(root, "/"), handlers.IndexHandler),
            (r"%s" % rooted_path(root, "/captcha/(.*)"),
             handlers.CaptchaHandler),
            (r"%s" % rooted_path(root, "/profile"), handlers.ProfileHandler),
            (r"%s" % rooted_path(root, "/sign_in"), handlers.SigninHandler),
            (r"%s" % rooted_path(root, "/sign_up"), handlers.SignupHandler),
            (r"%s" % rooted_path(root, "/sign_up/social"),
             handlers.SignupSocialHandler),
            (r"%s" % rooted_path(root, "google/sign_up"),
             handlers.GoogleSignupHandler),
            (r"%s" % rooted_path(root, "google/oauth2callback"),
             handlers.GoogleLoginHandler),
            (r"%s" % rooted_path(root, "discourse/sign_on"),
             handlers.DiscourseSSOHandler),
            (r"%s" % rooted_path(root, "discourse/login"),
             handlers.LoginHandler),
        ]

    def get_ui_modules(self):
        return uimodules

    def get_config_file(self):
        return "ddosso"

    def install(self):
        from sqlalchemy import text
        from firenado.util.sqlalchemy_util import Base
        from .diaspora.models import DddossoUserBase
        print('Installing DDOSSO...')
        print('Creating DDOSSO users table ...')
        engine = self.application.get_data_source(
            'diaspora').engine
        engine.echo = False
        # Dropping all
        # TODO Not to drop all if something is installed right?

        DddossoUserBase.__table__.drop(engine, checkfirst=True)
        # Creating database
        DddossoUserBase.__table__.create(engine)
        engine.dispose()
