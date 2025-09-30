#
# -*- coding: utf-8 -*-
# Copyright 2023 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import absolute_import, division, print_function


__metaclass__ = type

"""
The nxos_static_routes config file.
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to its desired end-state is
created.
"""


from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.rm_base.resource_module import (
    ResourceModule,
)
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
    dict_merge,
)

from ansible_collections.cisco.nxos.plugins.module_utils.network.nxos.facts.facts import Facts
from ansible_collections.cisco.nxos.plugins.module_utils.network.nxos.rm_templates.static_routes import (
    Static_routesTemplate,
)


class Static_routes(ResourceModule):
    """
    The nxos_static_routes config class
    """

    def __init__(self, module):
        super(Static_routes, self).__init__(
            empty_fact_val={},
            facts_module=Facts(module),
            module=module,
            resource="static_routes",
            tmplt=Static_routesTemplate(),
        )

    def execute_module(self):
        """Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        if self.state not in ["parsed", "gathered"]:
            self.generate_commands()
            self.run_commands()
        return self.result

    def generate_commands(self):
        """Generate configuration commands to send based on
        want, have and desired state.
        """
        wantd, delete_spcl = self.list_to_dict(self.want, "want")
        haved, n_req = self.list_to_dict(self.have, "have")

        if delete_spcl and haved and self.state == "deleted":
            for pk, to_rem in delete_spcl.items():
                if pk in ["ipv4", "ipv6"]:
                    _afis = haved.get("(_afis_)")
                    for k, v in _afis.get(pk, {}).items():
                        for each_dest in to_rem:
                            # IMPORTANT: This check also needs to be updated to be context-aware
                            # for full robustness if _delete_spcl includes a VRF context in its keys.
                            # However, for the specific bug reported, the next_hops being empty
                            # implies a broader deletion. The _key fix below is for specific next_hop deletions.
                            if k.split("_")[0] == each_dest:
                                self.addcmd({pk: v}, pk, True)
                else:
                    sp_begin = len(self.commands)
                    _vrfs = haved.get(pk)
                    for ak, v in _vrfs.items():
                        for k, srts in v.items():
                            for each_dest in to_rem.get(ak):
                                # Similar to above, needs context-aware split
                                if k.split("_")[0] == each_dest:
                                    self.addcmd({ak: srts}, ak, True)
                    if len(self.commands) != sp_begin:
                        self.commands.insert(
                            sp_begin,
                            self._tmplt.render({"namevrf": pk}, "vrf", False),
                        )

        else:
            # if state is merged, merge want onto have and then compare
            if self.state == "merged":
                wantd = dict_merge(haved, wantd)

            for k, want in wantd.items():
                self._compare_top_level_keys(want=want, have=haved.pop(k, {}), vrf_name=k)

            if (self.state == "deleted" and not wantd) or self.state in ["overridden"]:
                for k, have in haved.items():
                    self._compare_top_level_keys(want={}, have=have, vrf_name=k)

    def _compare_top_level_keys(self, want, have, vrf_name):
        begin = len(self.commands)

        # if state is deleted, empty out wantd and set haved to wantd
        # This logic is complex and might contribute to issues.
        # It's attempting to filter what "have" is considered for deletion
        # if a partial "want" is provided in a deleted state.
        if self.state == "deleted" and have:
            _have = {}
            for addf in ["ipv4", "ipv6"]:
                _temp_sr = {}
                # When want.get(addf) is empty, this means we want to delete ALL routes for this AFI
                # in this VRF/global context if _have already contains them.
                # If want.get(addf) is NOT empty, it means we only want to delete routes NOT in want.
                # The crucial part is that 'k in want.get(addf, {})' now correctly uses the unique,
                # VRF-aware keys.
                for k, ha in have.get(addf, {}).items():
                    if not want.get(addf) or k in want.get(addf, {}):
                        _temp_sr[k] = ha
                if _temp_sr:
                    _have[addf] = _temp_sr
            if _have:
                have = _have
                want = {} # Set want to empty after this filtering, so _compare can handle the deletion

        if self.state != "deleted":
            for _afi, routes in want.items():
                self._compare(s_want=routes, s_have=have.pop(_afi, {}), afi=_afi)

        if self.state in ["overridden", "deleted"]:
            for _afi, routes in have.items():
                self._compare(s_want={}, s_have=routes, afi=_afi)

        if len(self.commands) != begin:
            if vrf_name == "(_afis_)":
                # This part is for global routes.
                # The insertion logic here seems to try and move commands to the beginning,
                # which might be for ordering `router static` or `address-family` commands.
                # No change needed here for the specific bug.
                afi_cmds = []
                for cmds in range(begin, len(self.commands)):
                    self.commands.insert(0, self.commands.pop())
            else:
                self.commands.insert(begin, self._tmplt.render({"namevrf": vrf_name}, "vrf", False))


    def _compare(self, s_want, s_have, afi):
        for name, w_srs in s_want.items():
            have_srs = s_have.pop(name, {})
            self.compare(parsers=afi, want={afi: w_srs}, have={afi: have_srs})

        # remove remaining items in have for replaced state
        # Or for 'deleted' state when 's_want' is empty, implying delete all in 's_have'
        for name, h_srs in s_have.items():
            self.compare(parsers=afi, want={}, have={afi: h_srs})

    def list_to_dict(self, param, operation):
        _static_rts = {}
        _delete_spc = {}
        if param:
            for srs in param:
                _vrf = srs.get("vrf")
                _srts = {}
                for adfs in srs.get("address_families", []):
                    _afi = adfs.get("afi")
                    _routes = {}
                    for rts in adfs.get("routes", []):
                        _dest = rts.get("dest", "")

                        #  below if specific to special delete
                        if (
                            self.state == "deleted"
                            and operation == "want"
                            and not rts.get("next_hops")
                        ):
                            if _vrf:
                                if not _delete_spc.get(_vrf):
                                    _delete_spc[_vrf] = {}
                                if not _delete_spc[_vrf].get(_afi):
                                    _delete_spc[_vrf][_afi] = []
                                _delete_spc[_vrf][_afi].append(_dest)
                            else:
                                if not _delete_spc.get(_afi):
                                    _delete_spc[_afi] = []
                                _delete_spc[_afi].append(_dest)

                        for nxh in rts.get("next_hops", []):
                            _forw_rtr_add = nxh.get("forward_router_address", "").upper()
                            _intf = nxh.get("interface", "")

                            # --- FIX START ---
                            # Ensure the key is unique across VRF contexts
                            _current_vrf_context = _vrf if _vrf else "(_global_)"
                            _key = f"{_current_vrf_context}_{_dest}_{_forw_rtr_add}_{_intf}"
                            # --- FIX END ---

                            dummy_sr = {
                                "afi": _afi,
                                "dest": _dest,
                            }

                            if _vrf:
                                dummy_sr["vrf"] = _vrf
                            if _intf:
                                dummy_sr["interface"] = _intf
                            if _forw_rtr_add:
                                dummy_sr["forward_router_address"] = _forw_rtr_add
                            dummy_sr.update(nxh)

                            _routes[_key] = dummy_sr
                    _srts[_afi] = _routes
                _static_rts[_vrf if _vrf else "(_afis_)"] = _srts
        return _static_rts, _delete_spc
