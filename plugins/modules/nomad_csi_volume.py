#!/usr/bin/python
# Copyright (c) George Bolo <gbolo@linuxctl.com>
# SPDX-License-Identifier: MIT


import json

from ansible.module_utils.basic import AnsibleModule, env_fallback

from ..module_utils.nomad import NomadAPI
from ..module_utils.utils import del_none, is_subset


def run_module():
    # define available arguments/parameters a user can pass to the module
    mount_options_spec = dict(
        fs_type=dict(type="str", aliases=["FSType"]),
        mount_flags=dict(type="list", elements="str", aliases=["MountFlags"]),
    )
    capabilities_spec = dict(
        access_mode=dict(type="str", aliases=["AccessMode"], required=True),
        attachment_mode=dict(type="str", aliases=["AttachmentMode"], required=True),
    )
    module_args = dict(
        state=dict(type="str", choices=["present", "absent"], default="present"),
        url=dict(type="str", required=True, fallback=(env_fallback, ["NOMAD_ADDR"])),
        validate_certs=dict(type="bool", default=True),
        connection_timeout=dict(type="int", default=10),
        management_token=dict(type="str", required=True, no_log=True, fallback=(env_fallback, ["NOMAD_TOKEN"])),
        id=dict(type="str", required=True),
        name=dict(type="str", required=True),
        namespace=dict(type="str", default="default"),
        plugin_id=dict(type="str", required=True),
        mount_options=dict(type="dict", required=False, options=mount_options_spec),
        capabilities=dict(type="list", required=True, elements="dict", options=capabilities_spec),
        capacity_gb=dict(type="int", required=False),
        parameters=dict(type="dict", required=False),
    )

    # seed the final result dict in the object. Default nothing changed ;)
    result = dict(
        changed=False,
        mismatched=False,
    )

    # the AnsibleModule object
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    # the NomadAPI can init itself via the module args
    nomad = NomadAPI(module)

    # NOTE: csi volumes CANNOT be modified after being created!
    #       this module does not report any mismatches in desired
    #       state vs the actual state. However it does output the
    #       volume spec along with a mismatched bool that can be
    #       inspected by the caller.

    desired_volume = del_none(
        dict(
            ID=module.params.get("id"),
            Name=module.params.get("name"),
            Namespace=module.params.get("namespace"),
            PluginID=module.params.get("plugin_id"),
            Parameters=module.params.get("parameters"),
        )
    )
    if module.params.get("capabilities") is not None:
        capabilities = []
        for c in module.params.get("capabilities"):
            capabilities.append(
                dict(
                    AccessMode=c.get("access_mode"),
                    AttachmentMode=c.get("attachment_mode"),
                )
            )
        desired_volume["RequestedCapabilities"] = capabilities

    if module.params.get("mount_options") is not None:
        desired_volume["MountOptions"] = del_none(
            dict(
                FsType=module.params.get("mount_options").get("fs_type"),
                MountFlags=module.params.get("mount_options").get("mount_flags"),
            )
        )

    volume_id = module.params.get("id")
    existing_volume = nomad.get_csi_volume(volume_id)

    if module.params.get("state") == "absent":
        if existing_volume is not None:
            nomad.delete_csi_volume(volume_id)
            result["changed"] = True

    if module.params.get("state") == "present":
        # NOTE: remember we cannot modify existing CSI volumes.
        #       simply report the mismatch.
        if existing_volume is not None:
            if not is_subset(desired_volume, existing_volume):
                result["mismatched"] = True
        else:
            request_body = {"Volumes": [desired_volume]}
            result["volume"] = nomad.create_csi_volume(volume_id, json.dumps(request_body))
            result["changed"] = True

    # post final results
    if result.get("volume") is None and existing_volume is not None:
        result["volume"] = existing_volume

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
