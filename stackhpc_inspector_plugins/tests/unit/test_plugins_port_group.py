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

from unittest import mock

from ironic.conductor import task_manager
from ironic import objects
from ironic.tests.unit.db import base as db_base
from ironic.tests.unit.objects import utils as obj_utils
from ironic.conf import CONF

from stackhpc_inspector_plugins.plugins import port_group


class TestPortGroupHook(db_base.DbTestCase):
    def setUp(self):
        super().setUp()
        CONF.set_override('enabled_inspect_interfaces',
                          ['agent', 'no-inspect'])
        self.node = obj_utils.create_test_node(self.context,
                                               inspect_interface='agent')

    @mock.patch.object(objects.Port, 'list_by_node_id', autospec=True)
    def test_port_group_works(self, mock_list_by_nodeid):
        CONF.set_override('port_group_switches',
                          ['my_switch_1', 'my_switch_2'],
                          group='port_group')
        with task_manager.acquire(self.context, self.node.id) as task:
            port1 = obj_utils.create_test_port(self.context,
                                               address='11:11:11:11:11:11',
                                               node_id=self.node.id)
            port2 = obj_utils.create_test_port(
                self.context, id=988,
                uuid='2be26c0b-03f2-4d2e-ae87-c02d7f33c781',
                address='22:22:22:22:22:22', node_id=self.node.id,
                local_link_connection={
                    'switch_info': 'my_switch_1',
                })
            port3 = obj_utils.create_test_port(
                self.context, id=989,
                uuid='2be26c0b-03f2-4d2e-ae87-c02d7f33c784',
                address='22:22:22:22:22:23', node_id=self.node.id,
                local_link_connection={
                    'switch_info': 'my_switch_2',
                })
            port4 = obj_utils.create_test_port(
                self.context, id=990,
                uuid='2be26c0b-03f2-4d2e-ae87-c02d7f33c786',
                address='22:22:22:22:22:24', node_id=self.node.id,
                local_link_connection={
                    'switch_info': 'my_switch_3',
                })
            port5 = obj_utils.create_test_port(
                self.context, id=991,
                uuid='2be26c0b-03f2-4d2e-ae87-c02d7f33c788',
                address='22:22:22:22:22:25', node_id=self.node.id,
                local_link_connection={
                    'foo': 'bar',
                })
            ports = [port1, port2, port3, port4, port5]
            mock_list_by_nodeid.return_value = ports

            port_group.PortGroupsHook().__call__(
                task, {}, {})

            port1.refresh()
            port2.refresh()
            port3.refresh()
            self.assertEqual(port1.portgroup_id, None)

            new_port_groups = objects.Portgroup.list_by_node_id(
                self.context, self.node.id)
            self.assertEqual(len(new_port_groups), 1)
            new_port_group = new_port_groups[0]

            self.assertEqual(port2.portgroup_id, new_port_group.id)
            self.assertEqual(port3.portgroup_id, new_port_group.id)
            self.assertEqual(port2.address, new_port_group.address)

    @mock.patch.object(objects.Port, 'list_by_node_id', autospec=True)
    def test_port_group_skip_three_ports(self, mock_list_by_nodeid):
        CONF.set_override('port_group_switches',
                          ['my_switch_1', 'my_switch_2'],
                          group='port_group')
        with task_manager.acquire(self.context, self.node.id) as task:
            port1 = obj_utils.create_test_port(self.context,
                                               address='11:11:11:11:11:11',
                                               node_id=self.node.id)
            port2 = obj_utils.create_test_port(
                self.context, id=988,
                uuid='2be26c0b-03f2-4d2e-ae87-c02d7f33c781',
                address='22:22:22:22:22:22', node_id=self.node.id,
                local_link_connection={
                    'switch_info': 'my_switch_1',
                })
            port3 = obj_utils.create_test_port(
                self.context, id=989,
                uuid='2be26c0b-03f2-4d2e-ae87-c02d7f33c784',
                address='22:22:22:22:22:23', node_id=self.node.id,
                local_link_connection={
                    'switch_info': 'my_switch_1',
                })
            port4 = obj_utils.create_test_port(
                self.context, id=990,
                uuid='2be26c0b-03f2-4d2e-ae87-c02d7f33c786',
                address='22:22:22:22:22:24', node_id=self.node.id,
                local_link_connection={
                    'switch_info': 'my_switch_1',
                })
            port5 = obj_utils.create_test_port(
                self.context, id=991,
                uuid='2be26c0b-03f2-4d2e-ae87-c02d7f33c788',
                address='22:22:22:22:22:25', node_id=self.node.id,
                local_link_connection={
                    'foo': 'bar',
                })
            ports = [port1, port2, port3, port4, port5]
            mock_list_by_nodeid.return_value = ports

            port_group.PortGroupsHook().__call__(
                task, {}, {})

            port1.refresh()
            port2.refresh()
            port3.refresh()
            self.assertEqual(port1.portgroup_id, None)
            # check no port group created
            new_port_groups = objects.Portgroup.list_by_node_id(
                self.context, self.node.id)
            self.assertEqual(len(new_port_groups), 0)
            self.assertIsNone(port2.portgroup_id)
            self.assertIsNone(port3.portgroup_id)
