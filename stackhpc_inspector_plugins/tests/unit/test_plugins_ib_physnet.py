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

import mock

from ironic_inspector import node_cache
from ironic_inspector.test import base as test_base
from oslo_config import cfg

from stackhpc_inspector_plugins.plugins import ib_physnet


class TestIBPhysnetHook(test_base.NodeTest):

    def setUp(self):
        super(TestIBPhysnetHook, self).setUp()
        self.hook = ib_physnet.IBPhysnetHook()
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
                    'client_id': ('ff:00:00:00:00:00:02:00:00:02:c9:00:7c:fe:'
                                  '90:03:00:3a:4b:0a'),
                },
            }
        }

        ports = [mock.Mock(spec=['address', 'uuid', 'physical_network'],
                           address=a, physical_network='physnet1')
                 for a in ('11:11:11:11:11:11',)]
        self.node_info = node_cache.NodeInfo(uuid=self.uuid, started_at=0,
                                             node=self.node, ports=ports)

    def test_expected_data_ib(self):
        cfg.CONF.set_override('ib_physnet', 'physnet1',
                              group='port_physnet')
        port = self.node_info.ports().values()[0]
        physnet = self.hook.get_physnet(port, 'em1', self.data)
        self.assertEqual(physnet, 'physnet1')

    def test_expected_data_client_id_is_none(self):
        cfg.CONF.set_override('ib_physnet', 'physnet1',
                              group='port_physnet')
        self.data['all_interfaces']['em1']['client_id'] = None
        port = self.node_info.ports().values()[0]
        physnet = self.hook.get_physnet(port, 'em1', self.data)
        self.assertIsNone(physnet)

    def test_expected_data_no_client_id(self):
        cfg.CONF.set_override('ib_physnet', 'physnet1',
                              group='port_physnet')
        del self.data['all_interfaces']['em1']['client_id']
        port = self.node_info.ports().values()[0]
        physnet = self.hook.get_physnet(port, 'em1', self.data)
        self.assertIsNone(physnet)
