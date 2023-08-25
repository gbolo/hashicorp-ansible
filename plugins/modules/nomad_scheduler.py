#!/usr/bin/python
# Copyright (c) George Bolo <gbolo@linuxctl.com>
# SPDX-License-Identifier: MIT


from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.nomad import NomadAPI
from ansible.module_utils.utils import del_none, is_subset

import json


def run_module():
    # define available arguments/parameters a user can pass to the module
    preemption_config_spec = dict(
        system_scheduler_enabled=dict(type="bool", aliases=["SystemSchedulerEnabled"], default=True),
        sys_batch_scheduler_enabled=dict(type="bool", aliases=["SysBatchSchedulerEnabled"], default=False),
        batch_scheduler_enabled=dict(type="bool", aliases=["BatchSchedulerEnabled"], default=False),
        service_scheduler_enabled=dict(type="bool", aliases=["ServiceSchedulerEnabled"], default=False),
    )
    module_args = dict(
        url=dict(type="str", required=True, fallback=(env_fallback, ["NOMAD_ADDR"])),
        validate_certs=dict(type="bool", default=True),
        connection_timeout=dict(type="int", default=10),
        management_token=dict(
            type="str", required=True, no_log=True, fallback=(env_fallback, ["NOMAD_TOKEN"])
        ),
        scheduler_algorithm=dict(type="str", choices=["binpack", "spread"], default='binpack'),
        memory_oversubscription_enabled=dict(type="bool", default=False),
        reject_job_registration=dict(type="bool", default=False),
        pause_eval_broker=dict(type="bool", default=False),
        preemption_config=dict(type=dict, aliases=["PreemptionConfig"], options=preemption_config_spec),
    )

    # seed the final result dict in the object. Default nothing changed ;)
    result = dict(
        changed=False,
    )

    # the AnsibleModule object
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    # the NomadAPI can init itself via the module args
    nomad = NomadAPI(module)

    existing_config = nomad.get_scheduler_config().get('SchedulerConfig')
    desired_config = dict(
        SchedulerAlgorithm=module.params.get("scheduler_algorithm"),
        MemoryOversubscriptionEnabled=module.params.get("memory_oversubscription_enabled"),
        RejectJobRegistration=module.params.get("reject_job_registration"),
        PauseEvalBroker=module.params.get("pause_eval_broker"),
        PreemptionConfig=dict(
            SystemSchedulerEnabled=module.params.get("preemption_config").get("system_scheduler_enabled"),
            SysBatchSchedulerEnabled=module.params.get("preemption_config").get("sys_batch_scheduler_enabled"),
            BatchSchedulerEnabled=module.params.get("preemption_config").get("batch_scheduler_enabled"),
            ServiceSchedulerEnabled=module.params.get("preemption_config").get("service_scheduler_enabled"),
        ),
    )
    if not is_subset(desired_config, existing_config):
        nomad.update_scheduler_config(json.dumps(desired_config))
        result["changed"] = True
  
    result["scheduler_config"] = desired_config
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
