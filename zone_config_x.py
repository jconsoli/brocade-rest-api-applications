#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright 2023, 2024 Consoli Solutions, LLC.  All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may also obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.

The license is free for single customer use (internal applications). Use of this module in the production,
redistribution, or service delivery for commerce requires an additional license. Contact jack@consoli-solutions.com for
details.

:mod:`zone_config.py` - Examples on how to create, modify and delete zone objects using the brcdapi.zone library.

**Description**

    This spawned from https://github.com/jconsoli/brocade-rest-api-examples/zone_config.py. zone_config.py was
    written for the sole purpose of illustrating automated zoning design considerations and to provide coding examples.
    I never thought anyone would zone form a workbook, but I needed something to validate zone changes ahead of a change
    control window, so I hacked zone_config.py to use the database in brcddb to facilitate this. Over time, I figured
    since I already had a workbook of validated zone changes, I may as well use it to save and activate the zone
    changes, so I added logic for that as well.

    The operation is essentially the same as how FOS handles zoning in that zoning transactions are stored in memory and
    then applied to the switch all at once. Specifically:

    1.  The zone database is read from the switch and added to the brcddb database referred to herein as the “local
        database”.
    2.  Actions specified in the input workbook are tested against the local database and if there are no errors, the
        local database is updated. (the ability to do is what supports the test mode, -t option).
    3.  A zone configuration activation (equivalent to cfgenable) or save (equivalent to cfgsave) then write the revised
        zone database to the switch.

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 4.0.0     | 04 Aug 2023   | Re-Launch                                                                         |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 4.0.1     | 06 Mar 2024   | Removed deprecated parameter in enable_zonecfg()                                  |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2023, 2024 Consoli Solutions, LLC'
__date__ = '06 Mar 2024'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack@consoli-solutions.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '4.0.1'

import collections
import sys
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

_DOC_STRING = False  # Should always be False. Prohibits any actual I/O. Only useful for building documentation
# _STAND_ALONE: True: Executes as a standalone module taking input from the command line. False: Does not automatically
# execute. This is useful when importing this module into another module that calls psuedo_main().
_STAND_ALONE = True  # See note above

_input_d = gen_util.parseargs_login_false_d.copy()
_input_d.update(
    i=dict(r=False,
           h='Optional. Output of capture.py, multi_capture.py, or combine.py. When this option is specified, -ip, '
             '-id, -pw, -s, and -a are ignored. This is for offline test purposes only.'),
    fid=dict(t='int', v=gen_util.range_to_list('1-128'), h='Required. Fabric ID of logical switch.'),
    z=dict(h='Required. Workbook with zone definitions. ".xlsx" is automatically appended. See zone_sample.xlsx.'),
    a=dict(r=False, d=False, t='bool',
           h='Optional. No parameters. Activate or save zone changes. By default, this module is in a test mode. '
             'Test mode validates that the zone changes can be made but does not make any zone changes.'),
)
_input_d.update(gen_util.parseargs_log_d.copy())
_input_d.update(gen_util.parseargs_debug_d.copy())

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
                el.append('Alias ' + mem + ' used in zone ' + zone_name + ' not found' + row_str)

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
        z_row_l = gen_util.convert_to_list(_tracking['zone_cfg'].get(zonecfg_name))
        for mem in [m for m in zonecfg_obj.r_members() if fab_obj.r_zone_obj(m) is None]:
            _non_recoverable_error = True
            row_l = z_row_l + gen_util.convert_to_list(_tracking['zone'].get(mem))
            row_str = '.' if len(row_l) == 0 else '. Rows: ' + ', '.join([str(i+1) for i in row_l])
            el.append('Zone ' + mem + ' used in zone configuration ' + zonecfg_name + ' not found' + row_str)

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
    global _non_recoverable_error, _pending_flag

    el = list()

    # Make sure it's a valid alias definition
    if len(zone_d['Principal Member']) > 0:
        _non_recoverable_error = True
        el.append('Principal members not supported in alias create at row ' + str(zone_d['row']+1))
    if not gen_util.is_valid_zone_name(zone_d['Name']):
        _non_recoverable_error = True
        el.append('Invalid alias name, ' + zone_d['Name'] + ', at row ' + str(zone_d['row']+1))
    if isinstance(zone_d['Member'], str):
        for member in [m for m in zone_d['Member'].split(';')]:
            if not gen_util.is_wwn(member, full_check=True) or not gen_util.is_di(member):
                _non_recoverable_error = True
                el.append('Invalid alias member, ' + member + ', at row ' + str(zone_d['row']+1))

    if len(el) > 0:
        return el
    fab_obj.s_add_alias(zone_d['Name'], zone_d['Member'])
    _pending_flag = True
    return _add_to_tracking('alias', zone_d)


def _alias_delete(fab_obj, zone_d):
    """Delete an alias. See _invalid_action() for parameter descriptions"""
    global _pending_flag
    fab_obj.s_del_alias(zone_d['Name'])
    _pending_flag = True
    return _add_to_tracking('alias', zone_d)


def _alias_remove_mem(fab_obj, zone_d):
    """Remove alias members. See _invalid_action() for parameter descriptions"""
    global _pending_flag
    alias_obj = fab_obj.r_alias_obj(zone_d['Name'])
    if alias_obj is not None:
        alias_obj.s_del_member(zone_d['Name'], zone_d['Member'])
        _pending_flag = True
    return _add_to_tracking('alias', zone_d)


def _peer_zone_create(fab_obj, zone_d):
    """Create a peer zone. See _invalid_action() for parameter descriptions"""
    global _pending_flag

    el = list()

    # Make sure it's a valid zone definition
    if not gen_util.is_valid_zone_name(zone_d['Name']):
        _non_recoverable_error = True
        el.append('Invalid zone name, ' + zone_d['Name'] + ', at row ' + str(zone_d['row']+1))
    if isinstance(zone_d['Member'], str):
        for member in [m for m in zone_d['Member'].split(';')]:
            if not gen_util.is_wwn(member, full_check=True) or not gen_util.is_di(member):
                _non_recoverable_error = True
                el.append('Invalid zone member, ' + member + ', at row ' + str(zone_d['row']+1))

    if len(el) > 0:
        return el
    fab_obj.s_add_zone(zone_d['Name'], brcddb_common.ZONE_USER_PEER, zone_d['Member'], zone_d['Principal Member'])
    _pending_flag = True
    return _add_to_tracking('zone', zone_d)


def _zone_create(fab_obj, zone_d):
    """Create a zone. See _invalid_action() for parameter descriptions"""
    global _non_recoverable_error, _pending_flag

    el = list()

    # Make sure it's a valid zone definition
    if len(zone_d['Principal Member']) > 0:
        _non_recoverable_error = True
        return ['Principal members only supported in peer zones at row ' + str(zone_d['row']+1)]
    if not gen_util.is_valid_zone_name(zone_d['Name']):
        _non_recoverable_error = True
        el.append('Invalid zone name, ' + zone_d['Name'] + ', at row ' + str(zone_d['row']+1))
    if isinstance(zone_d['Member'], str):
        for member in [m for m in zone_d['Member'].split(';')]:
            if not gen_util.is_wwn(member, full_check=True) or not gen_util.is_di(member):
                _non_recoverable_error = True
                el.append('Invalid zone member, ' + member + ', at row ' + str(zone_d['row']+1))

    if len(el) > 0:
        return el
    fab_obj.s_add_zone(zone_d['Name'], brcddb_common.ZONE_STANDARD_ZONE, zone_d['Member'], zone_d['Principal Member'])
    _pending_flag = True
    return _add_to_tracking('zone', zone_d)


def _zone_delete(fab_obj, zone_d):
    """Delete a zone. See _invalid_action() for parameter descriptions"""
    global _pending_flag
    fab_obj.s_del_zone(zone_d['Name'])
    _pending_flag = True
    return _add_to_tracking('zone', zone_d)


def _zone_remove_mem(fab_obj, zone_d):
    """Remove zone members. See _invalid_action() for parameter descriptions"""
    global _pending_flag
    zone_obj = fab_obj.r_zone_obj(zone_d['Name'])
    if zone_obj is not None:
        zone_obj.s_del_member(zone_d['Member'] + zone_d['Principal Member'])
        _pending_flag = True
    return _add_to_tracking('zone', zone_d)


def _zonecfg_create(fab_obj, zone_d):
    """Create a zone configuration. See _invalid_action() for parameter descriptions"""
    global _pending_flag
    if len(zone_d['Principal Member']) > 0:
        return ['Principal members not supported in zone configurations at row ' + str(zone_d['row']+1)]
    fab_obj.s_add_zonecfg(zone_d['Name'], zone_d['Member'])
    _pending_flag = True
    return _add_to_tracking('zone_cfg', zone_d)


def _zonecfg_delete(fab_obj, zone_d):
    """Delete a zone config. See _invalid_action() for parameter descriptions"""
    global _non_recoverable_error, _pending_flag
    el = list()
    eff_zonecfg_obj = fab_obj.r_eff_zone_cfg_obj()
    if eff_zonecfg_obj is not None and zone_d['Name'] == fab_obj.r_eff_zone_cfg_obj().r_obj_key():
        _non_recoverable_error = True
        el.extend(_add_to_tracking('zone_cfg', zone_d))
        el.append('The defined zone configuration, ' + zone_d['Name'] +
                  ' is the effective zone and cannot be deleted at row ' + str(zone_d['row']+1))
    else:
        fab_obj.s_del_zonecfg(zone_d['Name'])
        _pending_flag = True
        el.extend(_add_to_tracking('zone_cfg', zone_d))
    return el


def _zonecfg_remove_mem(fab_obj, zone_d):
    """Remove zone config members. See _invalid_action() for parameter descriptions"""
    global _pending_flag
    zonecfg_obj = fab_obj.r_zonecfg_obj(zone_d['Name'])
    if zonecfg_obj is not None:
        zonecfg_obj.s_del_member(zone_d['Member'])
        _pending_flag = True
    return _add_to_tracking('zone_cfg', zone_d)


def _zonecfg_activate(fab_obj, zone_d):
    """Activate a zone configuration. See _invalid_action() for parameter descriptions"""
    if fab_obj.r_zonecfg_obj(zone_d['Name']) is None:
        return ['Zone configuration ' + zone_d['Name'] + ' does not exist at row ' + str(zone_d['row']+1)]
    el = _validation_check(fab_obj)
    if len(el) == 0:
        raise ZoneCfgActivate  # No errors if we get here so let it rip
    return el


def _zonecfg_save(fab_obj, zone_d):
    """Activate a zone configuration. See _invalid_action() for parameter descriptions"""
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
        add_mem=dict(a=_alias_create, as_l=list()),  # If the alias already exists it will just add the members
        create=dict(a=_alias_create, as_l=list()),
        delete=dict(a=_alias_delete, as_l=list()),
        remove_mem=dict(a=_alias_remove_mem, as_l=list()),
        save=dict(a=_invalid_action),
    ),
    peer_zone=dict(
        activate=dict(a=_invalid_action),
        add_mem=dict(a=_peer_zone_create, as_l=list()),  # If the zone already exists it will just add the members
        create=dict(a=_peer_zone_create, as_l=list()),
        delete=dict(a=_zone_delete, as_l=list()),
        remove_mem=dict(a=_zone_remove_mem, as_l=list()),
        save=dict(a=_invalid_action),
    ),
    zone=dict(
        activate=dict(a=_invalid_action),
        add_mem=dict(a=_zone_create, as_l=list()),  # If the zone already exists it will just add the members
        create=dict(a=_zone_create, as_l=list()),
        delete=dict(a=_zone_delete, as_l=list()),
        remove_mem=dict(a=_zone_remove_mem, as_l=list()),
        save=dict(a=_invalid_action),
    ),
    zone_cfg=dict(
        activate=dict(a=_zonecfg_activate),
        add_mem=dict(a=_zonecfg_create, as_l=list()),
        create=dict(a=_zonecfg_create, as_l=list()),
        delete=dict(a=_zonecfg_delete, as_l=list()),
        remove_mem=dict(a=_zonecfg_remove_mem, as_l=list()),
        save=dict(a=_zonecfg_save),
    ),
)


def _parse_zone_workbook(al):
    """Parse the 'zone' worksheet in the zone workbook into a list of dictionaries as follows:

    +-----------+-------+-------------------------------------------------------+
    | Key       | Type  | Description                                           |
    +===========+=======+=======================================================+
    | row       | int   | Zero relative row numbers. Used for error reporting   |
    +-----------+-------+-------------------------------------------------------+
    | zone_obj  | str   | Value in "Zone_Object" column                         |
    +-----------+-------+-------------------------------------------------------+
    | action    | str   | Value in "Action" column                              |
    +-----------+-------+-------------------------------------------------------+
    | name      | str   | Value in "Name" column                                |
    +-----------+-------+-------------------------------------------------------+
    | member    | list  | Converted CSV in "Member" column to a list            |
    +-----------+-------+-------------------------------------------------------+
    | pmember   | list  | Converted CSV in "Principal Member" column to a list  |
    +-----------+-------+-------------------------------------------------------+

    :return el: List of error messages.
    :rtype el: list
    :return zone_lists_d: Dictionary as noted in the description
    :rtype zone_lists_d: dict
    """
    global _pertinent_headers

    el, rl = list(), list()

    previous_d = collections.OrderedDict(Zone_Object=None, Action=None, Name=None)  # Keep track of the previous value
    csv_d = dict({'Member': True, 'Principal Member': True})  # If True, split S-CSV into list

    # Find the headers
    if len(al) < 2:
        el.append('Empty zone worksheet. Nothing to process')
    hdr_d = excel_util.find_headers(al[0], hdr_l=_pertinent_headers, warn=False)
    for key in hdr_d.keys():
        if hdr_d.get(key) is None:
            el.append('Missing column "' + str(key) + '" in zone workbook.')

    # Keeping track of the row is for error reporting purposes so a specific row on the worksheet can be referenced.
    for row in range(1, len(al)):  # Starting from the row past the header.
        try:
            for col in hdr_d.values():  # It's a blank line if all cells are None
                if al[row][col] is not None:
                    raise Found
        except Found:
            d = dict(row=row)
            for key in _pertinent_headers:
                val = al[row][hdr_d[key]]
                if key in previous_d:
                    if val is None:
                        val = previous_d[key]
                        if val is None:
                            el.append('Missing required key, ' + key + ' at row ' + str(row+1))
                    else:
                        previous_d[key] = val
                        # Once a required key is found, all subsequent keys are required
                        clear_flag = False
                        for p_key in previous_d.keys():
                            if clear_flag:
                                previous_d[p_key] = None
                            if p_key == key:
                                clear_flag = True
                if bool(csv_d.get(key)):
                    val = list() if val is None else [str(v).strip() for v in val.split(';')]
                d.update({key: val})
                if key in previous_d and isinstance(previous_d[key], str) and previous_d[key] == 'save' and \
                        isinstance(previous_d['Zone_Object'], str) and previous_d['Zone_Object'] == 'zone_cfg':
                    break  # I forgot that "save" doesn't need a Name so this was a quick and dirty fix
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
    :param inf: Output of capture.py, combine.py, or multi_capture.py
    :type inf: str, None
    :return el: List of error messages
    :rtype el: list
    :return session: Session object returned from brcdapi.brcdapi_auth.login(). None if file is specified
    :rtype session: dict, None
    :return fab_obj: Fabric object
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

    else:  # Login and get data from the switch

        # Create project
        proj_obj = brcddb_project.new('zone_config_x', datetime.datetime.now().strftime('%d %b %Y %H:%M:%S'))
        proj_obj.s_python_version(sys.version)
        proj_obj.s_description('zone_config_x')

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


def pseudo_main(user_id, pw, ip, sec, fid, test_mode, inf, zone_l):
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
    :return: Exit code
    :rtype: int
    """
    global _zone_action_d, _zone_kpis, _pending_flag, _non_recoverable_error, _change_flag

    ec, el, session, zone_d = brcddb_common.EXIT_STATUS_OK, list(), None, None

    try:

        # Read or capture zoning data
        temp_l, session, fab_obj = _get_project(user_id, pw, ip, sec, fid, inf)
        el.extend(temp_l)
        if len(temp_l) > 0 or fab_obj is None:
            brcdapi_log.log(el, echo=True)
            return brcddb_common.EXIT_STATUS_ERROR
        proj_obj = fab_obj.r_project_obj()

        # Process each action in zone_l
        for zone_d in zone_l:
            action_d = _zone_action_d.get(zone_d['Zone_Object'])
            if action_d is None:
                el.append('Invalid Zone_Object, ' + str(zone_d['Zone_Object']) + ' in row ' + str(zone_d['row']+1))
                continue
            try:
                temp_l = action_d[zone_d['Action']]['a'](fab_obj, zone_d)
                if len(temp_l) > 0:
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
    buf = 'Outstanding zone changes not saved' if _pending_flag else 'Zone transactions saved.' if _change_flag \
        else 'No changes made.'
    el.append(buf)
    if test_mode:
        el.append('Test mode only. No attempt was made to make zoning changes.')
    brcdapi_log.log(el, echo=True)

    return ec


def _get_input():
    """Retrieves the command line input, reads the input Workbook, and validates the input

    :return ec: Error code. See brcddb_common.EXIT_* for details
    :rtype ec: int
    """
    global __version__, _input_d

    ec, error_l, args_i_help, zone_l = brcddb_common.EXIT_STATUS_OK, list(), '', list()

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
        brcdapi_rest.verbose_debug(True)
    brcdapi_log.open_log(folder=args_d['log'], supress=args_d['sup'], no_log=args_d['nl'])

    # If an input file wasn't specified, make sure all the login credentials were.
    if args_d['i'] is None:
        el = list()
        for key, buf in dict(ip=args_d['ip'], id=args_d['id'], pw=args_d['pw']).items():
            if buf is None:
                el.append('Missing -' + key + ' parameter. Rerun with -h for additional help')
        if len(el) > 0:
            brcdapi_log.log(el, echo=True)
            return brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Read in the workbook with the zone definitions
    args_z = brcdapi_file.full_file_name(args_d['z'], '.xlsx')
    error_l, workbook_l = excel_util.read_workbook(args_z, dm=3, sheets='zone')
    if len(error_l) > 0:
        brcdapi_log.log(error_l, echo=True)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    elif len(workbook_l) != 1:
        error_l.append(' *ERROR: worksheet "zone" missing')
    else:
        el, zone_l = _parse_zone_workbook(workbook_l[0]['al'])
        if len(el) > 0:
            error_l.extend(el)
            args_i_help = ' *ERROR: Invalid worksheet. See below for details.'
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Command line feedback
    ml = [
        'zone_config_x.py version: ' + __version__,
        'IP address, -ip:          ' + brcdapi_util.mask_ip_addr(args_d['ip']),
        'ID, -id:                  ' + str(args_d['id']),
        'HTTPS, -s:                ' + str(args_d['s']),
        'Input file, -i:           ' + str(args_d['i']),
        'Fabric ID (FID), -fid:    ' + str(args_d['fid']),
        'Activate or save, -a:     ' + str(args_d['a']),
        'Zone workbook:            ' + str(args_d['z']) + args_i_help,
        'Log, -log:                ' + str(args_d['log']),
        'No log, -nl:              ' + str(args_d['nl']),
        'Debug, -d:                ' + str(args_d['d']),
        'Supress, -sup:            ' + str(args_d['sup']),
        '',
        ]
    ml.extend(error_l)
    brcdapi_log.log(ml + error_l, echo=True)
    
    """Initially, "test mode" was a "-t" option. By default, all actions were taken unless -t was specified. Then one
    day someone forgot to enter "-t". I'll assume no additional explanation is needed as to why I modified this script
    to default to test mode. So I removed -t, added -a, and to minimize any other logic changes I passed "not args_a"
    instead of what used to be args_t below. This is not mentioned in the Version Control section because it changed a
    preliminary version prior to publication of this script.

    Furthermore, adding the ability to test against previously captured data, -i, was an after thought. Since you can't
    do anything but test without a connection to a switch, test mode is artificially forced by setting args_a to False.
    Don't forget we are passing "not args_a" to pseudo_main())"""
    if isinstance(args_d['i'], str):
        args_d['a'] = False
    return ec if ec != brcddb_common.EXIT_STATUS_OK else \
        pseudo_main(args_d['id'],
                    args_d['pw'],
                    args_d['ip'],
                    args_d['s'],
                    args_d['fid'],
                    not args_d['a'],
                    brcdapi_file.full_file_name(args_d['i'], '.json'),
                    zone_l)


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
