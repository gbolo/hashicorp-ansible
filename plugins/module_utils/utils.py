# Copyright (c) George Bolo <gbolo@linuxctl.com>
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, division, print_function

__metaclass__ = type


def del_none(d):
    """
    Delete keys with the value ``None`` in a dictionary, recursively.
    Returns a copy of the input d.
    """
    cloned = d.copy()
    for key, value in list(cloned.items()):
        if value is None:
            del cloned[key]
        elif isinstance(value, dict):
            del_none(value)
    return cloned


def is_subset(subset, superset):
    """
    Returns True if subset is part of the superset.
    Essentially compares the dicts while ignoring missing fields ;)
    """

    # NOTE: match is not available until python 3.10. the target servers have python 3.9 ;(
    # match subset:
    #     case dict(_):
    #         return all(key in superset and is_subset(val, superset[key]) for key, val in subset.items())
    #     case list(_) | set(_):
    #         return all(any(is_subset(subitem, superitem) for superitem in superset) for subitem in subset)
    #     # assume that subset is a plain value if none of the above match
    #     case _:
    #         return subset == superset

    # using conditional statements instead
    if isinstance(subset, dict):
        return all(key in superset and is_subset(val, superset[key]) for key, val in subset.items())
    elif isinstance(subset, list):
        return all(any(is_subset(subitem, superitem) for superitem in superset) for subitem in subset)
    # assume that subset is a plain value if none of the above match
    else:
        return subset == superset
