from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import traceback
import copy
import sys

from datetime import datetime, timedelta

from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.common.text.converters import to_native

URL_ACL_POLICIES = "{url}/v1/acl/policies"
URL_ACL_POLICY = "{url}/v1/acl/policy/{name}"
URL_ACL_TOKENS = "{url}/v1/acl/tokens"
URL_ACL_TOKEN = "{url}/v1/acl/token"
URL_ACL_TOKEN_ID = "{url}/v1/acl/token/{id}"
URL_ACL_TOKEN_SELF = "{url}/v1/acl/token/self"
URL_ACL_BOOTSTRAP = "{url}/v1/acl/bootstrap"
URL_NAMESPACES = "{url}/v1/namespaces"
URL_NAMESPACE = "{url}/v1/namespace/{name}"
URL_OPERATOR_SCHEDULER = "{url}/v1/operator/scheduler/configuration"

class ModuleTest(object):
    def __init__(self, data):
        self.params = data
    def fail_json(self, msg):
        print(msg)
        sys.exit(1)


class NomadAPI(object):
    """ NomadAPI is used to interact with the nomad API
    """
    def __init__(self, module):
        self.module = module
        self.url = self.module.params.get('url')
        self.management_token = self.module.params.get('management_token')
        self.validate_certs = self.module.params.get('validate_certs')
        self.connection_timeout = self.module.params.get('connection_timeout')
        self.headers = {
            "Content-Type": "application/json",
            "X-Nomad-Token": self.management_token,
            "User-Agent": "ansible-module-nomad"
        }

    def api_request(self, url, method, headers=None, body=None, json_response=True, accept_404=False):
        if headers is None:
            headers = self.headers
        try:
            response = open_url(
                url=url,
                method=method,
                data=body,
                headers=headers,
                timeout=self.connection_timeout,
                validate_certs=self.validate_certs
            )
            # print("{method} {url} -> {status}".format(method=method, url=url, status=response.getcode()))
            if json_response:
                try:
                    return json.loads(to_native(response.read()))
                except ValueError as e:
                    self.module.fail_json(msg='API returned invalid JSON: %s'
                                            % (str(e)))
            return response.read().decode('utf-8')
        
        except HTTPError as e:
            if e.code == 401 or e.code == 403:
                self.module.fail_json(msg='Not Authorized: status=%s [%s] %s ->\n%s'
                                          % (e.code, method, url, e.read().decode('utf-8')))
            if e.code == 404 and accept_404:
                return None
            
            self.module.fail_json(msg='Error: status=%s [%s] %s ->\n%s'
                                          % (e.code, method, url, e.read().decode('utf-8')))
            
        except Exception as e:
            print('here')
            self.module.fail_json(msg='Could not make API call: [%s] %s ->\n%s'
                                          % (method, url, str(e)))

    #
    # ACL Policies
    #
    def get_acl_policies(self):
        return self.api_request(
            url=URL_ACL_POLICIES.format(url=self.url),
            method='GET',
            json_response=True,
        )
    
    def get_acl_policy(self, policy_name):
        return self.api_request(
            url=URL_ACL_POLICY.format(url=self.url, name=policy_name),
            method='GET',
            json_response=True,
            accept_404=True,
        )
    
    def delete_acl_policy(self, policy_name):
        return self.api_request(
            url=URL_ACL_POLICY.format(url=self.url, name=policy_name),
            method='DELETE',
            json_response=False,
            accept_404=True,
        ) 

    def create_or_update_acl_policy(self, policy_name, body):
        return self.api_request(
            url=URL_ACL_POLICY.format(url=self.url, name=policy_name),
            method='POST',
            body=body,
            json_response=False,
        )

    #
    # ACL Tokens
    #
    def get_acl_tokens(self):
        return self.api_request(
            url=URL_ACL_TOKENS.format(url=self.url),
            method='GET',
            json_response=True,
        )
    
    def get_acl_token(self, accessor_id):
        return self.api_request(
            url=URL_ACL_TOKEN_ID.format(url=self.url,id=accessor_id),
            method='GET',
            json_response=True,
            accept_404=True,
        )
    
    def find_acl_token_by_name(self, name):
        for token in self.get_acl_tokens():
            if token.get('Name') == name:
                return self.get_acl_token(token.get('AccessorID'))
    
    def delete_acl_token(self, accessor_id):
        return self.api_request(
            url=URL_ACL_TOKEN_ID.format(url=self.url,id=accessor_id),
            method='DELETE',
            json_response=False,
            accept_404=True,
        )
    
    def create_acl_token(self, body):
        return self.api_request(
            url=URL_ACL_TOKEN.format(url=self.url),
            method='POST',
            body=body,
            json_response=True,
        )
    
    def update_acl_token(self, accessor_id, body):
        return self.api_request(
            url=URL_ACL_TOKEN_ID.format(url=self.url,id=accessor_id),
            method='POST',
            body=body,
            json_response=True,
        )
    
    def get_self_token(self):
        return self.api_request(
            url=URL_ACL_TOKEN_SELF.format(url=self.url),
            method='GET',
            json_response=True,
            accept_404=True,
        )
    
    def acl_bootstrap(self):
        return self.api_request(
            url=URL_ACL_BOOTSTRAP.format(url=self.url),
            method='POST',
            body=json.dumps(dict(BootstrapSecret=self.management_token)),
            json_response=True,
        )

    #
    # Namespaces
    #
    def get_namespaces(self):
        return self.api_request(
            url=URL_NAMESPACES.format(url=self.url),
            method='GET',
            json_response=True,
        )
    
    def get_namespace(self, name):
        return self.api_request(
            url=URL_NAMESPACE.format(url=self.url, name=name),
            method='GET',
            json_response=True,
            accept_404=True,
        )
    
    def delete_namespace(self, name):
        return self.api_request(
            url=URL_NAMESPACE.format(url=self.url, name=name),
            method='DELETE',
            json_response=False,
            accept_404=True,
        )
    
    def create_or_update_namespace(self, name, body):
        return self.api_request(
            url=URL_NAMESPACE.format(url=self.url, name=name),
            method='POST',
            body=body,
            json_response=False,
        )
    
    #
    # Operator
    #
    def get_scheduler_config(self):
        return self.api_request(
            url=URL_OPERATOR_SCHEDULER.format(url=self.url),
            method='GET',
            json_response=True,
        )
    
    def update_scheduler_config(self, body):
        return self.api_request(
            url=URL_OPERATOR_SCHEDULER.format(url=self.url),
            method='PUT',
            body=body,
            json_response=True,
        )