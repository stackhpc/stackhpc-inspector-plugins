# Copyright (c) 2018 StackHPC Ltd.
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

from ironic_inspector import utils
from oslo_config import cfg

from stackhpc_inspector_plugins.plugins import base_physnet

LOG = utils.getProcessingLogger(__name__)

CONF = cfg.CONF


class IBPhysnetHook(base_physnet.BasePhysnetHook):
    """Inspector hook to assign ports a physical network for IB interfaces.

    This plugin sets the physical network for ports that are determined to be
    Infiniband ports.  The physical network is given by the configuration
    option [port_physnet] ib_physnet.
    """

    def get_physnet(self, port, iface_name, introspection_data):
        """Return a physical network to apply to a port.

        :param port: The ironic port to patch.
        :param iface_name: Name of the interface.
        :param introspection_data: Introspection data.
        :returns: The physical network to set, or None.
        """
        proc_data = introspection_data['all_interfaces'][iface_name]
        if proc_data.get('client_id'):
            LOG.debug("Interface %s is an Infiniband port, physnet %s",
                      iface_name, CONF.port_physnet.ib_physnet)
            return CONF.port_physnet.ib_physnet
