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

from oslo_config import cfg

from ironic_inspector.common.i18n import _


PORT_PHYSNET_OPTS = [
    cfg.StrOpt(
        'ib_physnet',
        help=_('Name of the physical network that the Infiniband network is '
               'on')),
    cfg.ListOpt(
        'switch_sys_name_mapping',
        default=[],
        help=_('Comma-separated list of '
               '<switch system name>:<physical network> tuples mapping switch '
               'system names received via LLDP to a physical network to apply '
               'to ports that are connected to a switch with a matching '
               'system name.')),
]


cfg.CONF.register_opts(PORT_PHYSNET_OPTS, group='port_physnet')


def list_opts():
    return [
        ('port_physnet', PORT_PHYSNET_OPTS),
    ]
