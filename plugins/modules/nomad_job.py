#!/usr/bin/python
# Copyright (c) George Bolo <gbolo@linuxctl.com>
# SPDX-License-Identifier: MIT


from ansible.module_utils.basic import AnsibleModule, env_fallback
from ..module_utils.nomad import NomadAPI

import json


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        state=dict(type="str", choices=["present", "absent", "purged"], default="present"),
        url=dict(type="str", required=True, fallback=(env_fallback, ["NOMAD_ADDR"])),
        validate_certs=dict(type="bool", default=True),
        connection_timeout=dict(type="int", default=10),
        management_token=dict(
            type="str", required=True, no_log=True, fallback=(env_fallback, ["NOMAD_TOKEN"])
        ),
        name=dict(type="str"),
        namespace=dict(type="str", default="default"),
        hcl_spec=dict(type="str"),
    )

    # the AnsibleModule object
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False,
        mutually_exclusive=[
            ["name", "hcl_spec"]
        ],
        required_one_of=[
            ["name", "hcl_spec"]
        ],
        required_if = [
            ["state", "present", ["hcl_spec"]]
        ]
    )

    # seed the final result dict in the object. Default nothing changed ;)
    result = dict(
        changed=False,
    )

    # the NomadAPI can init itself via the module args
    nomad = NomadAPI(module)

    # parse the job to get the job ID
    # check if an existing job exists
    parsed_job = None
    if module.params.get("name") is not None:
        job_id = module.params.get("name")
    else:
        parsed_job = nomad.parse_job(json.dumps(dict(
            JobHCL=module.params.get("hcl_spec")
        )))
        job_id = parsed_job["ID"]

    existing_job = nomad.get_job(job_id)

    if module.params.get("state") in ("absent", "purged"):
        purged = False
        if module.params.get("state") == "purged":
            purged = True
        # if the job is already stopped but purge is set, we need to purge it.
        # also the job can still exist but not purged, in this case the
        # job has Stop set to True
        if (existing_job is not None and purged) or \
           (existing_job is not None and not existing_job["Stop"]):
            nomad.delete_job(job_id, purged)
            result["changed"] = True

    # we can rely on nomad plan to decide if we should submit a job ;)
    if module.params.get("state") == "present":
        plan = nomad.plan_job(job_id, json.dumps(dict(
            Job=parsed_job,
            Diff=True,
        )))
        result["plan_diff"] = plan["Diff"]
        if plan["Diff"].get("Type") != "None":
            result["submit_response"] = nomad.create_or_update_job(job_id, json.dumps(dict(
                Job=parsed_job,
                Submission=dict(
                    Format="hcl2",
                    Source=module.params.get("hcl_spec"),
                )
            )))
            result["changed"] = True

    
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
