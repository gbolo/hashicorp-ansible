#!/usr/bin/python
# Copyright (c) George Bolo <gbolo@linuxctl.com>
# SPDX-License-Identifier: MIT


from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.nomad import NomadAPI
from ansible.module_utils.utils import del_none, is_subset

import json


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        state=dict(type="str", choices=["present", "absent"], default="present"),
        url=dict(type="str", required=True, fallback=(env_fallback, ["NOMAD_ADDR"])),
        validate_certs=dict(type="bool", default=True),
        connection_timeout=dict(type="int", default=10),
        management_token=dict(
            type="str", required=True, no_log=True, fallback=(env_fallback, ["NOMAD_TOKEN"])
        ),
        type=dict(type="str", choices=["client", "management"], default="client"),
        name=dict(type="str"),
        match_on_name=dict(type="bool", default=True),
        is_global=dict(type="bool", default=False),
        policies=dict(type="list", elements="str", required=True),
        expiration_ttl=dict(type="str"),
        accessor_id=dict(type="str"),
    )

    # seed the final result dict in the object. Default nothing changed ;)
    result = dict(
        changed=False,
    )

    # the AnsibleModule object
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    # the NomadAPI can init itself via the module args
    nomad = NomadAPI(module)

    desired_token_body = del_none(
        dict(
            AccessorID=module.params.get("accessor_id"),
            Name=module.params.get("name"),
            Type=module.params.get("type"),
            Policies=module.params.get("policies"),
            Global=module.params.get("is_global"),
            ExpirationTTL=module.params.get("expiration_ttl"),
        )
    )

    # find an existing token by name is we match by name
    existing_token = None
    if module.params.get("match_on_name"):
        existing_token = nomad.find_acl_token_by_name(module.params.get("name"))

    # find an existing token if an accessor_id is provided
    if module.params.get("accessor_id") is not None:
        existing_token = nomad.get_acl_token(module.params.get("accessor_id"))

    if module.params.get("state") == "absent":
        if existing_token is not None:
            nomad.delete_acl_token(existing_token.get("AccessorID"))
            result["changed"] = True

    if module.params.get("state") == "present":
        if existing_token is None:
            result["token"] = nomad.create_acl_token(
                json.dumps(desired_token_body)
            )
            result["changed"] = True
        else:
            # compare if we need to change anything about the token
            # NOTE: DO NOT compare expiration
            if desired_token_body.get('ExpirationTTL') is not None:
                desired_token_body.pop('ExpirationTTL')
            if not is_subset(desired_token_body, existing_token):
                result["token"] = nomad.update_acl_token(
                    existing_token.get('AccessorID'), json.dumps(existing_token)
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
