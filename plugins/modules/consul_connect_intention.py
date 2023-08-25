#!/usr/bin/python
# Copyright (c) George Bolo <gbolo@linuxctl.com>
# SPDX-License-Identifier: MIT


from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.consul import ConsulAPI
from ansible.module_utils.utils import del_none, is_subset

import json

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        state=dict(type="str", choices=["present", "absent"], default="present"),
        url=dict(type="str", required=True, fallback=(env_fallback, ["CONSUL_HTTP_ADDR"])),
        validate_certs=dict(type="bool", default=True),
        connection_timeout=dict(type="int", default=10),
        management_token=dict(
            type="str", required=True, no_log=True, fallback=(env_fallback, ["CONSUL_HTTP_TOKEN"])
        ),
        source=dict(type="str", required=True),
        destination=dict(type="str", required=True),
        description=dict(type="str"),
        action=dict(type="str"),
        permissions=dict(type="list"),
    )
    
    # seed the final result dict in the object. Default nothing changed ;)
    result = dict(
        changed=False,
    )

    # the AnsibleModule object
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    # the ConsulAPI can init itself via the module args
    consul = ConsulAPI(module)

    existing_intention = consul.get_connect_intention(
        source=module.params.get("source"),
        destination=module.params.get("destination"),
    )

    desired_intention_body = del_none(dict(
        SourceType="consul",
        Description=module.params.get("description"),
        Action=module.params.get("action"),
        Permissions=module.params.get("permissions"),
    ))

    if module.params.get('state') == "absent":
        if existing_intention is not None:
            consul.delete_connect_intention(
                source=module.params.get("source"),
                destination=module.params.get("destination"),
            )
            result["changed"] = True

    if module.params.get('state') == "present":
        if existing_intention is None or not is_subset(desired_intention_body, existing_intention):
            consul.create_or_update_connect_intention(
                source=module.params.get("source"),
                destination=module.params.get("destination"),
                body=json.dumps(desired_intention_body)
            )
            result["changed"] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
