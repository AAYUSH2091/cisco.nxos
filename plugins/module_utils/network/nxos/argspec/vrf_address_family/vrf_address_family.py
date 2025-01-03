# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function


__metaclass__ = type

#############################################
#                WARNING                    #
#############################################
#
# This file is auto generated by the
# ansible.content_builder.
#
# Manually editing this file is not advised.
#
# To update the argspec make the desired changes
# in the documentation in the module file and re-run
# ansible.content_builder commenting out
# the path to external 'docstring' in build.yaml.
#
##############################################

"""
The arg spec for the nxos_vrf_address_family module
"""


class Vrf_address_familyArgs(object):  # pylint: disable=R0903
    """The arg spec for the nxos_vrf_address_family module"""

    argument_spec = {
        "config": {
            "type": "list",
            "elements": "dict",
            "options": {
                "name": {"type": "str", "required": True},
                "address_families": {
                    "type": "list",
                    "elements": "dict",
                    "options": {
                        "afi": {"type": "str", "choices": ["ipv4", "ipv6"]},
                        "safi": {
                            "type": "str",
                            "choices": ["multicast", "unicast"],
                        },
                        "maximum": {
                            "type": "dict",
                            "options": {
                                "max_routes": {"type": "int"},
                                "max_route_options": {
                                    "type": "dict",
                                    "mutually_exclusive": [
                                        ["warning_only", "threshold"],
                                    ],
                                    "options": {
                                        "warning_only": {"type": "bool"},
                                        "threshold": {
                                            "type": "dict",
                                            "options": {
                                                "threshold_value": {"type": "int"},
                                                "reinstall_threshold": {
                                                    "type": "int",
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                        "route_target": {
                            "type": "list",
                            "elements": "dict",
                            "mutually_exclusive": [["import", "export"]],
                            "options": {
                                "import": {"type": "str"},
                                "export": {"type": "str"},
                            },
                        },
                        "export": {
                            "type": "list",
                            "elements": "dict",
                            "mutually_exclusive": [["map", "vrf"]],
                            "options": {
                                "map": {"type": "str"},
                                "vrf": {
                                    "type": "dict",
                                    "options": {
                                        "max_prefix": {"type": "int"},
                                        "map_import": {"type": "str"},
                                        "allow_vpn": {"type": "bool"},
                                    },
                                },
                            },
                        },
                        "import": {
                            "type": "list",
                            "elements": "dict",
                            "mutually_exclusive": [["map", "vrf"]],
                            "options": {
                                "map": {"type": "str"},
                                "vrf": {
                                    "type": "dict",
                                    "options": {
                                        "max_prefix": {"type": "int"},
                                        "map_import": {"type": "str"},
                                        "advertise_vpn": {"type": "bool"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
        "running_config": {"type": "str"},
        "state": {
            "choices": [
                "parsed",
                "gathered",
                "deleted",
                "purged",
                "merged",
                "replaced",
                "rendered",
                "overridden",
            ],
            "default": "merged",
            "type": "str",
        },
    }  # pylint: disable=C0301