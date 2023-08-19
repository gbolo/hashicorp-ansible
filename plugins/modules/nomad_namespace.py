#!/usr/bin/python

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
        name=dict(type="str", required=True),
        description=dict(type="str"),
        meta=dict(type="str"),
    )

    # seed the final result dict in the object. Default nothing changed ;)
    result = dict(
        changed=False,
    )

    # the AnsibleModule object
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    # the NomadAPI can init itself via the module args
    nomad = NomadAPI(module)

    existing_namespace = nomad.get_namespace(module.params.get('name'))
    desired_namespace = del_none(dict(
        Name=module.params.get('name'),
        Description=module.params.get('description'),
        Meta=module.params.get('meta'),
        Capabilities=module.params.get('capabilities'),
    ))

    if module.params.get("state") == "absent":
        if existing_namespace is not None:
            nomad.delete_namespace(module.params.get('name'))
            result["changed"] = True
    
    # decide if we should create/update a namespace
    create_namespace = False
    if module.params.get("state") == "present":
        if existing_namespace is None:
            create_namespace = True
        else:
            if not is_subset(desired_namespace, existing_namespace):
                create_namespace = True

    if create_namespace:
        nomad.create_or_update_namespace(
                module.params.get('name'),
                json.dumps(desired_namespace),
            )
        result["changed"] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
