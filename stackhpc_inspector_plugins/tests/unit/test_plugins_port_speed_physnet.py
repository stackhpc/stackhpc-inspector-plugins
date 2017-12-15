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

from stackhpc_inspector_plugins.plugins import port_speed_physnet


class TestPortSpeedPhysnetHook(test_base.NodeTest):

    def setUp(self):
        super(TestPortSpeedPhysnetHook, self).setUp()
        self.hook = port_speed_physnet.PortSpeedPhysnetHook()
        self.data = {
            'inventory': {
                'cpu': 1,
                'disks': 1,
                'memory': 1
            },
            'extra': {
                'network': {
                    'em1': {
                        'speed': '10Gbit/s'
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
        port_speed_mapping = '10Gbit/s:physnet1,40Gbit/s:physnet2'
        cfg.CONF.set_override('port_speed_mapping', port_speed_mapping,
                              group='port_physnet')
        port = self.node_info.ports().values()[0]
        physnet = self.hook.get_physnet(port, 'em1', self.data)
        self.assertEqual(physnet, 'physnet1')

    def test_no_extra(self):
        del self.data['extra']
        port = self.node_info.ports().values()[0]
        physnet = self.hook.get_physnet(port, 'em1', self.data)
        self.assertIsNone(physnet)

    def test_no_extra_network(self):
        del self.data['extra']['network']
        port = self.node_info.ports().values()[0]
        physnet = self.hook.get_physnet(port, 'em1', self.data)
        self.assertIsNone(physnet)

    def test_no_extra_interface(self):
        del self.data['extra']['network']['em1']
        port = self.node_info.ports().values()[0]
        physnet = self.hook.get_physnet(port, 'em1', self.data)
        self.assertIsNone(physnet)

    def test_no_mapping(self):
        port_speed_mapping = '40Gbit/s:physnet1'
        cfg.CONF.set_override('port_speed_mapping', port_speed_mapping,
                              group='port_physnet')
        port = self.node_info.ports().values()[0]
        physnet = self.hook.get_physnet(port, 'em1', self.data)
        self.assertIsNone(physnet)

    def test_invalid_mapping(self):
        sys_name_mapping = '10Gbit/s:physnet1,10Gbit/s:physnet2'
        cfg.CONF.set_override('port_speed_mapping', sys_name_mapping,
                              group='port_physnet')
        port = self.node_info.ports().values()[0]
        self.assertRaises(ValueError,
                          self.hook.get_physnet, port, 'em1', self.data)
