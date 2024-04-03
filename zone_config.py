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

+-----------+---------------+-----------------------------------------------------------------------------------+
| Version   | Last Edit     | Description                                                                       |
+===========+===============+===================================================================================+
| 4.0.0     | 04 Aug 2023   | Re-Launch                                                                         |
+-----------+---------------+-----------------------------------------------------------------------------------+
| 4.0.1     | 06 Mar 2024   | Removed deprecated parameter in enable_zonecfg()                                  |
+-----------+---------------+-----------------------------------------------------------------------------------+
| 4.0.2     | 03 Apr 2024   | Renamed to zone_config.py from zone_config_x.py, Added version numbers of         |
|           |               | imported libraries. Added zone by sheet name, -sheet. Added -cli                  |
+-----------+---------------+-----------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2023, 2024 Consoli Solutions, LLC'
__date__ = '03 Apr 2024'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack@consoli-solutions.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '4.0.2'

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
_DEBUG = True  # Forces local debug without setting -d

_input_d = gen_util.parseargs_login_false_d.copy()
_input_d.update(
    i=dict(r=False,
           h='Optional. Output of capture.py, multi_capture.py, or combine.py. When this option is specified, -ip, '
             '-id, -pw, -s, and -a are ignored. This is for offline test purposes only.'),
    fid=dict(t='int', v=gen_util.range_to_list('1-128'), h='Required. Fabric ID of logical switch.'),
    z=dict(h='Required. Workbook with zone definitions. ".xlsx" is automatically appended. See zone_sample.xlsx.'),
    sheet=dict(h='Required. Sheet name in workbook, -z, to use for zoning definitions.'),
    a=dict(r=False, d=False, t='bool',
           h='Optional. No parameters. Activate or save zone changes. By default, this module is in a test mode. '
             'Test mode validates that the zone changes can be made but does not make any zone changes.'),
    cli=dict(r=False, d=None, h='Optional. Name of the file for CLI commands. ".txt" is automatically appended.'),
)
_input_d.update(gen_util.parseargs_log_d.copy())
_input_d.update(gen_util.parseargs_debug_d.copy())

_debug = False
_eff_zone_d, _eff_alias_d = dict(), dict()
_pertinent_headers = ('Zone_Object', 'Action', 'Name', 'Member', 'Principal Member')
_zone_kpis = ('running/brocade-fibrechannel-switch/fibrechannel-switch',
              'running/brocade-interface/fibrechannel',
              'running/brocade-zone/defined-configuration',
              'running/brocade-zone/effective-configuration',
              'running/brocade-fibrechannel-configuration/zone-configuration',
              'running/brocade-fibrechannel-configuration/fabric')
_non_recoverable_error = False  # A non-recoverable error occurred. Abort the transaction and terminate.
_pending_flag = False  # Updates were made to the brcddb zone database that have not been written to the switch yet.
_change_flag = False  # Changes were made successfully on the switch.
# _tracking: They key in each sub-dictionary is the zone object name. The value is the list of rows in the workbook.
# This is used for error reporting only.
_tracking = dict(alias=dict(), zone=dict(), zone_cfg=dict())

# List of CLI commands
_cli_l = list()
_MAX_ROWS = 20


class Found(Exception):
    pass


class NotFound(Exception):
    pass


class FOSError(Exception):
    pass


class ZoneCfgSave(Exception):
    pass


class ZoneCfgActivate(Exception):
    pass


def _add_to_tracking(key, zone_d):
    """Adds an item to the tracking dictionary

    :param key: 'alias', 'zone', or 'zone-cfg'
    :type key: str
    :param zone_d: Entry in the list returned from _parse_zone_workbook
    :type zone_d: dict
    :return: List of error messages. In this version, no error checking is done so the list is empty
    :rtype: list
    """
    global _tracking

    d = _tracking[key].get(zone_d['Name'])
    if d is None:
        d = list()
        _tracking[key].update({zone_d['Name']: d})
    d.append(zone_d['row'])
    return list()


def _build_cli_file(cli_file):
    """Write the CLI commands to a file

    :param cli_file: Name of CLI file
    :type cli_file: str, None
    :return: Error code
    :rtype: int
    """
    global _cli_l, _MAX_ROWS

    ec = brcddb_common.EXIT_STATUS_OK
    if isinstance(cli_file, str) and len(_cli_l) > 0:
        i, temp_l = 0, list()
        for buf in _cli_l:
            temp_l.append(buf)
            if i >= _MAX_ROWS:
                temp_l.append('')
                i = 0
            else:
                i += 1
        el = brcdapi_file.write_file(cli_file, temp_l)
        if len(el) > 0:
            brcdapi_log.log(el, echo=True)
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    return ec


def _validation_check(fab_obj):
    """Check for common mistakes - names are valid and membership is correct

    :param fab_obj: Fabric object
    :type fab_obj: brcddb.classes.fabric.FabricObj
    """
    global _non_recoverable_error, _tracking

    el = list()

    # Alias checks
    for name, row_l in _tracking['alias'].items():
        row_str = '. Rows: ' + ', '.join([str(i+1) for i in row_l])
        alias_obj = fab_obj.r_alias_obj(name)
        if alias_obj is None:
            # The only reason an alias in _tracking wouldn't be here is if it was deleted or a previously reported error
            continue
        # Make sure it has a valid name
        if not gen_util.is_valid_zone_name(name):
            _non_recoverable_error = True
            el.append('Invalid alias name, ' + name + row_str)
        # Make sure there is at least one member
        if len(alias_obj.r_members()) == 0:
            el.append('Alias ' + name + ' has no members' + row_str)
        # Make sure the members are valid WWNs or d,i
        for mem in alias_obj.r_members():
            if not gen_util.is_wwn(mem, full_check=True) and not gen_util.is_di(mem):
                el.append('Invalid member name: ' + mem + ' in alias ' + name + row_str)

    # Zone checks
    for name, row_l in _tracking['zone'].items():
        row_str = '. Rows: ' + ', '.join([str(i+1) for i in row_l])
        zone_obj = fab_obj.r_zone_obj(name)
        # The only reason a zone in _tracking wouldn't be here is if it was deleted or a previously reported error
        if zone_obj is None:
            continue
        # Make sure it has a valid name
        if not gen_util.is_valid_zone_name(name):
            _non_recoverable_error = True
            el.append('Invalid zone name, ' + name + row_str)
        member_len, pmember_len = len(zone_obj.r_members()), len(zone_obj.r_pmembers())
        if member_len == 0:
            el.append('Zone ' + name + ' has no members' + row_str)
        if zone_obj.r_is_peer() and pmember_len == 0:
            el.append('Zone ' + name + ' has no peer members' + row_str)
        if member_len + pmember_len < 2:
            el.append('Zone ' + name + ' has ' + str(member_len+pmember_len) + ' members' + row_str)
    # Check all zones to make sure an alias used in any zone (new or existing) wasn't deleted
    for zone_obj in fab_obj.r_zone_objects():
        for mem in [m for m in zone_obj.r_members() + zone_obj.r_pmembers()
                    if not gen_util.is_di(m) and not gen_util.is_wwn(m, full_check=True)]:
            if fab_obj.r_alias_obj(mem) is None:
                _non_recoverable_error = True
                zone_name = zone_obj.r_obj_key()
                row_l = gen_util.convert_to_list(_tracking['alias'].get(mem))
                row_l.extend(gen_util.convert_to_list(_tracking['zone'].get(zone_name)))
                row_str = '.' if len(row_l) == 0 else '. Rows: ' + ', '.join([str(i+1) for i in row_l])
                el.append('Alias ' + mem + ' used in zone ' + zone_name + ' does not exist.' + row_str)

    # Zone configuration checks
    for name, row_l in _tracking['zone_cfg'].items():
        row_str = '. Rows: ' + ', '.join([str(i+1) for i in row_l])
        # Make sure it has a valid name
        if fab_obj.r_zonecfg_obj(name) is not None and not gen_util.is_valid_zone_name(name):
            _non_recoverable_error = True
            el.append('Invalid zone configuration name, ' + name + row_str)
    # Did we delete any zones that are in a zone configuration?
    for zonecfg_obj in fab_obj.r_zonecfg_objects():
        zonecfg_name = zonecfg_obj.r_obj_key()
        if zonecfg_name == '_effective_zone_cfg':
            continue
        z_row_l = gen_util.convert_to_list(_tracking['zone_cfg'].get(zonecfg_name))
        for mem in [m for m in zonecfg_obj.r_members() if fab_obj.r_zone_obj(m) is None]:
            _non_recoverable_error = True
            row_l = z_row_l + gen_util.convert_to_list(_tracking['zone'].get(mem))
            row_str = '.' if len(row_l) == 0 else '. Rows: ' + ', '.join([str(i+1) for i in row_l])
            el.append('Zone ' + mem + ' used in zone configuration ' + zonecfg_name + ' does not exist. ' + row_str)

    return el


#################################################
#                                               #
#         Actions for _zone_action_d            #
#                                               #
#################################################
def _invalid_action(fab_obj, zone_d):
    """Error handler for "Actions" not supported by the "Zone_Object"
    
    :param fab_obj: Fabric object
    :type fab_obj: brcddb.classes.fabric.FabricObj
    :param zone_d: Entry in the list returned from _parse_zone_workbook
    :type zone_d: dict
    :return: List of error messages
    :rtype: list
    """
    global _non_recoverable_error
    _non_recoverable_error = True
    return ['"' + zone_d['Action'] + '" is not a valid Action for Zone_Object "' + zone_d['Zone_Object'] + '" at row ' +
            str(zone_d['row']+1)]


def _alias_create(fab_obj, zone_d):
    """Create an alias. See _invalid_action() for parameter descriptions"""
    global _non_recoverable_error, _pending_flag, _cli_l

    # Make sure it's a valid alias definition
    el = list()
    if isinstance(zone_d['Principal Member'], str):  # Principal members are not supported in an alias
        _non_recoverable_error = True
        el.append('Principal members not supported in alias create at row ' + str(zone_d['row']+1))
    if not gen_util.is_valid_zone_name(zone_d['Name']):  # Is it a valid alias name?
        _non_recoverable_error = True
        el.append('Invalid alias name, ' + zone_d['Name'] + ', at row ' + str(zone_d['row']+1))
    if not gen_util.is_wwn(zone_d['Member'], full_check=True) and not gen_util.is_di(zone_d['Member']):
        _non_recoverable_error = True
        el.append('Invalid alias member, ' + zone_d['Member'] + ', at row ' + str(zone_d['row']+1))
    if fab_obj is not None:
        alias_obj = fab_obj.r_alias_obj(zone_d['Name'])
        if alias_obj is not None:  # If the alias already exists, do they have the same members?
            if zone_d['Member'] in alias_obj.r_members():
                return el
            else:
                _non_recoverable_error = True
                el.append('Zone ' + zone_d['Name'] + ' in row ' + str(zone_d['row']) +
                          ' already exists and has different members.')
    if len(el) > 0:
        return el

    # Create the alias
    if fab_obj is not None:
        fab_obj.s_add_alias(zone_d['Name'], zone_d['Member'])
        _pending_flag = True
    _cli_l.append('alicreate "' + zone_d['Name'] + '", "' + zone_d['Member'] + '"')
    return _add_to_tracking('alias', zone_d)


def _alias_delete(fab_obj, zone_d):
    """Delete an alias. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_l, _eff_alias_d, _non_recoverable_error

    if fab_obj is not None:
        if bool(_eff_alias_d.get(zone_d['Name'])):
            return list()  # It's in the effective zone, so it can't be deleted.
        alias_obj = fab_obj.r_alias_obj(zone_d['Name'])
        if alias_obj is not None:
            zone_l = [obj.r_obj_key() for obj in obj_convert.obj_extract(alias_obj, 'ZoneObj')]
            if len(zone_l) > 0:
                return ['Cannot delete alias ' + alias_obj.r_obj_key() + ' because it is used in zones ' +
                        ', '.join(zone_l)]
            fab_obj.s_del_alias(zone_d['Name'])
            _pending_flag = True
            _cli_l.append('alidelete "' + zone_d['Name'] + '"')
    else:
        _cli_l.append('alidelete "' + zone_d['Name'] + '"')
    return _add_to_tracking('alias', zone_d)


def _alias_add_mem(fab_obj, zone_d):
    """Add alias members. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _non_recoverable_error, _cli_l

    # Validate the members
    el = list()
    if zone_d['Principal Member'] is not None:
        _non_recoverable_error = True
        el.append('Principal members not supported in alias create at row ' + str(zone_d['row']+1))
    if not gen_util.is_wwn(zone_d['Member'], full_check=True) and not gen_util.is_di(zone_d['Member']):
        _non_recoverable_error = True
        el.append('Invalid alias member, ' + zone_d['Member'] + ', at row ' + str(zone_d['row']+1))
    if fab_obj is not None:
        alias_obj = fab_obj.r_alias_obj(zone_d['Name'])
        if alias_obj is None:
            _non_recoverable_error = True
            el.append('Alias at row ' + str(zone_d['row']) + ' does not exist')
        elif zone_d['Member'] in alias_obj.r_members():
            return el  # The member is already in the alias so there is nothing to do.
    if len(el) > 0:
        return el

    # Add the alias
    if fab_obj is not None:
        alias_obj = fab_obj.r_alias_obj(zone_d['Name'])
        if alias_obj is None:
            return ['Alias, ' + zone_d['Name'] + ' does not exist at row ' + str(zone_d['row'])]
        alias_obj.s_add_member(zone_d['Name'], zone_d['Member'])
        _pending_flag = True
    _cli_l.append('aliadd "' + zone_d['Name'] + '", "' + zone_d['Member'] + '"')
    return _add_to_tracking('alias', zone_d)


def _alias_remove_mem(fab_obj, zone_d):
    """Remove alias members. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_l, _non_recoverable_error

    if fab_obj is not None:
        alias_obj = fab_obj.r_alias_obj(zone_d['Name'])
        if alias_obj is None:
            _non_recoverable_error = True
            return ['Alias, ' + zone_d['Name'] + ', does not exist at row ' + str(zone_d['row'])]
        alias_obj.s_del_member(zone_d['Name'], zone_d['Member'])
        _pending_flag = True
    _cli_l.append('aliremove "' + zone_d['Name'] + '", "' + zone_d['Member'] + '"')
    return _add_to_tracking('alias', zone_d)


def _peer_zone_create(fab_obj, zone_d):
    """Create a peer zone. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _non_recoverable_error, _cli_l

    el = list()

    # If it's a previous action, members are being added
    if zone_d['name_c']:
        return _zone_add_mem(fab_obj, zone_d)

    # Make sure it's a valid zone definition
    if not gen_util.is_valid_zone_name(zone_d['Name']):
        _non_recoverable_error = True
        el.append('Invalid zone name, ' + zone_d['Name'] + ', at row ' + str(zone_d['row']+1))
    m = zone_d['Member']
    if isinstance(m, str) and \
            not gen_util.is_wwn(m, full_check=True) and \
            not gen_util.is_di(m) and \
            not gen_util.is_valid_zone_name(m):
        _non_recoverable_error = True
        el.append('Invalid zone member, ' + m + ', at row ' + str(zone_d['row']+1))
    zone_obj = fab_obj.r_zone_obj(zone_d['Name'])
    if zone_obj is not None:
        _non_recoverable_error = True
        el.append('Zone ' + zone_d['Name'] + ' in row ' + str(zone_d['row']) +
                  ' already exists. Consider using "add_mem".')
    if len(el) > 0:
        return el

    # Create the peer zone
    if fab_obj is not None:
        fab_obj.s_add_zone(zone_d['Name'], brcddb_common.ZONE_USER_PEER, zone_d['Member'], zone_d['Principal Member'])
        _pending_flag = True
    buf = 'zonecreate --peerzone "' + zone_d['Name'] + '"'
    if isinstance(zone_d['Principal Member'], str):
        buf += ' -principal "' + zone_d['Principal Member'] + '"'
    if isinstance(zone_d['Member'], str):
        buf += ' -members "' + zone_d['Member'] + '"'
    _cli_l.append(buf)
    return _add_to_tracking('zone', zone_d)


def _zone_create(fab_obj, zone_d):
    """Create a zone. See _invalid_action() for parameter descriptions"""
    global _non_recoverable_error, _pending_flag, _cli_l

    el = list()

    # If it's a previous action, members are being added
    if zone_d['name_c']:
        return _zone_add_mem(fab_obj, zone_d)

    # Make sure it's a valid zone definition
    if zone_d['Principal Member'] is not None:  # Principal members are only supported in peer zones
        _non_recoverable_error = True
        el.append('Principal members only supported in peer zones at row ' + str(zone_d['row']+1))
    if not gen_util.is_valid_zone_name(zone_d['Name']):  # Is the zone name valid?
        _non_recoverable_error = True
        el.append('Invalid zone name, ' + zone_d['Name'] + ', at row ' + str(zone_d['row']+1))
    m = zone_d['Member']
    if not gen_util.is_wwn(m, full_check=True) and not gen_util.is_di(m) and not gen_util.is_valid_zone_name(m):
        _non_recoverable_error = True
        el.append('Invalid zone member, ' + m + ', at row ' + str(zone_d['row']+1))
    zone_obj = fab_obj.r_zone_obj(zone_d['Name'])
    if zone_obj is not None:  # If the zone already exists, do they have the same members?
        el.append('Zone ' + zone_d['Name'] + ' in row ' + str(zone_d['row']) +
                  ' already exists. Consider using "adm_mem".')
    if len(el) > 0:
        return el

    # Create the zone
    if fab_obj is not None:
        fab_obj.s_add_zone(zone_d['Name'],
                           brcddb_common.ZONE_STANDARD_ZONE,
                           zone_d['Member'],
                           zone_d['Principal Member'])
        _pending_flag = True
    _cli_l.append('zonecreate "' + zone_d['Name'] + '", "' + zone_d['Member'] + '"')
    return _add_to_tracking('zone', zone_d)


def _zone_delete(fab_obj, zone_d):
    """Delete a zone. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_l, _eff_zone_d, _non_recoverable_error

    if fab_obj is not None:
        zone_obj = fab_obj.r_zone_obj(zone_d['Name'])
        if zone_obj is not None and bool(_eff_zone_d.get(zone_d['Name'])):
            _non_recoverable_error = True
            return [zone_d['Name'] + ' at row ' + str(zone_d['row']) +
                    ' is in the effective zone configuration and cannot be deleted']
        fab_obj.s_del_zone(zone_d['Name'])
        _pending_flag = True
    _cli_l.append('zonedelete ' + zone_d['Name'])
    return _add_to_tracking('zone', zone_d)


def _zone_add_mem(fab_obj, zone_d):
    """Remove zone members. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _non_recoverable_error, _cli_l

    el = list()

    if fab_obj is not None:

        # Validate the parameters
        zone_obj = fab_obj.r_zone_obj(zone_d['Name'])
        if zone_obj is None:
            return [zone_d['Name'] + ' does not exist at row ' + str(zone_d['row']+1)]
        buf = 'zoneadd --peerzone "' + zone_d['Name'] + '"' if zone_obj.r_is_peer() else \
            'zoneadd "' + zone_d['Name'] + '"'
        m = zone_d['Principal Member']
        if isinstance(m, str):
            if not zone_obj.r_is_peer():
                return ['Principal members are not supported in ' + zone_d['Name'] +
                        ' because is not a peer zone at row ' + str(zone_d['row']+1)]
            if not gen_util.is_wwn(m, full_check=True) and not gen_util.is_di(m) and not gen_util.is_valid_zone_name(m):
                _non_recoverable_error = True
                el.append('Invalid zone member, ' + m + ', at row ' + str(zone_d['row']+1))
        for m in [mem for mem in [zone_d['Member'], zone_d['Principal Member']] if isinstance(mem, str)]:
            if not gen_util.is_wwn(m, full_check=True) and not gen_util.is_di(m) and not gen_util.is_valid_zone_name(m):
                _non_recoverable_error = True
                el.append('Invalid zone member, ' + m + ', at row ' + str(zone_d['row'] + 1))
        if len(el) > 0:
            return el

        # Add the zone members
        zone_obj.s_add_member(zone_d['Member'])
        zone_obj.s_add_pmember(zone_d['Principal Member'])
        _pending_flag = True
    else:
        buf = 'zoneadd --peerzone "' + zone_d['Name'] + '"' if zone_d['Zone_Object'] == 'peer_zone' else \
            'zoneadd "' + zone_d['Name'] + '"'
    if isinstance(zone_d['Principal Member'], str):
        buf += ' -principal "' + zone_d['Principal Member'] + '"'
    if isinstance(zone_d['Member'], str):
        buf += ' -members "' + zone_d['Member'] + '"'
    _cli_l.append(buf)
    return _add_to_tracking('zone', zone_d)


def _peer_zone_remove_mem(fab_obj, zone_d):
    """Remove zone members. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_l, _non_recoverable_error

    if fab_obj is not None:
        # Validate the input
        zone_obj = fab_obj.r_zone_obj(zone_d['Name'])
        if zone_obj is None:
            return [zone_d['Name'] + ' does not exist at row ' + str(zone_d['row']+1)]
        if not zone_obj.r_is_peer():
            return ['Zone type mismatch. ' + zone_d['Name'] + ' is not a peer zone at row ' + str(zone_d['row']+1) +
                    ' Consider using Zone_Object "zone"']
        member, pmember = zone_d['Member'], zone_d['Principal Member']
        if isinstance(member, str):
            if member not in zone_obj.r_member():
                if isinstance(pmember, str) and pmember not in zone_obj.r_pmembers():
                    return list()  # There is nothing to do
            if member in zone_obj.r_pmembers():
                _non_recoverable_error = False
                return ['The "Member" in row ' + str(zone_d['row']+1) + ' is a "Principal Member".']
        if isinstance(pmember, str) and pmember in zone_obj.r_members():
            _non_recoverable_error = False
            return ['The "Principal Member" in row ' + str(zone_d['row'] + 1) + ' is a "Member".']

        # Make the zoning changes
        zone_obj.s_del_member(zone_d['Member'])
        zone_obj.s_del_pmember(zone_d['Principal Member'])
        _pending_flag = True
    buf = 'zoneremove --peerzone "' + zone_d['Name'] + '"'
    if isinstance(zone_d['Principal Member'], str):
        buf += ' -principal "' + zone_d['Principal Member'] + '"'
    if isinstance(zone_d['Member'], str):
        buf += ' -members "' + zone_d['Member'] + '"'
    _cli_l.append(buf)
    return _add_to_tracking('zone', zone_d)


def _zone_remove_mem(fab_obj, zone_d):
    """Remove zone members. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_l, _non_recoverable_error

    # Validate the parameters
    if zone_d['Principal Member'] is not None:
        _non_recoverable_error = True
        return ['Principal members not supported in zone member remove at row ' + str(zone_d['row']+1)]
    zone_obj = None
    if fab_obj is not None:
        zone_obj = fab_obj.r_zone_obj(zone_d['Name'])
        if zone_obj is not None:
            if zone_obj.r_is_peer():
                _non_recoverable_error = True
                return ['Zone type mismatch. ' + zone_d['Name'] + ' is a peer zone at row ' + str(zone_d['row']+1)]
            if zone_d['Member'] not in zone_obj.r_members():
                return list()  # There is nothing to do

    # Remove the members
    if zone_obj is not None:
        zone_obj.s_del_member(zone_d['Member'])
        _pending_flag = True
    _cli_l.append('zoneremove "' + zone_d['Name'] + '", ' + zone_d['Member'])
    return _add_to_tracking('zone', zone_d)


def _zonecfg_create(fab_obj, zone_d):
    """Create a zone configuration. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _non_recoverable_error, _cli_l

    # If it's a previous action, members are being added
    if zone_d['name_c']:
        return _zonecfg_add_mem(fab_obj, zone_d)

    # Validate the input
    if zone_d['Principal Member'] is not None:
        _non_recoverable_error = True
        return ['Principal members not supported in zone configuration at row ' + str(zone_d['row']+1)]
    zonecfg_obj = fab_obj.r_zone_obj(zone_d['Name'])
    if zonecfg_obj is not None:  # If it exists, do they have the same members?
        if gen_util.compare_lists(zonecfg_obj.r_members(), zone_d['Member']):
            return list()  # There is nothing to do. As a practical matter, this is highly unlikely.
        else:
            return ['Zone configuration in row ' + str(zone_d['row']) +
                    ' already exists, but the membership list does not match. Consider using "Action" "add_mem"']
    
    if fab_obj is not None:
        fab_obj.s_add_zonecfg(zone_d['Name'], zone_d['Member'])
        _pending_flag = True
    buf = 'cfgcreate "' + zone_d['Name'] + '"'
    if isinstance(zone_d['Member'], str):
        buf += ' "' + zone_d['Member'] + '"'
    _cli_l.append('cfgcreate "' + zone_d['Name'] + '", "' + zone_d['Member'] + '"')
    return _add_to_tracking('zone_cfg', zone_d)


def _zonecfg_delete(fab_obj, zone_d):
    """Delete a zone config. See _invalid_action() for parameter descriptions"""
    global _non_recoverable_error, _pending_flag, _cli_l

    el = list()

    # Validate - Make sure the zone configuration exists and that it's not the effective zone.
    if fab_obj is not None:
        eff_zonecfg = fab_obj.r_defined_eff_zonecfg_key()
        if isinstance(eff_zonecfg, str) and eff_zonecfg == zone_d['Name']:
            _non_recoverable_error = True
            el.append('Cannot delete the zone configuration at row ' + str(zone_d['row']+1) +
                      ' because it is the effective zone configuration.')
            return el

        # Delete the zone configuration
        fab_obj.s_del_zonecfg(zone_d['Name'])
        _pending_flag = True
    _cli_l.append('cfgdelete "' + zone_d['Name'] + '"')
    return _add_to_tracking('zone_cfg', zone_d)


def _zonecfg_add_mem(fab_obj, zone_d):
    """Add zone config members. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_l, _non_recoverable_error

    if fab_obj is not None:
        zonecfg_obj = fab_obj.r_zonecfg_obj(zone_d['Name'])
        if zonecfg_obj is None:
            _non_recoverable_error = True
            return ['Zone configuration ' + zone_d['Name'] + ' does not exist at row ' + str(zone_d['row'])]
        zonecfg_obj.s_add_member(zone_d['Member'])
        _pending_flag = True
        _cli_l.append('cfgadd "' + zone_d['Name'] + '", "' + zone_d['Member'] + '"')
    else:
        _cli_l.append('cfgadd "' + zone_d['Name'] + '", "' + zone_d['Member'] + '"')
    return _add_to_tracking('zone_cfg', zone_d)


def _zonecfg_remove_mem(fab_obj, zone_d):
    """Remove zone config members. See _invalid_action() for parameter descriptions"""
    global _pending_flag, _cli_l, _non_recoverable_error

    if fab_obj is not None:
        zonecfg_obj = fab_obj.r_zonecfg_obj(zone_d['Name'])
        if zonecfg_obj is None:
            _non_recoverable_error = True
            return ['The zone configuration, ' + zone_d['Name'] + ' does not exist.']
        if isinstance(zone_d['Member'], str) and zone_d['Member'] not in zonecfg_obj.r_members():
            return list()  # There is nothing to do
        zonecfg_obj.s_del_member(zone_d['Member'])
        _pending_flag = True
        _cli_l.append('cfgremove "' + zone_d['Name'] + '", "' + ';'.join(zone_d['Member']) + '"')
    else:
        _cli_l.append('cfgremove "' + zone_d['Name'] + '", "' + ';'.join(zone_d['Member']) + '"')
    return _add_to_tracking('zone_cfg', zone_d)


def _zonecfg_activate(fab_obj, zone_d):
    """Activate a zone configuration. See _invalid_action() for parameter descriptions"""
    global _cli_l

    el = list()
    _cli_l.append('cfgenable "' + zone_d['Name'] + '" -f')
    if fab_obj is not None:
        if fab_obj.r_zonecfg_obj(zone_d['Name']) is None:
            return ['Zone configuration ' + zone_d['Name'] + ' does not exist at row ' + str(zone_d['row']+1)]
        el = _validation_check(fab_obj)
        if len(el) == 0:
            raise ZoneCfgActivate  # No errors if we get here so let it rip
    return el


def _zonecfg_save(fab_obj, zone_d):
    """Activate a zone configuration. See _invalid_action() for parameter descriptions"""
    global _cli_l

    el = list()
    _cli_l.append('cfgsave -f')
    if fab_obj is not None:
        el = _validation_check(fab_obj)
        if len(el) == 0:
            raise ZoneCfgSave  # No errors if we get here so let it rip
    return el


"""
_zone_action_d: I could have just had one dictionary with a pointer to the method and handled the activate list
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
        activate=dict(a=_invalid_action),
        add_mem=dict(a=_alias_add_mem, as_l=list()),
        create=dict(a=_alias_create, as_l=list()),
        delete=dict(a=_alias_delete, as_l=list()),
        remove_mem=dict(a=_alias_remove_mem, as_l=list()),
        save=dict(a=_invalid_action),
    ),
    peer_zone=dict(
        activate=dict(a=_invalid_action),
        add_mem=dict(a=_zone_add_mem, as_l=list()),
        create=dict(a=_peer_zone_create, as_l=list()),
        delete=dict(a=_zone_delete, as_l=list()),
        remove_mem=dict(a=_peer_zone_remove_mem, as_l=list()),
        save=dict(a=_invalid_action),
    ),
    zone=dict(
        activate=dict(a=_invalid_action),
        add_mem=dict(a=_zone_add_mem, as_l=list()),
        create=dict(a=_zone_create, as_l=list()),
        delete=dict(a=_zone_delete, as_l=list()),
        remove_mem=dict(a=_zone_remove_mem, as_l=list()),
        save=dict(a=_invalid_action),
    ),
    zone_cfg=dict(
        activate=dict(a=_zonecfg_activate),
        add_mem=dict(a=_zonecfg_add_mem, as_l=list()),
        create=dict(a=_zonecfg_create, as_l=list()),
        delete=dict(a=_zonecfg_delete, as_l=list()),
        remove_mem=dict(a=_zonecfg_remove_mem, as_l=list()),
        save=dict(a=_zonecfg_save),
    ),
)


def _parse_zone_workbook(al):
    """Parse the 'zone' worksheet in the zone workbook into a list of dictionaries as follows:

    +---------------+-------+-------------------------------------------------------------------+
    | Key           | Type  | Description                                                       |
    +===============+=======+===================================================================+
    | row           | int   | Zero relative row numbers. Used for error reporting               |
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
            d = dict(row=row)
            for k0, k1 in previous_key_d.items():
                d.update({k1: False})
            for key in _pertinent_headers:
                val = al[row][hdr_d[key]]
                if key == 'Zone_Object' and isinstance(val, str) and val == 'comment':
                    d = None
                    break
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
                if key in previous_d and isinstance(previous_d[key], str) and previous_d[key] == 'save' and \
                        isinstance(previous_d['Zone_Object'], str) and previous_d['Zone_Object'] == 'zone_cfg':
                    break  # I forgot that "save" doesn't need a Name so this was a quick and dirty fix
            if isinstance(d, dict):
                rl.append(d)

    return el, rl


def _capture_data(session, proj_obj, fid):
    """Capture basic zoning information

    :param session: Session object returned from brcdapi.fos_auth.login()
    :type session: dict
    :param proj_obj: brcddb project object
    :type proj_obj: brcddb.classes.project.ProjObj
    :param fid: Logical FID number for the fabric of interest
    :type fid: int
    :return: The fabric object matching the FID
    :rtype: brcddb.classes.fabric.FabricObj
    """
    global _zone_kpis, _pending_flag

    if not api_int.get_batch(session, proj_obj, _zone_kpis, fid):
        raise FOSError
    fab_obj_l = brcddb_project.fab_obj_for_fid(proj_obj, fid)
    if len(fab_obj_l) == 1:
        return fab_obj_l[0]
    elif len(fab_obj_l) == 0:
        raise NotFound
    raise FOSError


def _get_project(user_id, pw, ip, sec, fid, inf):
    """Returns a login session and a project object with an initial data capture

    :param user_id: User ID. Only used if inf is None
    :type user_id: str, None
    :param pw: Password. Only used if inf is None
    :type pw: str, None
    :param ip: IP address. Only used if inf is None
    :type ip: str, None
    :param sec: . Only used if inf is None. Security. 'none' for HTTP. 'self' for self-signed certificate.
    :type sec: str, None
    :param fid: Fabric ID
    :type fid: int
    :param inf: None if not used. otherwise, output of capture.py, combine.py, or multi_capture.py
    :type inf: str, None
    :return el: List of error messages
    :rtype el: list
    :return session: Session object returned from brcdapi.brcdapi_auth.login(). None if file is specified
    :rtype session: dict, None
    :return fab_obj: Fabric object as read from the input file, -i, or from reading the fabric information from the API
    :rtype fab_obj: brcddb.classes.fabric.FabricObj, None
    """
    el, session, proj_obj, fab_obj = list(), None, None, None

    # If a file name was specified, read the project object from the file. If not, read data directly from the switch
    if isinstance(inf, str):
        try:
            proj_obj = brcddb_project.read_from(inf)
        except FileNotFoundError:
            el.append('Input file, ' + inf + ', not found')
        except FileExistsError:
            el.append('Folder in ' + inf + ' does not exist')
        if proj_obj is None:
            el.append('Unknown error reading ' + inf + '. This typically occurs when ' + inf +
                      ' is not JSON formatted.')
        else:
            fab_obj_l = list()
            for fab_obj in proj_obj.r_fabric_objects():
                for fab_fid in brcddb_fabric.fab_fids(fab_obj):
                    if fab_fid == fid:
                        fab_obj_l.append(fab_obj)
                        break
            if len(fab_obj_l) == 0:
                el.append('Fabric ID (FID) ' + str(fid) + ' not found.')
            elif len(fab_obj_l) > 1:
                el.append('Multiple fabrics matching FID ' + str(fid) + ' found:')
                el.extend(['  ', '  \n'.join([brcddb_fabric.best_fab_name(obj, wwn=True) for obj in fab_obj_l])])

    elif isinstance(user_id, str) and isinstance(pw, str) and isinstance(ip, str):

        # Create project
        proj_obj = brcddb_project.new('zone_config', datetime.datetime.now().strftime('%d %b %Y %H:%M:%S'))
        proj_obj.s_python_version(sys.version)
        proj_obj.s_description('zone_config')

        # Login
        session = api_int.login(user_id, pw, ip, sec, proj_obj)
        if fos_auth.is_error(session):
            el.append('Login failed.')   # api_int.login posts a more detailed error message.
            return el, session, fab_obj

        try:
            # Get some basic zoning information
            fab_obj = _capture_data(session, proj_obj, fid)
        except NotFound:
            el.append('Fabric ID (FID) ' + str(fid) + ' not found.')
        except FOSError:
            el.append('Unexpected response from FOS. See previous messages.')

    return el, session, fab_obj


def pseudo_main(user_id, pw, ip, sec, fid, test_mode, inf, zone_l, cli_file):
    """Basically the main().

    :param user_id: User ID
    :type user_id: str
    :param pw: Password
    :type pw: str
    :param ip: IP address
    :type ip: str
    :param sec: Security. 'none' for HTTP, 'self' for self-signed certificate, 'CA' for signed certificate
    :type sec: str
    :param fid: Fabric ID
    :type fid: int
    :param test_mode: If True, validate that the zone changes can be made but does not make any zone changes
    :type test_mode: bool
    :param inf: Output of capture.py, combine.py, or multi_capture.py
    :type inf: str, None
    :param zone_l: Output of _parse_zone_workbook() - List of actions to take
    :type zone_l: list
    :param cli_file: Name of CLI file
    :type cli_file: str, None
    :return: Exit code
    :rtype: int
    """
    global _zone_action_d, _zone_kpis, _pending_flag, _non_recoverable_error, _change_flag, _debug
    global _eff_zone_d, _eff_alias_d

    ec, el, session, zone_d = brcddb_common.EXIT_STATUS_OK, list(), None, None

    try:

        # Read or capture zoning data
        temp_l, session, fab_obj = _get_project(user_id, pw, ip, sec, fid, inf)
        for zone_obj in fab_obj.r_zone_objects():
            _eff_zone_d.update({zone_obj.r_obj_key(): True})
            for alias in zone_obj.r_members():
                _eff_alias_d.update({alias: True})
        el.extend(temp_l)
        if len(temp_l) > 0:
            brcdapi_log.log(el, echo=True)
            return brcddb_common.EXIT_STATUS_ERROR
        proj_obj = None if fab_obj is None else fab_obj.r_project_obj()

        # Process each action in zone_l
        for zone_d in zone_l:
            if _debug:
                brcdapi_log.log(pprint.pformat(zone_d), echo=True)
            action_d = _zone_action_d.get(zone_d['Zone_Object'])
            if action_d is None:
                el.append('Invalid Zone_Object, ' + str(zone_d['Zone_Object']) + ' in row ' + str(zone_d['row']+1))
                continue
            try:
                temp_l = action_d[zone_d['Action']]['a'](fab_obj, zone_d)
                if len(temp_l) > 0:
                    if _debug:
                        brcdapi_log.log(temp_l, echo=True)
                    ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
                el.extend(temp_l)
            except KeyError:
                el.append('Invalid Action: ' + str(zone_d['Action']) + ' in row ' + str(zone_d['row']+1))
                ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
            except brcdapi_util.VirtualFabricIdError:
                el.append('Software error. Search the log for "Invalid FID" for details.')
                ec = brcddb_common.EXIT_STATUS_API_ERROR
            except ZoneCfgActivate:
                if test_mode:
                    _pending_flag = False
                    el.append('Test mode, -t, set. Zone ' + zone_d['Name'] + ' not activated')
                elif _non_recoverable_error or ec != brcddb_common.EXIT_STATUS_OK:
                    el.append('Could not activate ' + zone_d['Name'] + ' due to previous errors')
                    ec = brcddb_common.EXIT_STATUS_API_ERROR
                else:
                    # Commit whatever transactions are in buffer
                    if _pending_flag:
                        obj = api_zone.replace_zoning(session, fab_obj, fid)
                        _pending_flag = False
                        if fos_auth.is_error(obj):
                            _non_recoverable_error, ec = True, brcddb_common.EXIT_STATUS_API_ERROR
                            el.extend(['Failed to replace zoning:', fos_auth.formatted_error_msg(obj)])
                            raise FOSError

                        # Clear out the local zone database and recapture the zone database from FOS
                        proj_obj.s_del_chassis(session.pop('chassis_wwn'))
                        fab_obj = _capture_data(session, proj_obj, fid)

                    # Enable the zone configuration
                    eff_zonecfg_obj = fab_obj.r_eff_zone_cfg_obj()
                    if eff_zonecfg_obj is not None and zone_d['Name'] == fab_obj.r_eff_zone_cfg_obj().r_obj_key():
                        buf = 'The defined zone configuration, ' + zone_d['Name']
                        buf += ' is already active. The zone configuration activate at row ' + str(zone_d['row'] + 1)
                        buf += ' was ignored.'
                        el.append(buf)
                    obj = api_zone.enable_zonecfg(session, fid, zone_d['Name'])
                    if fos_auth.is_error(obj):
                        brcdapi_zone.abort(session, fid)
                        el.extend(['Failed to enable zone config: ' + zone_d['Name'],
                                   'FOS error is:',
                                   fos_auth.formatted_error_msg(obj)])
                        _non_recoverable_error, ec = True, brcddb_common.EXIT_STATUS_API_ERROR
                    else:
                        _change_flag = True
                        # Clear out the local zone database and recapture the zone database from FOS
                        proj_obj.s_del_chassis(session.pop('chassis_wwn'))
                        fab_obj = _capture_data(session, proj_obj, fid)
            except ZoneCfgSave:
                if test_mode:
                    _pending_flag = False
                    el.append('Test mode, -t, set. Zone DB not saved')
                elif _non_recoverable_error or ec != brcddb_common.EXIT_STATUS_OK:
                    el.append('Could not save zoning changes due to previous errors')
                    ec = brcddb_common.EXIT_STATUS_API_ERROR
                else:
                    obj = api_zone.replace_zoning(session, fab_obj, fid)
                    if fos_auth.is_error(obj):
                        _non_recoverable_error, ec = True, brcddb_common.EXIT_STATUS_API_ERROR
                        el.extend(['Failed to replace zoning:', fos_auth.formatted_error_msg(obj)])
                    else:
                        _pending_flag, _change_flag = False, True
                # Clear out the local zone database and recapture the zone database from FOS
                proj_obj.s_del_chassis(session.pop('chassis_wwn'))
                fab_obj = _capture_data(session, proj_obj, fid)

    except NotFound:
        el.append('Fabric ID (FID) ' + str(fid) + ' not found.')
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    except brcdapi_util.VirtualFabricIdError:
        el.append('Software error. Search the log for "Invalid FID" for details.')
    except FOSError:
        el.append('Unexpected response from FOS. See previous messages.')
        ec = brcddb_common.EXIT_STATUS_API_ERROR
    except BaseException as e:
        el.extend(['Software error.', str(type(e)) + ': ' + str(e), 'zone_d:', pprint.pformat(zone_d)])
        ec = brcddb_common.EXIT_STATUS_ERROR

    # Log out
    if session is not None:
        brcdapi_log.log('Logging out', echo=True)
        obj = brcdapi_rest.logout(session)
        if fos_auth.is_error(obj):
            el.extend(['Logout failed', fos_auth.formatted_error_msg(obj)])

    # Print any wrap up messages
    el.append('0 Errors' if ec == brcddb_common.EXIT_STATUS_OK else str(len(el)) + ' Errors')
    buf = 'Outstanding zone changes not saved. If you intended to save changes, you must add -a on the command line. '\
          'In the workbook you must select "zone_cfg" as the "Zone_Object" and either "save" or "activate" as the '\
          '"action" in the workbook.'
    buf = buf if _pending_flag else 'Zone transactions saved.' if _change_flag else 'No changes made.'
    el.append(buf)
    if test_mode:
        el.append('Test mode only. No attempt was made to make zoning changes.')
    brcdapi_log.log(el, echo=True)

    ec = _build_cli_file(cli_file)

    return ec


def _get_input():
    """Retrieves the command line input, reads the input Workbook, and validates the input

    :return ec: Error code. See brcddb_common.EXIT_* for details
    :rtype ec: int
    """
    global __version__, _input_d, _version_d, _debug, _DEBUG

    ec, error_l, args_z_help, args_sheet_help, zone_l = brcddb_common.EXIT_STATUS_OK, list(), '', '', list()

    # Get command line input
    buf = 'Creates, deletes, and modifies zone objects from a workbook. See zone_sample.xlsx for details and ' \
          'examples. This module is primarily for examples but can be used for simple zone changes. Minimal ' \
          'error checking is performed. Minimal batching of zone operations is performed. For more complex ' \
          'zoning transactions and higher performance, use applications zone_restore.py or zone_merge.py.'
    try:
        args_d = gen_util.get_input(buf, _input_d)
    except TypeError:
        return brcddb_common.EXIT_STATUS_INPUT_ERROR  # gen_util.get_input() already posted the error message.

    # Set up logging
    if args_d['d']:
        _debug = True
        brcdapi_rest.verbose_debug(True)
    if _DEBUG:
        _debug = True
    brcdapi_log.open_log(folder=args_d['log'], supress=args_d['sup'], no_log=args_d['nl'], version_d=_version_d)

    # If an input file and -cli wasn't specified, make sure all the login credentials were.
    if args_d['i'] is None and args_d['cli'] is None:
        el = list()
        for key, buf in dict(ip=args_d['ip'], id=args_d['id'], pw=args_d['pw']).items():
            if buf is None:
                el.append('Missing -' + key + ' parameter. Rerun with -h for additional help')
        if len(el) > 0:
            brcdapi_log.log(el, echo=True)
            return brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Read in the workbook with the zone definitions
    args_z = brcdapi_file.full_file_name(args_d['z'], '.xlsx')
    error_l, workbook_l = excel_util.read_workbook(args_z, dm=0, sheets=args_d['sheet'])
    if len(error_l) > 0:
        brcdapi_log.log(error_l, echo=True)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    elif len(workbook_l) != 1:
        error_l.append(' *ERROR: worksheet "' + args_d['sheet'] + '" not found in ' + str(args_d['z']))
        args_sheet_help = ' *ERROR: Missing'
    else:
        el, zone_l = _parse_zone_workbook(workbook_l[0]['al'])
        if len(el) > 0:
            error_l.extend(el)
            args_sheet_help = ' *ERROR: Invalid. See below for details.'
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Command line feedback
    ml = [
        os.path.basename(__file__) + ', ' + __version__,
        'IP address, -ip:          ' + brcdapi_util.mask_ip_addr(args_d['ip']),
        'ID, -id:                  ' + str(args_d['id']),
        'HTTPS, -s:                ' + str(args_d['s']),
        'Input file, -i:           ' + str(args_d['i']),
        'Fabric ID (FID), -fid:    ' + str(args_d['fid']),
        'Zone workbook:            ' + str(args_d['z']) + args_z_help,
        'Zone worksheet, -sheet:   ' + str(args_d['sheet']) + args_sheet_help,
        'Activate or save, -a:     ' + str(args_d['a']),
        'CLI file, -cli:           ' + str(args_d['cli']),
        'Log, -log:                ' + str(args_d['log']),
        'No log, -nl:              ' + str(args_d['nl']),
        'Debug, -d:                ' + str(args_d['d']),
        'Supress, -sup:            ' + str(args_d['sup']),
        '',
        ]
    ml.extend(error_l)
    brcdapi_log.log(ml + error_l, echo=True)
    
    if isinstance(args_d['i'], str):
        args_d['a'] = False  # We're not connected to a real switch so force the zone configuration activation to False
    return ec if ec != brcddb_common.EXIT_STATUS_OK else \
        pseudo_main(args_d['id'],
                    args_d['pw'],
                    args_d['ip'],
                    args_d['s'],
                    args_d['fid'],
                    not args_d['a'],
                    brcdapi_file.full_file_name(args_d['i'], '.json'),
                    zone_l,
                    brcdapi_file.full_file_name(args_d['cli'], '.txt'))


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
