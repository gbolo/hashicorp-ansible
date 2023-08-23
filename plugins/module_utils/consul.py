from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json

from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.common.text.converters import to_native

def del_none(d):
    """
    Delete keys with the value ``None`` in a dictionary, recursively.
    Returns a copy of the input d.
    """
    cloned = d.copy()
    for key, value in list(cloned.items()):
        if value is None:
            del cloned[key]
        elif isinstance(value, dict):
            del_none(value)
    return cloned

URL_ACL_POLICIES = "{url}/v1/acl/policies"
URL_ACL_POLICY_ID = "{url}/v1/acl/policy/{id}"
URL_ACL_POLICY_NAME = "{url}/v1/acl/policy/name/{name}"
URL_ACL_POLICY_CREATE = "{url}/v1/acl/policy"
URL_ACL_TOKENS = "{url}/v1/acl/tokens"
URL_ACL_TOKEN = "{url}/v1/acl/token"
URL_ACL_TOKEN_ID = "{url}/v1/acl/token/{id}"


class ConsulAPI(object):
    """ ConsulAPI is used to interact with the consul API
    """
    def __init__(self, module):
        self.module = module
        self.url = self.module.params.get('url')
        self.management_token = self.module.params.get('management_token')
        self.validate_certs = self.module.params.get('validate_certs')
        self.connection_timeout = self.module.params.get('connection_timeout')
        self.headers = {
            "Content-Type": "application/json",
            "X-Consul-Token": self.management_token,
            "User-Agent": "ansible-module-consul"
        }

    def api_request(self, url, method, headers=None, body=None, json_response=True, ignore_codes=[]):
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
            if e.code in ignore_codes:
                return None
            
            if e.code == 401 or e.code == 403:
                self.module.fail_json(msg='Not Authorized: status=%s [%s] %s ->\n%s'
                                          % (e.code, method, url, e.read().decode('utf-8')))
            
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

    def get_acl_policy(self, policy_id):
        return self.api_request(
            url=URL_ACL_POLICY_ID.format(url=self.url, id=policy_id),
            method='GET',
            json_response=True,
            ignore_codes=[404],
        )

    def get_acl_policy_by_name(self, policy_name):
        return self.api_request(
            url=URL_ACL_POLICY_NAME.format(url=self.url, name=policy_name),
            method='GET',
            json_response=True,
            ignore_codes=[404],
        )
    
    def delete_acl_policy(self, policy_id):
        return self.api_request(
            url=URL_ACL_POLICY_ID.format(url=self.url, id=policy_id),
            method='DELETE',
            json_response=False,
            ignore_codes=[404],
        ) 

    def create_acl_policy(self, body):
        return self.api_request(
            url=URL_ACL_POLICY_CREATE.format(url=self.url),
            method='PUT',
            body=body,
            json_response=True,
        )

    def update_acl_policy(self, policy_id, body):
        return self.api_request(
            url=URL_ACL_POLICY_ID.format(url=self.url, id=policy_id),
            method='PUT',
            body=body,
            json_response=True,
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
            # for some reason, consul api returns 403 if token not found...
            # despite the actual response body revealing it could not find
            # the token ;)
            ignore_codes=[403],
        )
    
    def delete_acl_token(self, accessor_id):
        return self.api_request(
            url=URL_ACL_TOKEN_ID.format(url=self.url,id=accessor_id),
            method='DELETE',
            json_response=False,
            ignore_codes=[404],
        )
    
    def create_acl_token(self, body):
        return self.api_request(
            url=URL_ACL_TOKEN.format(url=self.url),
            method='PUT',
            body=body,
            json_response=True,
        )
    
    def update_acl_token(self, accessor_id, body):
        return self.api_request(
            url=URL_ACL_TOKEN_ID.format(url=self.url,id=accessor_id),
            method='PUT',
            body=body,
            json_response=True,
        )