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
from firenado.util import file as _file
import firenado.conf
#import logging
import os
import htmlmin
#from css_html_js_minify.minify import prepare
#from css_html_js_minify import html_minify


class RootedPath(tornado.web.UIModule):

    def render(self, path):
        root = self.handler.component.conf['root']
        return rooted_path(root, path)


class EmbedStache(tornado.web.UIModule):

    def render(self, embeded_id, embeded_path, component=None):
        # This is to fix the issue with the css_html_js_minify
        # https://github.com/juancarlospaco/css-html-js-minify/issues/43
        #prepare()
        # TODO: MOVE THIS TO FIRENADO. GREAT UI MODULE!!!
        if component is None:
            component = firenado.conf.app['component']
        component_path = self.handler.application.components[
            component].get_component_path()
        # TODO: check if this path exists
        content = htmlmin.minify(_file.read(os.path.join(
            component_path, "static", "stache", embeded_path)))
        template = "ddosso:uimodules/embeded_stache.html"
        embeded = self.render_string(template, embeded_id=embeded_id,
                                     embeded_content=content)
        return embeded.decode("utf-8")


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
