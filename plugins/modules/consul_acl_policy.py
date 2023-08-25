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
        id=dict(type="str"),
        name=dict(type="str", required=True),
        description=dict(type="str"),
        rules=dict(type="str", required=True),
        datacenters=dict(type="list", elements="str"),
    )
    
    # seed the final result dict in the object. Default nothing changed ;)
    result = dict(
        changed=False,
    )

    # the AnsibleModule object
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    # the ConsulAPI can init itself via the module args
    consul = ConsulAPI(module)

    policy_name = module.params.get("name")
    policy_id = module.params.get("id")
    
    existing_policy = None
    desired_policy_body = del_none(dict(
        Name=policy_name,
        Description=module.params.get("description"),
        Rules=module.params.get("rules"),
        Datacenters=module.params.get("datacenters"),
    ))

    # try to find an existing policy.
    # policy IDs are randomly generated when creating a policy.
    # policy names MUST be unique.
    # if both policy ID and name are provided, we assume the intent
    # is to change an existing policy's name or other properties.

    if policy_id is not None:
        existing_policy = consul.get_acl_policy(policy_id)
    else:
        existing_policy = consul.get_acl_policy_by_name(policy_name)
        if existing_policy is not None:
            policy_id = existing_policy["ID"]

    if module.params.get("state") == "absent":
        if existing_policy is not None:
            consul.delete_acl_policy(policy_id)
            result["changed"] = True
        else:
            existing_policy = consul.get_acl_policy_by_name(policy_name)
            if existing_policy is not None:
                consul.delete_acl_policy(policy_id)
                result["changed"] = True

    if module.params.get("state") == "present":
        if existing_policy is None:
            result["policy"] = consul.create_acl_policy(
                json.dumps(desired_policy_body)
            )
            result["changed"] = True
        else:
            # compare if we need to change anything about the policy
            if not is_subset(desired_policy_body, existing_policy):
                result["policy"] = consul.update_acl_policy(
                    policy_id, json.dumps(desired_policy_body)
                )
                result["changed"] = True

    # post final results
    if result.get('policy') is None and existing_policy is not None:
        result["policy"] = existing_policy

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
