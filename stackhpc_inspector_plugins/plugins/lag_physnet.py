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

LOG = utils.getProcessingLogger(__name__)

CONF = cfg.CONF


class LAGPhysnetHook(base_physnet.BasePhysnetHook):
    """Inspector hook to assign ports a physical network for LAG members.

    This plugin sets the physical network for ports that are members of a link
    aggregate group (determined by recieved LLDP data).  The physical network
    is given by the configuration option [port_physnet] lag_physnet.
    """

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
            LOG.debug("Interface %s received no LLDP data, skipping physnet "
                      "mapping", iface_name)
            return

        lldp_proc = proc_data['lldp_processed']

        # Switch system name mapping.
        lag_enabled = lldp_proc.get(lldp_parsers.LLDP_PORT_LINK_AGG_ENABLED_NM)
        if lag_enabled:
            LOG.debug("Interface %s is a link aggregate member, physnet %s",
                      iface_name, CONF.port_physnet.lag_physnet)
            return CONF.port_physnet.lag_physnet
