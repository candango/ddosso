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

from .util import rooted_path
import tornado.web
import os


class RootedPath(tornado.web.UIModule):

    def render(self, path):
        root = self.handler.component.conf['root']
        return rooted_path(root, path)


class PrintIfError(tornado.web.UIModule):

    def render(self, key, code):
        if self.handler.session.has('login_errors'):
            errors = self.handler.session.get('login_errors')
            if key in errors:
                return code
        return ""


class LoginErrorMessage(tornado.web.UIModule):

    def render(self, key):

        if self.handler.session.has('login_errors'):
            errors = self.handler.session.get('login_errors')
            if key in errors:
                template = "ddosso:uimodules/login_error_message.html"
                return self.render_string(template, message=errors[key])
        return ""
