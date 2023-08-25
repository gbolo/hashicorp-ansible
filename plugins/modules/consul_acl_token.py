#!/usr/bin/python
# Copyright (c) George Bolo <gbolo@linuxctl.com>
# SPDX-License-Identifier: MIT


from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.consul import ConsulAPI
from ansible.module_utils.utils import del_none, is_subset

import json


def run_module():
    # define available arguments/parameters a user can pass to the module
    polcies_spec = dict(
        id=dict(type="str", aliases=["ID"]),
        name=dict(type="str", aliases=["Name"]),    
    )
    module_args = dict(
        state=dict(type="str", choices=["present", "absent"], default="present"),
        url=dict(type="str", required=True, fallback=(env_fallback, ["NOMAD_ADDR"])),
        validate_certs=dict(type="bool", default=True),
        connection_timeout=dict(type="int", default=10),
        management_token=dict(
            type="str", required=True, no_log=True, fallback=(env_fallback, ["NOMAD_TOKEN"])
        ),
        accessor_id=dict(type="str"),
        secret_id=dict(type="str"),
        description=dict(type="str"),
        policies=dict(type="list", elements="dict", options=polcies_spec),
        roles=dict(type="list", elements="dict"),
        match_on_name=dict(type="bool", default=True),
        is_local=dict(type="bool", default=False),
        expiration_ttl=dict(type="str"),
    )

    # seed the final result dict in the object. Default nothing changed ;)
    result = dict(
        changed=False,
    )

    # the AnsibleModule object
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    # the ConsulAPI can init itself via the module args
    consul = ConsulAPI(module)

    desired_token_body = del_none(
        dict(
            AccessorID=module.params.get('accessor_id'),
            Description=module.params.get('description'),
            ExpirationTTL=module.params.get('expiration_ttl'),
            Local=module.params.get('local'),
            # Policies=module.params.get('policies'),
            # Roles=module.params.get('roles'),
            SecretID=module.params.get('secret_id'),
            ServiceIdentities=module.params.get('service_identities'),
        )
    )
    if module.params.get("policies") is not None:
        policies = []
        for p in module.params.get("policies"):
            policies.append(del_none(dict(
                ID=p.get('id'),
                Name=p.get('name'),
            )))
        desired_token_body['Policies'] = policies

    # if an accessor_id is defined, try to find the token
    existing_token = None
    accessor_id = module.params.get('accessor_id')
    if accessor_id is not None:
        existing_token = consul.get_acl_token(accessor_id)

    # delete token only when it exists
    if module.params.get('state') == "absent":
        if existing_token is not None:
            consul.delete_acl_token(accessor_id)
            result['changed'] == True

    if module.params.get('state') == "present":
        # decide to create a token if accessor_id is not set
        # or one does not already exsit
        if accessor_id is None or existing_token is None:
            result['token'] = consul.create_acl_token(json.dumps(desired_token_body))
            result['changed'] = True

        else:
            # compare if we need to change anything about the token
            # NOTE: DO NOT compare expiration
            if desired_token_body.get('ExpirationTTL') is not None:
                desired_token_body.pop('ExpirationTTL')
            if not is_subset(desired_token_body, existing_token):
                result["token"] = consul.update_acl_token(
                    existing_token.get('AccessorID'), json.dumps(desired_token_body)
                )
                result["changed"] = True

    # post final results
    if result.get('token') is None and existing_token is not None:
        result["token"] = existing_token
    
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
