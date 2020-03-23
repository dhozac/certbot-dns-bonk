#!/usr/bin/python3 -tt
#
# Copyright 2020 Qliro AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import zope.interface
import requests

from certbot import errors
from certbot import interfaces
from certbot.plugins import dns_common
from certbot.plugins import dns_common_lexicon

logger = logging.getLogger(__name__)


@zope.interface.implementer(interfaces.IAuthenticator)
@zope.interface.provider(interfaces.IPluginFactory)
class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for bonk

    This authenticator uses the bonk API to fulfill a dns-01 challenge.
    """

    description = 'Obtain certificates using a DNS TXT record (if you are using bonk for DNS).'
    ttl = 60

    def __init__(self, *args, **kwargs):
        super(Authenticator, self).__init__(*args, **kwargs)
        self.credentials = None

    @classmethod
    def add_parser_arguments(cls, add):
        super(Authenticator, cls).add_parser_arguments(add, default_propagation_seconds=300)
        add('credentials', help='bonk credentials INI file.')

    def more_info(self):
        return 'This plugin uses the bonk API to fulfill a dns-01 challenge.'

    def _setup_credentials(self):
        self.credentials = self._configure_credentials(
            'credentials',
            'bonk credentials INI file',
            {
                'endpoint': 'bonk API endpoint (such as https://server/bonk/)',
                'username': 'Username for bonk API',
                'password': 'Password for bonk API',
                'group': 'Group to set as a writer',
                'cleanup_action': 'Whether to delete the record or the value',
            }
        )

    def _perform(self, domain, validation_name, validation):
        session = requests.Session()
        session.auth=(self.credentials.conf('username'), self.credentials.conf('password'))
        url = "{0}/record/{1}/TXT/".format(self.credentials.conf('endpoint'), validation_name)
        response = session.get(url)
        if response.status_code == 401:
            raise errors.PluginError('Invalid credentials talking to bonk')
        elif response.status_code not in (200, 404):
            logger.error("Invalid response from bonk on %s: %d %s", url, response.status_code, response.text)
            raise errors.PluginError("Invalid response from bonk")

        # The record does not exist, create it
        if response.status_code == 404:
            # Find zone to add record to
            url = "{0}/zone/".format(self.credentials.conf('endpoint'))
            response = session.get(url, params={'type': 'external'})
            if response.status_code != 200:
                logger.error("Invalid response from bonk on %s: %d %s", url, response.status_code, response.text)
                raise errors.PluginError("Invalid response from bonk")
            zones = response.json()
            base_domains = dns_common.base_domain_name_guesses(domain)
            for zone in zones:
                if zone['name'] in base_domains:
                    break
            else:
                logger.error("Unable to find zone for domain %s", domain)
                raise errors.PluginError('Unable to find zone for domain')

            record = {
                'zone': zone['name'],
                'name': validation_name,
                'type': 'TXT',
                'value': ['"{0}"'.format(validation)],
                'ttl': 60,
                'permissions': {
                    'write': [self.credentials.conf('group')],
                },
            }
            logger.debug("Creating record %r", record)
            response = session.post("{0}/record/".format(self.credentials.conf('endpoint')), json=record)
            if response.status_code != 201:
                logger.error("Unable to create record in bonk: %d %s", response.status_code, response.text)
                raise errors.PluginError('Unable to create record')

        # The record does exist, patch it
        elif response.status_code == 200:
            record = response.json()
            patch = {
                'value': [v for v in record['value'] if v != '""'] + ['"{0}"'.format(validation)],
            }
            response = session.patch(url, json=patch)
            if response.status_code != 200:
                logger.error("Unable to update record %s: %d %s", url, response.status_code, response.text)
                raise errors.PluginError('Unable to update record')

    def _cleanup(self, domain, validation_name, validation):
        session = requests.Session()
        session.auth=(self.credentials.conf('username'), self.credentials.conf('password'))
        url = "{0}/record/{1}/TXT/".format(self.credentials.conf('endpoint'), validation_name)
        if self.credentials.conf('cleanup_action') == 'record':
            response = session.delete(url)
            if response.status_code not in (204, 404):
                logger.error("Unable to delete record %s: %d %s", url, response.status_code, response.text)
                raise errors.PluginError('Unable to delete record')
        elif self.credentials.conf('cleanup_action') == 'value':
            response = session.get(url)
            if response.status_code != 200:
                logger.error("Unable to get record to delete value %s: %d %s", url, response.status_code, response.text)
                raise errors.PluginError('Unable to delete value')
            record = response.json()
            patch = {'value': [v for v in record['value'] if v != '"{0}"'.format(validation)]}
            if patch['value'] == []:
                patch['value'] = ['""']
            response = session.patch(url, json=patch)
            if response.status_code != 200:
                logger.error("Unable to delete value %s: %d %s", url, response.status_code, response.text)
                raise errors.PluginError('Unable to delete value')
