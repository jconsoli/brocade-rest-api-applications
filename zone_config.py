#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright 2023, 2024 Consoli Solutions, LLC.  All rights reserved.

**License**

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may also obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.

The license is free for single customer use (internal applications). Use of this module in the production,
redistribution, or service delivery for commerce requires an additional license. Contact jack@consoli-solutions.com for
details.

**Description**

Examples on how to create, modify and delete zone objects using the brcdapi.zone library. It's also a good walk through
to determine considerations for adding, deleting, modifying, and creating zone objects

I never thought anyone would zone form a workbook, but I needed something to validate zone changes ahead of a change
control window. So I created this module. A common use for it is to validate zone changes before attempting to make the
changes.

The operation is essentially the same as how FOS handles zoning in that zoning transactions are stored in memory and
then applied to the switch all at once. Specifically:

    1.  The zone database is read from the switch and added to the brcddb database referred to herein as the “local
        database”.
    2.  Actions specified in the input workbook are tested against the local database and if there are no errors, the
        local database is updated. (the ability to do is what supports the test mode, -t option).
    3.  A zone configuration activation (equivalent to cfgenable) or save (equivalent to cfgsave) then write the revised
        zone database to the switch.

**Version Control**

+-----------+---------------+---------------------------------------------------------------------------------------+
| Version   | Last Edit     | Description                                                                           |
+===========+===============+=======================================================================================+
| 4.0.0     | 04 Aug 2023   | Re-Launch                                                                             |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.1     | 06 Mar 2024   | Removed deprecated parameter in enable_zonecfg()                                      |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.2     | 03 Apr 2024   | Renamed to zone_config.py from zone_config_x.py, Added version numbers of imported    |
|           |               | libraries. Added zone by sheet name, -sheet. Added -cli                               |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.3     | 15 May 2024   | Added migration and purge capabilities.                                               |
+-----------+---------------+---------------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2023, 2024 Consoli Solutions, LLC'
__date__ = '15 May 2024'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack@consoli-solutions.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '4.0.3'

import collections
import sys
import os
import pprint
import datetime
import brcdapi.gen_util as gen_util
import brcdapi.brcdapi_rest as brcdapi_rest
import brcdapi.fos_auth as fos_auth
import brcdapi.log as brcdapi_log
import brcdapi.file as brcdapi_file
import brcdapi.util as brcdapi_util
import brcdapi.excel_util as excel_util
import brcdapi.zone as brcdapi_zone
import brcddb.brcddb_common as brcddb_common
import brcddb.brcddb_project as brcddb_project
import brcddb.brcddb_fabric as brcddb_fabric
import brcddb.brcddb_switch as brcddb_switch
import brcddb.api.interface as api_int
import brcddb.api.zone as api_zone
import brcddb.util.obj_convert as obj_convert
_version_d = dict(
    brcdapi_log=brcdapi_log.__version__,
    gen_util=gen_util.__version__,
    brcdapi_rest=brcdapi_rest.__version__,
    fos_auth=fos_auth.__version__,
    excel_util=excel_util.__version__,
    brcdapi_file=brcdapi_file.__version__,
    brcdapi_util=brcdapi_util.__version__,
    brcdapi_zone=brcdapi_zone.__version__,
    brcddb_project=brcddb_project.__version__,
    brcddb_common=brcddb_common.__version__,
    brcddb_fabric=brcddb_fabric.__version__,
    api_int=api_int.__version__,
    api_zone=api_zone.__version__,
    obj_convert=obj_convert.__version__,
)

_DOC_STRING = False  # Should always be False. Prohibits any actual I/O. Only useful for building documentation
# _STAND_ALONE: True: Executes as a standalone module taking input from the command line. False: Does not automatically
# execute. This is useful when importing this module into another module that calls psuedo_main().
_STAND_ALONE = True  # Typically True. See note above
_DEBUG = False  # Forces local debug without setting -d

_input_d = gen_util.parseargs_login_false_d.copy()
_input_d['fid'] = dict(
    r=False, d=None, t='int', v=gen_util.range_to_list('1-128'),
    h='Optional. Required when -i is not specified. Fabric ID of logical switch.')
_input_d['i'] = dict(
    r=False, d=None,
    h='Optional. Output of capture.py, multi_capture.py, or combine.py. When this option is specified, -ip, -id, -pw, '
      '-s, and -a are ignored. This is for offline test purposes only.')
_input_d['wwn'] = dict(r=False, d=None, h='Optional. Fabric WWN. Required when -i is specified. Otherwise not used.')
_input_d['z'] = dict(
    r=False, d=None,
    h='Required unless using -scan. Workbook with zone definitions. ".xlsx" is automatically appended. See '
      'zone_sample.xlsx.')
_input_d['sheet'] = dict(
    r=False, d=None,
    h='Required unless using -scan. Sheet name in workbook, -z, to use for zoning definitions.')
_input_d['a'] = dict(r=False, d=None, h='Optional. Name of zone configuration to activate (enable).')
_input_d['save'] = dict(r=False, d=False, t='bool',
                        h='Optional. Save changes to the switch. By default, this module is in test mode only. '
                          'Activating a zone configuration, -a, automatically saves changes.')
_input_d['cli'] = dict(
    r=False, d=None,
    h='Optional. Name of the file for CLI commands. ".txt" is automatically appended if a "." is not found in the file '
      'name. CLI commands are generated whether -save is specified or not.')
_input_d['strict'] = dict(r=False, d=False, t='bool',
                          h='Optional. When set, warnings are treated as errors. Warnings are for inconsequential '
                            'errors, such as deleting a zone that doesn\'t exist.')
_input_d['scan'] = dict(
    r=False, d=False, t='bool',
    h='Optional. No parameters. Scan fabric information. No other actions are taken.')
_input_d.update(gen_util.parseargs_log_d.copy())
_input_d.update(gen_util.parseargs_debug_d.copy())

_debug = False
_eff_zone_l, _eff_mem_l = list(), list()
_pertinent_headers = ('Zone_Object', 'Action', 'Name', 'Match', 'Member', 'Principal Member')
_zone_kpis = ('running/brocade-fibrechannel-switch/fibrechannel-switch',
              'running/brocade-interface/fibrechannel',
              'running/brocade-zone/defined-configuration',
              'running/brocade-zone/effective-configuration',
              'running/brocade-fibrechannel-configuration/zone-configuration',
              'running/brocade-fibrechannel-configuration/fabric')
_pending_flag = False  # Updates were made to the brcddb zone database that have not been written to the switch yet.
# _tracking_d: They key in each sub-dictionary is the zone object name. The value is the list of rows in the workbook.
# This is used for error reporting only.
_tracking_d = dict(alias=dict(), zone=dict(), zone_cfg=dict(), eff_zonecfg_del=False)
# _modified_d keeps track of all zone objects that were modified (members removed or added). Each sub-dictionary
# key is the zone object name. The value is True except purge_d. The value for purge_d is a list of aliases which have
# been purged from that zone. purge_d is used in _purge() to report errors when a zone can't be deleted.
_modified_d = dict(alias=dict(), zone=dict(), zone_cfg=dict(), purge_d=dict())
# _ignore_mem_d: Remaining zone members of a zone effected by a purge action to ignore when determining if it should be
# # deleted. Value is True
_ignore_mem_d = dict()  # see note above
# _purge_d: Used for tracking ports affected by purge actions. Key is the switch WWN. The value is a dictionary of
# ports whose value is a list of aliases. Keep in mind that with NPIV, there can be multiple aliases associated with a
# port. Although not the best practice, someone could have multiple aliases for the same WWN.
_purge_d = dict()  # See note above
# CLI commands
_cli_d = dict(
    alias=dict(create=list(), delete=list(), add=list(), remove=list()),
    zone=dict(create=list(), delete=list(), add=list(), add_peer=list(), remove=list(), remove_peer=list()),
    zonecfg=dict(create=list(), delete=list(), add=list(), remove=list()),
    enable=None,
    save=False,
)
_MAX_ROWS = 20


class Found(Exception):
    pass


class FOSError(Exception):
    pass


def _reference_rows(row_l):
    """Formats the reference rows for error reporting.

    :param row_l: Row references
    :type row_l: list
    :return: Formatted CSV of row numbers
    :rtype: str
    """
    return ', '.join(gen_util.remove_duplicates([str(row) for row in row_l])) if len(row_l) == 0 else 'none'


def _add_to_tracking(key, zone_d, eff_zonecfg_del=False):
    """Adds an item to the tracking dictionary

    :param key: 'alias', 'zone', or 'zone-cfg'
    :type key: str
    :param zone_d: Entry in the list returned from _parse_zone_workbook
    :type zone_d: dict
    :param eff_zonecfg_del: If True, the tracked item has been deleted from the effective zone configuration
    :type eff_zonecfg_del: bool
    :rtype: None
    """
    global _tracking_d

    d = _tracking_d[key].get(zone_d['Name'])
    if d is None:
        d = list()
        _tracking_d[key].update({zone_d['Name']: d})
    d.append(zone_d['row'])
    if eff_zonecfg_del:
        _tracking_d['eff_zonecfg_del'] = True


def _build_cli_file(cli_file):
    """Write the CLI commands to a file

    :param cli_file: Name of CLI file
    :type cli_file: str, None
    :return: Error messages
    :rtype: list
    """
    global _cli_d, _MAX_ROWS

    if not isinstance(cli_file, str):
        return list()

    cli_l = list()
    for d in (
            dict(o='zonecfg', a='delete', c='# Delete Zone Configurations'),
            dict(o='zonecfg', a='remove', c='# Remove Zone Configuration Members'),
            dict(o='zone', a='delete', c='# Delete Zones'),
            dict(o='zone', a='remove', c='# Remove Zone Members'),
            dict(o='alias', a='delete', c='# Delete Aliases'),
            dict(o='alias', a='remove', c='# Remove Alias Members'),
            dict(o='alias', a='create', c='# Create Aliases'),
            dict(o='alias', a='add', c='# Add Alias Members'),
            dict(o='zone', a='create', c='# Create Zone'),
            dict(o='zone', a='add', c='# Add Zone Members'),
            dict(o='zonecfg', a='create', c='# Create Zone Configurations'),
            dict(o='zonecfg', a='add', c='# Add Zone Configuration Members'),
    ):
        temp_l = _cli_d[d['o']][d['a']]
        if len(temp_l) > 0:
            cli_l.extend(['', d['c']])
            i = 0
            for buf in temp_l:
                if i >= _MAX_ROWS:
                    cli_l.append('')
                    i = 0
                else:
                    i += 1
                cli_l.append(buf)

    # Save or enable
    if isinstance(_cli_d['enable'], str):
        cli_l.append('cfgenable "' + str(_cli_d['enable']) + '" -f')
    elif _cli_d['save']:
        cli_l.append('cfgsave -f')
    cli_l.append('')

    return brcdapi_file.write_file(cli_file, cli_l)


def _validation_check(args_d, fab_obj):
    """Validates the zone database

    :param args_d: Input arguments. See _input_d for details.
    :type args_d: dict
    :param fab_obj: Fabric object
    :type fab_obj: brcddb.classes.fabric.FabricObj
    :return el: Error messages
    :rtype el: list
    """
    global _tracking_d

    el = list()

    if fab_obj is None:
        return el

    # Make sure all the zones and aliases used in each configuration still exist
    zone_done_d, alias_done_d = dict(), dict()  # Avoid duplicate messages. Zones may be used in multiple configurations
    for zonecfg_obj in fab_obj.r_zonecfg_objects():
        zonecfg = zonecfg_obj.r_obj_key()
        for zone_obj in zonecfg_obj.r_zone_objects():
            zone = zone_obj.r_obj_key()
            if zone_done_d.get(zone, False):
                continue
            zone_done_d[zone] = True
            if fab_obj.r_zone_obj(zone) is None:
                row_buf = _reference_rows(_tracking_d['zone'].get(zone, list()))
                el.append('Zone ' + zone + ', used in ' + zonecfg + ' does not exist. Rows: ' + row_buf)
            else:
                # Make sure all the aliases exist
                for alias in zone_obj.r_members() + zone_obj.r_pmembers():
                    if alias_done_d.get(alias, False):
                        continue
                    alias_done_d[alias] = True
                    if gen_util.is_valid_zone_name(alias) and fab_obj.r_alias_obj(alias) is None:
                        buf = 'Alias ' + alias + ', used in ' + zone + ' does not exist. Rows: '
                        buf += _reference_rows(_tracking_d['alias'].get(alias, list()))
                        el.append(buf)

    # Make sure zones and aliases in the effective zone configuration weren't deleted or modified
    eff_zonecfg_name = fab_obj.r_defined_eff_zonecfg_key()
    if isinstance(args_d['a'], str):
        if fab_obj.r_zonecfg_obj(args_d['a']) is None:
            buf = 'Zone configuration, ' + args_d['a'] + ', specified with -a parameter doesn\'t exist. Rows: '
            buf += _reference_rows(_tracking_d['zone_cfg'].get(args_d['a'], list()))
            el.append(buf)
    if isinstance(eff_zonecfg_name, str) and not args_d['save'] and not isinstance(args_d['a'], str):
        row_buf = _reference_rows(_tracking_d['zone_cfg'].get(eff_zonecfg_name, list()))
        e_buf = 'Zone members or aliases in the zone members of the effective zone configuration, ' + \
                eff_zonecfg_name + ', were deleted. Either a new zone configuration or the same effective zone ' + \
                'configuration must be activated using the -a option. Rows: ' + row_buf
        w_buf = 'Zone members or aliases in the zone members of the effective zone configuration, ' + \
                eff_zonecfg_name + ', were modified. To avoid a mismatch between the effective zone configuration, ' + \
                'either a new zone configuration or the same effective zone configuration must be activated using ' + \
                'the -a option. Rows: ' + row_buf
        buf = e_buf if _tracking_d['eff_zonecfg_del'] else w_buf
        new_eff_zone_l, new_eff_mem_l = list(), list()
        for zone_obj in fab_obj.r_eff_zone_objects():
            new_eff_zone_l.append(zone_obj.r_obj_key())
            new_eff_mem_l.extend(zone_obj.r_members() + zone_obj.r_pmembers())
        if gen_util.compare_lists(_eff_zone_l, new_eff_zone_l):
            if gen_util.compare_lists(_eff_mem_l, new_eff_mem_l):
                el.append(buf)
        else:
            el.append(buf)

    return el


#################################################
#                                               #
#         Actions for _zone_action_d            #
#                                               #
#################################################
def _invalid_action(fab_obj, zone_d, search_d):
    """Error handler for "Actions" not supported by the "Zone_Object"
    
    :param fab_obj: Fabric object
    :type fab_obj: brcddb.classes.fabric.FabricObj
    :param zone_d: Entry in the list returned from _parse_zone_workbook
    :type zone_d: dict
    :param search_d: Search terms. See search_d in pseudo_main() for details.
    :type search_d: dict
    :return el: Error messages
    :rtype el: list
    :return wl: Warning messages
    :rtype wl: list
    """
    stype = 'exact' if zone_d['Match'] is None else zone_d['Match']
    el = ['"' + zone_d['Action'] + '" is not a valid Action for Zone_Object "' + zone_d['Zone_Object'] +
          '" for match type "' + stype + ' at row ' + str(zone_d['row'])]
    return el, list()


def _alias_create(fab_obj, zone_d, search_d):
    """Create an alias. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_d

    # Make sure it's a valid alias definition
    el, wl = list(), list()
    if isinstance(zone_d['Principal Member'], str):  # Principal members are not supported in an alias
        el.append('Principal members not supported in alias create at row ' + str(zone_d['row']))
    elif not gen_util.is_valid_zone_name(zone_d['Name']):  # Is it a valid alias name?
        el.append('Invalid alias name, ' + zone_d['Name'] + ', at row ' + str(zone_d['row']))
    elif not gen_util.is_wwn(zone_d['Member'], full_check=True) and not gen_util.is_di(zone_d['Member']):  # Valid WWN?
        el.append('Invalid alias member, ' + zone_d['Member'] + ', at row ' + str(zone_d['row']))
    elif fab_obj is not None:
        alias_obj = fab_obj.r_alias_obj(zone_d['Name'])
        if alias_obj is None:
            fab_obj.s_add_alias(zone_d['Name'], zone_d['Member'])
            _pending_flag = True
        else:
            el.append('Alias ' + zone_d['Name'] + ' in row ' + str(zone_d['row']) + ' already exists.')

    _cli_d['alias']['create'].append('alicreate "' + zone_d['Name'] + '", "' + zone_d['Member'] + '"')
    _add_to_tracking('alias', zone_d)

    return el, wl


def _alias_delete(fab_obj, zone_d, search_d):
    """Delete an alias. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_d

    el, wl = list(), list()
    if fab_obj is not None:
        alias_obj = fab_obj.r_alias_obj(zone_d['Name'])
        if alias_obj is None:
            buf = 'Alias ' + zone_d['Name'] + ' in row ' + str(zone_d['row']) + ' does not exist.'
            if not gen_util.is_valid_zone_name(zone_d['Name']):
                buf += ' Did you intend to set a match type in the "Match" column?'
            el.append(buf)
        else:
            fab_obj.s_del_alias(zone_d['Name'])
            _pending_flag = True
            _cli_d['alias']['delete'].append('alidelete "' + zone_d['Name'] + '"')
            if search_d['eff_alias_d'].get(zone_d['Name']) is not None:
                copy_zone_d = zone_d.copy()
                copy_zone_d['Name'] = search_d['eff_zonecfg_obj'].r_obj_key()
                _add_to_tracking('zone_cfg', copy_zone_d, eff_zonecfg_del=True)
    else:
        _cli_d['alias']['delete'].append('alidelete "' + zone_d['Name'] + '"')
    _add_to_tracking('alias', zone_d)

    return el, wl


def _alias_delete_m(fab_obj, zone_d, search_d):
    """Delete aliases based on a regex or wild card match. See _invalid_action() for parameter descriptions"""
    el, wl = list(), list()
    copy_zone_d = zone_d.copy()

    for alias in gen_util.match_str(search_d['alias_l'], zone_d['Name'], stype=zone_d['Match']):
        copy_zone_d['Name'] = alias
        temp_el, temp_wl = _alias_delete(fab_obj, copy_zone_d, search_d)
        el.extend(temp_el)
        wl.extend(temp_wl)

    return el, wl


def _alias_add_mem(fab_obj, zone_d, search_d):
    """Add alias members. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_d

    el, wl = list(), list()

    # Validate the members
    if zone_d['Principal Member'] is not None:
        el.append('Principal members not supported in alias create at row ' + str(zone_d['row']))
    elif not gen_util.is_wwn(zone_d['Member'], full_check=True) and not gen_util.is_di(zone_d['Member']):
        el.append('Invalid alias member, ' + zone_d['Member'] + ', at row ' + str(zone_d['row']))
    elif fab_obj is not None:
        alias_obj = fab_obj.r_alias_obj(zone_d['Name'])
        if alias_obj is None:
            buf = 'Alias ' + zone_d['Name'] + ' in row ' + str(zone_d['row']) + ' does not exist.'
            if not gen_util.is_valid_zone_name(zone_d['Name']):
                buf += ' Did you intend to set a match type in the "Match" column?'
            el.append(buf)
        elif zone_d['Member'] in alias_obj.r_members():
            wl.append('Member ' + zone_d['Member'] + ' is already in ' + zone_d['Name'] + ' in row ' +
                      str(zone_d['row']))
            return el, wl  # The member is already in the alias so there is nothing to do.
        else:
            alias_obj.s_add_member(zone_d['Name'], zone_d['Member'])
            _pending_flag = True
            if search_d['eff_alias_d'].get(zone_d['Name']) is not None:
                copy_zone_d = zone_d.copy()
                copy_zone_d['Name'] = search_d['eff_zonecfg_obj'].r_obj_key()
                _add_to_tracking('zone_cfg', copy_zone_d)

    # Add to CLI
    if len(el) == 0:
        _cli_d['alias']['add'].append('aliadd "' + zone_d['Name'] + '", "' + zone_d['Member'] + '"')
    _add_to_tracking('alias', zone_d)

    return el, wl


def _alias_remove_mem(fab_obj, zone_d, search_d):
    """Remove alias members. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_d

    el, wl = list(), list()
    if fab_obj is not None:
        alias_obj = fab_obj.r_alias_obj(zone_d['Name'])
        if alias_obj is None:
            buf = 'Alias ' + zone_d['Name'] + ' in row ' + str(zone_d['row']) + ' does not exist.'
            if not gen_util.is_valid_zone_name(zone_d['Name']):
                buf += ' Did you intend to set a match type in the "Match" column?'
            el.append(buf)
        else:
            alias_obj.s_del_member(zone_d['Name'], zone_d['Member'])
            _pending_flag = True
            if search_d['eff_alias_d'].get(zone_d['Name']) is not None:
                copy_zone_d = zone_d.copy()
                copy_zone_d['Name'] = search_d['eff_zonecfg_obj'].r_obj_key()
                _add_to_tracking('zone_cfg', copy_zone_d)
    _cli_d['alias']['remove'].append('aliremove "' + zone_d['Name'] + '", "' + zone_d['Member'] + '"')
    _add_to_tracking('alias', zone_d)

    return el, wl


def _alias_purge(fab_obj, zone_d, search_d):
    """Purges an alias. See _invalid_action() for parameters"""
    global _modified_d, _purge_d

    el, wl = list(), list()
    if fab_obj is not None:
        alias_obj = fab_obj.r_alias_obj(zone_d['Name'])
        if alias_obj is not None:
            alias = alias_obj.r_obj_key()

            # Update _purge_d
            for port_obj in obj_convert.obj_extract(alias_obj, 'PortObj'):
                port = port_obj.r_obj_key()
                switch = port_obj.r_switch_obj().r_obj_key()
                port_d = _purge_d.get(switch)
                if port_d is None:
                    port_d = dict()
                    _purge_d[switch] = port_d
                alias_l = port_d.get(port)
                if alias_l is None:
                    alias_l = list()
                    port_d[port] = alias_l
                alias_l.append(alias)

            # Delete the alias in every zone where it is used.
            for zone_obj in obj_convert.obj_extract(alias_obj, 'ZoneObj'):
                zone_obj.s_del_member(alias)
                zone_obj.s_del_pmember(alias)
                zone = zone_obj.r_obj_key()
                alias_l = _modified_d['purge_d'].get(zone)
                if alias_l is None:
                    alias_l = list()
                    _modified_d['purge_d'].update({zone: alias_l})
                alias_l.append(alias)

            temp_el, temp_wl = _alias_delete(fab_obj, zone_d, search_d)
            el.extend(temp_el)
            wl.extend(temp_wl)

    return el, wl


def _alias_purge_m(fab_obj, zone_d, search_d):
    """Purges aliases based on a regex or wild card match. See _invalid_action() for parameters"""
    el, wl = list(), list()
    copy_zone_d = zone_d.copy()
    for alias in gen_util.match_str(search_d['alias_l'], zone_d['Name'], stype=zone_d['Match']):
        copy_zone_d['Name'] = alias
        temp_el, temp_wl = _alias_purge(fab_obj, copy_zone_d, search_d)
        el.extend(temp_el)
        wl.extend(temp_wl)

    return el, wl


def _alias_ignore(fab_obj, zone_d, search_d):
    """Set alias to ignore. See _invalid_action() for parameters"""
    global _ignore_mem_d

    _ignore_mem_d.update({zone_d['Member']: True})

    return list(), list()


def _alias_ignore_m(fab_obj, zone_d, search_d):
    """Set aliases to ignore based on a regex or wild card match. See _invalid_action() for parameters"""
    for alias in gen_util.match_str(search_d['alias_l'], zone_d['Name'], stype=zone_d['Match']):
        _ignore_mem_d.update({alias: True})

    return list(), list()


def _peer_zone_create(fab_obj, zone_d, search_d):
    """Create a peer zone. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_d

    el, wl = list(), list()

    # If it's a previous action, members are being added
    if zone_d['name_c']:
        return _zone_add_mem(fab_obj, zone_d, search_d)

    # Make sure it's a valid zone definition
    if not gen_util.is_valid_zone_name(zone_d['Name']):
        el.append('Invalid zone name, ' + zone_d['Name'] + ', at row ' + str(zone_d['row']))
        return el, wl
    m = zone_d['Member']
    if isinstance(m, str) and \
            not gen_util.is_wwn(m, full_check=True) and \
            not gen_util.is_di(m) and \
            not gen_util.is_valid_zone_name(m):
        el.append('Invalid zone member, ' + m + ', at row ' + str(zone_d['row']))
        return el, wl
    zone_obj = fab_obj.r_zone_obj(zone_d['Name'])
    if zone_obj is not None:
        el.append('Zone ' + zone_d['Name'] + ' in row ' + str(zone_d['row']) + ' already exists.')
        return el, wl

    # Create the peer zone
    if fab_obj is not None:
        fab_obj.s_add_zone(zone_d['Name'], brcddb_common.ZONE_USER_PEER, zone_d['Member'], zone_d['Principal Member'])
        _pending_flag = True
    buf = 'zonecreate --peerzone "' + zone_d['Name'] + '"'
    if isinstance(zone_d['Principal Member'], str):
        buf += ' -principal "' + zone_d['Principal Member'] + '"'
    if isinstance(zone_d['Member'], str):
        buf += ' -members "' + zone_d['Member'] + '"'
    _cli_d['zone']['create'].append(buf)
    _add_to_tracking('zone', zone_d)

    return el, wl


def _zone_create(fab_obj, zone_d, search_d):
    """Create a zone. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_d

    el, wl = list(), list()

    # If it's a previous action, members are being added
    if zone_d['name_c']:
        return _zone_add_mem(fab_obj, zone_d, search_d)

    # Make sure it's a valid zone definition
    if zone_d['Principal Member'] is not None:  # Principal members are only supported in peer zones
        el.append('Principal members only supported in peer zones at row ' + str(zone_d['row']))
    if not gen_util.is_valid_zone_name(zone_d['Name']):  # Is the zone name valid?
        el.append('Invalid zone name, ' + zone_d['Name'] + ', at row ' + str(zone_d['row']))
    m = zone_d['Member']
    if not gen_util.is_wwn(m, full_check=True) and not gen_util.is_di(m) and not gen_util.is_valid_zone_name(m):
        el.append('Invalid zone member, ' + m + ', at row ' + str(zone_d['row']))
    zone_obj = fab_obj.r_zone_obj(zone_d['Name'])
    if zone_obj is not None:  # If the zone already exists, do they have the same members?
        el.append('Zone ' + zone_d['Name'] + ' in row ' + str(zone_d['row']) + ' already exists.')

    # Create the zone
    if len(el) == 0 and fab_obj is not None:
        fab_obj.s_add_zone(zone_d['Name'],
                           brcddb_common.ZONE_STANDARD_ZONE,
                           zone_d['Member'],
                           zone_d['Principal Member'])
        _pending_flag = True
    _cli_d['zone']['create'].append('zonecreate "' + zone_d['Name'] + '", "' + zone_d['Member'] + '"')
    _add_to_tracking('zone', zone_d)

    return el, wl


def _zone_delete(fab_obj, zone_d, search_d):
    """Delete a zone. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_d

    el, wl = list(), list()
    if fab_obj is not None:
        if fab_obj.r_zone_obj(zone_d['Name']) is None:
            buf = 'Zone ' + zone_d['Name'] + ' in row ' + str(zone_d['row']) + ' does not exist.'
            if not gen_util.is_valid_zone_name(zone_d['Name']):
                buf += ' Did you intend to set a match type in the "Match" column?'
            wl.append(buf)
        else:
            fab_obj.s_del_zone(zone_d['Name'])
            _pending_flag = True
            if search_d['eff_zone_d'].get(zone_d['Name']) is not None:
                copy_zone_d = zone_d.copy()
                copy_zone_d['Name'] = search_d['eff_zonecfg_obj'].r_obj_key()
                _add_to_tracking('zone_cfg', copy_zone_d, eff_zonecfg_del=True)
    _cli_d['zone']['delete'].append('zonedelete ' + zone_d['Name'])
    _add_to_tracking('zone', zone_d)

    return el, wl


def _zone_delete_m(fab_obj, zone_d, search_d):
    """Delete zones based on a regex or wild card match. See _invalid_action() for parameters"""
    el, wl = list(), list()

    copy_zone_d = zone_d.copy()
    for zone in gen_util.match_str(search_d['zone_l'], zone_d['Name'], stype=zone_d['Match']):
        copy_zone_d['Name'] = zone
        temp_el, temp_wl = _zone_delete(fab_obj, copy_zone_d, search_d)
        el.extend(temp_el)
        wl.extend(temp_wl)

    return el, wl


def _zone_add_mem(fab_obj, zone_d, search_d):
    """Add zone members. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_d

    el, wl = list(), list()

    if fab_obj is not None:
        # Validate the parameters
        zone_obj = fab_obj.r_zone_obj(zone_d['Name'])
        if zone_obj is None:
            buf = 'Zone ' + zone_d['Name'] + ' in row ' + str(zone_d['row']) + ' does not exist.'
            if not gen_util.is_valid_zone_name(zone_d['Name']):
                buf += ' Did you intend to set a match type in the "Match" column?'
            el.append(buf)
            return el, wl
        buf = 'zoneadd --peerzone "' + zone_d['Name'] + '"' if zone_obj.r_is_peer() else \
            'zoneadd "' + zone_d['Name'] + '"'
        m = zone_d['Principal Member']
        if isinstance(m, str):
            if not zone_obj.r_is_peer():
                el.append('Principal members are not supported in ' + zone_d['Name'] +
                          ' because is not a peer zone at row ' + str(zone_d['row']))
                return el, wl
            if not gen_util.is_wwn(m, full_check=True) and not gen_util.is_di(m) and not gen_util.is_valid_zone_name(m):
                el.append('Invalid zone member, ' + m + ', at row ' + str(zone_d['row']))
                return el, wl
        for m in [mem for mem in [zone_d['Member'], zone_d['Principal Member']] if isinstance(mem, str)]:
            if not gen_util.is_wwn(m, full_check=True) and not gen_util.is_di(m) and not gen_util.is_valid_zone_name(m):
                el.append('Invalid zone member, ' + m + ', at row ' + str(zone_d['row']))
                return el, wl

        # Add the zone members
        zone_obj.s_add_member(zone_d['Member'])
        zone_obj.s_add_pmember(zone_d['Principal Member'])
        _pending_flag = True
        if search_d['eff_zone_d'].get(zone_d['Name']) is not None:
            copy_zone_d = zone_d.copy()
            copy_zone_d['Name'] = search_d['eff_zonecfg_obj'].r_obj_key()
            _add_to_tracking('zone_cfg', copy_zone_d)
    else:
        buf = 'zoneadd --peerzone "' + zone_d['Name'] + '"' if zone_d['Zone_Object'] == 'peer_zone' else \
            'zoneadd "' + zone_d['Name'] + '"'
    if isinstance(zone_d['Principal Member'], str):
        buf += ' -principal "' + zone_d['Principal Member'] + '"'
    if isinstance(zone_d['Member'], str):
        buf += ' -members "' + zone_d['Member'] + '"'
    _cli_d['zone']['add'].append(buf)
    _add_to_tracking('zone', zone_d)

    return el, wl


def _peer_zone_remove_mem(fab_obj, zone_d, search_d):
    """Remove zone members. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_d

    el, wl = list(), list()
    if fab_obj is not None:
        # Validate the input
        zone_obj = fab_obj.r_zone_obj(zone_d['Name'])
        if zone_obj is None:
            buf = 'Zone ' + zone_d['Name'] + ' in row ' + str(zone_d['row']) + ' does not exist.'
            if not gen_util.is_valid_zone_name(zone_d['Name']):
                buf += ' Did you intend to set a match type in the "Match" column?'
            el.append(buf)
        elif not zone_obj.r_is_peer():
            el.append('Zone type mismatch. ' + zone_d['Name'] + ' is not a peer zone at row ' + str(zone_d['row']))
        else:
            member, pmember = zone_d['Member'], zone_d['Principal Member']
            if isinstance(member, str):
                if member not in zone_obj.r_member():
                    if isinstance(pmember, str) and pmember not in zone_obj.r_pmembers():
                        el.append('The "Member" in row ' + str(zone_d['row']) + ' is a "Principal Member".')
                    else:
                        wl.append(member + ' in row ' + str(zone_d['row']) + ' is not a member of ' + zone_d['Name'])
                elif member in zone_obj.r_pmembers():
                    el.append('The "Member" in row ' + str(zone_d['row']) + ' is a "Principal Member".')
            if isinstance(pmember, str):
                if pmember not in zone_obj.r_pmember():
                    if isinstance(member, str) and member not in zone_obj.r_members():
                        el.append('The "Principal Member" in row ' + str(zone_d['row']) + ' is a "Member".')
                    else:
                        wl.append(pmember + ' in row ' + str(zone_d['row']) + ' is not a principal member of ' +
                                  zone_d['Name'])
                elif pmember in zone_obj.r_members():
                    el.append('The "Principal Member" in row ' + str(zone_d['row']) + ' is a " Member".')

        if len(el) == 0:
            # Make the zoning changes
            zone_obj.s_del_member(zone_d['Member'])
            zone_obj.s_del_pmember(zone_d['Principal Member'])
            _pending_flag = True
            if search_d['eff_zone_d'].get(zone_d['Name']) is not None:
                copy_zone_d = zone_d.copy()
                copy_zone_d['Name'] = search_d['eff_zonecfg_obj'].r_obj_key()
                _add_to_tracking('zone_cfg', copy_zone_d)

    # Update CLI
    buf = 'zoneremove --peerzone "' + zone_d['Name'] + '"'
    if isinstance(zone_d['Principal Member'], str):
        buf += ' -principal "' + zone_d['Principal Member'] + '"'
    if isinstance(zone_d['Member'], str):
        buf += ' -members "' + zone_d['Member'] + '"'
    _cli_d['zone']['remove'].append(buf)

    _add_to_tracking('zone', zone_d)

    return el, wl


def _zone_remove_mem(fab_obj, zone_d, search_d):
    """Remove zone members. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_d

    el, wl, zone_obj, member = list(), list(), None, zone_d['Member']

    # Validate the parameters
    if zone_d['Principal Member'] is not None:
        el.append('Principal members not supported in zone member remove at row ' + str(zone_d['row']))
    elif fab_obj is not None:
        zone_obj = fab_obj.r_zone_obj(zone_d['Name'])
        if zone_obj is not None:
            if zone_obj.r_is_peer():
                el.append('Zone type mismatch. ' + zone_d['Name'] + ' is a peer zone at row ' + str(zone_d['row']))
            elif member not in zone_obj.r_members():
                wl.append(member + ' in row ' + str(zone_d['row']) + ' is not a member of ' + zone_d['Name'])

    # Remove the members
    if len(el) == 0 and zone_obj is not None:
        zone_obj.s_del_member(member)
        _pending_flag = True
        if search_d['eff_zone_d'].get(zone_d['Name']) is not None:
            copy_zone_d = zone_d.copy()
            copy_zone_d['Name'] = search_d['eff_zonecfg_obj'].r_obj_key()
            _add_to_tracking('zone_cfg', copy_zone_d)
    _cli_d['zone']['remove'].append('zoneremove "' + zone_d['Name'] + '", ' + member)
    _add_to_tracking('zone', zone_d)

    return el, wl


def _zone_purge(fab_obj, zone_d, search_d):
    """Purges a zone. See _invalid_action() for parameters"""
    global _modified_d

    el, wl = list(), list()
    if fab_obj is not None:
        zone_obj = fab_obj.r_zone_obj(zone_d['Name'])
        if zone_obj is not None:
            zone = zone_obj.r_obj_key()
            for zonecfg_obj in obj_convert.obj_extract(zone_obj, 'ZoneCfgObj'):
                zonecfg_obj.s_del_member(zone)
                _modified_d['zone'].update({zone: True})
            temp_el, temp_wl = _zone_delete(fab_obj, zone_d, search_d)
            el.extend(temp_el)
            wl.extend(temp_wl)

    return el, wl


def _zone_purge_m(fab_obj, zone_d, search_d):
    """Purges zones based on a regex or wild card match. See _invalid_action() for parameters"""
    el, wl, copy_zone_d = list(), list(), zone_d.copy()
    for zone in gen_util.match_str(search_d['zone_l'], zone_d['Name'], stype=zone_d['Match']):
        copy_zone_d['Name'] = zone
        temp_el, temp_wl = _zone_purge(fab_obj, copy_zone_d, search_d)
        el.extend(temp_el)
        wl.extend(temp_wl)

    return el, wl


def _zone_full_purge(fab_obj, zone_d, search_d):
    """Full purge of a zone. See _invalid_action() for parameters"""
    el, wl, copy_zone_d = list(), list(), zone_d.copy()
    if fab_obj is not None:
        zone_obj = fab_obj.r_zone_obj(zone_d['Name'])
        if zone_obj is None:
            buf = 'Zone ' + zone_d['Name'] + ' in row ' + str(zone_d['row']) + ' does not exist.'
            if not gen_util.is_valid_zone_name(zone_d['Name']):
                buf += ' Did you intend to set a match type in the "Match" column?'
            el.append(buf)
        else:
            for mem in zone_obj.r_members() + zone_obj.r_pmembers():
                copy_zone_d['Name'] = mem
                temp_el, temp_wl = _alias_purge(fab_obj, copy_zone_d, search_d)
                el.extend(temp_el)
                wl.extend(temp_wl)
            temp_el, temp_wl = _zone_purge(fab_obj, zone_d, search_d)
            el.extend(temp_el)
            wl.extend(temp_wl)

    return el, wl


def _zone_full_purge_m(fab_obj, zone_d, search_d):
    """Full purge zones based on a regex or wild card match. See _invalid_action() for parameters"""
    el, wl, copy_zone_d = list(), list(), zone_d.copy()
    for zone in gen_util.match_str(search_d['zone_l'], zone_d['Name'], stype=zone_d['Match']):
        copy_zone_d['Name'] = zone
        temp_el, temp_wl = _zone_full_purge(fab_obj, copy_zone_d, search_d)
        el.extend(temp_el)
        wl.extend(temp_wl)

    return el, wl


def _zonecfg_create(fab_obj, zone_d, search_d):
    """Create a zone configuration. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_d

    el, wl = list(), list()

    # If it's a previous action, members are being added
    if zone_d['name_c']:
        return _zonecfg_add_mem(fab_obj, zone_d, search_d)

    # Validate the input
    if zone_d['Principal Member'] is not None:
        el.append('Principal members not supported in zone configuration at row ' + str(zone_d['row']))
    else:
        zonecfg_obj = fab_obj.r_zone_obj(zone_d['Name'])
        if zonecfg_obj is not None:
            el.append('Zone configuration in row ' + str(zone_d['row']) + ' already exists.')
    
    if len(el) == 0 and fab_obj is not None:
        fab_obj.s_add_zonecfg(zone_d['Name'], zone_d['Member'])
        _pending_flag = True
    buf = 'cfgcreate "' + zone_d['Name'] + '"'
    if isinstance(zone_d['Member'], str):
        buf += ' "' + zone_d['Member'] + '"'
    _cli_d['zonecfg']['create'].append('cfgcreate "' + zone_d['Name'] + '", "' + zone_d['Member'] + '"')
    _add_to_tracking('zone_cfg', zone_d)

    return el, wl


def _zonecfg_delete(fab_obj, zone_d, search_d):
    """Delete a zone config. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_d

    el, wl = list(), list()

    # Validate - Make sure the zone configuration exists and that it's not the effective zone.
    if fab_obj is not None:
        zonecfg_obj = fab_obj.r_zonecfg_obj(zone_d['Name'])
        if zonecfg_obj is None:
            wl.append(zone_d['Name'] + ' does not exist. Row: ' + str(zone_d['row']))
        else:
            fab_obj.s_del_zonecfg(zone_d['Name'])
            _pending_flag = True
    _cli_d['zonecfg']['delete'].append('cfgdelete "' + zone_d['Name'] + '"')
    _add_to_tracking('zone_cfg', zone_d)

    return el, wl


def _zonecfg_add_mem(fab_obj, zone_d, search_d):
    """Add zone config members. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_d

    el, wl = list(), list()
    if fab_obj is not None:
        zonecfg_obj = fab_obj.r_zonecfg_obj(zone_d['Name'])
        if zonecfg_obj is None:
            el.append('Zone configuration ' + zone_d['Name'] + ' does not exist at row ' + str(zone_d['row']))
        else:
            zonecfg_obj.s_add_member(zone_d['Member'])
            _pending_flag = True

    _cli_d['zonecfg']['add'].append('cfgadd "' + zone_d['Name'] + '", "' + zone_d['Member'] + '"')
    _add_to_tracking('zone_cfg', zone_d)

    return el, wl


def _zonecfg_remove_mem(fab_obj, zone_d, search_d):
    """Remove zone config members. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_d

    el, wl = list(), list()
    if fab_obj is not None:
        zonecfg_obj = fab_obj.r_zonecfg_obj(zone_d['Name'])
        if zonecfg_obj is None:
            el.append('The zone configuration, ' + zone_d['Name'] + ' does not exist.')
        elif zone_d['Member'] in zonecfg_obj.r_members():
            zonecfg_obj.s_del_member(zone_d['Member'])
            _pending_flag = True
        else:
            wl.append(zone_d['Member'] + ' is not a member of ' + zone_d['Name'] + ' at row ' + str(zone_d['Row']))
    _cli_d['zonecfg']['remove'].append('cfgremove "' + zone_d['Name'] + '", "' + ';'.join(zone_d['Member']) + '"')
    _add_to_tracking('zone_cfg', zone_d)

    return el, wl


"""_zone_action_d: I could have just had one dictionary with a pointer to the method and handled the activate list
separately but I was thinking of maybe doing some more complex checking and error messaging so the dictionary of
dictionaries was done to simplify future script enhancements.
+-------+-----------+-----------------------------------------------------------------------------------------------+
| Key   | Type      | Description                                                                                   |
+=======+===========+===============================================================================================+
| a     | method    | Pointer to method to handle this action                                                       |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| as_l  | list      | Action specific list. When this was written, it was only applicable for the Action "activate" |
|       |           | for Zone_Object "zone_cfg"                                                                    |
+-------+-----------+-----------------------------------------------------------------------------------------------+
"""
_zone_action_d = dict(
    alias=dict(
        create=dict(
            exact=dict(a=_alias_create, as_l=list()),
        ),
        add_mem=dict(
            exact=dict(a=_alias_add_mem, as_l=list()),
        ),
        delete=dict(
            exact=dict(a=_alias_delete, as_l=list()),
            wild=dict(a=_alias_delete_m, as_l=list()),
            regex_m=dict(a=_alias_delete_m, as_l=list()),
            regex_s=dict(a=_alias_delete_m, as_l=list()),
        ),
        remove_mem=dict(
            exact=dict(a=_alias_remove_mem, as_l=list()),
        ),
        purge=dict(
            exact=dict(a=_alias_purge, as_l=list()),
            wild=dict(a=_alias_purge_m, as_l=list()),
            regex_m=dict(a=_alias_purge_m, as_l=list()),
            regex_s=dict(a=_alias_purge_m, as_l=list()),
        ),
        ignore=dict(
            exact=dict(a=_alias_ignore, as_l=list()),
            wild=dict(a=_alias_ignore_m, as_l=list()),
            regex_m=dict(a=_alias_ignore_m, as_l=list()),
            regex_s=dict(a=_alias_ignore_m, as_l=list()),
        ),
    ),
    peer_zone=dict(
        create=dict(
            exact=dict(a=_peer_zone_create, as_l=list()),
        ),
        add_mem=dict(
            exact=dict(a=_zone_add_mem, as_l=list()),
        ),
        delete=dict(
            exact=dict(a=_zone_delete, as_l=list()),
            wild=dict(a=_zone_delete_m, as_l=list()),
            regex_m=dict(a=_zone_delete_m, as_l=list()),
            regex_s=dict(a=_zone_delete_m, as_l=list()),
        ),
        remove_mem=dict(
            exact=dict(a=_peer_zone_remove_mem, as_l=list()),
        ),
        purge=dict(
            exact=dict(a=_zone_purge, as_l=list()),
            wild=dict(a=_zone_purge_m, as_l=list()),
            regex_m=dict(a=_zone_purge_m, as_l=list()),
            regex_s=dict(a=_zone_purge_m, as_l=list()),
        ),
        full_purge=dict(
            exact=dict(a=_zone_full_purge, as_l=list()),
            wild=dict(a=_zone_full_purge_m, as_l=list()),
            regex_m=dict(a=_zone_full_purge_m, as_l=list()),
            regex_s=dict(a=_zone_full_purge_m, as_l=list()),
        ),
    ),
    zone=dict(
        create=dict(
            exact=dict(a=_zone_create, as_l=list()),
        ),
        add_mem=dict(
            exact=dict(a=_zone_add_mem, as_l=list()),
        ),
        delete=dict(
            exact=dict(a=_zone_delete, as_l=list()),
            wild=dict(a=_zone_delete_m, as_l=list()),
            regex_m=dict(a=_zone_delete_m, as_l=list()),
            regex_s=dict(a=_zone_delete_m, as_l=list()),
        ),
        remove_mem=dict(
            exact=dict(a=_zone_remove_mem, as_l=list()),
        ),
        purge=dict(
            exact=dict(a=_zone_purge, as_l=list()),
            wild=dict(a=_zone_purge_m, as_l=list()),
            regex_m=dict(a=_zone_purge_m, as_l=list()),
            regex_s=dict(a=_zone_purge_m, as_l=list()),
        ),
        full_purge=dict(
            exact=dict(a=_zone_full_purge, as_l=list()),
            wild=dict(a=_zone_full_purge_m, as_l=list()),
            regex_m=dict(a=_zone_full_purge_m, as_l=list()),
            regex_s=dict(a=_zone_full_purge_m, as_l=list()),
        ),
    ),
    zone_cfg=dict(
        create=dict(
            exact=dict(a=_zonecfg_create, as_l=list()),
        ),
        add_mem=dict(
            exact=dict(a=_zonecfg_add_mem, as_l=list()),
        ),
        delete=dict(
            exact=dict(a=_zonecfg_delete, as_l=list()),
        ),
        remove_mem=dict(
            exact=dict(a=_zonecfg_remove_mem, as_l=list()),
        ),
    ),
)


def _parse_zone_workbook(al):
    """Parse the 'zone' worksheet in the zone workbook into a list of dictionaries as follows:

    +---------------+-------+-------------------------------------------------------------------+
    | Key           | Type  | Description                                                       |
    +===============+=======+===================================================================+
    | row           | int   | Excel workbook row number. Used for error reporting               |
    +---------------+-------+-------------------------------------------------------------------+
    | zone_obj      | str   | Value in "Zone_Object" column                                     |
    +---------------+-------+-------------------------------------------------------------------+
    | zone_obj_c    | bool  | If True, the Zone_Object is the same as a previous zone object.   |
    +---------------+-------+-------------------------------------------------------------------+
    | action        | str   | Value in "Action" column                                          |
    +---------------+-------+-------------------------------------------------------------------+
    | action_c      | bool  | If True, the action is the same as a previous action              |
    +---------------+-------+-------------------------------------------------------------------+
    | name          | str   | Value in "Name" column                                            |
    +---------------+-------+-------------------------------------------------------------------+
    | name_c        | bool  | If True, the name is the same as the previous name.               |
    +---------------+-------+-------------------------------------------------------------------+
    | match         | str   | Cell contents in "Match"                                          |
    +---------------+-------+-------------------------------------------------------------------+
    | member        | str   | Cell contents in "Member"                                         |
    +---------------+-------+-------------------------------------------------------------------+
    | pmember       | str   | Cell contents of "Principal Member"                               |
    +---------------+-------+-------------------------------------------------------------------+

    :return el: List of error messages.
    :rtype el: list
    :return zone_lists_d: Dictionary as noted in the description
    :rtype zone_lists_d: dict
    """
    global _pertinent_headers

    el, rl = list(), list()

    previous_key_d = dict(Zone_Object='zone_obj_c', Action='action_c', Name='name_c')
    previous_d = collections.OrderedDict(Zone_Object=None, Action=None, Name=None)  # Keep track of the previous value

    # Find the headers
    if len(al) < 2:
        el.append('Empty zone worksheet. Nothing to process')
    hdr_d = excel_util.find_headers(al[0], hdr_l=_pertinent_headers, warn=False)
    for key in hdr_d.keys():
        if hdr_d.get(key) is None:
            el.append('Missing column "' + str(key) + '" in zone workbook.')

    # Keeping track of the row is for error reporting purposes.
    for row in range(1, len(al)):  # Starting from the row past the header.
        try:
            for col in hdr_d.values():  # It's a blank line if all cells are None
                if al[row][col] is not None:
                    raise Found
        except Found:
            d = dict(row=row+1)
            for k0, k1 in previous_key_d.items():
                d.update({k1: False})
            for key in _pertinent_headers:
                val = al[row][hdr_d[key]]
                if key == 'Match' and val is None:
                    val = 'exact'
                if key in previous_d:
                    if val is None:
                        val = previous_d[key]
                        if val is None:
                            el.append('Missing required key, ' + key + ' at row ' + str(row+1))
                        else:
                            temp_key = previous_key_d.get(key)
                            if isinstance(temp_key, str):
                                d[temp_key] = True
                    else:
                        previous_d[key] = val
                        # Once a required key is found, all subsequent keys are required
                        clear_flag = False
                        for p_key in previous_d.keys():
                            if clear_flag:
                                previous_d[p_key] = None
                            if p_key == key:
                                clear_flag = True
                d.update({key: val})
            if isinstance(d, dict):
                rl.append(d)

    return el, rl


def _get_fabric(args_d):
    """Returns a login session and a fabric object with an initial data capture

    :param args_d: Input arguments. See _input_d for details.
    :type args_d: dict
    :return session: Session object returned from brcdapi.brcdapi_auth.login(). None if file is specified
    :rtype session: dict, None
    :return fab_obj: Fabric object as read from the input file, -i, or from reading the fabric information from the API
    :rtype fab_obj: brcddb.classes.fabric.FabricObj, None
    """
    for key in ('id', 'pw', 'ip'):
        if args_d.get(key) is None:
            return None, None
    # Create a project
    proj_obj = brcddb_project.new('zone_config', datetime.datetime.now().strftime('%d %b %Y %H:%M:%S'))
    proj_obj.s_python_version(sys.version)
    proj_obj.s_description('zone_config')

    # Login
    session = api_int.login(args_d['id'], args_d['pw'], args_d['ip'], args_d['s'], proj_obj)
    if not fos_auth.is_error(session):
        # Get some basic zoning information
        try:
            if not api_int.get_batch(session, proj_obj, _zone_kpis, args_d['fid']):
                return None, None  # api_int.get_batch() logs a detailed error message
            fab_obj_l = brcddb_project.fab_obj_for_fid(proj_obj, args_d['fid'])
            if len(fab_obj_l) == 1:
                return session, fab_obj_l[0]
            brcdapi_log.log('Fabric ID (FID), ' + str(args_d['fid']) + ', not found.', echo=True)
        except brcdapi_util.VirtualFabricIdError:
            brcdapi_log.log('Software error. Search the log for "Invalid FID" for details.', echo=True)
        except FOSError:
            brcdapi_log.log('Unexpected response from FOS. See previous messages.')
        api_int.logout(session)

    return None, None


def _remove_duplicates():
    """Remove duplicates in global tracking lists. This is probably excessive as some lists can't have duplicates
    :rtype: None
    """
    global _tracking_d, _modified_d, _purge_d

    # _tracking_d
    for key in ('alias', 'zone', 'zone_cfg'):
        for key_1 in _tracking_d.keys():
            _tracking_d[key][key_1] = gen_util.remove_duplicates(_tracking_d[key])

    # _modified_d
    for zone in _modified_d['purge_d'].keys():
        _modified_d['purge_d'][zone] = gen_util.remove_duplicates(_modified_d['purge_d'][zone])

    # _purge_d
    for port_d in _purge_d.values():
        for key in port_d.keys():
            port_d[key] = gen_util.remove_duplicates(port_d[key])


def _purge(fab_obj):
    """When possible, delete all zones with purged members

    :param fab_obj: Fabric object
    :type fab_obj: brcddb.classes.fabric.FabricObj
    """
    global _modified_d, _ignore_mem_d, _cli_d

    el, zone_purge_d = list(), dict()
    zone_purge_d = dict()
    for zone, alias_l in _modified_d['purge_d'].items():
        zone_obj = fab_obj.r_zone_obj(zone)
        if zone_obj is not None:
            mem_l = [mem for mem in zone_obj.r_members() + zone_obj.r_pmembers() if not _ignore_mem_d.get(mem, False)]
            if len(mem_l) == 0:
                zone = zone_obj.r_obj_key()
                for zonecfg_obj in obj_convert.obj_extract(zone_obj, 'ZoneCfgObj'):
                    zonecfg_obj.s_del_member(zone)
                    _cli_d['zonecfg']['remove'].append('cfgremove "' + zonecfg_obj.r_obj_key() + '", "' + zone + '"')
                fab_obj.s_del_zone(zone)
                _cli_d['zone']['delete'].append('zonedelete ' + zone)
            else:
                zone_purge_d[zone] = mem_l.copy()

    return zone_purge_d


def _summary_report(fab_obj, args_d, saved, cli_el, purge_fault_d, el, wl):
    """ Print any wrap up messages to the console and log

    :param fab_obj: Fabric object
    :type fab_obj: None, brcddb.classes.fabric.FabricObj
    :param args_d: Input arguments. See _input_d for details.
    :type args_d: dict
    :param saved: If True, the zoning database was saved to the switch.
    :type saved: bool
    :param cli_el: Error messages from _build_cli_file
    :type cli_el: list
    :param purge_fault_d: Failed zone purges. Key is the zone name. Value is a list of remaining members
    :type purge_fault_d: dict()
    :param el: Error messages from processing workbook actions
    :type el: list
    :param wl: Warning messages from processing workbook actions
    :type wl: list
    """
    global _purge_d

    summary_l = ['', 'CLI File Update Errors', '______________________']
    if len(cli_el) == 0:
        cli_el.append('None')
    summary_l.extend(cli_el)

    summary_l.extend(['',
                      'Purge Faults (zone name followed by remaining members)',
                      '______________________________________________________'])
    if len(purge_fault_d) == 0:
        summary_l.append('None')
    else:
        for zone, mem_l in purge_fault_d.items():
            summary_l.append(zone)
            summary_l.extend(['  ' + mem for mem in mem_l])
        summary_l.extend(['',
                          'Purge Faults (members only)',
                          '___________________________'])
        for zone, mem_l in purge_fault_d.items():
            summary_l.extend(mem_l)

    summary_l.extend(['', 'Error Detail', '____________'])
    summary_l.extend(el)
    if len(el) == 0:
        summary_l.append('None')
    summary_l.extend(['', 'Warning Detail', '______________'])
    summary_l.extend(wl)
    if len(wl) == 0:
        summary_l.append('None')

    summary_l.extend(['',
                      'Ports Effected By Purge (switch name followed by ports)',
                      '_______________________________________________________'])
    temp_l = list()
    for wwn, port_d in _purge_d.items():
        switch_obj = None if fab_obj is None else fab_obj.r_switch_obj(wwn)
        switch_name = brcddb_switch.best_switch_name(switch_obj, wwn=True, did=True, fid=True)
        if switch_name == 'Unknown':
            switch_name += ' (' + wwn + ')'
        temp_l.extend(['', switch_name])
        for port, alias_l in port_d.items():
            temp_l.append(gen_util.pad_string(port, 7, ' ') + ': ' + ', '.join(alias_l))
    if len(temp_l) == 0:
        temp_l.append('None')
    summary_l.extend(temp_l)

    summary_l.extend(['', 'Summary:', ''])
    summary_l.append(gen_util.pad_string(str(len(el)), 5, ' ') + ' Errors')
    summary_l.append(gen_util.pad_string(str(len(wl)), 5, ' ') + ' Warnings')
    if args_d['i']:
        summary_l.append('Working from a project file ' + args_d['i'])
    if saved:
        summary_l.append('Zone changes saved.')
    elif _pending_flag:
        buf = 'Pending zone changes not saved.'
        if not args_d['save'] and not isinstance(args_d['a'], str):
            buf += ' Use -a or -save to save changes.'
        summary_l.append(buf)
    else:
        buf = 'No changes to save.'
        if not args_d['save'] and not isinstance(args_d['a'], str):
            buf += ' Use -a or -save to save changes.'
        summary_l.append(buf)

    brcdapi_log.log(summary_l, echo=True)


def pseudo_main(args_d, fab_obj, zone_wb_l):
    """Basically the main().

    :param args_d: Input arguments. See _input_d for details.
    :type args_d: dict
    :param fab_obj: Fabric object
    :type fab_obj: None, brcddb.classes.fabric.FabricObj
    :param zone_wb_l: Output of _parse_zone_workbook() - List of actions to take
    :type zone_wb_l: list
    :return: Exit code
    :rtype: int
    """
    global _zone_action_d, _pending_flag, _debug, _eff_zone_l, _eff_mem_l

    saved, purge_fail_d, el, wl = False, dict(), list(), list()
    session, zone_d, action, proj_obj, eff_zonecfg = None, None, None, None, None

    # Get the project object
    if fab_obj is None:
        session, fab_obj = _get_fabric(args_d)
    if fab_obj is not None:
        proj_obj = fab_obj.r_project_obj()
        # Perform all pre-processing (build cross-references, add search terms, and build effective zone tables)
        brcddb_project.build_xref(proj_obj)
        brcddb_project.add_custom_search_terms(proj_obj)
        for zone_obj in fab_obj.r_eff_zone_objects():
            _eff_zone_l.append(zone_obj.r_obj_key())
            _eff_mem_l.extend(zone_obj.r_members() + zone_obj.r_pmembers())

    if proj_obj is None:
        brcdapi_log.log('Could not find or create a project object.', echo=True)
        return brcddb_common.EXIT_STATUS_INPUT_ERROR
    if args_d['scan']:
        brcddb_project.scan(proj_obj, fab_only=False, logical_switch=True)
        return brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Fill in search_d (lists of all items to use where Match is supported).
    eff_zonecfg_obj = fab_obj.r_defined_eff_zonecfg_obj()
    search_d = dict(wwn_l=fab_obj.r_login_keys(),
                    alias_l=fab_obj.r_alias_keys(),
                    zone_l=fab_obj.r_zone_keys(),
                    eff_alias_d=dict(),
                    eff_zone_d=dict(),
                    eff_zonecfg_obj=eff_zonecfg_obj)
    if eff_zonecfg_obj is not None:
        for zone_obj in eff_zonecfg_obj.r_zone_objects():
            for alias in zone_obj.r_members() + zone_obj.r_pmembers():
                search_d['eff_alias_d'][alias] = True
            search_d['eff_zone_d'][zone_obj.r_obj_key()] = True

    try:
        # Process each action in zone_wb_l
        for zone_d in zone_wb_l:

            # Debug
            # if zone_d['row'] == 45:
            #     print('TP_100')

            if _debug:
                brcdapi_log.log(pprint.pformat(zone_d), echo=True)
            try:
                action = _zone_action_d[zone_d['Zone_Object']][zone_d['Action']][zone_d['Match']]['a']
            except KeyError:
                action = _invalid_action
            temp_el, temp_wl = action(fab_obj, zone_d, search_d)
            if len(temp_el) > 0:
                if _debug:  # Leave this on a separate line so a break point could be set when _debug is not True.
                    brcdapi_log.log(temp_el + temp_wl, echo=True)
            el.extend(temp_el)
            wl.extend(temp_wl)

        # Some lists can end up with duplicates.
        _remove_duplicates()

        # Complete the purges
        purge_fail_d = _purge(fab_obj)
        if len(purge_fail_d) > 0:
            el.append('Could not complete purges. See "Purge Faults" for details.')

        # Validate the zone database
        el.extend(_validation_check(args_d, fab_obj))

        # If strict, treat all warnings as errors
        if args_d['strict']:
            el.extend(wl)
            wl = list()

        # Save the zone changes
        if len(el) == 0 and session is not None:
            if _pending_flag:
                if args_d['save'] or isinstance(args_d['a'], str):
                    obj = api_zone.replace_zoning(session, fab_obj, args_d['fid'], args_d['a'])
                    if fos_auth.is_error(obj):
                        el.extend(['Failed to replace zoning:', fos_auth.formatted_error_msg(obj)])
                    else:
                        _pending_flag, saved = False, True
                    _cli_d['save'] = True
            elif isinstance(args_d['a'], str):
                obj = api_zone.enable_zonecfg(session, args_d['fid'], args_d['a'])
                if fos_auth.is_error(obj):
                    brcdapi_zone.abort(session, args_d['fid'])
                    el.extend(['Failed to enable zone config: ' + args_d['a'],
                               'FOS error is:',
                               fos_auth.formatted_error_msg(obj)])
                else:
                    saved = True
                _cli_d['enable'] = args_d['a']

    except BaseException as e:
        el.extend(['Software error.', str(type(e)) + ': ' + str(e), 'zone_d:', pprint.pformat(zone_d)])

    # Log out
    if session is not None:
        brcdapi_log.log('Logging out', echo=True)
        obj = brcdapi_rest.logout(session)
        if fos_auth.is_error(obj):
            el.extend(['Logout failed', fos_auth.formatted_error_msg(obj)])

    # Write out the CLi file
    cli_el = _build_cli_file(args_d['cli'])

    # Write out the summaries
    _summary_report(fab_obj, args_d, saved, cli_el, purge_fail_d, el, wl)

    return brcddb_common.EXIT_STATUS_OK if len(el) == 0 else brcddb_common.EXIT_STATUS_INPUT_ERROR


def _get_input():
    """Retrieves the command line input, reads the input Workbook, and validates the input

    :return ec: Error code. See brcddb_common.EXIT_* for details
    :rtype ec: int
    """
    global __version__, _input_d, _version_d, _debug, _DEBUG

    args_z_help = args_sheet_help = args_i_help = args_fid_help = args_wwn_help = ''
    ec, error_l, zone_wb_l, proj_obj, fab_obj = brcddb_common.EXIT_STATUS_OK, list(), list(), None, None
    e_buf = ' **ERROR**: Missing required input parameter'
    w_buf = ' Ignored because -i was specified.'

    # Get command line input
    buf = 'Creates, deletes, and modifies zone objects from a workbook. See zone_sample.xlsx for details and ' \
          'examples. Also used for migrating or decommissioning storage arrays and servers. You can work on a live ' \
          'switch or from previously collected data. When working on a live switch, enter -ip, -id, -pw, and -fid. ' \
          'For offline planning purposes, specify the previously collected data with -i and -wwn instead.'
    try:
        args_d = gen_util.get_input(buf, _input_d)
    except TypeError:
        return brcddb_common.EXIT_STATUS_INPUT_ERROR  # gen_util.get_input() already posted the error message.

    # Get full file names
    args_d['i'] = brcdapi_file.full_file_name(args_d['i'], '.json')
    args_d['cli'] = brcdapi_file.full_file_name(args_d['cli'], '.txt', dot=True)

    # Set up logging
    _debug = _DEBUG
    if args_d['d']:
        _debug = True
        brcdapi_rest.verbose_debug(True)
    brcdapi_log.open_log(folder=args_d['log'], supress=args_d['sup'], no_log=args_d['nl'], version_d=_version_d)

    login_credentials_d = dict(ip=dict(s=args_d['ip'], m=''),
                               id=dict(s=args_d['id'], m=''),
                               pw=dict(s=args_d['pw'], m=''))

    # If a file name was specified, read the project object from the file.
    if isinstance(args_d['i'], str):
        try:
            proj_obj = brcddb_project.read_from(args_d['i'])
            if proj_obj is None:
                args_i_help += ' *ERROR: ' if len(args_i_help) == 0 else ', '
                args_i_help += 'Unknown error. Typical of a non-JSON formatted project file.'
                ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
            elif not args_d['scan']:
                if args_d['wwn'] is None:
                    args_wwn_help = e_buf
                    ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
                else:
                    fab_obj = proj_obj.r_fabric_obj(args_d['wwn'])
                    if fab_obj is None:
                        args_wwn_help = ' *ERROR: Fabric with this WWN not found in ' + args_d['i']
                        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
        except FileNotFoundError:
            args_i_help += ' *ERROR: ' if len(args_i_help) == 0 else ', '
            args_i_help += 'Not found'
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
        except FileExistsError:
            args_i_help += ' *ERROR: ' if len(args_i_help) == 0 else ', '
            args_i_help += 'A Folder in parameter does not exist'
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Input validation
    if not args_d['scan']:

        # Validate the login credentials.
        buf = e_buf if args_d['i'] is None else w_buf
        for key, d in login_credentials_d.items():
            if isinstance(d['s'], str):
                if args_d['i'] is not None:
                    d['m'] = buf
            elif args_d['i'] is None:
                d['m'] = buf
                ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

        # Is the fid required?
        if args_d['i'] is None and args_d['fid'] is None:
            args_fid_help = ' *ERROR: Required when -i is not specified.'
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

        # Read in the workbook with the zone definitions
        if not isinstance(args_d['z'], str):
            args_z_help = e_buf
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
        if not isinstance(args_d['sheet'], str):
            args_sheet_help = e_buf
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
        if isinstance(args_d['z'], str) and isinstance(args_d['sheet'], str):
            args_z = brcdapi_file.full_file_name(args_d['z'], '.xlsx')
            el, workbook_l = excel_util.read_workbook(args_z, dm=0, sheets=args_d['sheet'], hidden=False)
            if len(el) > 0:
                error_l.extend(el)
                args_z_help += ' *ERROR: ' + ','.join(el)
                ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
            elif len(workbook_l) != 1:
                args_sheet_help += ' *ERROR: Worksheet not found.'
            else:
                el, zone_wb_l = _parse_zone_workbook(workbook_l[0]['al'])
                if len(el) > 0:
                    error_l.extend(el)
                    args_sheet_help = ' *ERROR: Invalid. See below for details.'
                    ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Command line feedback
    ml = [
        os.path.basename(__file__) + ', ' + __version__,
        'IP address, -ip:          ' + brcdapi_util.mask_ip_addr(args_d['ip']) + login_credentials_d['ip']['m'],
        'ID, -id:                  ' + str(args_d['id']) + login_credentials_d['id']['m'],
        'Password, -pw:            ' + login_credentials_d['pw']['m'],
        'HTTPS, -s:                ' + str(args_d['s']),
        'Fabric ID (FID), -fid:    ' + str(args_d['fid']) + args_fid_help,
        'Input file, -i:           ' + str(args_d['i']) + args_i_help,
        'Fabric WWN, -wwn:         ' + str(args_d['wwn']) + args_wwn_help,
        'Zone workbook:            ' + str(args_d['z']) + args_z_help,
        'Zone worksheet, -sheet:   ' + str(args_d['sheet']) + args_sheet_help,
        'Activate, -a:             ' + str(args_d['a']),
        'Save, -save:              ' + str(args_d['save']),
        'CLI file, -cli:           ' + str(args_d['cli']),
        'Scan, -scan:              ' + str(args_d['scan']),
        'Log, -log:                ' + str(args_d['log']),
        'No log, -nl:              ' + str(args_d['nl']),
        'Debug, -d:                ' + str(args_d['d']),
        'Supress, -sup:            ' + str(args_d['sup']),
        '',
        ]
    ml.extend(error_l)
    if args_d['scan']:
        ml.extend(['', 'Scan of ' + args_d['i'], '_________________________________________________'])
        ml.extend(brcddb_project.scan(proj_obj, fab_only=False, logical_switch=True))
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    brcdapi_log.log(ml, echo=True)
    
    if isinstance(args_d['i'], str):
        args_d['a'] = False  # We're not connected to a real switch so force the zone configuration activation to False
    return ec if ec != brcddb_common.EXIT_STATUS_OK else pseudo_main(args_d, fab_obj, zone_wb_l)


###################################################################
#
#                    Main Entry Point
#
###################################################################
if _DOC_STRING:
    print('_DOC_STRING is True. No processing')
    exit(0)

if _STAND_ALONE:
    _ec = _get_input()
    brcdapi_log.close_log(['', 'Processing Complete. Exit code: ' + str(_ec)], echo=True)
    exit(_ec)
