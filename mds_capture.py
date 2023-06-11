#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2022, 2023 Broadcom.  All rights reserved.
#
# NOT BROADCOM SUPPORTED
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may also obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
:mod:`mds_capture` - Converts Nexus-OS CLI responses | json to FOS API which are added to brcddb class objects.

**Description**

This was developed for a specific project to migrate the zone database from Cisco to Brocade. That project only required
basic zone analysis and simple zone migrations. The customer did not use (and therefore these are not interpreted by
this script):

    * Inter-VSAN Routing (IVR)
    * Smart zones (sort of equivalent to peer zones)
    * FCIP fabrics

Copy and paste all the commands below into an SSH session with an MDS switch. Code was added to parse the output when
the pipe to JSON is not supported so this should work regardless of the NX-OS code level.

    show fcdomain | json | no-more
    show fabric switch information | json | no-more
    show interface brief | json | no-more
    show flogi database details | json | no-more
    show fdmi database detail | json | no-more
    show device-alias database | json | no-more
    show zoneset | json | no-more
    show zoneset active | json | no-more
    show fcns database | json | no-more

The log file with the output of these commands should be the input file, -i option, when running this script.

**Warnings**

    * This script does a simple text search for a command prompt followed by the commands above. Backspaces and cursor
      control are not interpreted. Always copy and paste the commands to avoid typos and other errors.
    * This script relies on finding the command prompt, -p option. Often, the first command is not preceded with the
      command prompt so you will need to copy the command prompt and paste it in front of the first command.
    * Do not include any other command output

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 1.0.0     | 22 Jan 2021   | Initial Launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.1     | 22 Jun 2022   | Added # -*- coding: utf-8 -*-. Updated comments. Added error messages.            |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.2     | 24 Oct 2022   | Fixed issues when json output is not available.                                   |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.3     | 01 Jan 2023   | Fixed empty zoneset error                                                         |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.4     | 01 Jun 2023   | Fixed alias bug with multiple VSANs                                               |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2022, 2023 Broadcom'
__date__ = '01 Jun 2023'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '1.0.4'

import argparse
import json
import datetime
import sys
import pprint
import brcdapi.log as brcdapi_log
import brcdapi.file as brcdapi_file
import brcdapi.gen_util as gen_util
import brcddb.brcddb_common as brcddb_common
import brcddb.brcddb_project as brcddb_project
import brcddb.util.copy as brcddb_copy
import brcddb.util.util as brcddb_util
import brcddb.util.obj_convert as brcddb_convert
import brcddb.brcddb_port as brcddb_port
import brcddb.util.parse_nx as parse_nx

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = False  # When True, use _DEBUG_xxx instead of passed arguments
_DEBUG_i = 'sacz_0/sdc_sanprd_100.txt'
_DEBUG_o = 'sacz_0/sacz_0'
_DEBUG_p = 'sdc-sanprd-100'
_DEBUG_log = '_logs'
_DEBUG_nl = False

# Allowable VSAN numbers exceed the range of allowable FID numbers so this is used to map VSANs to FIDs.
_vsan_to_fid_map = {1: 128}
_chassis_name = ''
_chassis_obj = None
_vsan_to_switch_wwn = dict()


# Utility Methods

def _key_match(test_d, key, buf):
    """Checks to see if buf begins with key

    :param test_d: Dictionary of NX-OS keys (should be the pointer to _nexus_to_fos)
    :type test_d: dict
    :param key: The in test_d we're looking to match
    :type key: str
    :param buf: The input line buffer
    :type buf: str
    :return: True if there is a match. Otherwise False
    :rtype: bool
    """
    len_key, len_buf = len(key), len(buf)
    if len_buf >= len_key and buf[0: len_key] == key:
        # Make sure the beginning of key doesn't match a longer key. For example: 'show zoneset' will match
        # 'show zoneset active'
        for test_key in test_d.keys():
            len_test_key = len(test_key)
            if len_test_key > len_key and len_buf >= len_test_key and buf[0: len_test_key] == test_key:
                return False
        return True

    return False


# Methods to convert values used in _nexus_to_fos
def _vsan_id_to_vf_id(obj, v):
    global _vsan_to_fid_map
    return _vsan_to_fid_map[v]


def _principal_switch(obj, v):
    return 0 if 'Subordinated' in v else 1


def _domain_id(obj, v):
    try:
        return int(gen_util.non_decimal.sub('', v[v.find('('):]))
    except (AttributeError, ValueError, TypeError, IndexError):
        return None


def _port_speed(obj, v):
    try:
        return int(v) * 1000000000
    except ValueError:
        return 32000000000


def _add_neighbor(obj, v):  # $ToDO - What do NPIV logins look like?, How do a I add base WWN first?
    neighbor_d = obj.r_get('fibrechannel/neighbor')
    wwn_l = neighbor_d.get('wwn')
    if wwn_l is None:
        wwn_l = list()
        neighbor_d.update(dict(wwn=wwn_l))
    wwn_l.append(v)
    return None


def _clean_port_ref(obj, v):
    return v.replace('fc', '')


# def _vsan_fcdomain(obj, v):
#     global _chassis_name, _vsan_to_fid_map
#
#     base_name = _chassis_name + '_vsan_' + str(v)
#     brcddb_util.add_to_obj(obj, 'brocade-fibrechannel-switch/fibrechannel-switch/user-friendly-name',
#                            base_name + '_sw')
#     brcddb_util.add_to_obj(obj, 'brocade-fabric/fabric-switch/switch-user-friendly-name', base_name + '_sw')
#     brcddb_util.add_to_obj(obj, 'brocade-fibrechannel-switch/fibrechannel-switch/fabric-user-friendly-name',
#                            base_name + '_fab')
#     brcddb_util.add_to_obj(obj, 'brocade-fibrechannel-logical-switch/fibrechannel-logical-switch/default-switch-status',
#                            1 if v == 1 else 0)
#
#     return _vsan_to_fid_map[v]


def _add_keys(obj, fos_d, nexus_d):
    """Adds a key value pair returned from Nexus to the equivalent FOS key value pair

    :param obj: The brcddb class object or list of objects the keys are to be added to
    :type obj: brcddb.classes.chassis.ChassisObj,  brcddb.classes.fabric.FabricObj,  brcddb.classes.switch.SwitchObj, \
                brcddb.classes.login.LoginObj,  brcddb.classes.port.PortObj,  brcddb.classes.zone.ZoneCfgObj, \
                ZoneCfgObj.zone.ZoneObj, ZoneObj.zone.AliasObj, None
    :param fos_d: Pointer to conv_d table in _nexus_to_fos
    :type fos_d: dict
    :param nexus_d: Key value pairs from Nexus to be converted and added to FOS
    :type nexus_d: dict
    """
    for k, nexus_v in nexus_d.items():

        # Get the conversion dictionary
        conv_d = fos_d.get(k)
        if not isinstance(conv_d, dict):
            continue  # Not all NX_OS keys are converted to a FOS key

        # Convert the NX_OS value to a FOS value
        v = conv_d.get('v')
        if isinstance(v, dict):
            dv = conv_d.get('dv')
            v = v[nexus_v] if nexus_v in v else dv(obj, nexus_v) if callable(dv) else dv if 'dv' in conv_d else nexus_v
        else:
            v = nexus_v if v is None else v(obj, nexus_v) if callable(v) else v

        # Get the brcddb class object(s) to work on
        obj_l = gen_util.convert_to_list(obj) if conv_d.get('o') is None else \
            brcddb_convert.obj_extract(obj, conv_d.get('o'))

        # Add the value to the brcddb object
        for brcddb_obj in obj_l:
            for fos_k in gen_util.convert_to_list(conv_d.get('bk')):
                brcddb_util.add_to_obj(brcddb_obj, fos_k, v)


def _vsan_to_fid(vsan):
    """Converts a VSAN number to a FID number.

    :param vsan: VSAN or list of VSAN numbers to add to _vsan_to_fid_map
    :type vsan: list, int
    """
    global _vsan_to_fid_map

    # If possible, make the FID = VSAN ID if the VSAN ID is a valid FID number
    vl = gen_util.convert_to_list(vsan)
    for vsan_id in [v for v in vl if v < 128] + [v for v in vl if v >= 128]:
        if vsan_id not in _vsan_to_fid_map:
            if vsan_id < 128 and vsan_id not in _vsan_to_fid_map.values():
                _vsan_to_fid_map.update({vsan_id: vsan_id})
            else:  # Find an unused FID to use chossing a valid FID number if possible
                for fid in range(1, 99999999):  # Max FID for FOS is 128 but Nexus-OS can have thousands
                    if fid not in _vsan_to_fid_map.values():
                        _vsan_to_fid_map.update({vsan_id: fid})
                        break


################################################################################
#
#                     Methods for 'ja' in _nexus_to_fos.
#
################################################################################

def _show_interface_brief_json(proj_obj, c_out, conv_d, row):
    """Convert "show interface brief" to equivalent FOS API dictionaries

    :param proj_obj: Project Object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :param c_out: NX-OS command output
    :type c_out: dict
    :param conv_d: Table to convert NX-OS output to FOS. See conv_d in _nexus_to_fos for details
    :type conv_d: dict
    :param row: Row number of input file. Used for error reporting.
    :type row: int
    :return: List of equivalent FOS API dictionaries
    :rtype: list
    """
    global _vsan_to_switch_wwn

    for port_d in c_out['TABLE_interface_brief_fc']['ROW_interface_brief_fc']:

        vsan = port_d.get('vsan_brief') if port_d.get('vsan') is None else port_d.get('vsan')
        if vsan is None:
            continue

        switch_obj = proj_obj.r_switch_obj(_vsan_to_switch_wwn.get(int(vsan)))
        if switch_obj is not None:  # It's None when the ISL is to a virtual E-Port (FC-IP)
            interface = port_d.get('interface_fc') if port_d.get('interface') is None else port_d.get('interface')
            _add_keys(switch_obj.s_add_port(interface.replace('fc', '')), conv_d, port_d)


def _show_fcdomain_json(proj_obj, c_out, conv_d, row):
    """Convert "show fcdomain" to equivalent FOS API dictionaries. See _show_interface_brief_json()"""
    global _chassis_name, _vsan_to_fid_map, _vsan_to_switch_wwn, _chassis_obj

    switch_l = c_out['TABLE_switch_status']['ROW_switch_status']
    _vsan_to_fid([switch.get('vsan_id') for switch in switch_l])  # Convert all the VSAN numbers to FIDs
    switch_obj = None
    for switch_d in switch_l:
        for table_d in gen_util.convert_to_list(switch_d.get('TABLE_localswitch_run_info')):
            for row_d in gen_util.convert_to_list(table_d.get('ROW_localswitch_run_info')):
                fabric_wwn = row_d.get('running_fabric_name')
                if isinstance(fabric_wwn, str):
                    fab_obj = proj_obj.s_add_fabric(fabric_wwn)
                    switch_wwn = row_d.get('local_switch_wwn')
                    _vsan_to_switch_wwn.update({switch_d['vsan_id']: switch_wwn})
                    switch_obj = fab_obj.s_add_switch(switch_wwn)
                    if _chassis_obj is None:
                        # I don't need the chassis WWN. I just need a unique chassis reference so this is good enough
                        _chassis_obj = proj_obj.s_add_chassis(switch_wwn)
                        brcddb_util.add_to_obj(_chassis_obj, 'brocade-chassis/chassis/chassis-user-friendly-name',
                                               _chassis_name)
                    _chassis_obj.s_add_switch(switch_wwn)
                if switch_obj is None:
                    brcdapi_log.exception('Missing "running_fabric_name"', echo=True)
                    return
                _add_keys(switch_obj, conv_d, row_d)
                switch_obj.rs_key('brocade-fibrechannel-logical-switch/fibrechannel-logical-switch/fabric-id',
                                  _vsan_to_fid_map[switch_d['vsan_id']])


def _show_flogi_database_detail_json(proj_obj, c_out, conv_d, row):
    """Convert "show flogi database detail" to equivalent FOS API dictionaries. See _show_interface_brief_json()"""
    global _vsan_to_switch_wwn

    for port in c_out['TABLE_flogi_entry']['ROW_flogi_entry']:
        switch_wwn = _vsan_to_switch_wwn.get(int(port['vsan']))
        if switch_wwn is not None:  # It's None when the ISL is to a virtual E-Port (FC-IP)
            switch_obj = proj_obj.r_switch_obj(switch_wwn)
            _add_keys(switch_obj.s_add_port(port['interface'].replace('fc', '')), 'show_flogi_database_details', port)
            fabric_obj = switch_obj.r_fabric_obj()
            login_obj = fabric_obj.s_add_login(port['port_name'])
            brcddb_util.add_to_obj(login_obj, 'brocade-name-server/port-id', port['fcid'])
            brcddb_util.add_to_obj(login_obj, 'brocade-name-server/node-name', port['node_name'])
            brcddb_util.add_to_obj(login_obj, 'brocade-name-server/port-name', port['port_name'])


def _show_zoneset_json(proj_obj, c_out, conv_d, row):
    """Convert "show zoneset" to equivalent FOS API dictionaries. See _show_interface_brief_json()"""
    for zoneset_d in gen_util.convert_to_list(c_out['TABLE_zoneset']['ROW_zoneset']):

        # Some sanity checks
        zoneset_name = zoneset_d.get('zoneset_name') if zoneset_d.get('name') is None else zoneset_d.get('name')
        if zoneset_name is None:
            brcdapi_log.exception('Could not get zoneset name.', echo=True)
            continue
        vsan = zoneset_d.get('zoneset_vsan_id') if zoneset_d.get('vsan_id') is None else zoneset_d.get('vsan_id')
        if vsan is None:
            brcdapi_log.exception('Could not find vsan in zoneset.', echo=True)
            continue

        # Add the zoning information to the fabric object
        fabric_obj = proj_obj.r_switch_obj(_vsan_to_switch_wwn[vsan]).r_fabric_obj()

        # Add any aliases - I should have gotten them all in _show_device_alias_database_json() but just in case...
        # alias_d = zoneset_d.get('zoneset_alias')
        # if isinstance(alias_d, dict):
        #     for alias, mem_l in zoneset_d['zoneset_alias'].items():
        #         fabric_obj.s_add_alias(alias, gen_util.remove_duplicates(mem_l))

        zone_l = list()
        try:
            for zone_d in gen_util.convert_to_list(zoneset_d['TABLE_zone']['ROW_zone']):
                zone_name = zone_d.get('zone_name') if zone_d.get('name') is None else zone_d.get('name')
                if zone_name is None:
                    brcdapi_log.exception('Could not find zone name.', echo=True)
                    continue
                try:
                    index_0 = 'TABLE_member' if 'TABLE_member' in zone_d else 'TABLE_zone_member'
                    index_1 = 'ROW_member' if 'ROW_member' in zone_d[index_0] else 'ROW_zone_member'
                    zone_mem_l = zone_d[index_0][index_1]
                except (TypeError, KeyError):
                    brcdapi_log.exception('Could not find zone member list in ' + zone_name, echo=True)
                    continue
                fabric_obj.s_add_zone(zone_name,
                                      0,
                                      [mem_d.get('wwn') if mem_d.get('dev_alias') is None else mem_d.get('dev_alias')
                                       for mem_d in zone_mem_l])
                zone_l.append(zone_name)
        except KeyError:
            pass  # There are no zones in this zoneset.

        fabric_obj.s_add_zonecfg(zoneset_name, zone_l)


def _show_device_alias_database_json(proj_obj, c_out, conv_d, row):
    """Convert "show device-alias database" to equivalent FOS API dictionaries. See _show_interface_brief_json()"""
    global _chassis_obj

    # Cisco only has one alias DB per chassis. Adding the alias to all fabrics keeps it simple
    for alias_d in c_out['TABLE_device_alias_database']['ROW_device_alias_database']:
        for fab_obj in _chassis_obj.r_fabric_objects():
            fab_obj.s_add_alias(alias_d['dev_alias_name'], alias_d['pwwn'])


def _show_zoneset_active_json(proj_obj, c_out, conv_d, row):
    """Convert "show zoneset active" to equivalent FOS API dictionaries. See _show_interface_brief_json()"""
    for zoneset in gen_util.convert_to_list(c_out['TABLE_zoneset']['ROW_zoneset']):
        zoneset_name = zoneset.get('zoneset_name') if zoneset.get('name') is None else zoneset.get('name')
        if zoneset_name is None:
            brcdapi_log.exception('Could not get zoneset name.', echo=True)
            continue
        vsan = zoneset.get('zoneset_vsan_id') if zoneset.get('vsan_id') is None else zoneset.get('vsan_id')
        if vsan is None:
            brcdapi_log.exception('Could not find vsan in zoneset.', echo=True)
            continue
        fabric_obj = proj_obj.r_switch_obj(_vsan_to_switch_wwn[vsan]).r_fabric_obj()
        zone_l = list()
        enabled_zone = list()
        for zone in zoneset['TABLE_zone']['ROW_zone']:

            # I don't care if they are online or offline. I'm going to process both lists the same way.
            mem_d_l = list()
            for temp_d in (dict(t='TABLE_online_member', r='ROW_online_member'),
                           dict(t='TABLE_member', r='ROW_member')):
                for table_d in gen_util.convert_to_list(zone.get(temp_d['t'])):
                    mem_d_l.extend(gen_util.convert_to_list(table_d.get(temp_d['r'])))

            zone_name = zone.get('zone_name') if zone.get('name') is None else zone.get('name')
            if not isinstance(zone_name, str):
                brcdapi_log.exception('Could not find zone name or zone name.', echo=True)
                continue

            # I can't think of a reason why mem_d.get('wwn') would ever be None but just in case...
            mem_l = [mem_d['wwn'] for mem_d in mem_d_l if mem_d.get('wwn') is not None]
            fabric_obj.s_add_eff_zone(zone_name, 0, mem_l)
            zone_l.append(zone_name)
            for mem_d in mem_d_l:
                port_obj = brcddb_port.port_obj_for_wwn(proj_obj, mem_d.get('wwn'))
                if port_obj is not None and mem_d.get('dev_type'):  # IDK why either wouldn't be found
                    port_obj.s_new_key('cisco_dev_type', mem_d.get('dev_type'))
            enabled_zone.append({'member-entry': {'entry-name': mem_l},
                                 'zone-name': zone_name,
                                 'zone-type': 0,
                                 'zone-type-string': 'zone'})

        # Add the effective zones and zone configurations to the fabric object
        fabric_obj.s_add_eff_zonecfg(zone_l)
        effective_config = {
            'cfg-name': zoneset_name,
            'checksum': '0',
            'db-avail': 0,
            'db-chassis-wide-committed': 0,
            'db-committed': 0,
            'db-max': 0,
            'db-transaction': 0,
            'default-zone-access': 1,
            # 'enabled-zone': enabled_zone,
            'transaction-token': 0}
        brcddb_util.add_to_obj(fabric_obj, 'brocade-zone/effective-configuration', effective_config)


def _show_fabric_switch_information_json(proj_obj, c_out, conv_d, row):
    """Convert "show fcdomain" to equivalent FOS API dictionaries. See _show_interface_brief_json()"""
    global _chassis_name, _chassis_obj

    # I never saw the table returned as anything other than a dict and the row anything other than a list but I got bit
    # by this with zoning. Once bitten twice shy was the approach here. See comments in _show_zoneset_active_json()
    for table_d in gen_util.convert_to_list(c_out.get('TABLE_fabric_switch_vsan')):
        for row_d in gen_util.convert_to_list(table_d.get('ROW_fabric_switch_vsan')):
            for table_d1 in gen_util.convert_to_list(row_d.get('TABLE_fabric_switch_info')):
                for row_d1 in gen_util.convert_to_list(table_d1.get('ROW_fabric_switch_info')):
                    if row_d1.get('name') is not None and row_d1.get('name') == _chassis_name:
                        for switch_obj in _chassis_obj.r_switch_objects():
                            brcddb_util.add_to_obj(switch_obj, 'brocade-fabric/fabric-switch/firmware-version',
                                                   str(row_d1.get('version')))
    _add_keys(_chassis_obj, 'show_fabric_switch_information', c_out)


################################################################################
#
#                     Methods for 'nja' in _nexus_to_fos.
#
################################################################################

def _show_fcdomain_njson(proj_obj, c_out, conv_d, row):
    """Convert "show fcdomain" to equivalent FOS API dictionaries. See _show_interface_brief_json()"""
    _show_fcdomain_json(proj_obj, parse_nx.show_fcdomain(c_out), conv_d, row)


def _show_zoneset_njson(proj_obj, c_out, conv_d, row):
    """Convert "show fcdomain" to equivalent FOS API dictionaries. See _show_interface_brief_json()"""
    _show_zoneset_json(proj_obj, parse_nx.show_zoneset(c_out), conv_d, row)


def _show_interface_brief_njson(proj_obj, c_out, conv_d, row):
    """Convert "show interface brief" to equivalent FOS API dictionaries. See _show_interface_brief_json()"""
    _show_interface_brief_json(proj_obj, parse_nx.show_interface_brief(c_out), conv_d, row)


def _show_device_alias_database_njson(proj_obj, c_out, conv_d, row):
    """Convert "show device-alias database" to equivalent FOS API dictionaries. See _show_interface_brief_json()"""
    _show_device_alias_database_json(proj_obj, parse_nx.show_device_alias_database(c_out), conv_d, row)


def _null_njson(proj_obj, c_out, conv_d, row):
    brcdapi_log.log('Non-JSON converter not available in row ' + str(row), echo=False)


"""The _nexus_to_fos table is used to determine how to translate and process Nexus commands and data types. The key is
the command (immediately following the prompt).
    +-------+---------------------------------------------------------------------------------------------------+
    | Key   | Description                                                                                       |
    +=======+===================================================================================================+
    | o     | A brcddb simple object type. This is the object that the key is associated with. If not           |
    |       | specified, the key is added to the object passed to _add_keys(). Although not currently used, it  |
    |       | is coded in _add_key().                                                                           |
    +-------+---------------------------------------------------------------------------------------------------+
    | bk    | The equivalent FOS key or list of keys matching ck. Note that some data is stored in multiple     |
    |       | keys. If ck is None, whatever is in v is assigned to bk.                                          |
    +-------+---------------------------------------------------------------------------------------------------+
    | v     | The value. May be a method to call to convert the value, a dictionary to look up the value, or a  |
    |       | hard coded value. A deep copy is made if v is a hard coded dict or list.                          |
    +-------+---------------------------------------------------------------------------------------------------+
    | dv    | The default value when v is a dict but the key is not present in v. May be a method to call to    |
    |       | convert the value. If neither v or dv is defined, the same value returned from nexus is used for  |
    |       | FOS.                                                                                              |
    +-------+---------------------------------------------------------------------------------------------------+
    | ef    | Error Flag. Assumed to be True when not specified. When True, an error is reported if the key in  |
    |       | ck does not exist.                                                                                |
    +-------+---------------------------------------------------------------------------------------------------+
    | ja    | Action to call to parse content when the content is JSON                                          |
    +-------+---------------------------------------------------------------------------------------------------+
    | nja   | Action to call to parse content when content is standard CLI output                               |
    +-------+---------------------------------------------------------------------------------------------------+
"""
_nexus_to_fos = {
    'show fcdomain': dict(
        conv_d=dict(
            state=dict(bk='brocade-fibrechannel-switch/fibrechannel-switch/operational-status',
                       v=dict(Stable=2),
                       dv=3),
            current_domain_id=dict(bk='brocade-fibrechannel-switch/fibrechannel-switch/domain-id',
                                   v=_domain_id,
                                   ef=False),
            local_switch_wwn=dict(bk=['brocade-fibrechannel-switch/fibrechannel-switch/name',
                                      'brocade-fabric/fabric-switch/name'])),
        ja=_show_fcdomain_json,
        nja=_show_fcdomain_njson
    ),
    'show fabric switch information': dict(
        conv_d=dict(),
        ja=_show_fabric_switch_information_json,
        nja=_null_njson
    ),
    'show interface brief': dict(
        conv_d=dict(
            interface_fc=dict(bk='fibrechannel/name',
                              v=_clean_port_ref),
            interface=dict(bk='fibrechannel/name',
                           v=_clean_port_ref),
            status=dict(bk='fibrechannel/operational-status',
                        v=dict(notConnected=3, fcotAbsent=3, up=2, sfpAbsent=3, trunking=2),
                        dv=0),
            admin_mode=dict(bk='fibrechannel/port-type',
                            v=dict(E=brcddb_common.PORT_TYPE_E,
                                   TE=brcddb_common.PORT_TYPE_E,
                                   F=brcddb_common.PORT_TYPE_F),
                            dv=brcddb_common.PORT_TYPE_U),
            oper_mode=dict(bk='fibrechannel/port-type',
                           v=dict(E=brcddb_common.PORT_TYPE_E,
                                  TE=brcddb_common.PORT_TYPE_E,
                                  F=brcddb_common.PORT_TYPE_F),
                           dv=brcddb_common.PORT_TYPE_U),
            oper_speed=dict(bk='fibrechannel/speed', v=_port_speed)
        ),
        ja=_show_interface_brief_json,
        nja=_show_interface_brief_njson
    ),
    'show flogi database details': dict(
        conv_d=dict(),
        ja=_show_flogi_database_detail_json,
        nja=_null_njson
    ),
    'show device-alias database': dict(
        conv_d=dict(),
        ja=_show_device_alias_database_json,
        nja=_show_device_alias_database_njson
    ),
    'show zoneset': dict(
        conv_d=dict(),
        ja=_show_zoneset_json,
        nja=_show_zoneset_njson
    ),
    'show zoneset active': dict(
        conv_d=dict(),
        ja=_show_zoneset_active_json,
        nja=_null_njson
    ),
}


def parse_args():
    """Parses the module load command line

    :return ip_addr: IP address
    :rtype ip_addr: str
    :return id: User ID
    :rtype id: str
    :return pw: Password
    :rtype pw: str
    :return file: Name of output file
    :rtype file: str
    :return http_sec: Type of HTTP security
    :rtype http_sec: str
    :return suppress_flag: True - suppress all print to STD_OUT
    :rtype suppress_flag: bool
    """
    global _DEBUG_i, _DEBUG_o, _DEBUG_p, _DEBUG_log, _DEBUG_nl

    if _DEBUG:
        return _DEBUG_i, _DEBUG_o, _DEBUG_p, _DEBUG_log, _DEBUG_nl
    parser = argparse.ArgumentParser(description='Convert MDS JSON command output to a brcddb library.')
    buf = 'Required. Name of file containing nx-os output piped to JSON. The file extension must be included.'
    parser.add_argument('-i', help=buf, required=True)
    buf = 'Required. Output file for converted data. ".json" is automatically appended.'
    parser.add_argument('-o', help=buf, required=True)
    buf = 'Required. Shell prompt. May or may not include the trailing "#". Case sensitive.'
    parser.add_argument('-p', help=buf, required=True)
    buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The log '\
          'file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
    parser.add_argument('-log', help=buf, required=False,)
    buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
    parser.add_argument('-nl', help=buf, action='store_true', required=False)
    args = parser.parse_args()
    return args.i, args.o, args.p, args.log, args.nl


###########################################
#
#                New
#
###########################################

def _nxos_to_brcddb_obj(prompt, content_l):
    """Converts command output from MDS to brcddb class objects

    :param prompt: Command prompt
    :type prompt: str
    :param content_l: Lit of command output
    :type content_l: list
    :return: Project Object
    :rtype: brcddb.classes.project.ProjectObj
    """
    cmd_in_prog, prompt_len, buf_l, content_d = None, len(prompt), list(), None

    # Create a project
    proj_obj = brcddb_project.new("Captured_data", datetime.datetime.now().strftime('%d %b %Y %H:%M:%S'))
    proj_obj.s_python_version(sys.version)
    proj_obj.s_description('MDS to brcddb conversion')

    for k, d in _nexus_to_fos.items():
        row = 0
        for buf in content_l:
            row += 1
            if len(buf) > prompt_len and buf[0: prompt_len] == prompt:
                if cmd_in_prog is not None:
                    try:
                        content_d = json.loads(''.join(buf_l))
                        try:
                            d['ja'](proj_obj, content_d, d['conv_d'], row)
                        except BaseException as e:
                            e_buf = 'Exception is: ' + str(e) if isinstance(e, (bytes, str)) else str(type(e))
                            brcdapi_log.exception(['Programming error encountered in row ' + str(row) + '.', e_buf],
                                                  echo=True)
                    except (KeyError, ValueError):
                        brcdapi_log.log('Non-JSON in row ' + str(row) + ' for: ' + k + '. Parsing as standard CLI',
                                        echo=True)
                        d['nja'](proj_obj, buf_l, d['conv_d'], row)
                    cmd_in_prog, buf_l = None, list()
                    break
                else:
                    if _key_match(_nexus_to_fos, k, buf[prompt_len+1:].strip()):
                        cmd_in_prog = k
            elif cmd_in_prog is not None:
                buf_l.append(buf)

    return proj_obj


def pseudo_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    global __version__

    # Get command line input
    inf, outf, prompt, log, nl = parse_args()
    outf = brcdapi_file.full_file_name(outf, '.json')
    if not nl:
        brcdapi_log.open_log(log)
    ml = ['WARNING!!! Debug is enabled'] if _DEBUG else list()
    ml.append('mds_capture:      ' + __version__)
    ml.append('MDS file, -i:     ' + inf)
    ml.append('Output file, -o:  ' + outf)
    ml.append('Prompt, -p:       ' + prompt)
    brcdapi_log.log(ml, echo=True)

    # Read the file (command output log)
    try:
        content_l = brcdapi_file.read_file(inf, remove_blank=True, rc=False)  # Read in the command log file
    except FileNotFoundError:
        brcdapi_log.log(['', 'Input file, -i, not found: ' + inf, ''], echo=True)
        return brcddb_common.EXIT_STATUS_INPUT_ERROR
    except FileExistsError:
        brcdapi_log.log(['', 'The folder in the Input file, -i, was not found: ' + inf, ''], echo=True)
        return brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Convert input to a project object
    proj_obj = _nxos_to_brcddb_obj(prompt, content_l)

    # Save the converted data to a file
    brcdapi_log.log("Saving project to: " + outf, echo=True)
    plain_copy = dict()
    brcddb_copy.brcddb_to_plain_copy(proj_obj, plain_copy)
    brcdapi_file.write_dump(plain_copy, outf)
    brcdapi_log.log("Save complete", echo=True)

    # Debug
    # brcdapi_log.log(['', 'CONTENT:'] + content_l + ['', 'PROJ_OBJ:'])
    brcdapi_log.log('PROJ_OBJ:')
    brcdapi_log.log(pprint.pformat(proj_obj))
    brcdapi_log.log('CONVERTED_PROJ_OBJ:')
    brcdapi_log.log(pprint.pformat(plain_copy))

    return brcddb_common.EXIT_STATUS_OK


###################################################################
#
#                    Main Entry Point
#
###################################################################
if _DOC_STRING:
    print('_DOC_STRING is True. No processing')
    exit(brcddb_common.EXIT_STATUS_OK)

_ec = pseudo_main()
brcdapi_log.close_log('\nProcessing Complete. Exit code: ' + str(_ec))
exit(_ec)
