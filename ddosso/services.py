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

from datetime import datetime
from firenado import service
from firenado.config import load_yaml_config_file
from .diaspora.models import (AspectBase, DddossoSocialLinkBase, PersonBase,
                              ProfileBase, UserBase)
import logging
from passlib.hash import bcrypt
import os
import sys
import uuid

logger = logging.getLogger(__name__)


class UserService(service.FirenadoService):

    def by_username(self, username, db_session=None):
        self_session = False
        if db_session is None:
            db_session = self.get_data_source('diaspora').session
            self_session = True
        user = db_session.query(UserBase).filter(
            UserBase.username == username.lower()).one_or_none()
        if self_session:
            db_session.close()
        return user

    def by_email(self, email, db_session=None):
        self_session = False
        if db_session is None:
            db_session = self.get_data_source('diaspora').session
            self_session = True
        user = db_session.query(UserBase).filter(
            UserBase.email == email).one_or_none()
        if self_session:
            db_session.close()
        return user

    def create(self, user_data, created_utc=None, db_session=None):
        from firenado.util import random_string
        if not created_utc:
            created_utc = datetime.utcnow()
        remote_ip = None
        if "remote_ip" in user_data:
            remote_ip = user_data['remote_ip']
        user = UserBase()
        user.username = user_data['username']
        # TODO: Generate the serialized private key
        user.serialized_private_key = user_data['private_key']
        user.getting_started = True
        user.disable_mail = False
        # TODO: Handle language
        user.language = 'en'
        user.email = user_data['email']
        # TODO: encrypt the password
        user.encrypted_password = bcrypt.encrypt(
            self.get_peppered_password(user_data['password']))
        # Not used
        user.invitation_token = None
        user.invitation_sent_at = None
        user.reset_password_sent_at = None
        user.sign_in_count = 1
        user.current_sign_in_at = created_utc
        user.last_sign_in_at = created_utc
        user.current_sign_in_ip = remote_ip
        user.last_sign_in_ip = remote_ip
        user.created_at = created_utc
        user.updated_at = created_utc
        user.invited_by_id = None
        user.authentication_token = None
        user.unconfirmed_email = None
        user.confirm_email_token = None
        user.locked_at = None
        # TODO: This should be set based on an application settings
        user.show_community_spotlight_in_stream = True
        user.auto_follow_back = False
        user.auto_follow_back_aspect_id = None
        user.hidden_shareables = None
        user.reset_password_sent_at = created_utc
        user.last_seen = None
        user.remove_after = None
        user.export = "%s_diaspora_data_%s.json.gz" % (
            user_data['username'], random_string(22))
        user.exported_at = None
        user.exporting = False
        user.strip_exif = True
        user.exported_photos_file = None
        user.exported_photos_at = None
        user.exporting_photos = False
        user.color_theme = "original"

        commit = False
        if not db_session:
            db_session = self.get_data_source(
                "diaspora").session
            commit = True
        db_session.add(user)
        if commit:
            db_session.commit()
            db_session.close()
        logger.info("Created user: %s" % user)
        return user

    def is_password_valid(self, challenge, encrypted_password):
        return bcrypt.verify(
            self.get_peppered_password(challenge), encrypted_password)

    def set_user_seem(self, user_data, remote_ip):
        db_session = self.get_data_source('diaspora').session
        user = self.by_username(user_data['username'], db_session)
        try:
            right_now = datetime.now()
            last_sign_in_at = user.current_sign_in_at
            last_sign_in_ip = user.current_sign_in_ip
            user.sign_in_count += 1
            user.current_sign_in_at = right_now
            user.last_sign_in_at = last_sign_in_at
            user.current_sign_in_ip = remote_ip
            user.last_sign_in_ip = last_sign_in_ip
            user.last_seen = right_now
            db_session.commit()
        except:
            db_session.rollback()
            logger.info("Unexpected error: %s" % sys.exc_info()[0])
        finally:
            db_session.close()

    def get_peppered_password(self, password):
        ddosso_conf = load_yaml_config_file(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'conf', 'ddosso.yml'))
        return '%s%s' % (password, ddosso_conf['diaspora']['password']['pepper'])


class PersonService(service.FirenadoService):

    def by_user(self, user):
        db_session = self.get_data_source('diaspora').session
        return db_session.query(PersonBase).filter(
            PersonBase.owner_id == user.id).one_or_none()
        db_session.close()

    def create(self, person_data, created_utc=None, db_session=None):
        from .util import generate_public_key
        if not created_utc:
            created_utc = datetime.utcnow()

        person = PersonBase()
        # TODO: It looks like the guid should be generated based on a random
        # string. This generation based on the timestamp is not correct and
        # should be fixed.
        person.guid = str(uuid.uuid5(
            uuid.NAMESPACE_URL, str(created_utc))).replace("-", "")
        person.diaspora_handle = "%s@%s" % (person_data['user'].username,
                                            person_data['pod'])
        person.serialized_public_key = generate_public_key(
            person_data['user'].serialized_private_key)
        person.owner_id = person_data['user'].id
        person.created_at = created_utc
        person.updated_at = created_utc
        person.closed_account = False
        person.fetch_status = 0
        commit = False
        if not db_session:
            session = self.get_data_source(
                    'diasporapy').get_connection()['session']
            commit = True
        db_session.add(person)
        if commit:
            db_session.commit()
            db_session.close()
        logger.info("Created person: %s" % person)
        return person


class AspectService(service.FirenadoService):

    def create(self, aspect_data, db_session=None):
        created_utc = datetime.utcnow()
        aspect = AspectBase()
        aspect.name = aspect_data['name']
        aspect.user_id = aspect_data['user'].id
        aspect.created_at = created_utc
        aspect.updated_at = created_utc
        aspect.contacts_visible = True
        aspect.order_id = aspect_data['order_id']

        commit = False
        if not db_session:
            db_session = self.get_data_source('diaspora').session
            commit = True
        db_session.add(aspect)
        if commit:
            db_session.commit()
            db_session.close()
        logger.info("Created aspect: %s" % aspect)
        return aspect


class SocialLinkService(service.FirenadoService):

    def create(self, social_data, db_session=None):
        created_utc = datetime.utcnow()
        social_link = DddossoSocialLinkBase()
        social_link.user_id = social_data['user'].id
        social_link.type = social_data['type']
        social_link.data = social_data['data']
        social_link.handler = social_data['handler']
        social_link.created_at = created_utc
        social_link.updated_at = created_utc

        commit = False
        if not db_session:
            db_session = self.get_data_source('diaspora').session
            commit = True
        db_session.add(social_link)
        if commit:
            db_session.commit()
            db_session.close()
        logger.info("Created social link: %s" % social_link)
        return social_link

    def by_handler(self, link_type, handler):
        db_session = self.get_data_source('diaspora').session
        return db_session.query(DddossoSocialLinkBase).filter(
            DddossoSocialLinkBase.type == link_type).filter(
            DddossoSocialLinkBase.handler == handler).one_or_none()
        db_session.close()


class ProfileService(service.FirenadoService):

    def by_person(self, person):
        db_session = self.get_data_source('diaspora').session
        return db_session.query(ProfileBase).filter(
            ProfileBase.person_id == person.id).one_or_none()
        db_session.close()

    def create(self, profile_data, created_utc=None, db_session=None):
        """
        :param person:
        :param first_name:
        :param last_name:
        :return:
        """
        if not created_utc:
            created_utc = datetime.utcnow()

        first_name = None
        last_name = None
        if 'first_name' in profile_data:
            first_name = profile_data['first_name']
        if 'last_name' in profile_data:
            last_name = profile_data['last_name']

        profile = ProfileBase()

        profile.first_name = first_name
        profile.last_name = last_name
        profile.birthday = None
        profile.gender = ''
        profile.bio = ''
        profile.searchable = True
        # TODO: this should be filled at the beginning
        profile.person_id = profile_data['person'].id
        profile.created_at = created_utc
        profile.updated_at = created_utc
        profile.location = ''
        profile.full_name = ''
        profile.nsfw = False
        profile.public_details = False

        commit = False
        if not db_session:
            db_session = self.get_data_source(
                    'diasporapy').get_connection()['session']
            commit = True
        db_session.add(profile)
        if commit:
            db_session.commit()
            db_session.close()
        logger.info("Created profile: %s" % profile)
        return profile


class LoginService(service.FirenadoService):

    def __init__(self, handler, data_source=None):
        service.FirenadoService.__init__(self, handler, data_source)

    @service.served_by("ddosso.services.PersonService")
    @service.served_by("ddosso.services.ProfileService")
    @service.served_by("ddosso.services.UserService")
    def is_valid(self, username, password):
        """ Checks if challenge username and password matches
        username and password defined on the service constructor..

        Args:
            username: A challenge username
            password: A challenge password

        Returns: Returns true if challenge username and password matches
        username and password defined on the service constructor.

        """
        user = self.user_service.by_username(username)

        if user:
            people = self.person_service.by_user(user)
            profile = self.profile_service.by_person(people)

            user_name = None
            if profile.full_name != "":
                user_name = profile.full_name
            elif profile.first_name != "":
                if profile.last_name != "":
                    user_name = "%s %s" % (
                    profile.first_name, profile.last_name)
                else:
                    user_name = profile.first_name
            else:
                user_name = user.username

            user_data = {
                "id": 0,
                "username": "",
                "email": "",
                "guid": "",
                "name": "",
                "avatar": "",
            }
            if self.user_service.is_password_valid(password,
                    user.encrypted_password):
                user_data['id'] = user.id
                user_data['username'] = user.username
                user_data['email'] = user.email
                user_data['guid'] = people.guid
                user_data['name'] = user_name.title()
                user_data['avatar'] = profile.image_url_medium
                return user_data
        return False


class AccountService(service.FirenadoService):

    @service.served_by(UserService)
    @service.served_by(PersonService)
    @service.served_by(ProfileService)
    @service.served_by(AspectService)
    @service.served_by(SocialLinkService)
    def register(self, account_data):
        logger.info("Received valid data to create account: %s" % account_data)
        db_session = self.get_data_source(
            'diaspora').session
        created_utc = datetime.utcnow()
        user = self.user_service.create(account_data,
                                        created_utc=created_utc,
                                        db_session=db_session)
        db_session.commit()
        person_data = {}
        person_data['user'] = user
        person_data['pod'] = account_data['pod']
        person = self.person_service.create(
            person_data, created_utc=created_utc, db_session=db_session)
        db_session.commit()
        profile_data = {}
        profile_data['person'] = person
        profile = self.profile_service.create(
            profile_data, created_utc=created_utc, db_session=db_session)
        db_session.commit()

        aspects = ["Acquaintances", "Work", "Friends", "Family"]
        order_id = 4
        for aspect in aspects:
            aspect_data = {}
            aspect_data['user'] = user
            aspect_data['name'] = aspect
            aspect_data['order_id'] = order_id
            order_id -= 1
            self.aspect_service.create(aspect_data, db_session=db_session)
            db_session.commit()

        for social_data in account_data['social']:
            social_data['user'] = user
            self.social_link_service.create(social_data, db_session=db_session)
            db_session.commit()

        db_session.close()
        return user

    @service.served_by(UserService)
    def is_login_valid(self, login_data):
        db_session = self.get_data_source(
            'diasporapy').get_connection()['session']
        user = self.user_service.get_by_user_name(
            login_data['username'], db_session)
        if user:
            if self.user_service.is_password_valid(
                    login_data['password'], user.encrypted_password):
                return user
        return False
