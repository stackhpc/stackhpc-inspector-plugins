=================================
StackHPC Ironic Inspector Plugins
=================================

This repository hosts plugins for use with the OpenStack Hardware Discovery
service, ironic inspector.

* Free software: Apache license
* Source: http://github.com/stackhpc/stackhpc-inspector-plugins
* Bugs: http://github.com/stackhpc/stackhpc-inspector-plugins/issues
* Documentation: https://github.com/stackhpc/ironic-inspector/blob/master/README.rst

Plugins
=======

Infiniband Physical Network
---------------------------

The ``ib_physnet`` plugin populates the ``physical_network`` field of ironic
ports determined to be Infiniband ports. Ports with a ``client-id`` field
in their ``extra`` attribute are determined to be IB ports.

The plugin is configured via the option ``[port_physnet] ib_physnet``, which is
the name of the physical network to apply.

System Name Local Link Connection
---------------------------------

The ``system_name_llc`` plugin uses LLDP data gathered by the discovery ramdisk
to populate the ``switch_info`` field of the ``local_link_connection``
attribute of ironic ports.  The field is populated with the contents of the
system name LLDP TLV if it was received by that port.

System Name Physical Network
----------------------------

The ``system_name_physnet`` plugin uses LLDP data gathered by the discovery
ramdisk to populate the ``physical_network`` field of ironic ports.

The plugin is configured via the option ``[port_physnet]
switch_sys_name_mapping``, which is a comma-separated list of ``<switch system
name>:<physical network>`` tuples.  If the switch system name LLDP TLV received
by a port matches an item in the mapping, the corresponding physical network
will be applied to the port.

Port Speed Physical Network
---------------------------

The ``port_speed_physnet`` plugin uses the interface speed reported by the
``extra-hardware`` collector in the discovery ramdisk to populate the
``physical_network`` field of ironic ports.

The plugin is configured via the option ``[port_physnet]
port_speed_mapping``, which is a comma-separated list of ``<port speed
>:<physical network>`` tuples.  If the interface speed reported by
``extra-hardware`` matches an item in the mapping, the corresponding physical
network will be applied to the port.

Usage
=====

This project is hosted on PyPI, and may be installed via pip:

.. code-block::

   pip install stackhpc-inspector-plugins
