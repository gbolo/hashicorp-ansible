# Copyright (c) George Bolo <gbolo@linuxctl.com>
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import sys

from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.urls import open_url

from . import debug

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
URL_CSI_VOLUMES = "{url}/v1/volumes?type=csi"
URL_CSI_VOLUME = "{url}/v1/volume/csi/{id}"
URL_CSI_VOLUME_CREATE = "{url}/v1/volume/csi/{id}/create"
URL_CSI_VOLUME_DELETE = "{url}/v1/volume/csi/{id}/delete"
URL_JOBS = "{url}/v1/jobs"
URL_JOB = "{url}/v1/job/{id}"
URL_JOB_DELETE = "{url}/v1/job/{id}?purge={purge}"
URL_JOB_PARSE = "{url}/v1/jobs/parse"
URL_JOB_PLAN = "{url}/v1/job/{id}/plan"


class NomadAPI(object):
    """NomadAPI is used to interact with the nomad API"""

    def __init__(self, module):
        self.module = module
        self.url = self.module.params.get("url")
        self.management_token = self.module.params.get("management_token")
        self.validate_certs = self.module.params.get("validate_certs")
        self.connection_timeout = self.module.params.get("connection_timeout")
        self.headers = {
            "Content-Type": "application/json",
            "X-Nomad-Token": self.management_token,
            "User-Agent": "ansible-module-nomad",
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
                validate_certs=self.validate_certs,
            )
            response_body = response.read().decode("utf-8")
            debug.log_request(
                self.module,
                url,
                method,
                body,
                response.getcode(),
                response_body,
            )
            if json_response:
                try:
                    return json.loads(to_native(response_body))
                except ValueError as e:
                    self.module.fail_json(msg="API returned invalid JSON: %s" % (str(e)))
            return response_body

        except HTTPError as e:
            response_body = e.read().decode("utf-8")
            debug.log_request(
                self.module,
                url,
                method,
                body,
                e.code,
                response_body,
            )
            if e.code == 401 or e.code == 403:
                self.module.fail_json(
                    msg="Not Authorized: status=%s [%s] %s ->\n%s" % (e.code, method, url, response_body)
                )
            if e.code == 404 and accept_404:
                return None

            self.module.fail_json(msg="Error: status=%s [%s] %s ->\n%s" % (e.code, method, url, response_body))

        except Exception as e:
            self.module.fail_json(msg="Could not make API call: [%s] %s ->\n%s" % (method, url, str(e)))

    #
    # ACL Policies
    #
    def get_acl_policies(self):
        return self.api_request(
            url=URL_ACL_POLICIES.format(url=self.url),
            method="GET",
            json_response=True,
        )

    def get_acl_policy(self, policy_name):
        return self.api_request(
            url=URL_ACL_POLICY.format(url=self.url, name=policy_name),
            method="GET",
            json_response=True,
            accept_404=True,
        )

    def delete_acl_policy(self, policy_name):
        return self.api_request(
            url=URL_ACL_POLICY.format(url=self.url, name=policy_name),
            method="DELETE",
            json_response=False,
            accept_404=True,
        )

    def create_or_update_acl_policy(self, policy_name, body):
        return self.api_request(
            url=URL_ACL_POLICY.format(url=self.url, name=policy_name),
            method="POST",
            body=body,
            json_response=False,
        )

    #
    # ACL Tokens
    #
    def get_acl_tokens(self):
        return self.api_request(
            url=URL_ACL_TOKENS.format(url=self.url),
            method="GET",
            json_response=True,
        )

    def get_acl_token(self, accessor_id):
        return self.api_request(
            url=URL_ACL_TOKEN_ID.format(url=self.url, id=accessor_id),
            method="GET",
            json_response=True,
            accept_404=True,
        )

    def find_acl_token_by_name(self, name):
        for token in self.get_acl_tokens():
            if token.get("Name") == name:
                return self.get_acl_token(token.get("AccessorID"))

    def delete_acl_token(self, accessor_id):
        return self.api_request(
            url=URL_ACL_TOKEN_ID.format(url=self.url, id=accessor_id),
            method="DELETE",
            json_response=False,
            accept_404=True,
        )

    def create_acl_token(self, body):
        return self.api_request(
            url=URL_ACL_TOKEN.format(url=self.url),
            method="POST",
            body=body,
            json_response=True,
        )

    def update_acl_token(self, accessor_id, body):
        return self.api_request(
            url=URL_ACL_TOKEN_ID.format(url=self.url, id=accessor_id),
            method="POST",
            body=body,
            json_response=True,
        )

    def get_self_token(self):
        return self.api_request(
            url=URL_ACL_TOKEN_SELF.format(url=self.url),
            method="GET",
            json_response=True,
            accept_404=True,
        )

    def acl_bootstrap(self):
        return self.api_request(
            url=URL_ACL_BOOTSTRAP.format(url=self.url),
            method="POST",
            body=json.dumps(dict(BootstrapSecret=self.management_token)),
            json_response=True,
        )

    #
    # Namespaces
    #
    def get_namespaces(self):
        return self.api_request(
            url=URL_NAMESPACES.format(url=self.url),
            method="GET",
            json_response=True,
        )

    def get_namespace(self, name):
        return self.api_request(
            url=URL_NAMESPACE.format(url=self.url, name=name),
            method="GET",
            json_response=True,
            accept_404=True,
        )

    def delete_namespace(self, name):
        return self.api_request(
            url=URL_NAMESPACE.format(url=self.url, name=name),
            method="DELETE",
            json_response=False,
            accept_404=True,
        )

    def create_or_update_namespace(self, name, body):
        return self.api_request(
            url=URL_NAMESPACE.format(url=self.url, name=name),
            method="POST",
            body=body,
            json_response=False,
        )

    #
    # Operator
    #
    def get_scheduler_config(self):
        return self.api_request(
            url=URL_OPERATOR_SCHEDULER.format(url=self.url),
            method="GET",
            json_response=True,
        )

    def update_scheduler_config(self, body):
        return self.api_request(
            url=URL_OPERATOR_SCHEDULER.format(url=self.url),
            method="PUT",
            body=body,
            json_response=True,
        )

    #
    # CSI Volumes
    #
    def get_csi_volumes(self):
        return self.api_request(
            url=URL_CSI_VOLUMES.format(url=self.url),
            method="GET",
            json_response=True,
        )

    def get_csi_volume(self, id):
        return self.api_request(
            url=URL_CSI_VOLUME.format(url=self.url, id=id),
            method="GET",
            json_response=True,
            accept_404=True,
        )

    def delete_csi_volume(self, id):
        return self.api_request(
            url=URL_CSI_VOLUME_DELETE.format(url=self.url, id=id),
            method="DELETE",
            json_response=True,
            accept_404=True,
        )

    def create_csi_volume(self, id, body):
        return self.api_request(
            url=URL_CSI_VOLUME_CREATE.format(url=self.url, id=id),
            method="PUT",
            body=body,
            json_response=True,
        )

    #
    # Jobs
    #
    def parse_job(self, body):
        return self.api_request(
            url=URL_JOB_PARSE.format(url=self.url),
            method="POST",
            body=body,
            json_response=True,
        )

    def plan_job(self, id, body):
        return self.api_request(
            url=URL_JOB_PLAN.format(url=self.url, id=id),
            method="POST",
            body=body,
            json_response=True,
        )

    def delete_job(self, id, purge=False):
        return self.api_request(
            url=URL_JOB_DELETE.format(url=self.url, id=id, purge=purge),
            method="DELETE",
            json_response=True,
        )

    def create_or_update_job(self, id, body):
        return self.api_request(
            url=URL_JOB.format(url=self.url, id=id),
            method="POST",
            body=body,
            json_response=True,
        )

    def get_job(self, id, namespace="default"):
        return self.api_request(
            url=URL_JOB.format(url=self.url, id=id),
            method="GET",
            json_response=True,
            accept_404=True,
        )
