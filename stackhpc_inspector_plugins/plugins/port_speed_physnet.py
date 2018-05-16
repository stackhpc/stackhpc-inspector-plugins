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

from ironic_inspector import utils
from oslo_config import cfg

from stackhpc_inspector_plugins.plugins import base_physnet
from stackhpc_inspector_plugins import utils as sip_utils

LOG = utils.getProcessingLogger(__name__)

CONF = cfg.CONF


class PortSpeedPhysnetHook(base_physnet.BasePhysnetHook):
    """Inspector hook to assign ports a physical network based on ????

    This plugin uses the configuration option [port_physnet]
    port_speed_mapping to map ports to a physical network by their speed.
    This relies on data returned by the extra-hardware collector, and added to
    the introspection data by the extra-hardware plugin.
    """

    def _get_port_speed_mapping(self):
        """Return a dict mapping port speeds to physical networks."""
        if not hasattr(self, '_port_speed_mapping'):
            self._port_speed_mapping = sip_utils.parse_mappings(
                CONF.port_physnet.port_speed_mapping)
        return self._port_speed_mapping

    def get_physnet(self, port, iface_name, introspection_data):
        """Return a physical network to apply to a port.

        :param port: The ironic port to patch.
        :param iface_name: Name of the interface.
        :param introspection_data: Introspection data.
        :returns: The physical network to set, or None.
        """
        extra = introspection_data.get('extra')
        if not extra:
            LOG.warn("'extra' field not present in introspection data - "
                     "cannot check network interface information")
            return

        interface = extra.get('network', {}).get(iface_name)
        if not interface:
            LOG.warn("Interface %s not present in extra introspection data - "
                     "cannot check physical network mapping for port speed",
                     iface_name)
            return

        speed = interface.get('speed')
        if not speed:
            LOG.warn("Interface %s has not reported a speed in its "
                     "introspection data - cannot check physical network "
                     "mapping for port speed", iface_name)
            return

        mapping = self._get_port_speed_mapping()
        return mapping.get(speed)
