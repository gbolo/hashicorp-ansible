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
        accessor_id=dict(type="str"),
    )

    # seed the final result dict in the object. Default nothing changed ;)
    result = dict(
        changed=False,
    )

    # the AnsibleModule object
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    # the ConsulAPI can init itself via the module args
    consul = ConsulAPI(module)

    result["token"] = consul.get_acl_token(module.params.get("accessor_id"))

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
