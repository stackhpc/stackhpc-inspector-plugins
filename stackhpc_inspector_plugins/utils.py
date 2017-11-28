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


def parse_mappings(mapping_list):
    """Parse a list of mapping strings into a dictionary.

    Adapted from neutron_lib.utils.helpers.parse_mappings.

    :param mapping_list: A list of strings of the form '<key>:<value>'.
    :returns: A dict mapping keys to values or to list of values.
    :raises ValueError: Upon malformed data or duplicate keys.
    """
    mappings = {}
    for mapping in mapping_list:
        mapping = mapping.strip()
        if not mapping:
            continue
        split_result = mapping.split(':')
        if len(split_result) != 2:
            raise ValueError("Invalid mapping: '%s'" % mapping)
        key = split_result[0].strip()
        if not key:
            raise ValueError("Missing key in mapping: '%s'" % mapping)
        value = split_result[1].strip()
        if not value:
            raise ValueError("Missing value in mapping: '%s'" % mapping)
        if key in mappings:
            raise ValueError("Key %(key)s in mapping: '%(mapping)s' not "
                             "unique" % {'key': key, 'mapping': mapping})
        mappings[key] = value
    return mappings
