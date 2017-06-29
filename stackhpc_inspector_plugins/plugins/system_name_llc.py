# Copyright (c) 2017 StackHPC Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""System name LLDP Processing Hook"""

import binascii

from ironic_inspector.common import lldp_parsers
from ironic_inspector.common import lldp_tlvs as tlv
from ironic_inspector.plugins import base
from ironic_inspector import utils
from oslo_config import cfg

LOG = utils.getProcessingLogger(__name__)

CONF = cfg.CONF

SYSTEM_NAME_ITEM_NAME = "switch_info"

LLDP_PROC_DATA_MAPPING = {lldp_parsers.LLDP_SYS_NAME_NM: SYSTEM_NAME_ITEM_NAME}


class SystemNameLocalLinkConnectionHook(base.ProcessingHook):
    """Process the system name LLDP packet field and set as switch_info.

    Some Neutron drivers expect the switch_info field in a port's
    local_link_connection attribute to contain the system name of a switch.
    This plugin will store the system name received via LLDP (if present) in
    the switch_info field of the Ironic port's local_link_connection attribute.

    It should be noted that some Neutron mechanism drivers expect switch_info
    to contain something other than the system name, in which case this plugin
    should not be used.
    """

    def _get_local_link_patch(self, tlv_type, tlv_value, port, node_info):
        try:
            data = bytearray(binascii.unhexlify(tlv_value))
        except TypeError:
            LOG.warning("TLV value for TLV type %d not in correct"
                        "format, ensure TLV value is in "
                        "hexidecimal format when sent to "
                        "inspector", tlv_type, node_info=node_info)
            return

        item = value = None
        if tlv_type == tlv.LLDP_TLV_SYS_NAME:
            try:
                sys_name = tlv.SysName.parse(data)
            except UnicodeDecodeError as e:
                LOG.warning("TLV parse error for System Name: %s", e,
                            node_info=node_info)
                return

            item = SYSTEM_NAME_ITEM_NAME
            value = sys_name.value

        if item and value:
            if (not CONF.processing.overwrite_existing and
                    item in port.local_link_connection):
                return
            return {'op': 'add',
                    'path': '/local_link_connection/%s' % item,
                    'value': value}

    def _get_lldp_processed_patch(self, name, item, lldp_proc_data, port):

        if 'lldp_processed' not in lldp_proc_data:
            return

        value = lldp_proc_data['lldp_processed'].get(name)

        if value:
            if (not CONF.processing.overwrite_existing and
                    item in port.local_link_connection):
                return
            return {'op': 'add',
                    'path': '/local_link_connection/%s' % item,
                    'value': value}

    def before_update(self, introspection_data, node_info, **kwargs):
        """Process LLDP data and patch Ironic port local link connection"""
        inventory = utils.get_inventory(introspection_data)

        ironic_ports = node_info.ports()

        for iface in inventory['interfaces']:
            if iface['name'] not in introspection_data['all_interfaces']:
                continue

            mac_address = iface['mac_address']
            port = ironic_ports.get(mac_address)
            if not port:
                LOG.debug("Skipping LLC processing for interface %s, matching "
                          "port not found in Ironic.", mac_address,
                          node_info=node_info, data=introspection_data)
                continue

            lldp_data = iface.get('lldp')
            if lldp_data is None:
                LOG.warning("No LLDP Data found for interface %s",
                            mac_address, node_info=node_info,
                            data=introspection_data)
                continue

            patches = []
            # First check if lldp data was already processed by lldp_basic
            # plugin which stores data in 'all_interfaces'
            proc_data = introspection_data['all_interfaces'][iface['name']]

            for name, item in LLDP_PROC_DATA_MAPPING.items():
                patch = self._get_lldp_processed_patch(name, item,
                                                       proc_data, port)
                if patch is not None:
                    patches.append(patch)

            # If no processed lldp data was available then parse raw lldp data
            if not patches:
                for tlv_type, tlv_value in lldp_data:
                    patch = self._get_local_link_patch(tlv_type, tlv_value,
                                                       port, node_info)
                    if patch is not None:
                        patches.append(patch)

            node_info.patch_port(port, patches)
