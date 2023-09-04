#!/usr/bin/python
# Copyright (c) George Bolo <gbolo@linuxctl.com>
# SPDX-License-Identifier: MIT


import json

from ansible.module_utils.basic import AnsibleModule, env_fallback

from ..module_utils.consul import ConsulAPI
from ..module_utils.utils import del_none, is_subset


def run_module():
    # define available arguments/parameters a user can pass to the module
    policies_and_roles_spec = dict(
        id=dict(type="str", aliases=["ID"]),
        name=dict(type="str", aliases=["Name"]),
    )
    module_args = dict(
        url=dict(type="str", required=True, fallback=(env_fallback, ["NOMAD_ADDR"])),
        validate_certs=dict(type="bool", default=True),
        connection_timeout=dict(type="int", default=10),
        management_token=dict(type="str", required=True, no_log=True, fallback=(env_fallback, ["NOMAD_TOKEN"])),
        service_name=dict(type="str", required=True),
    )

    # seed the final result dict in the object. Default nothing changed ;)
    result = dict(
        changed=False,
    )

    # the AnsibleModule object
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    # the ConsulAPI can init itself via the module args
    consul = ConsulAPI(module)

    result["instances"] = consul.get_service(module.params.get("service_name"))

    # since the point of this module is to figure out a service IP and port
    # let's throw an error if we don't find one...
    if len(result["instances"]) == 0:
        module.fail_json("could not find consul service named " + module.params.get("service_name"))

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
