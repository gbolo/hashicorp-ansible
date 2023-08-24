#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.nomad import NomadAPI
from ansible.module_utils.utils import del_none, is_subset

import json

def run_module():
    # define available arguments/parameters a user can pass to the module
    job_acl_spec = dict(
        namespace=dict(type="str", aliases=["Namespace"], default=""),
        job_id=dict(type="str", aliases=["JobID"], default=""),
        group=dict(type="str", aliases=["Group"], default=""),
        task=dict(type="str", aliases=["Task"], default=""),
    )
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
        rules=dict(type="str"),
        job_acl=dict(type="dict", default={}, options=job_acl_spec),
    )
    
    # seed the final result dict in the object. Default nothing changed ;)
    result = dict(
        changed=False,
    )

    # the AnsibleModule object
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False,
        required_if=[('state', 'present', ('rules',))],
    )

    # the NomadAPI can init itself via the module args
    nomad = NomadAPI(module)

    policy_name = module.params.get("name")
    existing_policy = nomad.get_acl_policy(policy_name)
    desired_policy_body = del_none(
        dict(
            Name=policy_name,
            Description=module.params.get("description"),
            Rules=module.params.get("rules"),
            JobACL=dict(
                Namespace=module.params.get("job_acl").get("namespace"),
                JobID=module.params.get("job_acl").get("job_id"),
                Group=module.params.get("job_acl").get("group"),
                Task=module.params.get("job_acl").get("task"),
            ),
        )
    )

    if module.params.get("state") == "absent":
        if existing_policy is not None:
            nomad.delete_acl_policy(policy_name)
            result["changed"] = True

    if module.params.get("state") == "present":
        if existing_policy is None:
            nomad.create_or_update_acl_policy(
                policy_name, json.dumps(desired_policy_body)
            )
            result["policy"] = nomad.get_acl_policy(policy_name)
            result["changed"] = True
        else:
            # compare if we need to change anything about the policy
            if not is_subset(desired_policy_body, existing_policy):
                nomad.create_or_update_acl_policy(
                    policy_name, json.dumps(desired_policy_body)
                )
                result["policy"] = nomad.get_acl_policy(policy_name)
                result["changed"] = True

    # post final results
    if result.get('policy') is None and existing_policy is not None:
        result["policy"] = existing_policy

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
