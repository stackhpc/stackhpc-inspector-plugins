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

from unittest import mock

from ironic.conductor import task_manager
from ironic import objects
from ironic.tests.unit.db import base as db_base
from ironic.tests.unit.objects import utils as obj_utils
from ironic.conf import CONF
import testtools

from stackhpc_inspector_plugins.plugins import ib_physnet


_INTERFACE_1 = {
    'name': 'em0',
    'mac_address': '11:11:11:11:11:11',
    'ipv4_address': '192.168.10.1',
    'ipv6_address': '2001:db8::1',
}

_INTERFACE_2 = {
    'name': 'em1',
    'mac_address': '22:22:22:22:22:22',
    'ipv4_address': '192.168.12.2',
    'ipv6_address': 'fe80:5054::',
    'client_id': ('ff:00:00:00:00:00:02:00:00:02:c9:00:7c:fe:'
                  '90:03:00:3a:4b:0a'),
    'parsed_lldp': {
        'switch_system_name': 'switch-1',
    }
}

_INTERFACE_3 = {
    'name': 'em2',
    'mac_address': '33:33:33:33:33:33',
    'ipv4_address': '192.168.12.3',
    'ipv6_address': 'fe80::5054:ff:fea7:87:6482',
}

_INVENTORY = {
    'interfaces': [_INTERFACE_1, _INTERFACE_2, _INTERFACE_3]
}

_PLUGIN_DATA = {
    'all_interfaces': {'em0': _INTERFACE_1, 'em1': _INTERFACE_2}
}


class TestIBPhysnetHook(db_base.DbTestCase):
    def setUp(self):
        super().setUp()
        CONF.set_override('enabled_inspect_interfaces',
                          ['agent', 'no-inspect'])
        self.node = obj_utils.create_test_node(self.context,
                                               inspect_interface='agent')
        self.inventory = _INVENTORY
        self.plugin_data = _PLUGIN_DATA

    @mock.patch.object(objects.Port, 'list_by_node_id', autospec=True)
    def test_physical_network(self, mock_list_by_nodeid):
        CONF.set_override('ib_physnet', 'ibphysnet',
                          group='port_physnet')
        with task_manager.acquire(self.context, self.node.id) as task:
            port1 = obj_utils.create_test_port(self.context,
                                               address='11:11:11:11:11:11',
                                               node_id=self.node.id)
            port2 = obj_utils.create_test_port(
                self.context, id=988,
                uuid='2be26c0b-03f2-4d2e-ae87-c02d7f33c781',
                address='22:22:22:22:22:22', node_id=self.node.id)
            ports = [port1, port2]

            mock_list_by_nodeid.return_value = ports

            ib_physnet.IBPhysnetHook().__call__(
                task, self.inventory, self.plugin_data)

            port1.refresh()
            port2.refresh()
            self.assertEqual(port2.physical_network, 'ibphysnet')
            self.assertIsNone(port1.physical_network)


class TestSystemNamePhysnetHook(db_base.DbTestCase):
    def setUp(self):
        super().setUp()
        CONF.set_override('enabled_inspect_interfaces',
                          ['agent', 'no-inspect'])
        self.node = obj_utils.create_test_node(self.context,
                                               inspect_interface='agent')
        self.inventory = _INVENTORY
        self.plugin_data = _PLUGIN_DATA

    @mock.patch.object(objects.Port, 'list_by_node_id', autospec=True)
    def test_physical_network(self, mock_list_by_nodeid):
        sys_name_mapping = 'switch-1:ibphysnet,switch-2:physnet2'
        CONF.set_override('switch_sys_name_mapping', sys_name_mapping,
                          group='port_physnet')
        with task_manager.acquire(self.context, self.node.id) as task:
            port1 = obj_utils.create_test_port(self.context,
                                               address='11:11:11:11:11:11',
                                               node_id=self.node.id)
            port2 = obj_utils.create_test_port(
                self.context, id=988,
                uuid='2be26c0b-03f2-4d2e-ae87-c02d7f33c781',
                address='22:22:22:22:22:22', node_id=self.node.id)
            ports = [port1, port2]

            mock_list_by_nodeid.return_value = ports

            ib_physnet.SystemNamePhysnetHook().__call__(
                task, self.inventory, self.plugin_data)

            port1.refresh()
            port2.refresh()
            self.assertEqual(port2.physical_network, 'ibphysnet')
            self.assertIsNone(port1.physical_network)

    def parse(self, mapping_list):
        return ib_physnet.parse_mappings(mapping_list)

    def test_parse_mappings_fails_for_missing_separator(self):
        with testtools.ExpectedException(ValueError):
            self.parse(['key'])

    def test_parse_mappings_fails_for_missing_key(self):
        with testtools.ExpectedException(ValueError):
            self.parse([':val'])

    def test_parse_mappings_fails_for_missing_value(self):
        with testtools.ExpectedException(ValueError):
            self.parse(['key:'])

    def test_parse_mappings_fails_for_extra_separator(self):
        with testtools.ExpectedException(ValueError):
            self.parse(['key:val:junk'])

    def test_parse_mappings_fails_for_duplicate_key(self):
        with testtools.ExpectedException(ValueError):
            self.parse(['key:val1', 'key:val2'])

    def test_parse_mappings_succeeds_for_one_mapping(self):
        self.assertEqual({'key': 'val'}, self.parse(['key:val']))

    def test_parse_mappings_succeeds_for_n_mappings(self):
        self.assertEqual({'key1': 'val1', 'key2': 'val2'},
                         self.parse(['key1:val1', 'key2:val2']))

    def test_parse_mappings_succeeds_for_duplicate_value(self):
        self.assertEqual({'key1': 'val', 'key2': 'val'},
                         self.parse(['key1:val', 'key2:val']))

    def test_parse_mappings_succeeds_for_no_mappings(self):
        self.assertEqual({}, self.parse(['']))
