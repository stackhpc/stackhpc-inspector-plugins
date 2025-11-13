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
from oslo_utils import uuidutils

from ironic.drivers.modules.inspector.hooks import base
from ironic import objects

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class PortGroupsHook(base.InspectionHook):
    """Hook to set add port groups based on switch name"""

    dependencies = ['validate-interfaces']

    def __call__(self, task, inventory, plugin_data):
        """Process inspection data and patch the port's physical network."""

        node_port_groups = objects.Portgroup.list_by_node_id(
            task.context, task.node.id)
        if len(node_port_groups) > 0:
            LOG.debug("Node %s already has port groups defined, skipping "
                      "port group creation.", task.node.uuid)
            return

        candidate_ports = []
        node_ports = objects.Port.list_by_node_id(task.context, task.node.id)
        for port in node_ports:
            if not port.local_link_connection:
                LOG.debug("Port %s has no local link connection data, "
                          "skipping.", port.uuid)
                continue

            switch_name = port.local_link_connection.get('switch_info', {})
            if not switch_name:
                LOG.debug("Port %s has no switch info in local link "
                          "connection data, skipping.", port.uuid)
                continue

            if switch_name not in CONF.port_group.port_group_switches:
                LOG.debug("Port %s connected to switch %s which is not in "
                          "the configured port group switches, skipping.",
                          port.uuid, switch_name)
                continue

            candidate_ports.append(port)

        if len(candidate_ports) != 2:
            LOG.debug("Found %d candidate ports for port group creation on "
                      "node %s, need exactly 2, skipping port group "
                      "creation.", len(candidate_ports), task.node.uuid)
            return

        # sort list by mac address
        candidate_ports.sort(key=lambda p: p.address)

        # create port group
        new_port_group = objects.Portgroup(
            task.context,
            uuid=uuidutils.generate_uuid(),
            mode=CONF.port_group.port_group_mode,
            node_id=task.node.id,
            address=candidate_ports[0].address,
            standalone_ports_supported=True,
            physical_network=candidate_ports[0].physical_network)
        new_port_group.create()
        new_port_group.refresh()
        LOG.info("Created port group %s on node %s",
                 new_port_group.uuid, task.node.uuid)

        for port in candidate_ports:
            port.portgroup_id = new_port_group.id
            port.save()
            LOG.info("Added port %s to port group %s",
                     port.uuid, new_port_group.uuid)
