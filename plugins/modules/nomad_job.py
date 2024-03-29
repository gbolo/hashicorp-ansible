#!/usr/bin/python
# Copyright (c) George Bolo <gbolo@linuxctl.com>
# SPDX-License-Identifier: MIT


import json

from ansible.module_utils.basic import AnsibleModule, env_fallback

from ..module_utils.nomad import NomadAPI

# import nomad_diff if it is available on the system
_nomad_diff_available = False
import importlib.util

nomad_diff_spec = importlib.util.find_spec("nomad_diff")
if nomad_diff_spec is not None:
    import nomad_diff

    _nomad_diff_available = True


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        state=dict(type="str", choices=["present", "absent", "purged"], default="present"),
        url=dict(type="str", required=True, fallback=(env_fallback, ["NOMAD_ADDR"])),
        validate_certs=dict(type="bool", default=True),
        connection_timeout=dict(type="int", default=10),
        management_token=dict(type="str", required=True, no_log=True, fallback=(env_fallback, ["NOMAD_TOKEN"])),
        name=dict(type="str"),
        namespace=dict(type="str", default="default"),
        hcl_spec=dict(type="str"),
    )

    # the AnsibleModule object
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[["name", "hcl_spec"]],
        required_one_of=[["name", "hcl_spec"]],
        required_if=[["state", "present", ["hcl_spec"]]],
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
        parsed_job = nomad.parse_job(json.dumps(dict(JobHCL=module.params.get("hcl_spec"))))
        job_id = parsed_job["ID"]

    existing_job = nomad.get_job(job_id)

    if module.params.get("state") in ("absent", "purged"):
        purged = False
        if module.params.get("state") == "purged":
            purged = True
        # if the job is already stopped but purge is set, we need to purge it.
        # also the job can still exist but not purged, in this case the
        # job has Stop set to True
        if (existing_job is not None and purged) or (existing_job is not None and not existing_job["Stop"]):
            result["changed"] = True
            result["diff"] = dict(
                before="Job ID {} in namespace {} will be STOPPED!\n".format(job_id, module.params.get("namespace")),
                after="",
            )
            # exit now if in check mode
            if module.check_mode:
                module.exit_json(**result)

            nomad.delete_job(job_id, purged)

    # we can rely on nomad plan to decide if we should submit a job ;)
    if module.params.get("state") == "present":
        plan = nomad.plan_job(
            job_id,
            json.dumps(
                dict(
                    Job=parsed_job,
                    Diff=True,
                )
            ),
        )

        # do a nice diff if the system has nomad_diff available
        if _nomad_diff_available and plan.get("Diff") is not None:
            try:
                result["diff"] = dict(prepared=nomad_diff.format(plan["Diff"], colors=True, verbose=False))
            except:
                # if we can't get a diff, it's not a big deal...
                pass

        # if nomad_diff is not available we can try to fallback to a manual diff
        elif plan.get("Diff") is not None and existing_job is not None:
            submission = nomad.get_job_submission(
                job_id,
                existing_job.get("Version", 1),
            )
            if submission is not None:
                result["diff"] = dict(
                    before=submission.get("Source"),
                    after=module.params.get("hcl_spec"),
                )

        if plan["Diff"].get("Type") != "None":
            result["changed"] = True
            # exit now if in check mode
            if module.check_mode:
                module.exit_json(**result)

            result["submit_response"] = nomad.create_or_update_job(
                job_id,
                json.dumps(
                    dict(
                        Job=parsed_job,
                        Submission=dict(
                            Format="hcl2",
                            Source=module.params.get("hcl_spec"),
                        ),
                    )
                ),
            )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
