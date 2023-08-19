#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.nomad import NomadAPI
from ansible.module_utils.utils import del_none, is_subset

import json


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        url=dict(type="str", required=True, fallback=(env_fallback, ["NOMAD_ADDR"])),
        validate_certs=dict(type="bool", default=True),
        connection_timeout=dict(type="int", default=10),
        management_token=dict(
            type="str", required=True, no_log=True, fallback=(env_fallback, ["NOMAD_TOKEN"])
        ),
    )

    # seed the final result dict in the object. Default nothing changed ;)
    result = dict(
        changed=False,
    )

    # the AnsibleModule object
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    # the NomadAPI can init itself via the module args
    nomad = NomadAPI(module)

    existing_token = nomad.get_self_token()
    if existing_token is None:
        # when bootstrapping, we should ensure the returned token is the same
        token = nomad.acl_bootstrap()
        result["changed"] = True
        if token.get('SecretID') != module.params.get('management_token'):
            module.fail_json('bootstrap token has unexpected value: ' + token.get('SecretID'))
    elif existing_token.get('Type') != "management":
        module.fail_json('token provided is not of management type')
    
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
