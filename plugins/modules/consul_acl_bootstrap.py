#!/usr/bin/python
# Copyright (c) George Bolo <gbolo@linuxctl.com>
# SPDX-License-Identifier: MIT


import json

from ansible.module_utils.basic import AnsibleModule, env_fallback

from ..module_utils.consul import ConsulAPI
from ..module_utils.utils import del_none, is_subset


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        url=dict(type="str", required=True, fallback=(env_fallback, ["CONSUL_HTTP_ADDR"])),
        validate_certs=dict(type="bool", default=True),
        connection_timeout=dict(type="int", default=10),
        management_token=dict(type="str", required=True, no_log=True, fallback=(env_fallback, ["CONSUL_HTTP_TOKEN"])),
    )

    # seed the final result dict in the object. Default nothing changed ;)
    result = dict(
        changed=False,
    )

    # the AnsibleModule object
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    # the ConsulAPI can init itself via the module args
    consul = ConsulAPI(module)

    existing_token = consul.get_self_token()
    if existing_token is None:
        # when bootstrapping, we should ensure the returned token is the same
        token = consul.acl_bootstrap()
        result["changed"] = True
        if token.get("SecretID") != module.params.get("management_token"):
            module.fail_json("bootstrap token has unexpected value: " + token.get("SecretID"))
    else:
        is_mgmt=False
        # consul management tokens have a policy with ID: 00000000-0000-0000-0000-000000000001 and named global-management
        for policy in existing_token.get("Policies"):
            if policy.get("Name") == "global-management":
                is_mgmt=True
                break
            
        if not is_mgmt:
            module.fail_json("token provided is not of management type")

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()