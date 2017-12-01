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

from ironic_inspector.common import lldp_parsers
from ironic_inspector import utils
from oslo_config import cfg

from stackhpc_inspector_plugins.plugins import base_physnet
from stackhpc_inspector_plugins import utils as sip_utils

LOG = utils.getProcessingLogger(__name__)

CONF = cfg.CONF


class SystemNamePhysnetHook(base_physnet.BasePhysnetHook):
    """Inspector hook to assign ports a physical network based on switch name.

    This plugin uses the configuration option [port_physnet]
    switch_sys_name_mapping to map switch names to a physical network. If a
    port has received LLDP data with a switch system name in the mapping, the
    corresponding physical network will be applied to the port.
    """

    def _get_switch_sys_name_mapping(self):
        """Return a dict mapping switch system names to physical networks."""
        if not hasattr(self, '_switch_sys_name_mapping'):
            self._switch_sys_name_mapping = sip_utils.parse_mappings(
                CONF.port_physnet.switch_sys_name_mapping)
        return self._switch_sys_name_mapping

    def get_physnet(self, port, iface_name, introspection_data):
        """Return a physical network to apply to a port.

        :param port: The ironic port to patch.
        :param iface_name: Name of the interface.
        :param introspection_data: Introspection data.
        :returns: The physical network to set, or None.
        """
        # Check if LLDP data was already processed by lldp_basic plugin
        # which stores data in 'all_interfaces'
        proc_data = introspection_data['all_interfaces'][iface_name]
        if 'lldp_processed' not in proc_data:
            return

        lldp_proc = proc_data['lldp_processed']

        # Switch system name mapping.
        switch_sys_name = lldp_proc.get(lldp_parsers.LLDP_SYS_NAME_NM)
        if switch_sys_name:
            mapping = self._get_switch_sys_name_mapping()
            if switch_sys_name in mapping:
                return mapping[switch_sys_name]
