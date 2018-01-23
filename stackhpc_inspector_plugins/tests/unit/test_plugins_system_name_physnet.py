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

import mock

from ironic_inspector import node_cache
from ironic_inspector.test import base as test_base
from oslo_config import cfg

from stackhpc_inspector_plugins.plugins import system_name_physnet


class TestSystemNamePhysnetHook(test_base.NodeTest):

    def setUp(self):
        super(TestSystemNamePhysnetHook, self).setUp()
        self.hook = system_name_physnet.SystemNamePhysnetHook()
        self.data = {
            'inventory': {
                'interfaces': [{
                    'name': 'em1', 'mac_address': '11:11:11:11:11:11',
                    'ipv4_address': '1.1.1.1',
                }],
                'cpu': 1,
                'disks': 1,
                'memory': 1
            },
            'all_interfaces': {
                'em1': {
                    'lldp_processed': {
                        'switch_system_name': 'switch-1',
                    }
                }
            }
        }

        ports = [mock.Mock(spec=['address', 'uuid', 'physical_network'],
                           address=a, physical_network='physnet1')
                 for a in ('11:11:11:11:11:11',)]
        self.node_info = node_cache.NodeInfo(uuid=self.uuid, started_at=0,
                                             node=self.node, ports=ports)

    def test_expected_data(self):
        sys_name_mapping = 'switch-1:physnet1,switch-2:physnet2'
        cfg.CONF.set_override('switch_sys_name_mapping', sys_name_mapping,
                              group='port_physnet')
        port = self.node_info.ports().values()[0]
        physnet = self.hook.get_physnet(port, 'em1', self.data)
        self.assertEqual(physnet, 'physnet1')

    def test_no_lldp_processed(self):
        del self.data['all_interfaces']['em1']['lldp_processed']
        port = self.node_info.ports().values()[0]
        physnet = self.hook.get_physnet(port, 'em1', self.data)
        self.assertIsNone(physnet)

    def test_no_lldp_system_name(self):
        proc_data = self.data['all_interfaces']['em1']
        del proc_data['lldp_processed']['switch_system_name']
        port = self.node_info.ports().values()[0]
        physnet = self.hook.get_physnet(port, 'em1', self.data)
        self.assertIsNone(physnet)

    def test_no_mapping(self):
        sys_name_mapping = 'switch-2:physnet2'
        cfg.CONF.set_override('switch_sys_name_mapping', sys_name_mapping,
                              group='port_physnet')
        port = self.node_info.ports().values()[0]
        physnet = self.hook.get_physnet(port, 'em1', self.data)
        self.assertIsNone(physnet)

    def test_invalid_mapping(self):
        sys_name_mapping = 'switch-2:physnet1,switch-2:physnet2'
        cfg.CONF.set_override('switch_sys_name_mapping', sys_name_mapping,
                              group='port_physnet')
        port = self.node_info.ports().values()[0]
        self.assertRaises(ValueError,
                          self.hook.get_physnet, port, 'em1', self.data)
