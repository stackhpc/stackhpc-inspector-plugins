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
from ironic_inspector import utils
from oslo_config import cfg

from stackhpc_inspector_plugins.plugins import system_name_llc


class TestSystemNameLocalLinkConnectionHook(test_base.NodeTest):
    hook = system_name_llc.SystemNameLocalLinkConnectionHook()

    def setUp(self):
        super(TestSystemNameLocalLinkConnectionHook, self).setUp()
        self.data = {
            'inventory': {
                'interfaces': [{
                    'name': 'em1', 'mac_address': '11:11:11:11:11:11',
                    'ipv4_address': '1.1.1.1',
                    'lldp': [
                        (0, ''),
                        (5, '7377697463682d31')  # switch-1
                    ]
                }],
                'cpu': 1,
                'disks': 1,
                'memory': 1
            },
            'all_interfaces': {
                'em1': {},
            }
        }

        llc = {
            'switch_info': 'switch-2'
        }

        ports = [mock.Mock(spec=['address', 'uuid', 'local_link_connection'],
                           address=a, local_link_connection=llc)
                 for a in ('11:11:11:11:11:11',)]
        self.node_info = node_cache.NodeInfo(uuid=self.uuid, started_at=0,
                                             node=self.node, ports=ports)

    @mock.patch.object(node_cache.NodeInfo, 'patch_port')
    def test_expected_data(self, mock_patch):
        patches = [
            {'path': '/local_link_connection/switch_info',
             'value': 'switch-1', 'op': 'add'},
        ]
        self.hook.before_update(self.data, self.node_info)
        self.assertCalledWithPatch(patches, mock_patch)

    @mock.patch.object(node_cache.NodeInfo, 'patch_port')
    def test_invalid_system_name_subtype(self, mock_patch):
        # The system name is a UTF-8 encoded string.
        self.data['inventory']['interfaces'][0]['lldp'][1] = (5, 'c328')
        patches = []
        self.hook.before_update(self.data, self.node_info)
        self.assertCalledWithPatch(patches, mock_patch)

    @mock.patch.object(node_cache.NodeInfo, 'patch_port')
    def test_lldp_none(self, mock_patch):
        self.data['inventory']['interfaces'][0]['lldp'] = None
        patches = []
        self.hook.before_update(self.data, self.node_info)
        self.assertCalledWithPatch(patches, mock_patch)

    @mock.patch.object(node_cache.NodeInfo, 'patch_port')
    def test_interface_not_in_all_interfaces(self, mock_patch):
        self.data['all_interfaces'] = {}
        patches = []
        self.hook.before_update(self.data, self.node_info)
        self.assertCalledWithPatch(patches, mock_patch)

    @mock.patch.object(node_cache.NodeInfo, 'patch_port')
    def test_interface_not_in_ironic(self, mock_patch):
        self.node_info._ports = {}
        patches = []
        self.hook.before_update(self.data, self.node_info)
        self.assertCalledWithPatch(patches, mock_patch)

    def test_no_inventory(self):
        del self.data['inventory']
        self.assertRaises(utils.Error, self.hook.before_update,
                          self.data, self.node_info)

    @mock.patch.object(node_cache.NodeInfo, 'patch_port')
    def test_no_overwrite(self, mock_patch):
        cfg.CONF.set_override('overwrite_existing', False, group='processing')
        patches = []
        self.hook.before_update(self.data, self.node_info)
        self.assertCalledWithPatch(patches, mock_patch)

    @mock.patch.object(node_cache.NodeInfo, 'patch_port')
    def test_processed_data_available(self, mock_patch):
        self.data['all_interfaces'] = {
            'em1': {
                "ip": self.ips[0], "mac": self.macs[0],
                "lldp_processed": {
                    "switch_system_name": "switch-1",
                }
            }
        }

        patches = [
            {'path': '/local_link_connection/switch_info',
             'value': 'switch-1', 'op': 'add'},
        ]
        self.hook.before_update(self.data, self.node_info)
        self.assertCalledWithPatch(patches, mock_patch)
