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

from stackhpc_inspector_plugins.plugins import pxe_physnet


class TestPXEPhysnetHook(test_base.NodeTest):

    def setUp(self):
        super(TestPXEPhysnetHook, self).setUp()
        self.hook = pxe_physnet.PXEPhysnetHook()
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
                    'pxe': True,
                },
            }
        }

        ports = [mock.Mock(spec=['address', 'uuid', 'physical_network'],
                           address=a, physical_network='physnet1')
                 for a in ('11:11:11:11:11:11',)]
        self.node_info = node_cache.NodeInfo(uuid=self.uuid, started_at=0,
                                             node=self.node, ports=ports)

    def test_expected_data_pxe(self):
        cfg.CONF.set_override('pxe_physnet', 'physnet1',
                              group='port_physnet')
        port = self.node_info.ports().values()[0]
        physnet = self.hook.get_physnet(port, 'em1', self.data)
        self.assertEqual(physnet, 'physnet1')

    def test_expected_data_non_pxe(self):
        cfg.CONF.set_override('pxe_physnet', 'physnet1',
                              group='port_physnet')
        self.data['all_interfaces']['em1']['pxe'] = False
        port = self.node_info.ports().values()[0]
        physnet = self.hook.get_physnet(port, 'em1', self.data)
        self.assertIsNone(physnet)
