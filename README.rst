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

System Name Local Link Connection
---------------------------------

The ``system_name_llc`` plugin uses LLDP data gathered by the discovery ramdisk
to populate the ``switch_info`` field of the ``local_link_connection``
attribute of ironic ports.  The field is populated with the contents of the
system name LLDP TLV if it was received by that port.
