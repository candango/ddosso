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

from firenado import service

from wtforms import ValidationError
from wtforms.fields import StringField, PasswordField
from wtforms.validators import DataRequired, Email
from wtforms_tornado import Form
SIGNUP_FORM_CAPTCHA_MISSING = ("Informe o valor da imagem.")
SIGNUP_FORM_CAPTCHA_NOT_MATCH = ("O valor informado não é igual o da imagem.")
SIGNUP_FORM_EMAIL_INVALID = "Informe um email válido."
SIGNUP_FORM_EMAIL_EXISTS = "Este email já está cadastrado."
SIGNUP_FORM_PASSWORD_MISSING = "Informe uma senha."
SIGNUP_FORM_PASSWORD_TOO_SHORT = "Informe uma senha com mais de 6 caracteres."
SIGNUP_FORM_PASSWORD_CONF_MISSING = "Confirme a senha."
SIGNUP_FORM_PASSWORD_CONF_NOT_MATCH = ("A confirmação da senha não é igual a "
                                       "senha.")
SIGNUP_FORM_USERNAME_MISSING = "Informe o nome do usuário."
SIGNUP_FORM_USERNAME_EXISTS = "Este usuário já está cadastrado."


class SignupForm(Form):

    email = StringField(validators=[Email(SIGNUP_FORM_EMAIL_INVALID)])
    password = PasswordField(validators=[DataRequired(
        SIGNUP_FORM_PASSWORD_MISSING)])
    passwordConf = PasswordField(validators=[DataRequired(
        SIGNUP_FORM_PASSWORD_CONF_MISSING)])
    username = StringField(validators=[DataRequired(
        SIGNUP_FORM_USERNAME_MISSING)])
    captcha = StringField(validators=[DataRequired(
        SIGNUP_FORM_CAPTCHA_MISSING)])

    def __init__(self, formdata=None, obj=None, prefix='', locale_code='en_US',
                 handler=None,
                 **kwargs):
        super(SignupForm, self).__init__(formdata, obj, prefix, **kwargs)
        self.handler = handler

    @service.served_by("ddosso.services.UserService")
    def validate_email(self, field):
        if self.user_service.by_email(field.data):
            raise ValidationError(SIGNUP_FORM_EMAIL_EXISTS)

    @service.served_by("ddosso.services.UserService")
    def validate_username(self, field):
        if self.user_service.by_username(field.data):
            raise ValidationError(SIGNUP_FORM_USERNAME_EXISTS)

    def validate_password(self, field):
        if len(field.data) < 6:
            raise ValidationError(SIGNUP_FORM_PASSWORD_TOO_SHORT)

    def validate_passwordConf(self, field):
        if self.password.data:
            if self.password.data != field.data:
                raise ValidationError(SIGNUP_FORM_PASSWORD_CONF_NOT_MATCH)

    def validate_captcha(self, field):
        if field.data != self.handler.session.get("captcha_string_sign_up"):
            raise ValidationError(SIGNUP_FORM_CAPTCHA_NOT_MATCH)

    def get_data_connected(self):
        if self.handler:
            return self.handler.application
        return None
