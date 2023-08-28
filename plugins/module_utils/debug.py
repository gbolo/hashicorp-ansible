# Copyright (c) George Bolo <gbolo@linuxctl.com>
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import inspect
import logging
import os

#
# This logger can only be enabled if env var ANSIBLE_DEBUG_LOGGER_ENABLED
# is set to true or yes. This will write debug logs to /tmp/DEBUG_ANSIBLE.log
# NOTE: the log file is on the host that ran the playbook not the
# control host (unless it was delegated locally).
#
# You can do this in the playbook for example:
#
# - name: bootstrap nomad acl token
#   nomad_acl_bootstrap:
#     url: http://127.0.0.1:4646
#     management_token: 28900e6d-6715-4ee8-9e1a-84ea086ac906
#   environment:
#     ANSIBLE_DEBUG_LOGGER_ENABLED: true
#

ENV_VAR = "ANSIBLE_DEBUG_LOGGER_ENABLED"
LOG_FILE = "/tmp/DEBUG_ANSIBLE.log"
DEBUG_LOGGER_ENABLED = os.environ.get(ENV_VAR, "").lower() in ["yes", "true"]

REQUEST_LOG_TEMPLATE = """Caller: {caller_func} ({caller_file})\n
REQUEST:\n{method} {url}\n{request_body}\n
RESPONSE:\n{status}\n{response_body}\n\n\n"""

if DEBUG_LOGGER_ENABLED:
    logging.basicConfig(
        filename=LOG_FILE,
        filemode="a",
        format="[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d @ %H:%M:%S",
        level=logging.DEBUG,
    )


def log_request(module, url, method, request_body=None, status=None, response_body=None):
    if DEBUG_LOGGER_ENABLED:
        # Emit a warning if this is enabled!
        module.warn("{var} is enabled! Sensitive information may be logged to disk!".format(var=ENV_VAR))

        logging.debug(
            REQUEST_LOG_TEMPLATE.format(
                caller_file=os.path.basename(inspect.currentframe().f_back.f_code.co_filename),
                caller_func=inspect.currentframe().f_back.f_code.co_name,
                url=url,
                method=method,
                request_body=request_body,
                status=status,
                response_body=response_body,
            )
        )
