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

from oslo_config import cfg
from oslo_log import log as logging

from ironic.drivers.modules.inspector.hooks import base
from ironic.drivers.modules.inspector import lldp_parsers
from ironic import objects

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class IBPhysnetHook(base.InspectionHook):
    """Hook to set the port's physical_network field.

    Set the ironic port's physical_network field based on a CIDR to physical
    network mapping in the configuration.
    """

    dependencies = ['validate-interfaces']

    def get_physical_network(self, interface, plugin_data):
        """Return a physical network to apply to a port.

        :param port: The ironic port to patch.
        :param iface_name: Name of the interface.
        :param introspection_data: Introspection data.
        :returns: The physical network to set, or None.
        """
        iface_name = interface['name']
        proc_data = plugin_data['all_interfaces'][iface_name]
        if proc_data.get('client_id'):
            LOG.debug("Interface %s is an Infiniband port, physnet %s",
                      iface_name, CONF.port_physnet.ib_physnet)
            return CONF.port_physnet.ib_physnet

    def __call__(self, task, inventory, plugin_data):
        """Process inspection data and patch the port's physical network."""

        node_ports = objects.Port.list_by_node_id(task.context, task.node.id)
        ports_dict = {p.address: p for p in node_ports}

        for interface in inventory['interfaces']:
            if interface['name'] not in plugin_data['all_interfaces']:
                continue

            mac_address = interface['mac_address']
            port = ports_dict.get(mac_address)
            if not port:
                LOG.debug("Skipping physical network processing for interface "
                          "%s on node %s - matching port not found in Ironic.",
                          mac_address, task.node.uuid)
                continue

            # Determine the physical network for this port, using the interface
            # IPs and CIDR map configuration.
            phys_network = self.get_physical_network(interface, plugin_data)
            if phys_network is None:
                LOG.debug("Skipping physical network processing for interface "
                          "%s on node %s - no physical network mapping.",
                          mac_address,
                          task.node.uuid)
                continue

            if getattr(port, 'physical_network', '') != phys_network:
                port.physical_network = phys_network
                port.save()
                LOG.info('Updated physical_network of port %s to %s',
                         port.uuid, port.physical_network)


def parse_mappings(mapping_list):
    """Parse a list of mapping strings into a dictionary.

    Adapted from neutron_lib.utils.helpers.parse_mappings.

    :param mapping_list: A list of strings of the form '<key>:<value>'.
    :returns: A dict mapping keys to values or to list of values.
    :raises ValueError: Upon malformed data or duplicate keys.
    """
    mappings = {}
    for mapping in mapping_list:
        mapping = mapping.strip()
        if not mapping:
            continue
        split_result = mapping.split(':')
        if len(split_result) != 2:
            raise ValueError("Invalid mapping: '%s'" % mapping)
        key = split_result[0].strip()
        if not key:
            raise ValueError("Missing key in mapping: '%s'" % mapping)
        value = split_result[1].strip()
        if not value:
            raise ValueError("Missing value in mapping: '%s'" % mapping)
        if key in mappings:
            raise ValueError("Key %(key)s in mapping: '%(mapping)s' not "
                             "unique" % {'key': key, 'mapping': mapping})
        mappings[key] = value
    return mappings


class SystemNamePhysnetHook(IBPhysnetHook):
    """Inspector hook to assign ports a physical network based on switch name.

    This plugin uses the configuration option [port_physnet]
    switch_sys_name_mapping to map switch names to a physical network. If a
    port has received LLDP data with a switch system name in the mapping, the
    corresponding physical network will be applied to the port.
    """

    def _get_switch_sys_name_mapping(self):
        """Return a dict mapping switch system names to physical networks."""
        if not hasattr(self, '_switch_sys_name_mapping'):
            self._switch_sys_name_mapping = parse_mappings(
                CONF.port_physnet.switch_sys_name_mapping)
        return self._switch_sys_name_mapping

    def get_physical_network(self, interface, plugin_data):
        """Return a physical network to apply to a port.

        :param port: The ironic port to patch.
        :param iface_name: Name of the interface.
        :param introspection_data: Introspection data.
        :returns: The physical network to set, or None.
        """
        # Check if LLDP data was already processed by lldp_basic plugin
        # which stores data in 'all_interfaces'
        iface_name = interface['name']
        proc_data = plugin_data['all_interfaces'][iface_name]
        if 'parsed_lldp' not in proc_data:
            return

        lldp_proc = proc_data['parsed_lldp']

        # Switch system name mapping.
        switch_sys_name = lldp_proc.get(lldp_parsers.LLDP_SYS_NAME_NM)
        if switch_sys_name:
            mapping = self._get_switch_sys_name_mapping()
            if switch_sys_name in mapping:
                return mapping[switch_sys_name]
