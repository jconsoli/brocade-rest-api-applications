#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright 2023, 2024, 2025, 2026 Jack Consoli.  All rights reserved.

**License**

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may also obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.

The license is free for single customer use (internal applications). Use of this module in the production,
redistribution, or service delivery for commerce requires an additional license. Contact jack_consoli@yahoo.com for
details.

**Description**

Configure logical switch(es) from a workbook

**Version Control**

+-----------+---------------+---------------------------------------------------------------------------------------+
| Version   | Last Edit     | Description                                                                           |
+===========+===============+=======================================================================================+
| 4.0.0     | 04 Aug 2023   | Re-Launch                                                                             |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.1     | 06 Mar 2024   | Improved handling of ports that could not be moved due to errors.                     |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.2     | 03 Apr 2024   | Added version numbers of imported libraries.                                          |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.3     | 06 Dec 2024   | Updated comments only.                                                                |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.4     | 27 Dec 2024   | Fixed address binding and invalid port keys.                                          |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.5     | 04 Jan 2025   | Added ability to make port configuration settings via the CLI.                        |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.6     | 12 Apr 2025   | Added support for $p and $i when interpreting CLI strings.                            |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.7     | 25 Aug 2025   | Use brcddb.util.util.get_import_modules to dynamically determined imported libraries. |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.8     | 19 Oct 2025   | Updated comments only.                                                                |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.9     | 20 Feb 2026   | Updated copyright notice.                                                             |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.1.0     | 10 Mar 2026   | Cleaned up handling of port definitions for ports not in the chassis.                 |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.1.1     | 01 Aug 2026   | Added CLI commands for switch and chassis. Added replace support for $cwwn, $swwn,    |
|           |               | $license, and $lwwn. Improved summary report.                                         |
+-----------+---------------+---------------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2024, 2025, 2026 Jack Consoli'
__date__ = '01 Aug 2026'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack_consoli@yahoo.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '4.1.1'

import sys
import datetime
import os
import time
import pprint
import brcdapi.log as brcdapi_log
import brcdapi.brcdapi_rest as brcdapi_rest
import brcdapi.switch as brcdapi_switch
import brcdapi.fos_auth as fos_auth
import brcdapi.fos_cli as fos_cli
import brcdapi.port as brcdapi_port
import brcdapi.util as brcdapi_util
import brcdapi.file as brcdapi_file
import brcdapi.gen_util as gen_util
import brcddb.brcddb_common as brcddb_common
import brcddb.brcddb_chassis as brcddb_chassis
import brcddb.brcddb_login as brcddb_login
import brcddb.report.utils as report_utils
import brcddb.api.interface as api_int
import brcddb.brcddb_project as brcddb_project
import brcddb.brcddb_fabric as brcddb_fabric
import brcddb.brcddb_switch as brcddb_switch
import brcddb.classes.util as class_util

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
# _STAND_ALONE: True: Executes as a standalone module taking input from the command line. False: Does not automatically
# execute. This is useful when importing this module into another module that calls psuedo_main().
_STAND_ALONE = True  # See note above

_input_d = gen_util.parseargs_login_d.copy()
_input_d.update(
    i=dict(h='Required. File name of Excel Workbook to read.'),
    cli=dict(r=False, d=False, t='bool',
             h='Optional. No parameters. CLI commands are only executed when this option is set.'),
    force=dict(r=False, d=False, t='bool',
               h='Optional. No parameters. If specified, move ports even if they are online. Setting -force is also '
                 'required to disable a chassis, switch, or port that is enabled. All CLI is executed. Typically only '
                 'used for service operations.'),
)
_input_d.update(gen_util.parseargs_log_d.copy())
_input_d.update(gen_util.parseargs_debug_d.copy())

# Time in seconds to wait after enabling a chassis or switch before continuing. This is necessary because FOS gets
# very busy after a chassis or switch enable. This is to give the switch time to settle down.
_ENABLE_WAIT = brcdapi_switch.enable_wait_time()  # See comment above

_bfc_fabric = 'running/' + brcdapi_util.bfc_uri
_chassis_uri = 'running/' + brcdapi_util.bcc_uri
_basic_capture_kpi_l = [
    # 'running/brocade-fabric/fabric-switch',  Done automatically in brcddb.api.interface.get_chassis()
    _chassis_uri,
    'running/' + brcdapi_util.bcmic_uri,
    _bfc_fabric,
    'running/' + brcdapi_util.bfs_uri,
    'running/' + brcdapi_util.bfc_sw_uri,
    'running/' + brcdapi_util.bfc_port_uri,
    'running/' + brcdapi_util.bfcfp_uri,
    'running/' + brcdapi_util.ficon_cup_uri,
    'running/' + brcdapi_util.bifc_uri,
]
_cli_error_l = ('not part of this switch', 'error', 'invalid', 'port is not present in this switch')
_db_read = 0

_parameters_d = dict(
    # Chassis
    chassis_name=brcdapi_util.bc_user_name,
    fcr=brcdapi_util.bc_fcr_en,
    msg_of_day=brcdapi_util.bc_motd,
    shell_to=brcdapi_util.bc_shell_to,
    session_to=brcdapi_util.bc_session_to,
    tcp_to=brcdapi_util.bc_tcp_to_level,
    max_rest=brcdapi_util.bc_max_rest,
    web_tools=brcdapi_util.bc_webtools,
    # Switch
    fab_name=brcdapi_util.bfs_fab_user_name,
    switch_name=brcdapi_util.bfs_sw_user_name,
    did=brcdapi_util.bfs_did,
    insistent_did=brcdapi_util.bfc_idid,
    fabric_principal=brcdapi_util.bfc_principal_en,
    fab_priority=brcdapi_util.bfc_principal_pri,
    xisl=brcdapi_util.bfc_xisl_en,
    login_banner=brcdapi_util.bfs_banner,
    switch_type=None,  # Not processed using this table
    dup_wwn=brcdapi_util.bfc_fport_enforce_login,
    bind=None,  # Not processed using this table
    config_ports=None,  # Not processed using this table
    cup=brcdapi_util.ficon_cup_en,
)


class ForceError(Exception):
    pass


#########################################
#                                       #
#           Progress Tracking           #
#                                       #
#########################################

"""tracker_d is added to any objects that have been modified. tracker_d is defined as follows:

+-------------------+-------+---------------------------------------------------------------------------------------+
| Key               | Type  | Description                                                                           |
+===================+=======+=======================================================================================+
| cli_success       | int   | Number of CLI commands that appear to have successfully completed.                    |
+-------------------+-------+---------------------------------------------------------------------------------------+
| cli_fail          | int   | Number of CLI commands that appear to have failed.                                    |
+-------------------+-------+---------------------------------------------------------------------------------------+
| config_success    | int   | Number of configuration changes successfully completed.                               |
+-------------------+-------+---------------------------------------------------------------------------------------+
| config_fail       | int   | Number of configuration changes that failed.                                          |
+-------------------+-------+---------------------------------------------------------------------------------------+
"""
_tracking_template_d = dict(
    cli_success=0,
    cli_fail=0,
    config_success=0,
    config_fail=0,
)

#########################################
#                                       #
#         Common/Utilitarian            #
#                                       #
#########################################


def _refresh_project(session, working_proj_obj, desc=None):
    """Clear out the existing project object and recapture all data

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param working_proj_obj: Project we're currently working on. This is needed to copy tracker_d
    :param desc: Project description
    :type desc: str, None
    :return: New project object
    :rtype: brcddb.classes.project.ProjectObj
    """
    global _basic_capture_kpi_l, _db_read

    # Refresh the project
    brcdapi_log.log('Reading project' if _db_read == 0 else 'Refreshing project', echo=True)
    _db_read += 1
    proj_obj = brcddb_project.new('Create_LS', datetime.datetime.now().strftime('%d %b %Y %H:%M:%S'))
    proj_obj.s_python_version(sys.version)
    proj_obj.s_description(str(desc))
    session.pop('chassis_wwn', None)
    brcdapi_log.set_suppress_all()
    api_int.get_batch(session, proj_obj, _basic_capture_kpi_l)
    brcdapi_log.clear_suppress_all()
    if working_proj_obj is None:
        return proj_obj

    # Add back tracker_d to the chassis object
    for working_chassis_obj in working_proj_obj.r_chassis_objects():  # There can only be one chassis.
        tracker_d = working_chassis_obj.r_get('tracker_d')
        if tracker_d is not None:
            chassis_obj = proj_obj.r_chassis_obj(working_chassis_obj.r_obj_key())
            if chassis_obj is not None:  # chassis_obj can't be None, but this code is identical for switch objects
                chassis_obj.s_new_key('tracker_d', tracker_d)

    # Add back tracker_d to the switch objects
    for working_switch_obj in working_proj_obj.r_switch_objects():
        tracker_d = working_switch_obj.r_get('tracker_d')
        if tracker_d is not None:
            switch_obj = proj_obj.r_switch_obj(working_switch_obj.r_obj_key())
            if switch_obj is not None:
                switch_obj.s_new_key('tracker_d', tracker_d)

    return proj_obj


def _cli_error(response_l):
    """Checks to see if there are any obvious errors in a CLI response

    :param response_l: Responses returned from fos_cli.send_command()
    :type response_l: list
    :return: True if errors were found, False otherwise
    :rtype: bool
    """
    global _cli_error_l

    for buf in _cli_error_l:
        for r_buf in response_l:
            if r_buf.lower() in buf:
                return True

    return False


def _replace_variables(obj, cmd_l, obj_d):
    """Replaces the $x variables for CLI commands

    :param obj: brcddb object
    :type obj: brcddb.classes.chassis.ChassisObj, brcddb.classes.switch.SwitchObj, brcddb.classes.port.PortObj
    :param cmd_l: CLI commands
    :type cmd_l: str, list, None
    :param obj_d: Dictionary in 'data_l' returned from report_utils.parse_switch_file()
    :type obj_d: dict
    :return: Commands with $x variables replaced with the appropriate text.
    :rtype: list
    """
    global _tracking_template_d

    r_cmd_l, error_l = list(), list()
    replace_d = dict()

    # Figure out what the replacements should be
    obj_class_type = class_util.get_simple_class_type(obj, all_types=True)
    chassis_obj = obj.r_chassis_obj()
    if chassis_obj is not None:
        replace_d['$cwwn'] = chassis_obj.r_obj_key()
        replace_d['$license'] = chassis_obj.r_get(brcdapi_util.bc_license_id, chassis_obj.r_obj_key())
    if obj_class_type == 'SwitchObj' or obj_class_type == 'PortObj':
        replace_d['$swwn'] = obj.r_switch_obj().r_obj_key()
    if obj_class_type == 'PortObj':
        replace_d['$p'] = obj.r_obj_key()
        replace_d['$i'] = str(obj.r_index())

    # Make the substitutions while building the return list.
    for cmd in gen_util.convert_to_list(cmd_l):
        temp_buf_l = list()
        buf = cmd
        for key, val in replace_d.items():
            buf = buf.replace(str(key), val)
        if buf.find('$lwwn') >= 0:
            for login_wwn in obj.r_login_keys():
                temp_buf_l.append(buf.replace('$lwwn', login_wwn))
        else:
            temp_buf_l.append(buf)

        # Check for invalid substitutions (anything beginning with $ wasn't replaced above, so it must be invalid
        for buf in temp_buf_l:
            if buf.find('$') >= 0:
                error_l.extend([
                    'ERROR: ' + buf[buf.find('$'):].split(' ')[
                        0] + ' is invalid for object type: ' + obj_class_type,
                    'Command: "' + cmd + '" skipped',
                    ])
                error_l.extend(_standard_error(obj_d['sheet'], obj_d['row'], None))
                tracker_d = obj.rs_key('tracker_d', _tracking_template_d.copy())
                tracker_d['config_fail'] += 1
            else:
                r_cmd_l.extend(temp_buf_l)

    if len(error_l) > 1:
        brcdapi_log.log(error_l, echo=True)

    return r_cmd_l


def _standard_error(in_sheet, in_row, in_fos_obj):
    """Formats a standard error message for responses returned from the API.

    :param in_sheet: The sheet name
    :type in_sheet: None, str
    :param in_row: The row number (zero relative, so 1 is added)
    :type in_row: None, int
    :param in_fos_obj: The object, if relevant, returned from FOS after attempting a PATCH
    :type in_fos_obj: None, dict
    :return: List of text to be displayed and written to the log.
    :rtype: list
    """
    sheet = in_sheet if isinstance(in_sheet, str) else 'Unknown'
    row = str(in_row + 1) if isinstance(in_row, int) else 'Unknown'
    fos_error = ' N/A' if in_fos_obj is None else fos_auth.formatted_error_msg(in_fos_obj).replace('\n', ' \n')

    return ['Sheet: ' + sheet, 'Row:   ' + row, 'FOS error:', fos_error, '',]


def _process_api_response(obj, class_obj, sheet, row, error_msg):
    """Evaluates FOS API return and updates _tracker_d accordingly.

    :param obj: Object returned from brcdapi_rest.send_request()
    :type obj: dict
    :param class_obj: Chassis, switch, or port object
    :type class_obj: brcddb.classes.chassis.ChassisObj, brcddb.classes.switch.SwitchObj, brcddb.classes.port.PortObj
    :param sheet: Sheet name. Used for error reporting only.
    :type sheet: str
    :param row: 0 based relative row number in worksheet. Used for error reporting only.
    :type row: int
    :param error_msg: Message to display if an error occurs
    :type error_msg: None, str, list
    :return: Internal processing only.
    :rtype: None
    """
    global _tracking_template_d

    tracker_d = class_obj.rs_key('tracker_d', _tracking_template_d.copy())
    if fos_auth.is_error(obj):
        tracker_d['config_fail'] += 1
        brcdapi_log.log(gen_util.convert_to_list(error_msg) + _standard_error(sheet, row, obj), echo=True)
    else:
        tracker_d['config_success'] += 1


def _send_request(session, class_obj, sheet, obj_d, uri, content_d, error_msg):
    """Send API requests

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param class_obj: Chassis, switch, or port object
    :type class_obj: brcddb.classes.chassis.ChassisObj, brcddb.classes.switch.SwitchObj, brcddb.classes.port.PortObj
    :param sheet: Sheet name. Used for error reporting only.
    :type sheet: str
    :param obj_d: Dictionary in 'data_l' returned from report_utils.parse_switch_file()
    :type obj_d: dict
    :param uri: High level URI and branch.
    :type uri: str
    :param content_d: Content to send to switch via the API
    :param error_msg: Message to display if an error occurs
    :type error_msg: None, str, list
    :return: FOS status response.
    :rtype: dict
    """
    fid = None if class_util.get_simple_class_type(class_obj) == 'ChassisObj' else class_obj.r_fid()
    obj = brcdapi_rest.send_request(session, uri, 'PATCH', content_d, fid)
    _process_api_response(obj, class_obj, sheet, obj_d['row'], error_msg)

    return obj


def _invalid_characters(ref_str, valid_str):
    """Returns a list of user-friendly messages indicating where invalid characters were found in names and banners

    :param ref_str: The text the user requested
    :type ref_str: str
    :param valid_str: The corrected text.
    :type valid_str: str
    :return: Description of changes
    :rtype: list
    """
    r_buf_l = list()
    i, len_valid_str = 0, len(valid_str)
    for rc in ref_str:
        if rc != valid_str[i]:
            rc_printable = rc.replace('\n', '<lf>').replace('\t', '<tab>')
            r_buf_l.append(
                '  ' + rc_printable + ' ' + hex(ord(rc)) + ' Position: ' + str(i) + ' Changed to ' + valid_str[i]
            )
        i += 1
        if i >= len_valid_str:
            break
    if len(r_buf_l) > 0:
        r_buf_l.insert(0, 'Invalid Characters Changed to a Hyphen')
    if len(ref_str) != len(valid_str):
        r_buf_l.extend([
            'Length Change:',
            '  Starting text length: ' + str(len(ref_str)),
            '  Ending text length:   ' + str(len(valid_str)),
        ])
    if len(r_buf_l) > 0:
        r_buf_l.extend([
            'Old text: ' + ref_str,
            'New text: ' + valid_str
        ])

    return r_buf_l


#########################################################
#                                                       #
#   Common in _chassis_config_d, _switch_config_d       #
#                                                       #
#########################################################


_switch_name_mode_conv_d = dict(index='default', fdmi='fdmi', dynamic='dynamic', open='off', ficon='off')
_switch_name_mode_conv_r_d = dict(default='index', fdmi='fdmi', dynamic='dynamic', off='open/ficon')


def _execute_cli(session, class_obj, sheet, obj_d, force, cli):
    """Send CLI commands.

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param class_obj: Chassis, switch, or port object
    :type class_obj: brcddb.classes.chassis.ChassisObj, brcddb.classes.switch.SwitchObj, brcddb.classes.port.PortObj
    :param sheet: Sheet name. Used for error reporting only.
    :type sheet: str
    :param obj_d: Dictionary in 'data_l' returned from report_utils.parse_switch_file()
    :type obj_d: dict
    :param force: True/False for -force command line parameter
    :type force: bool
    :param cli: True: execute CLI. False: Do not execute CLI
    :type cli: bool
    :return: True if the chassis should be re-read
    :rtype: bool
    """
    global _tracking_template_d

    refresh_flag = False

    if not cli:
        return refresh_flag

    fid = 0 if class_util.get_simple_class_type(class_obj, all_types=True) == 'ChassisObj' else class_obj.r_fid()
    try:
        cmd_l = gen_util.convert_to_list(obj_d['parameter'])  # It should be a list already. Just belt & suspenders.
        for cmd in _replace_variables(class_obj, cmd_l, obj_d):
            tracker_d = class_obj.rs_key('tracker_d', _tracking_template_d.copy())
            if _cli_error(fos_cli.send_command(session, fid, cmd, fosexec=True if fid > 0 else False)):
                tracker_d['cli_fail'] += 1
            else:
                tracker_d['cli_success'] += 1
            refresh_flag = True
    except KeyError:
        pass  # Nothing to do for this key

    return refresh_flag  # We have no idea what the CLI commands did, so force a re-read of the chassis data.


def _change_parameters(session, class_obj, sheet, obj_d, force, cli):
    """Sets changed parameters in the brocade-chassis/chassis branch. See _execute_cli() for parameters."""
    global _parameters_d

    # Set up the data structure to send to the API
    brcddb_key = _parameters_d[obj_d['key']]
    current_val = class_obj.r_get(brcddb_key)
    new_value = obj_d['parameter']
    try:
        if current_val is not None and current_val == new_value:
            return False  # The values match, so there is nothing to change.
    except TypeError:
        # If there is a type error, that's a bug having nothing to do with this script
        buf_l = [
            'Type mismatch',
            'current_val: ' + str(current_val) + ' (' + str(type(current_val)) + ')',
            'parameter: ' + str(new_value) + ' (' + str(type(new_value)) + ')',
            ]
        brcdapi_log.exception(buf_l, echo=True)  # Let someone know, but keep processing

    # If we got this far, there is something to change. Prepare the data structure to send to the API
    temp_l = brcddb_key.split('/')
    x = len(temp_l)
    url = 'running/' + '/'.join(temp_l[0:x-1])  # Everything but the final leaf

    # Send the change to the API
    buf_l = ['ERROR: Failed to set ' + obj_d['user_key'] + ' (' + str(new_value) + ').']
    if obj_d['key'] == 'fcr':
        buf_l.extend([
            ' This typically occurs when attempting to enable/disable FCR without a license.',
            ' Note that FOS does not return information about FCR status without a license.',
            ' FOS always checks for the license when changing the status, even when disabling it.',
            ' Clear the cell contents to avoid this error message.'
            ])
    _send_request(
        session,
        class_obj,
        sheet,
        obj_d,
        url,
        {temp_l[x-2]: {temp_l[x-1]: new_value}},
        buf_l,
        )

    return False  # None of these changes are going to effect any other changes.


def _chassis_name(session, chassis_obj, sheet, obj_d, force, cli):
    """Sets the chassis name. See _execute_cli() for parameters."""

    if obj_d['parameter'] is None:
        return False

    # Make sure the name is valid before setting it.
    valid_name = brcdapi_util.valid_chassis_name(obj_d.get('parameter'))
    buf_l = _invalid_characters(obj_d['parameter'], valid_name)
    if len(buf_l) > 0:
        buf_l.insert(0, 'WARNING: The chassis name was modified as follows:')
        buf_l.extend(_standard_error(obj_d['sheet'], obj_d['row'], None))
        brcdapi_log.log(buf_l, echo=True)
    obj_d['parameter'] = valid_name

    return _change_parameters(session, chassis_obj, sheet, obj_d, force, cli)


def _null_action(session, class_obj, sheet, obj_d, force, cli):
    """Send CLI commands. See _execute_cli() for parameters."""
    return False

#########################################
#                                       #
#               Port                    #
#                                       #
#########################################


def _enable_disable_ports(session, switch_obj, sheet, switch_port_d, force, enable, parameter_key):
    """Called by _configure_ports()

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param switch_obj: Switch object
    :type switch_obj: brcddb.classes.switch.SwitchObj
    :param switch_port_d: dict of port configurations for the switch returned from report_utils.parse_switch_file()
    :type switch_port_d: dict
    :param force: True if -force specified on command line.
    :type force: bool
    :param enable: "enable": Process all enables. "disable": Process all disables and decommissions. "all": Process all
    :type enable: str
    :param parameter_key: Key for parameter in port_d (the individual port dictionaries in switch_port_d)
    :type parameter_key: str
    :return: True if a data refresh is necessary.
    :rtype: bool
    """
    global _tracking_template_d

    fid = switch_obj.r_fid()
    enable_flag = True if enable == 'enable' or enable == 'all' else False
    disable_flag = True if enable == 'disable' or enable == 'all' else False

    # Start enable/disable: Figure out what gets enabled, disabled, decommissioned, etc.
    enable_port_l, disable_port_l, persistent_disable_port_l, decom_port_l, force_l = \
        list(), list(), list(), list(), list()

    for port, port_d in switch_port_d.items():
        port_obj = switch_obj.r_port_obj(port)
        parameter = port_d.get(parameter_key)
        if parameter is None:
            continue
        if 'enable' in parameter and enable_flag:
            if not port_obj.r_is_enabled():
                if switch_obj.r_is_enabled():
                    switch_port_d[port]['pending_enable'] = True
                else:
                    enable_port_l.append(port)
        elif parameter == 'disable':
            if disable_flag:
                if port_obj.r_is_enabled():
                    if port_obj.r_type() == 'e-port':
                        decom_port_l.append(port)
                    elif force:
                        disable_port_l.append(port)
                    else:
                        force_l.append(port)
        elif parameter == 'persistent_disable':
            if disable_flag:
                if port_obj.r_type() == 'e-port':
                    decom_port_l.append(port)
                    persistent_disable_port_l.append(port)
                elif force:
                    persistent_disable_port_l.append(port)
                else:
                    force_l.append(port)
        else:
            buf = 'ERROR: Invalid parameter, ' + parameter + '. Valid parameters are: Enable, Disable,  and '
            buf += 'Persistent Disable.'
            brcdapi_log.log([buf] + _standard_error(sheet, port_d['row'], None), echo=True)
            tracker_d = port_obj.rs_key('tracker_d', _tracking_template_d.copy())
            tracker_d['config_fail'] += 1

    # Act on the lists of ports. Note: Some day, I plan on picking the right port(s) for the one reporting the error.
    # Setting error_port to the first port in the list was an expedient. I set error_port to None to indicate that there
    # is nothing to do.
    for d in [
        dict(
            obj=brcdapi_port.disable_port(session, fid, disable_port_l, best=True),
            error_msg='ERROR: Failed to disable one or more ports.',
            error_port=disable_port_l[0] if len(disable_port_l) > 0 else None
        ),
        dict(
            obj=brcdapi_port.decommission_port(session, fid, decom_port_l, best=True),
            error_msg='ERROR: Failed to decommission one or more ports.',
            error_port=decom_port_l[0] if len(decom_port_l) > 0 else None
        ),
        dict(
            obj=brcdapi_port.disable_port(session, fid, persistent_disable_port_l, persistent=True, best=True),
            error_msg='ERROR: Failed to persistently disable one or more ports.',
            error_port=persistent_disable_port_l[0] if len(persistent_disable_port_l) > 0 else None
        ),
        dict(
            obj=brcdapi_port.enable_port(session, fid, enable_port_l, persistent=False, best=True),
            error_msg='ERROR: Failed to enable one or more ports.',
            error_port=enable_port_l[0] if len(enable_port_l) > 0 else None
        ),
    ]:
        if d['error_port'] is not None:
            _process_api_response(
                d['obj'],
                switch_obj.r_port_obj(d['error_port']),
                sheet,
                switch_port_d[d['error_port']]['row'],
                d['error_msg']
            )

    # Report any ports that couldn't be disabled because they were online.
    for port in force_l:
        port_obj = switch_obj.r_port_obj(port)
        buf_l = ['ERROR: Cannot disable port with active logins unless -force is specified. Active logins:']
        buf_l.extend(_standard_error(switch_port_d[port]['sheet'], switch_port_d[port]['row'], None))
        for login_obj in port_obj.r_login_objects():
            buf = '  ' + brcddb_login.best_login_name(switch_obj.r_fabric_obj(), login_obj.r_obj_key()) + ', '
            buf += brcddb_login.login_best_port_desc(login_obj)
            buf_l.append(buf)
        tracker_d = port_obj.rs_key('tracker_d', _tracking_template_d.copy())
        tracker_d['config_fail'] += 1

    return True if len(disable_port_l) + len(decom_port_l) + len(persistent_disable_port_l) + len(enable_port_l) > 0\
        else False


def _configure_ports(session, switch_obj, sheet, switch_param_d, force, cli):
    """Set, if necessary, switch configuration parameters. See _execute_cli() for parameters."""
    global _tracking_template_d, _switch_name_mode_conv_r_d

    if switch_obj is None:
        return  # The error message was printed elsewhere
    brcdapi_log.log('Configuring ports.', echo=True)

    # Just to save some typing and de-referencing
    switch_d = switch_param_d['switch_d']
    switch_port_d = dict()  # Gets filled with port definitions for ports that are actually in the switch.
    for port in [p for p in switch_d['port_l'] if switch_obj.r_port_obj(p) is not None]:
        switch_port_d[port] = switch_d['chassis_d']['port_d'][port]
    fid = switch_obj.r_fid()
    did = switch_obj.r_did()

    # The port must be reserved before the address can be bound, so binding addresses is last
    bind_flag = False
    for d in switch_d['data_l']:
        if d['key'] == 'bind':
            bind_flag = d['parameter']
            break

    # You can't enable a port if it doesn't have a POD license. You can't release a POD license if the port is enabled,
    # so process disable and decommission first, the POD licenses, and then port enable. Note: I should have done this
    # at switch creation time because some PODs in other switches may need to be released before having enough to
    # reserve. I'm assuming this situation is rare, if ever, and port_config.py can be used to get as granular as an
    # administrator needs to get.

    # Start enable/disable: Just the disables and decommissions
    if _enable_disable_ports(session, switch_obj, sheet, switch_port_d, force, 'disable', 'start_enable'):
        # Time isn't of the essence. I didn't bother with code to just refresh this FID.
        proj_obj = _refresh_project(session, switch_obj.r_project_obj(), desc='Port configuration for FID: ' + str(fid))
        switch_obj = brcddb_fabric.switch_for_did(proj_obj.r_fabric_objs_for_fid(fid)[0], did)

    # POD licensing: Get a list of ports to reserve and a list of ports to release
    release_pod_l, reserve_pod_l = list(), list()
    for port, port_d in switch_port_d.items():
        port_obj = switch_obj.r_port_obj(port)
        parameter = port_d.get('reserve')
        if isinstance(parameter, bool):
            if parameter:
                if not port_obj.r_is_pod_license():  # Only reserve it if it hasn't been reserved yet.
                    reserve_pod_l.append(port)
            else:
                if port_obj.r_is_enabled():
                    buf = 'ERROR: Cannot release POD while port is enabled.'
                    brcdapi_log.log([buf] + _standard_error(sheet, port_d['row'], None), echo=True)
                    tracker_d = port_obj.rs_key('tracker_d', _tracking_template_d.copy())
                    tracker_d['config_fail'] += 1
                else:
                    release_pod_l.append(port)

    # POD licensing: Release and reserve PODs. Search back for notes regarding "error_port"
    for d in [
        dict(
            obj=brcdapi_port.release_pod(session, fid, release_pod_l, best=True),
            error_msg='ERROR: Failed to disable one or more ports.',
            error_port=release_pod_l[0] if len(release_pod_l) > 0 else None
        ),
        dict(
            obj=brcdapi_port.reserve_pod(session, fid, reserve_pod_l, best=True),
            error_msg='ERROR: Failed to persistently disable one or more ports.',
            error_port=reserve_pod_l[0] if len(reserve_pod_l) > 0 else None
        )
    ]:
        if d['error_port'] is not None:
            _process_api_response(
                d['obj'],
                switch_obj.r_port_obj(d['error_port']),
                sheet,
                switch_port_d[d['error_port']]['row'],
                d['error_msg']
            )
    if len(release_pod_l) + len(reserve_pod_l) > 0:
        # Time isn't of the essence. I didn't bother with code to just refresh this FID.
        proj_obj = _refresh_project(session, switch_obj.r_project_obj(), desc='Port configuration for FID: ' + str(fid))
        switch_obj = brcddb_fabric.switch_for_did(proj_obj.r_fabric_objs_for_fid(fid)[0], did)

    # Start enable/disable: PODs have been assigned, so now the enables can be done.
    if _enable_disable_ports(session, switch_obj, sheet, switch_port_d, force, 'enable', 'start_enable'):
        # Time isn't of the essence. I didn't bother with code to just refresh this FID.
        proj_obj = _refresh_project(session, switch_obj.r_project_obj(), desc='Port configuration for FID: ' + str(fid))
        switch_obj = brcddb_fabric.switch_for_did(proj_obj.r_fabric_objs_for_fid(fid)[0], did)

    # Process CLI.
    if cli:
        refresh_flag = False
        for port, port_d in switch_port_d.items():
            if port_d['cli'] is not None:
                # sheet wasn't needed in obj_d when this was written. Just adding it for future proofing.
                obj_d = dict(parameter=port_d['cli'], sheet=port_d['sheet'], row=port_d['row'])
                if _execute_cli(session, switch_obj.r_port_obj(port), port_d['sheet'], obj_d, force, cli):
                    refresh_flag = True
        if refresh_flag:
            proj_obj = _refresh_project(session, switch_obj.r_project_obj(), desc='Post CLI action in _configure_ports')
            chassis_obj = proj_obj.r_chassis_obj(session.get('chassis_wwn'))
            switch_obj = chassis_obj.r_switch_obj_for_fid(switch_d['fid'])

    # Bind the addresses.
    if bind_flag:
        bind_d, port_d, port_obj = dict(), dict(row=0), None
        for port, port_d in switch_port_d.items():
            port_obj = switch_obj.r_port_obj(port)
            tracker_d = port_obj.rs_key('tracker_d', _tracking_template_d.copy())

            # This script only supports address binding mode for FICON, hence only checking for '8-bit'
            if str(port_obj.r_get(brcdapi_util.fc_bind_mode)) == '8-bit':

                # Make sure we have valid port addresses
                new_port_addr = port_d.get('port_addr')
                if not isinstance(new_port_addr, str) or len(new_port_addr) > 2:
                    buf_l = [
                        'ERROR: Invalid port address: ' + str(new_port_addr) + ' (' + str(type(new_port_addr)) + ')'
                    ]
                    brcdapi_log.log(buf_l + _standard_error(sheet, port_d['row'], None), echo=True)
                    tracker_d['config_fail'] += 1
                    continue
                if len(new_port_addr) == 1:
                    new_port_addr = '0' + new_port_addr
                new_port_addr = new_port_addr.lower()
                port_addr = port_obj.r_addr()
                if isinstance(port_addr, str) and len(port_addr) == 8:
                    port_addr = port_addr.lower()
                else:
                    # This should never happen.
                    buf_l = ['ERROR: Invalid port address, ' + str(port_addr) + ', read from project.']
                    brcdapi_log.log(buf_l + _standard_error(sheet, port_d['row'], None), echo=True)
                    tracker_d['config_fail'] += 1
                    continue

                # Is the address already bound to the desired address?
                if port_addr[4:6] == port_d['port_addr'][2:]:
                    continue  # Address binding mode is already set and the address matches.

            # If we got this far, bind the port address if the port is disabled.
            if port_obj.r_is_enabled():
                buf_l = ['ERROR: Cannot bind port address while the port is enabled.']
                brcdapi_log.log(buf_l + _standard_error(sheet, port_d['row'], None), echo=True)
                tracker_d['config_fail'] += 1
                continue
            bind_d[port] = '0x' + new_port_addr + '00'

        # Bind the ports
        if len(bind_d) > 0:
            _process_api_response(
                brcdapi_port.bind_addresses(session, fid, bind_d, best=True),
                port_obj,
                sheet,
                port_d['row'],
                'ERROR: Failed to bind one or more port addresses. See previous messages for details.'
            )

    # Set the port names
    update_port_d = dict()
    port_name_mode = switch_obj.r_get(brcdapi_util.bfc_portname_mode, 'off')
    for port, port_d in switch_port_d.items():
        if not isinstance(port_d['port_name'], str):
            continue  # Assume its None and therefore there is no change
        if port_name_mode != 'off':
            buf_l = [
                'ERROR: Port Name ignored. Port naming not supported by port name ',
                'mode: ' + _switch_name_mode_conv_r_d[port_name_mode] + ' (' + port_name_mode + ')',
                ]
            brcdapi_log.log(buf_l + _standard_error(port_d['sheet'], port_d['row'], None), echo=True)
            continue
        valid_name = brcdapi_util.valid_port_name(port_d['port_name'], ficon=switch_obj.r_is_ficon())
        port_obj = switch_obj.r_port_obj(port)
        if port_obj is None or port_obj.r_port_name() == valid_name:  # port_obj is None if a config error occurred
            continue
        buf_l = _invalid_characters(port_d['port_name'], valid_name)
        if len(buf_l) > 0:
            buf_l.insert(0, 'WARNING: The port name was modified as follows:')
            buf_l.extend(_standard_error(port_d['sheet'], port_d['row'], None))
            brcdapi_log.log(buf_l, echo=True)
        update_port_d[port] = valid_name

    if len(update_port_d) > 0:
        obj = brcdapi_port.user_name(session, fid, update_port_d, best=True)
        # Seed the port for error reporting. Hopefully, we can figure out which port had the actual error
        ref_port = [k for k in update_port_d.keys()][0]
        _process_api_response(
            obj,
            switch_obj.r_port_obj(ref_port),
            sheet,
            switch_port_d[ref_port]['row'],
            'ERROR: Failed to set the user friendly port name for one or more ports.'
        )

    # Final port enable/disable
    return _enable_disable_ports(session, switch_obj, sheet, switch_port_d, force, 'all', 'end_enable')

#########################################
#                                       #
#               Switch                  #
#                                       #
#########################################


def _switch_enable_disable(session, switch_obj, sheet, obj_d, force, cli):
    """Enables or disables the switch. See _execute_cli() for parameters. """
    global _ENABLE_WAIT, _tracking_template_d

    # Enable
    if obj_d['parameter'] == 'enable':
        if switch_obj.r_is_enabled():
            return False  # The switch is already enabled. Nothing to do.
        obj = brcdapi_switch.enable_switch(
            session,
            switch_obj.r_fid(),
            persistent=not switch_obj.r_is_persistent_disable()
        )
        _process_api_response(
            obj,
            switch_obj,
            sheet,
            obj_d['row'],
            'ERROR: Could not enable the switch.'
        )
        if not fos_auth.is_error(obj):
            time.sleep(_ENABLE_WAIT)
            return True

    # Persistent Disable
    elif obj_d['parameter'] == 'persistent_disable':
        if switch_obj.r_is_persistent_disable() and not switch_obj.r_is_enabled():
            pass  # Already persistently disabled. Nothing to do.
        elif force:
            obj = brcdapi_switch.disable_switch(session, switch_obj.r_fid(), persistent=True)
            _process_api_response(
                obj,
                switch_obj,
                sheet,
                obj_d['row'],
                'ERROR: Could not persistently disable the switch.'
            )
            if not fos_auth.is_error(obj):
                time.sleep(_ENABLE_WAIT)
                return True
        else:
            buf = 'ERROR: Cannot persistently disable switch. -force not specified.'
            brcdapi_log.log([buf] + _standard_error(sheet, obj_d['row'], None), echo=True)
            tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
            tracker_d['config_fail'] += 1

    # Disable
    elif obj_d['parameter'] == 'disable':
        if not switch_obj.r_is_enabled():
            pass  # The switch is already disabled. Nothing to do.
        elif force:
            obj = brcdapi_switch.disable_switch(session, switch_obj.r_fid(), persistent=False)
            _process_api_response(
                obj,
                switch_obj,
                sheet,
                obj_d['row'],
                'ERROR: Could not disable the switch.'
            )
            if not fos_auth.is_error(obj):
                time.sleep(_ENABLE_WAIT)
                return True
        else:
            buf = 'ERROR: Cannot disable switch. -force not specified.'
            brcdapi_log.log([buf] + _standard_error(sheet, obj_d['row'], None), echo=True)
            tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
            tracker_d['config_fail'] += 1

    else:
        buf = 'ERROR: Invalid parameter, ' + obj_d['parameter'] + '. Valid parameters are: Enable, Disable,  and '
        buf += 'Persistent Disable'
        brcdapi_log.log([buf] + _standard_error(sheet, obj_d['row'], None), echo=True)
        tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
        tracker_d['config_fail'] += 1
        raise ForceError

    return False


def _switch_fid(session, switch_obj, sheet, obj_d, force, cli):
    """FID is set when the logical switch is created. FID changes not supported in this script. See _execute_cli(). """
    global _tracking_template_d

    if switch_obj is not None:
        fid, new_fid = str(switch_obj.r_fid()), str(obj_d['parameter'])
        if fid != new_fid:
            buf_l = [
                'FID changing not supported by this script.',
                'Current   : ' + brcddb_switch.best_switch_name(switch_obj, fid=True),
                'Requested : ' + 'FID: ' + new_fid,
            ]
            brcdapi_log.log(buf_l + _standard_error(sheet, obj_d['row'], None), echo=True)
            tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
            tracker_d['config_fail'] += 1

    return False


def _switch_banner(session, switch_obj, sheet, obj_d, force, cli):
    """Sets the switch banner. See _execute_cli() for parameters."""

    banner = obj_d.get('parameter')
    if not isinstance(banner, str):
        return False
    # As of FOS 10.0, <lf> was not permitted in a switch banner. Replacing '\r\n' with '\n' is future proofing.
    banner = banner.replace('\r\n', '\n')
    if banner == switch_obj.r_get(brcdapi_util.bfs_banner):
        return False

    valid_banner = brcdapi_util.valid_switch_banner(banner)
    buf_l = _invalid_characters(banner, valid_banner)
    if len(buf_l) > 0:
        buf_l.insert(0, 'WARNING: The switch banner was modified as follows:')
        brcdapi_log.log(buf_l + _standard_error(sheet, obj_d['row'], None), echo=True)
    obj_d['parameter'] = valid_banner

    # Set up the data structure to send to the API
    _process_api_response(
        brcdapi_switch.fibrechannel_switch(
            session,
            switch_obj.r_fid(),
            dict(banner=valid_banner),
            wwn=switch_obj.r_obj_key()
        ),
        switch_obj,
        sheet,
        obj_d['row'],
        'ERROR: Failed to set Login Banner (' + valid_banner + ')'
    )


def _switch_type(session, switch_obj, sheet, obj_d, force, cli):
    """Switch type is set when the switch is created. Changing it is not supported. See _execute_cli(). """
    global _tracking_template_d

    switch_type = switch_obj.c_switch_type().replace('default', 'open')
    if switch_type != obj_d['parameter']:
        buf_l = [
            'Changing the switch type is not supported by this script.',
            'Current   : ' + switch_type,
            'Requested : ' + obj_d['parameter'],
            ]
        brcdapi_log.log(buf_l + _standard_error(sheet, obj_d['row'], None), echo=True)
        tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
        tracker_d['config_fail'] += 1

    return False


def _switch_name_mode(session, switch_obj, sheet, obj_d, force, cli):
    """Switch port-wide naming mode. See _execute_cli().

    When portname-mode is "dynamic", the dynamic port name mode is further defined by dynamic-portname-format. To
    determine if there is something to change when portname-mode is "dynamic", dynamic-portname-format must also be
    checked for a match.

    I discovered, by accident, that FOS allows portname-mode to be set as "dynamic" without setting
    dynamic-portname-format. I'm assuming "S.T.I.A" is the default. To keep the coding effort simple, I set all
    parameters. Therefore, there was no need to pursue this scenario.

    Since setting dynamic port name mode without any format is useless, I skipped researching and testing this scenario
    and just treated it as user input error.

    Relevant branch: brocade-fibrechannel-configuration/port-configuration
    """
    global _tracking_template_d, _switch_name_mode_conv_d

    if obj_d['parameter'] is None:
        return False

    # Make sure the port name mode is valid.
    port_name_mode = _switch_name_mode_conv_d.get(obj_d['parameter'])
    if port_name_mode is None:
        buf_l = [
            'ERROR: Parameter, ' + obj_d['parameter'] + ' for ' + obj_d['user_key'] + ' is invalid.',
            'Valid options are: ' + ', '.join([str(k) for k in _switch_name_mode_conv_d.keys()]) + '.',
        ]
        brcdapi_log.log(buf_l + _standard_error(sheet, obj_d['row'], None), echo=True)
        return False

    if port_name_mode == switch_obj.r_get(brcdapi_util.bfc_portname_mode):
        return False

    # Prepare the content
    content_d = None

    # If the port name mode is "dynamic", check the port name format and build the content
    if port_name_mode == 'dynamic':
        port_name_format_d = None

        # Find and validate Port Name Format
        for d in obj_d['switch_d']['data_l']:
            if d['key'] == 'port_name_format':
                port_name_format_d = d
                break
        if port_name_format_d is None:
            buf_l = [
                'ERROR: ' + obj_d['user_key'] + '  is ' + obj_d['parameter'] + ' which requires',
                'Port Name Format, but a row with Port Name Format was not found.'
            ]
            brcdapi_log.log(buf_l + _standard_error(sheet, obj_d['row'], None), echo=True)
            tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
            tracker_d['config_fail'] += 1
            return False
        port_name_format = port_name_format_d['parameter']
        if port_name_format is None or len(port_name_format) == 0:
            buf_l = ['ERROR: Port Name Format cannot be empty.']
            brcdapi_log.log(buf_l + _standard_error(sheet, port_name_format_d['row'], None), echo=True)
            tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
            tracker_d['config_fail'] += 1
            return False

        # If we got this far, the port name format is valid. Check to see if anything is changing.
        if switch_obj.r_get(brcdapi_util.bfc_portname_mode) != port_name_mode \
                or switch_obj.r_get(brcdapi_util.bfc_portname_format) != port_name_format:
            content_d = {
                'port-configuration': {
                    'portname-mode': port_name_mode,
                    'dynamic-portname-format': port_name_format,
                }
            }

    else:  # It's a mode other than dynamic, so just build content if it's changing
        if switch_obj.r_get(brcdapi_util.bfc_portname_mode) != port_name_mode:
            content_d = {
                'port-configuration': {
                    'portname-mode': port_name_mode,
                }
            }

    if isinstance(content_d, dict):
        # Send the change to the API
        _send_request(
            session,
            switch_obj,
            sheet,
            obj_d,
            'running/' + brcdapi_util.bfc_port_uri,
            content_d,
            'ERROR: Failed to set ' + obj_d['user_key'] + ' (' + obj_d['key'] + ')',
            )

    return False


def _dup_wwn(session, switch_obj, sheet, obj_d, force, cli):
    """Duplicate WWN (enforce login) handling. See _execute_cli(). """
    global _tracking_template_d

    if obj_d['parameter'] is None:
        return False
    if obj_d['parameter'] == switch_obj.r_get(brcdapi_util.bfc_fport_enforce_login):
        return False

    if switch_obj.r_is_enabled():
        buf_l = ['ERROR: The switch must be disabled to modify ' + obj_d['user_key'] + ' handling.',]
        brcdapi_log.log(buf_l + _standard_error(sheet, obj_d['row'], None), echo=True)
        tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
        tracker_d['config_fail'] += 1
        return False

    content_d = {'f-port-login-settings': {'enforce-login-string': obj_d['parameter']}}
    _send_request(
        session,
        switch_obj,
        sheet,
        obj_d,
        'running/' + brcdapi_util.bfcfp_uri,
        content_d,
        'ERROR: Failed to set ' + obj_d['user_key'] + ' (' + obj_d['key'] + ')',
        )

    return _change_parameters(session, switch_obj, sheet, obj_d, force, cli)

#####################################################
#                                                   #
#  Switch Functions That Require Special Handling   #
#                                                   #
#####################################################


def _switch_name(session, switch_obj, sheet, obj_d, force, cli):
    """Set the switch user-friendly name. See _execute_cli() for parameters."""
    switch_name = obj_d.get('parameter')
    if not isinstance(switch_name, str):
        return False

    valid_name = brcdapi_util.valid_switch_name(switch_name)
    if brcddb_switch.best_switch_name(switch_obj) != valid_name:
        buf_l = _invalid_characters(switch_name, valid_name)
        if len(buf_l) > 0:
            buf_l.insert(0, 'WARNING: The switch name was modified as follows:')
            brcdapi_log.log(buf_l + _standard_error(sheet, obj_d['row'], None), echo=True)
        content_d = {'user-friendly-name': valid_name}
        _process_api_response(
            brcdapi_switch.fibrechannel_switch(session, switch_obj.r_fid(), content_d, switch_obj.r_obj_key()),
            switch_obj,
            sheet,
            obj_d['row'],
            'ERROR: Failed to set switch user-friendly name.'
        )

    return False


def _switch_did(session, switch_obj, sheet, obj_d, force, cli):
    """Set the switch Domain ID. See _execute_cli() for parameters."""
    global _tracking_template_d

    switch_did = switch_obj.r_did()
    if switch_did is None or switch_did != obj_d['parameter']:
        # Is the switch enabled?
        if switch_obj.r_is_enabled():
            buf = 'ERROR: Switch must be disabled to change the DID.'
            brcdapi_log.log([buf] + _standard_error(sheet, obj_d['row'], None), echo=True)
            tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
            tracker_d['config_fail'] += 1
        else:
            content_d = {'domain-id': obj_d['parameter']}
            _process_api_response(
                brcdapi_switch.fibrechannel_switch(session, switch_obj.r_fid(), content_d, switch_obj.r_obj_key()),
                switch_obj,
                sheet,
                obj_d['row'],
                'ERROR: Failed to set switch Domain-ID.'
            )

    return False


def _switch_fab_principal(session, switch_obj, sheet, obj_d, force, cli):
    """Set this switch as the fabric principal. See _execute_cli() for parameters."""
    global _bfc_fabric, _tracking_template_d

    # Does fabric priority need to be enabled?
    new_fab_principal = obj_d.get('parameter')
    if not isinstance(new_fab_principal, bool):
        return False
    current_fab_principal = switch_obj.r_get(brcdapi_util.bfc_principal_en, False)
    if not new_fab_principal and not current_fab_principal:
        return False  # It's off on the worksheet and off on the switch. The priority doesn't matter.

    # Get the desired fabric priority
    current_fab_priority = switch_obj.r_get(brcdapi_util.bfc_principal_pri, 'None')
    new_fab_priority = None
    # Find the priority
    for data_d in obj_d['switch_d']['data_l']:
        if data_d['key'] == 'fab_priority':
            new_fab_priority = data_d.get('parameter')
            break
    if new_fab_principal and new_fab_priority is None:
        buf_l = ['ERROR: Fabric Principal Priority is required to set the Fabric Principal.']
        brcdapi_log.log(buf_l + _standard_error(sheet, obj_d['row'], None), echo=True)
        tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
        tracker_d['config_fail'] += 1
        return False
    if isinstance(new_fab_priority, str):
        new_fab_priority = new_fab_priority.lower().replace('0x0', '0x')
    current_fab_priority = current_fab_priority.lower().replace('0x0', '0x')  # Just to be sure...

    # If enabled, do the priorities match?
    if new_fab_principal == current_fab_principal and new_fab_priority == current_fab_priority:
        return False

    # If we got this far, something is changing
    e_buf = 'ERROR: Failed to '
    if new_fab_principal:
        content_d = dict(fabric={
            'principal-selection-enabled': new_fab_principal,
            'principal-priority': new_fab_priority
        })
        e_buf += 'enable fabric principal selection. Fabric priority: ' + new_fab_priority
    else:
        content_d = dict(fabric={'principal-selection-enabled': new_fab_principal})
        e_buf += 'clear (disable) fabric principal selection.'

    # Send the change
    _send_request(session, switch_obj, sheet, obj_d, _bfc_fabric, content_d, e_buf)

    return False


def _switch_fabric_name(session, switch_obj, sheet, obj_d, force, cli):
    """Set the fabric user-friendly name. See _execute_cli() for parameters."""
    if brcddb_fabric.best_fab_name(switch_obj) != obj_d['parameter']:
        content_d = {'fabric-user-friendly-name': obj_d['parameter']}
        _process_api_response(
            brcdapi_switch.fibrechannel_switch(session, switch_obj.r_fid(), content_d, switch_obj.r_obj_key()),
            switch_obj,
            sheet,
            obj_d['row'],
            'ERROR: Failed to set switch user-friendly name.'
        )

    return False


def _configure_switch(session, switch_obj, switch_d, force, cli):
    """Set, if necessary, switch configuration parameters. See _execute_cli() for parameters."""
    global _tracking_template_d

    if switch_obj is None:
        return False  # The error message was printed elsewhere

    # Perform switch configuration actions
    brcdapi_log.log('Configuring switch: ' + brcddb_switch.best_switch_name(switch_obj, did=True, fid=True), echo=True)
    for d in switch_d['data_l']:

        # Get the sheet name
        sheet = d.get('sheet', switch_d.get('sheet'))
        if not isinstance(sheet, str):
            # This is debug code I decided to leave in. This should never happen.
            brcdapi_log.exception(
                'Invalid or missing sheet name, ' + str(sheet) + ' (' + str(type(sheet)) + ')',
                echo=True
            )
            continue

        # Process all the actions for the switch sheet.
        try:
            if _switch_config_d[d['key']](session, switch_obj, sheet, d, force, cli):
                proj_obj = _refresh_project(
                    session,
                    switch_obj.r_project_obj(),
                    desc='Interim step in _configure_chassis'
                )
                chassis_obj = proj_obj.r_chassis_obj(session.get('chassis_wwn'))
                switch_obj = chassis_obj.r_switch_obj_for_fid(switch_d['fid'])
        except KeyError:
            buf = 'ERROR: Invalid key: ' + str(d['user_key']) + ' (' + str(d['key']) + ')'
            brcdapi_log.exception([buf] + _standard_error(sheet, d.get('row', 0), None), echo=True)
            tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
            tracker_d['config_fail'] += 1
        except ForceError:
            return False  # The error was already reported.
        except BaseException as e:
            buf_l = ['ERROR: Programming error encountered.:']
            buf_l.extend(_standard_error(sheet, d.get('row'), None))
            brcdapi_log.exception(buf_l, echo=True)
            if class_util.get_simple_class_type(switch_obj, all_types=True) == 'SwitchObj':
                tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
                tracker_d['config_fail'] += 1

    # Enable any ports waiting to be enabled.
    if switch_obj.r_is_enabled():
        port_d = switch_d['chassis_d']['port_d']
        enable_port_l = [port for port in switch_d['port_l'] if port_d[port]['pending_enable']]
        if len(enable_port_l) > 0:
            obj = brcdapi_port.enable_port(session, switch_obj.r_fid(), enable_port_l, persistent=False, best=True)
            if fos_auth.is_error(obj):
                _process_api_response(
                    obj,
                    switch_obj.r_port_obj(enable_port_l[0]),  # Port object
                    port_d[enable_port_l[0]]['sheet'],
                    port_d[enable_port_l[0]]['row'],
                    'ERROR: Could not create the switch.'
                )

    return False


def _enable_cup(session, switch_obj, sheet, switch_d, force, cli):
    """Enable CUP if it should be enabled. See _execute_cli() for parameters."""
    global _tracking_template_d

    # Do we need to enable CUP?
    if switch_d['parameter'] is None:
        return False
    if switch_obj.r_get(brcdapi_util.ficon_cup_en, False) == switch_d['parameter']:
        return False

    switch_type = switch_obj.c_switch_type()
    if switch_type == 'ficon':
        buf = 'ERROR: Failed to set ' + switch_d['user_key'] + ' (' + switch_d['key'] + '). This usually happens when '
        buf += 'the license has not been installed.'
        _send_request(
            session,
            switch_obj,
            sheet,
            switch_d,
            brcdapi_util.ficon_cup_uri,
            dict(cup={'fmsmode-enabled': switch_d['parameter']}),
            buf,
            )
    else:
        buf_l = ['Can only enable CUP on switches configured as "FICON". Switch type is: ' + switch_type]
        brcdapi_log.log(buf_l + _standard_error(sheet, switch_d['row'], None), echo=True)
        tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
        tracker_d['config_fail'] += 1

    return False


def _scc(session, switch_obj, sheet, switch_d, force, cli):
    """Enable CUP if it should be enabled. See _execute_cli() for parameters."""
    global _tracking_template_d

    # Is there anything to do?
    if not isinstance(switch_d['parameter'], str):
        return False

    # Figure out what WWNs to add
    wwn_l = list()
    for wwn in switch_d['parameter'].replace(' ', '').split(','):
        if wwn == '*':
            wwn_l.extend(switch_obj.r_fabric_obj().r_switch_keys())
        elif gen_util.is_wwn(wwn, full_check=True):
            wwn_l.append(wwn)
        else:
            brcdapi_log.log(['ERROR: Invalid WWN: ' + wwn] + _standard_error(sheet, switch_d['row'], None), echo=True)
            tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
            tracker_d['config_fail'] += 1

    # Update the SCC list
    if len(wwn_l) > 0:
        tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
        tracker_d['config_fail'] += 1
        buf_l = [
            'WARNING: SCC not yet implemented. Use scc_policy.py to set the SCC',
            'policy. No action taken.',
            'Defined WWNs: ' + ','.join(wwn_l)
        ]
        brcdapi_log.log(buf_l + _standard_error(sheet, switch_d['row'], None), echo=True)

    return False


def _ficon_zone(session, switch_obj, sheet, switch_d, force, cli):
    """Enable CUP if it should be enabled. See _execute_cli() for parameters."""
    global _tracking_template_d

    # Is there anything to do?
    if not isinstance(switch_d['parameter'], str):
        return False
    switch_type = str(switch_obj.c_switch_type())
    if switch_type != 'ficon':
        tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
        tracker_d['config_fail'] += 1

        buf_l = [
            'WARNING: FICON Zone is only supported with FICON fabrics. Switch type',
            'is: ' + switch_type + '. No action taken.',
        ]
        brcdapi_log.log(buf_l + _standard_error(sheet, switch_d['row'], None), echo=True)
        return False

    tracker_d = switch_obj.rs_key('tracker_d', _tracking_template_d.copy())
    tracker_d['config_fail'] += 1
    buf_l = [
        'WARNING: FICON Zone not yet implemented. Use mf_zone.py and zone_config.py',
        'to configure zoning. No action taken.',
    ]
    brcdapi_log.log(buf_l + _standard_error(sheet, switch_d['row'], None), echo=True)

    return False


_switch_config_d = dict(  # See brcddb.report.utils._conv_parameters_d for explanation of keys.
    cli=_execute_cli,  # CLI
    enable=_switch_enable_disable,  # Enable/Disable
    fid=_switch_fid,  # Fabric ID (FID). Note: FID is set when the switch is created.
    fab_name=_switch_fabric_name,  # Fabric Name
    switch_name=_switch_name,  # Switch Name
    did=_switch_did,  # Domain ID (DID)
    insistent_did=_change_parameters,  # Insistent DID
    fab_principal=_switch_fab_principal,  # Fabric Principal Priority
    fab_priority=_null_action,  # Set when processing fab_principal
    xisl=_change_parameters,  # Allow XISL
    login_banner=_switch_banner,  # Login Banner
    switch_type=_switch_type,  # Switch Type
    dup_wwn=_dup_wwn,  # Duplicate WWN
    bind=_null_action,  # Bind. Note: Set when processing config_ports
    routing_policy=_null_action,  # Set when the switch is created
    port_name=_switch_name_mode,  # Port Name
    port_name_format=_null_action,  # Port Name Format
    config_ports=_configure_ports,  # Configure Ports
    cup=_enable_cup,  # Enable CUP
    scc=_scc,  # SCC
    ficon_zone=_ficon_zone,  # FICON Zone
)

#########################################
#                                       #
#               Chassis                 #
#                                       #
#########################################


def _chassis_enable_disable(session, chassis_obj, sheet, obj_d, force, cli):
    """Enables or disables the chassis. See _execute_cli() for parameters."""
    global _chassis_uri, _ENABLE_WAIT, _tracking_template_d

    tracker_d = chassis_obj.rs_key('tracker_d', _tracking_template_d.copy())

    # Enable
    if obj_d['parameter'] == 'enable':
        if chassis_obj.r_is_enabled():
            return False

        obj = _send_request(
            session,
            chassis_obj,
            sheet,
            obj_d,
            _chassis_uri,
            dict(chassis={'chassis-enabled': True}),
            'ERROR: Could not enable the chassis.',
        )
        if fos_auth.is_error(obj):
            return False
        time.sleep(_ENABLE_WAIT)
        return True

    # Disable
    if obj_d['parameter'] == 'disable':
        if not chassis_obj.r_is_enabled():
            return False

        if not force:
            buf = 'ERROR: Cannot disable chassis. -force not specified.'
            brcdapi_log.log([buf] + _standard_error(sheet, obj_d['row'], None), echo=True)
            tracker_d['config_fail'] += 1
            raise ForceError

        # If we got this far, all is good. Send the request
        _send_request(
            session,
            chassis_obj,
            sheet,
            obj_d,
            _chassis_uri,
            dict(chassis={'chassis-enabled': False}),
            'ERROR: Could not disable the chassis.',
        )
        return True  # I don't think this change matters. Disabling a chassis is rare. Don't overthink it. Play it safe

    # Invalid parameter
    buf = 'ERROR: Invalid parameter, ' + obj_d['parameter'] + '. Valid parameters are: Enable and Disable.'
    brcdapi_log.log([buf] + _standard_error(sheet, obj_d['row'], None), echo=True)
    tracker_d['config_fail'] += 1
    raise ForceError


def _chassis_motd(session, chassis_obj, sheet, obj_d, force, cli):
    """Sets the chassis "Message of the Day". See _execute_cli() for parameters."""

    motd = obj_d.get('parameter')
    if not isinstance(motd, str):
        return False
    motd = motd.replace('\r\n', '\n')
    if motd == chassis_obj.r_get(brcdapi_util.bc_motd):
        return False

    valid_motd = brcdapi_util.valid_chassis_motd(motd)
    buf_l = _invalid_characters(motd, valid_motd)
    if len(buf_l) > 0:
        buf_l.insert(0, 'WARNING: The chassis MOTD was modified as follows:')
        buf_l.extend(_standard_error(obj_d['sheet'], obj_d['row'], None))
        brcdapi_log.log(buf_l, echo=True)
    obj_d['parameter'] = valid_motd

    return _change_parameters(session, chassis_obj, sheet, obj_d, force, cli)


def _chassis_web_tools(session, class_obj, sheet, obj_d, force, cli):
    """Enable/disables WebTools. See _execute_cli() for parameters.

    I think WebTools is always enabled and that brocade_chassis/management-interface-configuration/webtools-enabled
    is obsolete. Since I'm not sure, I read brocade_chassis/management-interface-configuration. If webtools-enabled
    is present, I try to change it. Otherwise, ignore it."""
    global _parameters_d

    if class_obj.r_get(_parameters_d[obj_d['key']]) is None:
        return False

    return _change_parameters(session, class_obj, sheet, obj_d, force, cli)


def _config_logical_switches(session, chassis_obj, sheet, obj_d, force, cli):
    """Creates logical switches and assigns ports. See _execute_cli() for parameters.

    port_map_d: If a switch already exists, it may contain ports that need to be moved to another logical switch. The
    easy thing to do would be to put those ports in the default switch and then put them in whatever logical switch
    they belong in when that switch is processed. Moving ports is very inefficient. port_map_d is used to determine
    where all the ports belong, so that they only need to be moved once.

    Key is the FID where the port is moving to ("to FID"). Value is a dictionary whose key is the FID where the port
    currently resides ("from FID"). The value is a list of ports in the "from FID" that need to be moved to the
    "to FID."

    pending_move_d: Key is the port number. Value is the "from FID". Contains all the ports that must be moved out of
    one of the switches defined with a "Switch_x" worksheet.
    """
    global _tracking_template_d

    # Setup
    switch_config_flag, port_config_flag = False, False  # Used to determine if we need to re-read the chassis data.
    param_d, port_map_d, pending_move_d, e_port_d = dict(), dict(), dict(), dict()  # see note in function header
    online_port_l, non_existent_port_l, non_existent_fid_l, api_move_fail_l = list(), list(), list(), list()
    obj, switch_fid, switch_d = None, None, dict()  # Initialized in case of a gross error.
    step = 'Start'  # Used for error reporting only

    # Create whatever switches need to be created.
    for switch_d in obj_d['chassis_d']['switch_d'].values():
        try:  # Lots of stuff going on in here. try/except was to aid debugging during development

            # This function relies on brcdapi.switch.create_switch() to create the logical switch. That library function
            # handles a few nuances with logical switch creation. It creates the logical switch with some basic
            # configuration data and adds ports. This is why the ports are gathered, then the switch configuration
            # data gathered, and then the call to create_switch(). Using this library greatly simplifies logical switch
            # creation

            switch_fid = switch_d['fid']

            # Determine what ports belong to this switch. Start with setting up the port tracking
            port_for_switch_d = dict()  # Used to quickly determine what ports belong to a switch
            from_fid_d = dict()
            port_map_d[switch_fid] = from_fid_d
            step = 'Add port tracking'
            for port in switch_d['port_l']:
                step = 'Add port tracking: ' + port
                port_for_switch_d[port] = True

                # Does the port exist? Is it already in the switch? Is it online?
                port_obj = chassis_obj.r_port_obj(port)
                if port_obj is None:
                    port_obj = chassis_obj.r_ge_port_obj(port)
                if port_obj is None:
                    non_existent_port_l.append(port)
                    continue
                from_fid = port_obj.r_fid()
                if from_fid == switch_fid:
                    continue
                if not force and len(port_obj.r_login_keys()) > 0:
                    if port_obj.r_type() == 'e-port':
                        e_port_d[port] = True
                    else:
                        tracker_d = port_obj.rs_key('tracker_d', _tracking_template_d.copy())
                        tracker_d['config_fail'] += 1
                        online_port_l.append(port)
                        continue

                # If we got this far, the port needs to be moved, so add it to port_map_d
                from_port_l = from_fid_d.get(from_fid)
                if from_port_l is None:
                    from_port_l = list()
                    from_fid_d[from_fid] = from_port_l
                from_port_l.append(port)
                if port in pending_move_d:
                    pending_move_d.pop(port)

            # Get the switch parameters
            step = 'Get parameters'
            param_d = dict()
            for data_d in switch_d['data_l']:
                param_d[data_d['key']] = data_d['parameter']
            fid = param_d.get('fid', 0)
            base_flag = True if param_d.get('switch_type', 'open') == 'base' else False
            ficon_flag = True if param_d.get('switch_type', 'open') == 'ficon' else False

            # If the switch already exists, we're just going to modify it later. For now, just update port_map_d
            step = 'Update port map'
            switch_obj = chassis_obj.r_switch_obj_for_fid(fid)
            if switch_obj is not None:  # The switch already exists
                for port_obj in switch_obj.r_port_objects():
                    step = 'Update port map: ' + port_obj.r_obj_key()
                    if not port_for_switch_d.get(port_obj.r_obj_key(), False):
                        step += '. Pending move'
                        pending_move_d[port_obj.r_obj_key()] = switch_fid
                continue

            # Create the logical switch
            step = 'Creating FID ' + str(fid)
            brcdapi_log.log('Creating FID ' + str(fid) + ' logical switch.', echo=True)
            switch_config_flag = True
            obj = brcdapi_switch.create_switch(session, fid, base_flag, ficon_flag)
            _process_api_response(obj, chassis_obj, sheet, obj_d['row'], 'ERROR: Could not create the switch.')

        except BaseException as e:
            msg_l = [str(type(e)) + ': ' + str(e), 'Last known FID: ' + str(switch_fid)]
            if obj is not None:
                msg_l.append(fos_auth.formatted_error_msg(obj))
            error_obj = fos_auth.create_error(
                brcdapi_util.HTTP_INT_SERVER_ERROR,
                'Programming error encountered. Last step: ' + step,
                msg=msg_l
            )
            brcdapi_log.exception(_standard_error(sheet, switch_d.get('row'), error_obj), echo=True)

    try:  # Lots of stuff going on in here. try/except was to aid debugging during development
        step = 'Completed switch creation'

        # re-read the chassis and logical switch data to pick up the switch(es) we just created.
        if switch_config_flag:
            proj_obj = _refresh_project(session, chassis_obj.r_project_obj(), desc='Completed logical switch creation')
            chassis_obj = proj_obj.r_chassis_obj(session.get('chassis_wwn'))

        # Map ports to move out of a switch that didn't get moved to another logical switch yet.
        step = 'Determine which ports to move'
        default_fid = chassis_obj.r_default_switch_fid()
        for port, from_fid in pending_move_d.items():
            try:
                to_fid = obj_d['port_d'][port]['fid']
            except KeyError:
                to_fid = default_fid
            step = 'Determine which ports to move. Port: ' + port + '. to_fid: ' + str(to_fid)
            if chassis_obj.r_switch_obj_for_fid(to_fid) is None:
                non_existent_fid_l.append(port)
                to_fid = default_fid
            from_fid_d = port_map_d.get(to_fid)
            if from_fid_d is None:
                from_fid_d = dict()
                port_map_d[to_fid] = from_fid_d
            port_l = from_fid_d.get(from_fid)
            if port_l is None:
                port_l = list()
                from_fid_d[from_fid] = port_l
            port_l.append(port)

        # Move ports
        step = 'Moving ports'
        config_errors, config_success = 0, 0
        for to_fid, from_fid_d in port_map_d.items():
            for from_fid, port_l in from_fid_d.items():
                port_config_flag = True
                step = 'Decommissioning E-Ports. from_fid: ' + str(from_fid) + '. to_fid: ' + str(to_fid)
                # Decommission any E-Ports
                # Python returns something odd when a dictionary is empty. That is why I converted the keys to list
                obj = brcdapi_port.decommission_port(session, from_fid, [str(k) for k in e_port_d.keys()], best=True)
                if fos_auth.is_error(obj):
                    config_errors += 1
                    brcdapi_log.log(
                        [
                            'ERROR: One or more ports could not be decommissioned. FOS Error: ',
                            ' ' + fos_auth.formatted_error_msg(obj).replace('\n', ' \n')
                        ],
                        echo=True
                    )

                step = 'Moving ports. from_fid: ' + str(from_fid) + '. to_fid: ' + str(to_fid)
                success_l, fault_l = brcdapi_switch.add_ports(
                    session,
                    to_fid,
                    from_fid,
                    ports=[p for p in port_l if 'ge' not in p.lower()],
                    ge_ports=[p for p in port_l if 'ge' in p.lower()]
                )
                config_success, config_errors = config_success + len(success_l), config_errors + len(fault_l)
                api_move_fail_l.extend(fault_l)

        # Process alerts
        step = 'Processing alerts'
        buf_l = list()
        for d in [
            dict(desc='Ports Not Moved Because They Were Online', port_l=online_port_l, track_flag=False),
            dict(desc='Ports That Do Not Exist In The Chassis', port_l=non_existent_port_l, track_flag=True),
            dict(desc='Ports Assigned To Non-Existent FIDs', port_l=non_existent_fid_l, track_flag=True),
            dict(desc='Port Moves Failed By FOS', port_l=api_move_fail_l, track_flag=True),
        ]:
            if len(d['port_l']) > 0:
                buf_l.append('')
                buf_l.append(d['desc'])
                buf_l.extend('  ' + port for port in d['port_l'])
                if d['track_flag']:
                    config_errors += len(d['port_l'])
        if len(buf_l) > 0:
            brcdapi_log.log(buf_l, echo=True)

        # Update the Tracker
        step = 'Update tracker_d'
        tracker_d = chassis_obj.rs_key('tracker_d', _tracking_template_d.copy())
        tracker_d['config_success'] += config_success
        tracker_d['config_fail'] += config_errors

        # Update the project object
        if switch_config_flag or port_config_flag:
            proj_obj = _refresh_project(session, chassis_obj.r_project_obj(), desc='Interim step in _configure_chassis')
            chassis_obj = proj_obj.r_chassis_obj(session.get('chassis_wwn'))

        # Configure the switches & bind port addresses if necessary
        step = 'Configure switches'
        for fid, switch_d in obj_d['chassis_d']['switch_d'].items():
            step = 'Configure switches. FID: ' + str(fid)
            switch_obj = chassis_obj.r_switch_obj_for_fid(fid)
            _configure_switch(session, switch_obj, switch_d, force, cli)

    except BaseException as e:
        error_obj = fos_auth.create_error(
            brcdapi_util.HTTP_INT_SERVER_ERROR,
            'Programming error encountered. ' + step,
            msg=str(type(e)) + ': ' + str(e)
        )
        brcdapi_log.exception(_standard_error(sheet, None, error_obj), echo=True)

    return True


_chassis_config_d = dict(  # See brcddb.report.utils._conv_parameters_d for explanation of keys
    cli=_execute_cli,  # CLI
    enable=_chassis_enable_disable,  # Enable/Disable
    chassis_name=_chassis_name,  # Chassis Name
    fcr=_change_parameters,  # FCR
    msg_of_day=_chassis_motd,  # Message Of The Day
    shell_to=_change_parameters,  # Shell Timeout
    session_to=_change_parameters,  # Session Timeout
    tcp_to=_change_parameters,  # TCP Timeout Level
    max_rest=_change_parameters,  # Max REST Sessions
    web_tools=_chassis_web_tools,  # Web Tools
    config_switches=_config_logical_switches,  # Configure Switches
)


def _configure_chassis(session, chassis_obj, chassis_d, force, cli):
    """Set chassis parameters, create and configure logical switches, move and configure ports

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param chassis_obj: Chassis object
    :type chassis_obj: brcddb.classes.chassis.ChassisObj
    :param chassis_d: Dictionary returned from report_utils.parse_switch_file()
    :type chassis_d: dict
    :param force: True: Perform disabled. False: Do not perform any disable requests.
    :type force: bool
    :param cli: True: Execute all CLI. False: Do not execute any CLI
    :type cli: bool
    :return: Internal processing only.
    :rtype: None
    """
    global _chassis_config_d, _tracking_template_d

    brcdapi_log.log('Configuring chassis: ' + brcddb_chassis.best_chassis_name(chassis_obj), echo=True)

    for d in chassis_d['data_l']:
        d['chassis_d'] = chassis_d  # Add the back link
        try:
            if _chassis_config_d[d['key']](session, chassis_obj, chassis_d['sheet'], d, force, cli):
                proj_obj = _refresh_project(
                    session,
                    chassis_obj.r_project_obj(),
                    desc='Interim step in _configure_chassis'
                )
                chassis_obj = proj_obj.r_chassis_obj(session.get('chassis_wwn'))
        except KeyError:
            buf = 'ERROR: Invalid key: ' + str(d['user_key']) + ' (' + str(d['key']) + ')'
            brcdapi_log.exception([buf] + _standard_error(chassis_d['sheet'], d['row'], None), echo=True)
            tracker_d = chassis_obj.rs_key('tracker_d', _tracking_template_d.copy())
            tracker_d['config_fail'] += 1
        except ForceError:
            return  # The error was already reported.
        # except BaseException as e:
        #     brcdapi_log.exception(
        #         [
        #             'Programming error encountered. All processing halted.',
        #             'Type: ' + str(type(e)),
        #             str(e)
        #         ],
        #         echo=True
        #     )

    #########################################
    #                                       #
    #           Summary Report              #
    #                                       #
    #########################################


def _report_null(start_obj, end_obj):
    """Returns an empty string.

    :param start_obj: Starting chassis or switch object
    :type start_obj: brcddb.classes.chassis.ChassisObj, brcddb.classes.switch.SwitchObj
    :param end_obj: Final chassis or switch object
    :type end_obj: brcddb.classes.chassis.ChassisObj, brcddb.classes.switch.SwitchObj
    :return: See function header
    :rtype: str
    """
    return ''


def _report_current_name(start_obj, end_obj):
    """Returns the previous (start) chassis name. See _report_null for parameter definitions."""
    return brcddb_chassis.best_chassis_name(end_obj, wwn=True) \
        if class_util.get_simple_class_type(end_obj) == 'ChassisObj'\
        else brcddb_switch.best_switch_name(end_obj, wwn=True, fid=True, did=True)


def _report_previous_name(start_obj, end_obj):
    """Returns the previous (start) chassis name. See _report_null for parameter definitions."""
    start_name = _report_current_name(start_obj, end_obj)
    end_name = 'N/A (New Switch)' if start_obj is None else \
        brcddb_chassis.best_chassis_name(start_obj, wwn=True) \
        if class_util.get_simple_class_type(start_obj) == 'ChassisObj' \
        else brcddb_switch.best_switch_name(start_obj, wwn=True, fid=True, did=True)

    return 'No change' if end_name == start_name else end_name


def _report_hdr(start_obj, end_obj):
    """Returns line filled with '_'. Intended as a seperator. See _report_null for parameter definitions."""
    return '_______________________________________________________'


def _report_status(start_obj, end_obj):
    """Returns the final chassis status. See _report_null for parameter definitions."""
    return 'Online' if end_obj.r_is_enabled() else 'Offline'


def _report_cli_success(start_obj, end_obj):
    """Returns number successful CLI executions for switches or chassis. See _report_null for parameter definitions."""
    return str(end_obj.r_get('tracker_d', dict()).get('cli_success', 0))


def _report_cli_fail(start_obj, end_obj):
    """Returns number of failed CLI executions for switches or chassis. See _report_null for parameter definitions."""
    return str(end_obj.r_get('tracker_d', dict()).get('cli_fail', 0))


def _report_config_success(start_obj, end_obj):
    """Returns number successful switch or chassis configuration changes. See _report_null for parameter definitions."""
    return str(end_obj.r_get('tracker_d', dict()).get('config_success', 0))


def _report_config_fail(start_obj, end_obj):
    """Returns number of failed switch or chassis configuration changes. See _report_null for parameter definitions."""
    return str(end_obj.r_get('tracker_d', dict()).get('config_fail', 0))


def _report_switches_added(start_obj, end_obj):
    """Returns the number of switches added. See _report_null for parameter definitions."""
    return str(len([k for k in end_obj.r_switch_keys() if start_obj.r_project_obj().r_switch_obj(k) is None]))


def _report_switches_removed(start_obj, end_obj):
    """Returns the number of switches removed. See _report_null for parameter definitions."""
    return str(len([k for k in start_obj.r_switch_keys() if end_obj.r_project_obj().r_switch_obj(k) is None]))


def _report_ports_added(start_obj, end_obj):
    """Returns the number of ports added. See _report_null for parameter definitions."""
    end_port_l = end_obj.r_port_keys()
    return str(len(end_port_l) if start_obj is None
               else len([p for p in end_port_l if start_obj.r_port_obj(p) is None]))


def _report_ports_removed(start_obj, end_obj):
    """Returns the number of ports removed. See _report_null for parameter definitions."""
    if start_obj is None:
        return 0
    start_port_l = start_obj.r_port_keys()
    return str(len(start_port_l) if end_obj is None
               else len([p for p in start_port_l if end_obj.r_port_obj(p) is None]))


def _report_port_cli_success(start_obj, end_obj):
    """Return number successful CLI executions for all ports in a switch. See _report_null for parameter definitions."""
    x = 0
    for port_obj in end_obj.r_port_objects():
        x += port_obj.r_get('tracker_d', dict()).get('cli_success', 0)
    return str(x)


def _report_port_cli_fail(start_obj, end_obj):
    """Return number failed CLI executions for all ports in a switch. See _report_null for parameter definitions."""
    x = 0
    for port_obj in end_obj.r_port_objects():
        x += port_obj.r_get('tracker_d', dict()).get('cli_fail', 0)
    return str(x)


def _report_port_config_success(start_obj, end_obj):
    """Returns number successful port configuration changes in a switch. See _report_null for parameter definitions."""
    x = 0
    for port_obj in end_obj.r_port_objects():
        x += port_obj.r_get('tracker_d', dict()).get('config_success', 0)
    return str(x)


def _report_port_config_fail(start_obj, end_obj):
    """Returns the number failed port configuration changes in a switch. See _report_null for parameter definitions."""
    x = 0
    for port_obj in end_obj.r_port_objects():
        x += port_obj.r_get('tracker_d', dict()).get('config_fail', 0)
    return str(x)


_report_chassis_l = [
    dict(hdr='', a=_report_null),
    dict(hdr='Summary:', a=_report_null),
    dict(hdr='', a=_report_null),
    dict(hdr='Chassis:', a=_report_current_name),
    dict(hdr='___', a=_report_hdr),
    dict(hdr='Previous Name:', a=_report_previous_name),
    dict(hdr='Status:', a=_report_status),
    dict(hdr='*CLI Success:', a=_report_cli_success),
    dict(hdr='*CLI Fail:', a=_report_cli_fail),
    dict(hdr='Config Success:', a=_report_config_success),
    dict(hdr='Config Fail:', a=_report_config_fail),
    dict(hdr='Switches Added:', a=_report_switches_added),
    dict(hdr='Switches Removed:', a=_report_switches_removed),
]
_report_switch_l = [
    dict(hdr='', a=_report_null),
    dict(hdr='Switch:', a=_report_current_name),
    dict(hdr='___', a=_report_hdr),
    dict(hdr='Previous Name:', a=_report_previous_name),
    dict(hdr='Status:', a=_report_status),
    dict(hdr='*CLI Success:', a=_report_cli_success),
    dict(hdr='*CLI Fail:', a=_report_cli_fail),
    dict(hdr='Config Success:', a=_report_config_success),
    dict(hdr='Config Fail:', a=_report_config_fail),
    dict(hdr='Ports Added:', a=_report_ports_added),
    dict(hdr='Ports Removed:', a=_report_ports_removed),
    dict(hdr='*Port CLI Success:', a=_report_port_cli_success),
    dict(hdr='*Port CLI Fail:', a=_report_port_cli_fail),
    dict(hdr='Port Config Success:', a=_report_port_config_success),
    dict(hdr='Port Config Fail:', a=_report_port_config_fail),
]


def _write_summary(start_proj_obj, end_proj_obj):
    """Write out a summary report

    :param start_proj_obj: Beginning project object
    :type start_proj_obj: brcddb.classes.project.ProjectObj
    :param end_proj_obj: Final project object
    :type end_proj_obj: brcddb.classes.project.ProjectObj
    :Return: None. Updates the log with a summary only.
    :rtype: None
    """
    global _report_chassis_l, _report_switch_l

    # Figure out the maximum header length
    max_hdr_len = 0
    for d in _report_chassis_l + _report_switch_l:
        max_hdr_len = max(max_hdr_len, len(d['hdr']))

    pad_len = max_hdr_len + 2
    for d in _report_chassis_l + _report_switch_l:
        if d['hdr'] == '___':
            d['hdr'] = gen_util.pad_string('___', pad_len, '_')

    # Gather everything for the report, report_l
    report_l = list()

    # Chassis
    for end_chassis_obj in end_proj_obj.r_chassis_objects():  # There can only be one when this was written
        start_chassis_obj = start_proj_obj.r_chassis_obj(end_chassis_obj.r_obj_key())
        for d in _report_chassis_l:
            report_l.append(gen_util.pad_string(d['hdr'], pad_len, ' ', append=True) +
                            d['a'](start_chassis_obj, end_chassis_obj))

        # New & Existing Switches
        for end_switch_obj in end_chassis_obj.r_switch_objects():
            start_switch_obj = start_proj_obj.r_switch_obj(end_switch_obj.r_obj_key())
            for d in _report_switch_l:
                buf = gen_util.pad_string(d['hdr'], pad_len, ' ', append=True)
                buf += str(d['a'](start_switch_obj, end_switch_obj))
                report_l.append(buf)

        # Switches Removed - In this version of switch_config.py, this can only happen if it was removed via CLI
        report_l.extend(['', 'Removed Switches:'])
        switch_count = 0
        for start_switch_obj in start_chassis_obj.r_switch_objects():
            end_switch_obj = end_proj_obj.r_switch_obj(start_switch_obj.r_obj_key())
            if end_switch_obj is None:
                switch_count += 1
                report_l.append(brcddb_switch.best_switch_name(start_switch_obj, wwn=True, fid=True, did=True))
        if switch_count == 0:
            report_l.append('None')

    # Write the report
    report_l.extend([
        '',
        'Use compare_report.py or multi_capture.py with the -r option',
        'for details.',
        '',
        '*CLI responses are only evaluated for some obvious errors.',
        'Success and fail may not be accurate.'
        ''
    ])
    brcdapi_log.log(report_l, echo=True)


def pseudo_main(args_d):
    """Basically the main().

    :param args_d: Input arguments
    :type args_d: dict
    :return: Exit code
    :rtype: int
    """
    ec = brcddb_common.EXIT_STATUS_OK
    start_proj_obj, end_proj_obj = None, None
    ec_l, error_l = [brcddb_common.EXIT_STATUS_OK], list()

    # Read in the switch configuration Workbook
    file = brcdapi_file.full_file_name(args_d['i'], '.xlsx')
    brcdapi_log.log('Reading ' + file, echo=True)
    error_l, chassis_d = report_utils.parse_switch_file(file)

    # Bail out if any errors were encountered
    if len(error_l) > 0:
        brcdapi_log.log(error_l, echo=True)
        return brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Add back links
    for switch_d in chassis_d['switch_d'].values():
        switch_d['chassis_d'] = chassis_d
        for switch_data_d in switch_d['data_l']:
            switch_data_d['switch_d'] = switch_d
    for port_data_d in chassis_d['port_d'].values():
        port_data_d.update(dict(chassis_d=chassis_d, pending_enable=False))

    # Login
    session = api_int.login(args_d['id'], args_d['pw'], args_d['ip'])
    if fos_auth.is_error(session):  # Errors are sent to the log in api_int.login()
        return brcddb_common.EXIT_STATUS_API_ERROR

    try:
        # Read some basic chassis information and initialize _tracker_d with existing switches and ports
        start_proj_obj = _refresh_project(session, None, desc='Initial data read')
        if start_proj_obj.r_is_any_error():  # Error details are logged in api_int.get_batch()
            return brcddb_common.EXIT_STATUS_API_ERROR
        chassis_obj = start_proj_obj.r_chassis_obj(session.get('chassis_wwn'))

        # Make the configuration changes
        _configure_chassis(session, chassis_obj, chassis_d, args_d['force'], args_d['cli'])
        end_proj_obj = _refresh_project(session, start_proj_obj, desc='Final refresh in switch_config.py')

    except ForceError:
        pass

    # Logout and display a summary report
    if session is not None:
        obj = brcdapi_rest.logout(session)
        if fos_auth.is_error(obj):
            brcdapi_log.exception(fos_auth.formatted_error_msg(obj), echo=True)
            ec_l.append(brcddb_common.EXIT_STATUS_API_ERROR)
    if len(error_l) > 0:
        brcdapi_log.log(error_l, echo=True)
        ec_l.append(brcddb_common.EXIT_STATUS_ERROR)
    if class_util.get_simple_class_type(start_proj_obj) == 'ProjectObj' and \
            class_util.get_simple_class_type(end_proj_obj) == 'ProjectObj':
        _write_summary(start_proj_obj, end_proj_obj)

    # Return the first error code, if there was an error
    for ec in ec_l:
        if ec != brcddb_common.EXIT_STATUS_OK:
            break

    return ec


def _get_input():
    """Retrieves the command line input, minimally validates the input, and sets up logging

    :return: Exit code
    :rtype: int
    """
    global __version__, _input_d

    # Get command line input
    buf = 'Compares a switch configuration workbook to actual switch configurations in a chassis. Except for CLI '\
          'commands, actions are only taken on differences. CLI commands are not interpreted by the script. They are '\
          'always sent to the switch, but only if the port is disabled.'
    args_d = gen_util.get_input(buf, _input_d)

    # Set up logging
    brcdapi_rest.verbose_debug(args_d['d'])
    brcdapi_log.open_log(
        folder=args_d['log'],
        suppress=args_d['sup'],
        no_log=args_d['nl'],
        version_d=brcdapi_util.get_import_modules()
    )

    # Command line feedback
    ml = [
        os.path.basename(__file__) + ', ' + __version__,
        'IP address, -ip:  ' + brcdapi_util.mask_ip_addr(args_d['ip']),
        'ID, -id:          ' + str(args_d['id']),
        'Workbook, -i:     ' + args_d['i'],
        'CLI, -cli:        ' + str(args_d['cli']),
        'force, -force     ' + str(args_d['force']),
        'Log, -log:        ' + str(args_d['log']),
        'No log, -nl:      ' + str(args_d['nl']),
        'Debug, -d:        ' + str(args_d['d']),
        'Suppress, -sup:   ' + str(args_d['sup']),
        '',
    ]
    brcdapi_log.log(ml, echo=True)

    return pseudo_main(args_d)


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
