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

**Important Programming Note**

I ran into some issues setting an SCC policy on non-FICON logical switches. As a practical matter, I don't know of any
customer using an SCC policy for any switch type not used for FICON. Search for "Important Programming Note" in
scc_policy.py additional details.

**Description**

Configure logical switch(es) from a workbook

ToDo - QSFP ports may not be handled properly for port decommissions.
ToDo - Figure out correct ports to return errors on in _enable_disable_ports()
ToDo - Figure out correct ports to return errors on in _pod_reserve_release(),
ToDo - If a port is disabled, I don't think the persistent bit gets cleared if Persistent Disable is selected.
ToDo - Same as above but in reverse. I don't think it gets cleared

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
| 4.1.2     | 26 Oct 2026   | Added support for FICON zoning, SCC policy, CLI for everything (chassis, switches and |
|           |               | and ports). This was a significant rewrite because it began as something much smaller |
|           |               | and grew into something that needed to be table driven.                               |
+-----------+---------------+---------------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2024, 2025, 2026 Jack Consoli'
__date__ = '26 Oct 2026'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack_consoli@yahoo.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '4.1.2'

import sys
import datetime
import copy
import os
import time
import pprint
import inspect
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
import brcddb.api.zone as brcddb_api_zone
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
    'running/brocade-security/policy-distribution-config',
    'running/brocade-security/active-scc-policy-member-list',
    'running/brocade-security/defined-scc-policy-member-list',
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
    global _basic_capture_kpi_l, _db_read, _tracking_template_d

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

    # Add back chassis_d, switch_d, and tracker_d to the objects. Variable names beginning with "working" are associated
    # with the previous objects
    for working_chassis_obj in working_proj_obj.r_chassis_objects():

        # Chassis objects. There could only be one chassis when this was written.
        chassis_obj = proj_obj.r_chassis_obj(working_chassis_obj.r_obj_key())
        if chassis_obj is None:
            brcdapi_log.exception('No chassis found in previous project.', echo=True)
            raise ForceError
        chassis_d = working_chassis_obj.r_get('chassis_d')
        chassis_obj.s_new_key('chassis_d', chassis_d)
        chassis_obj.s_new_key('tracker_d', working_chassis_obj.r_get('tracker_d'))

        # Switch objects.
        for fid, switch_d in chassis_d['switch_d'].items():
            switch_obj = chassis_obj.r_switch_obj_for_fid(fid)
            if switch_obj is None:
                continue  # switch_obj is None if there was an error creating the switch
            working_switch_obj = working_chassis_obj.r_switch_obj_for_fid(fid)
            if working_switch_obj is None:  # It's a new switch
                switch_obj.s_new_key('switch_d', switch_d)
                switch_obj.s_new_key('tracker_d', _tracking_template_d.copy())
            else:  # It's a previously existing switch
                switch_obj.s_new_key('switch_d', working_switch_obj.r_get('switch_d'))
                switch_obj.s_new_key('tracker_d', working_switch_obj.r_get('tracker_d'))

        # Port objects
        for port_obj in chassis_obj.r_port_objects():
            working_port_obj = working_chassis_obj.r_port_obj(port_obj.r_obj_key())
            if working_port_obj is None:
                # The only way I can think of for this to happen is if someone added a port card to a director in
                # the middle of running this script. During a hectic change control window with multiple things going
                # on, stuff happens sometimes.
                brcdapi_log.log('WARNING: Ports added to the chassis while running this script.', echo=True)
                # Other than using the wrong workbook template, which would have numerous other problems, port_d should
                # always be in chassis_d. Just in case I'm missing something in my thinking, I'll default to an empty
                # port_d
                try:
                    port_d = chassis_obj.r_get('chassis_d')['port_d'][port_obj.r_obj_key()]
                except KeyError:
                    port_d = report_utils.empty_port_d()
                port_obj.s_new_key('port_d', port_d)
                port_obj.s_new_key('tracker_d', _tracking_template_d.copy())
            else:
                port_obj.s_new_key('port_d', working_port_obj.r_get('port_d'))
                port_obj.s_new_key('tracker_d', working_port_obj.r_get('tracker_d'))

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
                obj.r_get('tracker_d')['config_fail'] += 1
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
    row = str(in_row + 1) if isinstance(in_row, int) else in_row if isinstance(in_row, str) else '?'
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
    :type row: None, int, str
    :param error_msg: Message to display if an error occurs
    :type error_msg: None, str, list
    :return: Internal processing only.
    :rtype: None
    """
    if fos_auth.is_error(obj):
        class_obj.r_get('tracker_d')['config_fail'] += 1
        brcdapi_log.log(gen_util.convert_to_list(error_msg) + _standard_error(sheet, row, obj), echo=True)
    else:
        class_obj.r_get('tracker_d')['config_success'] += 1


def _send_request(session, class_obj, sheet, sub_d, uri, content_d, error_msg):
    """Send API requests

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param class_obj: Chassis, switch, or port object
    :type class_obj: brcddb.classes.chassis.ChassisObj, brcddb.classes.switch.SwitchObj, brcddb.classes.port.PortObj
    :param sheet: Sheet name. Used for error reporting only.
    :type sheet: str
    :param sub_d: Dictionary in 'data_l' returned from report_utils.parse_switch_file()
    :type sub_d: dict
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
    _process_api_response(obj, class_obj, sheet, sub_d['row'], error_msg)

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


def _execute_cli(session, class_obj, sheet, sub_d, force, cli):
    """Send CLI commands.

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param class_obj: Chassis, switch, or port object
    :type class_obj: brcddb.classes.chassis.ChassisObj, brcddb.classes.switch.SwitchObj, brcddb.classes.port.PortObj
    :param sheet: Sheet name. Used for error reporting only.
    :type sheet: str
    :param sub_d: Dictionary associated with the specific command (usually the dict in 'data_l')
    :type sub_d: dict
    :param force: True/False for -force command line parameter
    :type force: bool
    :param cli: True: execute CLI. False: Do not execute CLI
    :type cli: bool
    :return: True if the chassis should be re-read
    :rtype: bool
    """
    refresh_flag = False

    if not cli:
        return refresh_flag

    fid = 0 if class_util.get_simple_class_type(class_obj, all_types=True) == 'ChassisObj' else class_obj.r_fid()
    try:
        cmd_l = gen_util.convert_to_list(sub_d['parameter'])  # It should be a list already. Just belt & suspenders.
        for cmd in _replace_variables(class_obj, cmd_l, sub_d):
            if _cli_error(fos_cli.send_command(session, fid, cmd, fosexec=True if fid > 0 else False)):
                class_obj.r_get('tracker_d')['cli_fail'] += 1
            else:
                class_obj.r_get('tracker_d')['cli_success'] += 1
            refresh_flag = True
    except KeyError:
        pass  # Nothing to do for this key
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return refresh_flag  # We have no idea what the CLI commands did, so force a re-read of the chassis data.


def _change_parameters(session, class_obj, sheet, sub_d, force, cli):
    """Generic change parameters. See _execute_cli() for parameters."""
    global _parameters_d

    new_value = None  # Just to keep the PyCharm warnings down.
    try:
        new_value = sub_d['parameter']
        if new_value is None:
            return False
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    # Set up the data structure to send to the API
    brcddb_key = _parameters_d[sub_d['key']]
    current_val = class_obj.r_get(brcddb_key)
    try:
        if current_val is not None and current_val == new_value:
            return False  # The values match, so there is nothing to change.
    except TypeError:
        # If there is a type error, that's a bug having nothing to do with this script
        buf_l = [
            'Type mismatch',
            'Line: ' + str(inspect.currentframe()),
            'current_val: ' + str(current_val) + ' (' + str(type(current_val)) + ')',
            'parameter: ' + str(new_value) + ' (' + str(type(new_value)) + ')',
            ]
        brcdapi_log.exception(buf_l, echo=True)  # Let someone know, but keep processing
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    # If we got this far, there is something to change. Prepare the data structure to send to the API
    try:
        temp_l = brcddb_key.split('/')
        x = len(temp_l)
        url = 'running/' + '/'.join(temp_l[0:x-1])  # Everything but the final leaf

        # Send the change to the API
        buf_l = ['ERROR: Failed to set ' + sub_d['user_key'] + ' (' + str(new_value) + ').']
        if sub_d['key'] == 'fcr':
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
            sub_d,
            url,
            {temp_l[x-2]: {temp_l[x-1]: new_value}},
            buf_l,
            )
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return False  # None of these changes are going to effect any other changes.


def _chassis_name(session, chassis_obj, sheet, sub_d, force, cli):
    """Sets the chassis name. See _execute_cli() for parameters."""

    try:
        chassis_d = chassis_obj.r_get('chassis_d')
        if sub_d['parameter'] is None:
            return False

        # Make sure the name is valid before setting it.
        valid_name = brcdapi_util.valid_chassis_name(sub_d['parameter'])
        buf_l = _invalid_characters(sub_d['parameter'], valid_name)
        if len(buf_l) > 0:
            buf_l.insert(0, 'WARNING: The chassis name was modified as follows:')
            buf_l.extend(_standard_error(chassis_d['sheet'], sub_d['row'], None))
            brcdapi_log.log(buf_l, echo=True)
        sub_d['parameter'] = valid_name

        return _change_parameters(session, chassis_obj, sheet, sub_d, force, cli)
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return False


def _chassis_fcr(session, chassis_obj, sheet, sub_d, force, cli):
    """Sets the chassis name. See _execute_cli() for parameters."""

    try:
        if sub_d['parameter'] is None:
            return False

        temp_d = copy.deepcopy(sub_d)
        temp_d['parameter'] = None if sub_d['parameter'] is None else True if sub_d['parameter'] == 'enable' else False

        return _change_parameters(session, chassis_obj, sheet, temp_d, force, cli)

    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return False


def _null_action(session, class_obj, sheet, sub_d, force, cli):
    """Send CLI commands. See _execute_cli() for parameters."""
    return False

#########################################
#                                       #
#               Port                    #
#                                       #
#########################################


def _port_enable(port_obj, force):
    """Determines if a port should be enabled. Essentially a case statement in _port_enable_case_d.

    port_d['enable_disable'] is updated as noted below. A full description is here for common reference. Only enable is
    applicable for this function.

    +---------------------------+-------+---------------------------------------------------------------------------+
    | Key                       | Type  | Description                                                               |
    +===========================+=======+===========================================================================|
    | pend_enable               | bool  | If True, the port should be enabled after the port is reserved and the    |
    |                           |       | switch is enabled.                                                        |
    +---------------------------+-------+---------------------------------------------------------------------------+
    | enable                    | bool  | If True, the port is ready to be enabled.                                 |
    +---------------------------+-------+---------------------------------------------------------------------------+
    | disable                   | bool  | If True, the port is ready to be disabled.                                |
    +---------------------------+-------+---------------------------------------------------------------------------+
    | persistent_disable        | bool  | If True, the port is ready to be persistently disabled.                   |
    +---------------------------+-------+---------------------------------------------------------------------------+
    | decommission              | bool  | If True, the port is ready to be decommissioned.                          |
    +---------------------------+-------+---------------------------------------------------------------------------+
    | persistent_decommission   | bool  | Same as decommission, but the port is persistently disabled after the     |
    |                           |       | decommission completes.                                                   |
    +---------------------------+-------+---------------------------------------------------------------------------+

    :param port_obj: Port object
    :type port_obj: brcddb.classes.port.PortObj
    :param force: Not relevant for port enable.
    :type force: bool
    :return: Error message(s), if any.
    :rtype: None, list
    """
    error_l = list()
    port_d = port_obj.r_get('port_d')
    if not isinstance(port_d, dict):
        error_l.append('port_d, type ' + str(type(port_d)) + ', is missing or invalid.')

    elif not port_obj.r_is_enabled():
        if not port_obj.r_is_pod_license() or port_obj.r_switch_obj().r_is_enabled():
            port_d['enable_disable'] = 'pend_enable'
        else:
            port_d['enable_disable'] = 'enable'

    if len(error_l) > 0:
        error_l.extend(_standard_error(port_d['sheet'], port_d['row'], None))
        port_obj.r_get('tracker_d')['config_fail'] += 1

    return error_l


def _port_disable(port_obj, force):
    """Determines if a port should be disabled. Essentially a case statement in _enable_disable_ports().

    See _port_enable() for details on how port_d is updated.

    WARNING: I didn't bother implementing persistence for E-Ports. E-Ports are just decommissioned.

    :param port_obj: Port object
    :type port_obj: brcddb.classes.port.PortObj
    :param force: If True, disable ports whether they are online or not.
    :type force: bool
    :return: Error message(s), if any.
    :rtype: None, list
    """
    error_l = list()
    port_d = port_obj.r_get('port_d')
    if not isinstance(port_d, dict):
        error_l.append('port_d, type ' + str(type(port_d)) + ', is missing or invalid.')

    elif port_obj.r_is_enabled():
        login_objects_l = port_obj.r_login_objects()
        if len(login_objects_l) == 0 or force:
            port_d['enable_disable'] = 'decommission' if port_obj.r_type() == 'e-port' else 'disable'
        else:
            error_l.extend(
                [
                    'ERROR: Cannot disable ports with active logins unless -force is specified.',
                    'Active logins:'
                ]
            )
            for login_obj in login_objects_l:
                error_l.append('  ' + brcddb_login.login_best_port_desc(login_obj))
    elif port_obj.r_is_persistent_disable():
        port_d['enable_disable'] = 'disable'

    if len(error_l) > 0:
        error_l.extend(_standard_error(port_d['sheet'], port_d['row'], None))
        port_obj.r_get('tracker_d')['config_fail'] += 1

    return error_l


def _port_persistent_disable(port_obj, force):
    """Determines if a port should be persistently disabled. Essentially a case statement in _enable_disable_ports().

    See _port_enable() for details on how port_d is updated.

    WARNING: I didn't bother implementing persistence for E-Ports. E-Ports are just decommissioned.

    :param port_obj: Port object
    :type port_obj: brcddb.classes.port.PortObj
    :param force: If True, disable ports whether they are online or not.
    :type force: bool
    :return: Error message(s), if any.
    :rtype: list
    """
    error_l = list()
    port_d = port_obj.r_get('port_d')
    if not isinstance(port_d, dict):
        error_l.append('port_d, type ' + str(type(port_d)) + ', is missing or invalid.')

    elif port_obj.r_is_enabled():
        login_objects_l = port_obj.r_login_objects()
        if len(login_objects_l) == 0 or force:
            port_d['enable_disable'] = 'persistent_decommission' if port_obj.r_type() == 'e-port' \
                else 'persistent_disable'
        else:
            error_l.extend(
                [
                    'ERROR: Cannot disable ports with active logins unless -force is specified.',
                    'Active logins:'
                ]
            )
            for login_obj in login_objects_l:
                error_l.append('  ' + brcddb_login.login_best_port_desc(login_obj))
    elif not port_obj.r_is_persistent_disable():
        port_d['enable_disable'] = 'persistent_disable'

    if len(error_l) > 0:
        error_l.extend(_standard_error(port_d['sheet'], port_d['row'], None))
        port_obj.r_get('tracker_d')['config_fail'] += 1

    return error_l


def _port_null(port_obj, force):
    """Does nothing

    :param port_obj: Port object
    :type port_obj: brcddb.classes.port.PortObj
    :param force: If True, disable ports whether they are online or not.
    :type force: bool
    :return: Error message(s), if any.
    :rtype: list
    """
    return list()


"""The pointer to the _port_xxx_case_d dictionaries are passed to _enable_disable_ports() as the action_d parameter. The
sub-dictionaries are: Key: e, Value: pointer to function used to evaluate the request. Key: a, Value: pointer to
function used to act on the request.
+-------+---------------------------+-------------------------------------------------------------------------------+
| Key   | Type                      | Description.                                                                  |
+=======+===========================+===============================================================================|
| e     | None, function pointer    | Pointer to function used to evaluate the request.                             |
+-------+---------------------------+-------------------------------------------------------------------------------+
| a     | None, function pointer    | Pointer to function used to act on the request.                               |
+-------+---------------------------+-------------------------------------------------------------------------------+
| p     | bool                      | Persistent flag.                                                              |
+-------+---------------------------+-------------------------------------------------------------------------------+
"""
_port_disable_case_d = dict(  # See comments above.
    enable=dict(e=_port_null, a=None, p=False),
    disable=dict(e=_port_disable, a=brcdapi_port.disable_port, p=False),
    persistent_disable=dict(e=_port_persistent_disable, a=brcdapi_port.disable_port, p=True),
    decommission=dict(e=_port_persistent_disable, a=brcdapi_port.decommission_port, p=False),
    persistent_decommission=dict(e=_port_persistent_disable, a=brcdapi_port.decommission_port, p=True),
)
_port_enable_case_d = dict(  # See comments above.
    enable=dict(e=_port_enable, a=brcdapi_port.enable_port, p=False),
    disable=dict(e=_port_null, a=None, p=False),
    persistent_disable=dict(e=_port_null, a=None, p=False),
    decommission=dict(e=_port_null, a=None, p=False),
    persistent_decommission=dict(e=_port_null, a=None, p=True),
)
_port_all_case_d = dict(  # See comments above.
    enable=dict(e=_port_null, a=None, p=False),
    disable=dict(e=_port_disable, a=brcdapi_port.disable_port, p=False),
    persistent_disable=dict(e=_port_persistent_disable, a=brcdapi_port.disable_port, p=True),
    decommission=dict(e=_port_persistent_disable, a=brcdapi_port.decommission_port, p=False),
    persistent_decommission=dict(e=_port_persistent_disable, a=brcdapi_port.decommission_port, p=True),
)


def _enable_disable_ports(session, switch_obj, sheet, port_l, force, parameter_key, action_d):
    """Called by _configure_ports()

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param switch_obj: Switch object
    :type switch_obj: brcddb.classes.switch.SwitchObj
    :param port_l: List of port configuration dict as returned from report_utils.parse_switch_file()
    :type port_l: list
    :param force: True if -force specified on command line.
    :type force: bool
    :param parameter_key: Key for parameter in port_d (the individual port dictionaries in switch_port_d)
    :type parameter_key: str
    :param action_d: See comments above the function definition (search _port_xxx_case_d) for a detailed explanation
    :type action_d: dict
    :return: True if a data refresh is necessary.
    :rtype: bool
    """
    return_val = False

    try:
        # Figure out what gets enabled, disabled, decommissioned, and what actions can't be taken
        fid = switch_obj.r_fid()
        error_l = list()
        for port_d in port_l:
            port_obj = switch_obj.r_port_obj(port_d['port_key'])
            if port_obj is None:
                continue  # An error occurred adding the port, which was already reported, if this happens.
            parameter = port_d.get(parameter_key)
            if isinstance(parameter, str):
                try:
                    error_l.extend(action_d[parameter]['e'](port_obj, force))
                except KeyError:
                    error_l.extend(['Invalid key: ' + parameter, 'Line: ' + str(inspect.currentframe())])
                    error_l.extend(_standard_error(sheet, port_d['row'], None))
        if len(error_l) > 0:
            brcdapi_log.log(error_l, echo=True)

        # Act on the lists of ports. Note: Some day, I plan on picking the right port(s) for the one reporting the
        # error. Setting error_port to the first port in the list was an expedient. I set error_port to None to indicate
        # that there is nothing to do. I check the fid in port_obj_l because a port defined for a fid on the slot sheet
        # that doesn't have a corresponding switch sheet may end up in the default switch.

        port_obj_l = [o for o in switch_obj.r_port_objects() if o.r_get('port_d', dict(fid=0))['fid'] == fid]
        disable_l = [o.r_obj_key() for o in port_obj_l if str(o.r_get('port_d')[parameter_key]) == 'disable']
        decom_l = [o.r_obj_key() for o in port_obj_l if str(o.r_get('port_d')[parameter_key]) == 'decommission']
        persistent_decom_l = \
            [o.r_obj_key() for o in port_obj_l if str(o.r_get('port_d')[parameter_key]) == 'persistent_decommission']
        persistent_disable_l = \
            [o.r_obj_key() for o in port_obj_l if str(o.r_get('port_d')[parameter_key]) == 'persistent_disable']
        enable_l = [o.r_obj_key() for o in port_obj_l if str(o.r_get('port_d')[parameter_key]) == 'enable']
        # Send all the enables and disables to the switch
        for control_d in [
            dict(  # Disable
                enable_func=action_d['disable']['a'],
                port_l=disable_l,
                persistent=action_d['disable']['p'],
                error_msg='ERROR: Failed to disable one or more ports.',
            ),
            dict(  # Decommission
                enable_func=action_d['decommission']['a'],
                port_l=decom_l,
                persistent=action_d['decommission']['p'],
                error_msg='ERROR: Failed to decommission one or more ports.',
            ),
            dict(  # Persistent Decommission
                enable_func=action_d['persistent_disable']['a'],
                port_l=persistent_decom_l,
                persistent=action_d['persistent_disable']['p'],
                error_msg='ERROR: Failed to persistently decommission one or more ports.',
            ),
            dict(  # Persistent Disable
                enable_func=action_d['persistent_disable']['a'],
                port_l=persistent_disable_l,
                persistent=action_d['persistent_disable']['p'],
                error_msg='ERROR: Failed to persistently disable one or more ports.',
            ),
            dict(  # Enable
                enable_func=action_d['enable']['a'],
                port_l=enable_l,
                persistent=action_d['enable']['p'],
                error_msg='ERROR: Failed to enable one or more ports.',
            ),
        ]:
            port_l = control_d['port_l']
            len_port_l = len(port_l)
            if len_port_l > 0:
                return_val = True
                port_obj = switch_obj.r_port_obj(port_l[0])

                # Enable/Disable Actions
                if callable(control_d['enable_func']):
                    _process_api_response(
                        control_d['enable_func'](session, fid, port_l, persistent=control_d['persistent'], best=True),
                        port_obj,
                        sheet,
                        port_obj.r_get('port_d/row', 0),
                        control_d['error_msg']
                    )

    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), 'parameter_key: ' + str(parameter_key), str(e)], echo=True)

    return return_val


def _pod_reserve_release(session, switch_obj):
    """Reserve and Release POD licenses

    :param session: Session object returned from brcdapi.brcdapi_auth.login()
    :type session: dict
    :param switch_obj: Switch object.
    :type switch_obj: brcddb.classes.switch.SwitchObj
    :return: True if a data refresh is necessary.
    :rtype: bool
    """
    release_pod_l, reserve_pod_l, error_release_pod_l = list(), list(), list()
    switch_sheet = switch_obj.r_get('switch_d/sheet', 'Unknown')

    # Sort out which POD licenses should be released and which ones should be reserved
    for port_obj in switch_obj.r_port_objects():
        port_d = port_obj.r_get('port_d', dict())
        parameter = port_d.get('reserve')
        if not isinstance(parameter, str):
            continue
        if parameter == 'Reserve':
            if not port_obj.r_is_pod_license():  # Only reserve it if it hasn't been reserved yet.
                reserve_pod_l.append(port_obj.r_obj_key())
        elif parameter == 'Release':
            if port_obj.r_is_pod_license():  # Only release it if it is reserved.
                if port_obj.r_is_enabled():  # A POD can't be release while the port is enabled.
                    error_release_pod_l.append(
                        '  ' + port_obj.r_obj_key() + ', Sheet: ' + port_d['sheet'] + ' Row: ' + str(port_d['row'] + 1)
                    )
                    buf = 'ERROR: Port ' + port_obj.r_obj_key() + ' '
                    brcdapi_log.log([buf] + _standard_error(port_d['sheet'], str(port_d['row'] + 1), None), echo=True)
                    port_obj.r_get('tracker_d')['config_fail'] += 1
                else:
                    release_pod_l.append(port_obj.r_obj_key())

    # Report any errors
    if len(error_release_pod_l) > 0:
        brcdapi_log.log(['', 'PODs not released because the port was enabled:'] + error_release_pod_l, echo=True)

    # Release and reserve the POD licences.
    for control_d in [
        dict(f=brcdapi_port.release_pod, port_l=release_pod_l, m='release'),
        dict(f=brcdapi_port.reserve_pod, port_l=reserve_pod_l, m='reserve'),
    ]:
        if len(control_d['port_l']) > 0:
            port_obj = switch_obj.r_port_obj(control_d['port_l'][0])
            _process_api_response(
                control_d['f'](session, switch_obj.r_fid(), control_d['port_l'], best=True),
                port_obj,
                port_obj.r_get('port_d/sheet', switch_sheet),
                port_obj.r_get('port_d/row'),
                'Failed to ' + control_d['m'] + ' POD on one or more ports.'
            )

    return True if len(release_pod_l) + len(release_pod_l) > 0 else False


def _configure_ports(session, switch_obj, sheet, sub_d, force, cli):
    """Set, if necessary, switch configuration parameters. See _execute_cli() for parameters."""
    global _switch_name_mode_conv_r_d, _port_disable_case_d, _port_enable_case_d, _port_all_case_d

    if class_util.get_simple_class_type(switch_obj) != 'SwitchObj':
        return  # The error message was printed elsewhere
    brcdapi_log.log('Configuring ports.', echo=True)

    # Initialize resources
    switch_wwn = switch_obj.r_obj_key()
    switch_d = switch_obj.r_get('switch_d')
    fid = switch_obj.r_fid()
    bind_flag = False
    for d in [o for o in switch_d['data_l'] if o['key'] == 'bind']:
        if d['parameter']:
            bind_flag = True
            break
    port_d = switch_obj.r_chassis_obj().r_get('chassis_d')['port_d']
    port_d_l = [d for d in port_d.values() if d['fid'] == fid]
    port_l = [d['port_key'] for d in port_d_l]

    # You can't enable a port if it doesn't have a POD license. You can't release a POD license if the port is enabled,
    # so process disable and decommission first, the POD licenses, and then port enable. Note: I should have done this
    # at switch creation time because some PODs in other switches may need to be released before having enough to
    # reserve. I'm assuming this situation is rare, if ever, and port_config.py can be used to get as granular as an
    # administrator needs to get.

    # Start enable/disable:
    try:
        if _enable_disable_ports(session, switch_obj, sheet, port_d_l, force, 'start_enable', _port_all_case_d):
            proj_obj = _refresh_project(session, switch_obj.r_project_obj(), desc='Post CLI action in _configure_ports')
            switch_obj = proj_obj.r_switch_obj(switch_wwn)
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    # Process CLI.
    try:
        if cli:
            refresh_flag = False
            for port_d in [d for d in port_d_l if d.get('cli') is not None]:
                if _execute_cli(
                        session,
                        switch_obj.r_port_obj(port_d['port_key']),
                        port_d.get('sheet', 'Unknown'),
                        port_d,
                        force,
                        cli
                ):
                    refresh_flag = True
            if refresh_flag:
                proj_obj = _refresh_project(
                    session,
                    switch_obj.r_project_obj(),
                    desc='Post CLI action in _configure_ports'
                )
                switch_obj = proj_obj.r_switch_obj(switch_wwn)
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    # Refresh the project if necessary
    try:
        # End enable/disable: Just the disables and decommissions. This needs to be done before releasing PODs
        if _enable_disable_ports(session, switch_obj, sheet, port_d_l, force, 'end_enable', _port_disable_case_d):
            proj_obj = _refresh_project(session, switch_obj.r_project_obj(), desc='Post CLI action in _configure_ports')
            switch_obj = proj_obj.r_switch_obj(switch_wwn)
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    # Release the PODs
    try:
        if _pod_reserve_release(session, switch_obj):
            proj_obj = _refresh_project(session, switch_obj.r_project_obj(), desc='Release POD in _configure_ports')
            switch_obj = proj_obj.r_switch_obj(switch_wwn)
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    # Bind the addresses.
    try:
        if bind_flag:
            bind_d = dict()
            for port in port_l:
                port_obj = switch_obj.r_port_obj(port)
                port_d = port_obj.r_get('port_d')

                # This script only supports address binding mode for FICON, hence only checking for '8-bit'
                if str(port_obj.r_get(brcdapi_util.fc_bind_mode)) == '8-bit':

                    # Make sure we have valid port addresses
                    new_port_addr = port_d.get('port_addr')
                    if not isinstance(new_port_addr, str) or len(new_port_addr) > 2:
                        buf = 'ERROR: Invalid port address: ' + str(new_port_addr) + ' (' + str(type(new_port_addr))
                        buf += ')'
                        brcdapi_log.log([buf] + _standard_error(sheet, port_d['row'], None), echo=True)
                        port_obj.r_get('tracker_d')['config_fail'] += 1
                        continue
                    if len(new_port_addr) == 1:
                        new_port_addr = '0' + new_port_addr
                    new_port_addr = new_port_addr.lower()
                    port_addr = port_obj.r_addr().lower()

                    # Is the address already bound to the desired address?
                    if port_addr[4:6] == new_port_addr and port_obj.r_get(brcdapi_util.fc_bind_mode):
                        continue  # Address binding mode is already set and the address matches.

                    # If we got this far, bind the port address if the port is disabled.
                    if port_obj.r_is_enabled():
                        buf_l = ['ERROR: Cannot bind port address while the port is enabled.']
                        brcdapi_log.log(buf_l + _standard_error(sheet, port_d['row'], None), echo=True)
                        port_obj.r_get('tracker_d')['config_fail'] += 1
                        continue
                    bind_d[port] = '0x' + new_port_addr + '00'

            # Bind the ports
            if len(bind_d) > 0:
                _process_api_response(
                    brcdapi_port.bind_addresses(session, fid, bind_d, best=True),
                    switch_obj.r_port_obj(port_l[0]),  # Just using the first port object for error reporting
                    sheet,
                    port_d['row'],
                    'ERROR: Failed to bind one or more port addresses. See previous messages for details.'
                )
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    # Set the port names
    port_obj, port_name_mode = None, 'Unknown'  # Needs to be initialized if there is an exception
    try:
        update_port_d = dict()
        port_name_mode = switch_obj.r_get(brcdapi_util.bfc_portname_mode, 'off')
        for port_obj in [switch_obj.r_port_obj(p) for p in port_l if p is not None]:  # None if an error occurred
            port_d = port_obj.r_get('port_d')
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
            if port_obj.r_port_name() == valid_name:  # port_obj is None if a config error occurred
                continue
            buf_l = _invalid_characters(port_d['port_name'], valid_name)
            if len(buf_l) > 0:
                buf_l.insert(0, 'WARNING: The port name was modified as follows:')
                buf_l.extend(_standard_error(port_d['sheet'], port_d['row'], None))
                brcdapi_log.log(buf_l, echo=True)
            update_port_d[port_obj.r_obj_key()] = valid_name

        for port_num in [str(k) for k in update_port_d.keys()]:
            port_obj = switch_obj.r_port_obj(port_num)
            obj = brcdapi_port.user_name(session, fid, update_port_d, best=True)
            _process_api_response(
                obj,
                port_obj,
                sheet,
                port_d['row'],
                'ERROR: Failed to set the user friendly port name for one or more ports.'
            )
            break

    except BaseException as e:
        buf_l = [
            'Sheet:          ' + str(sheet),
            'Port:           ' + 'None' if port_obj is None else port_obj.r_obj_key(),
            'port_name_mode: ' + port_name_mode,
            pprint.pformat(sub_d),
            str(e)
        ]
        brcdapi_log.exception(buf_l, echo=True)


#########################################
#                                       #
#               Switch                  #
#                                       #
#########################################

def _switch_enable_disable(session, switch_obj, sheet, sub_d, force, cli):
    """Enables or disables the switch. See _execute_cli() for parameters. """
    global _ENABLE_WAIT

    force_error = False

    try:
        # Enable
        if sub_d['parameter'] == 'enable':
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
                sub_d['row'],
                'ERROR: Could not enable the switch.'
            )
            if not fos_auth.is_error(obj):
                time.sleep(_ENABLE_WAIT)
                return True

        # Persistent Disable
        elif sub_d['parameter'] == 'persistent_disable':
            if switch_obj.r_is_persistent_disable() and not switch_obj.r_is_enabled():
                pass  # Already persistently disabled. Nothing to do.
            elif force:
                obj = brcdapi_switch.disable_switch(session, switch_obj.r_fid(), persistent=True)
                _process_api_response(
                    obj,
                    switch_obj,
                    sheet,
                    sub_d['row'],
                    'ERROR: Could not persistently disable the switch.'
                )
                if not fos_auth.is_error(obj):
                    time.sleep(_ENABLE_WAIT)
                    return True
            else:
                buf = 'ERROR: Cannot persistently disable switch. -force not specified.'
                brcdapi_log.log([buf] + _standard_error(sheet, sub_d['row'], None), echo=True)
                switch_obj.r_get('tracker_d')['config_fail'] += 1

        # Disable
        elif sub_d['parameter'] == 'disable':
            if not switch_obj.r_is_enabled():
                pass  # The switch is already disabled. Nothing to do.
            elif force:
                obj = brcdapi_switch.disable_switch(session, switch_obj.r_fid(), persistent=False)
                _process_api_response(
                    obj,
                    switch_obj,
                    sheet,
                    sub_d['row'],
                    'ERROR: Could not disable the switch.'
                )
                if not fos_auth.is_error(obj):
                    time.sleep(_ENABLE_WAIT)
                    return True
            else:
                buf = 'ERROR: Cannot disable switch. -force not specified.'
                brcdapi_log.log([buf] + _standard_error(sheet, sub_d['row'], None), echo=True)
                switch_obj.r_get('tracker_d')['config_fail'] += 1

        else:
            buf = 'ERROR: Invalid parameter, ' + sub_d['parameter'] + '. Valid parameters are: Enable, Disable,  and '
            buf += 'Persistent Disable'
            brcdapi_log.log([buf] + _standard_error(sheet, sub_d['row'], None), echo=True)
            switch_obj.r_get('tracker_d')['config_fail'] += 1
            force_error = True

    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    if force_error:
        raise ForceError

    return False


def _switch_fid(session, switch_obj, sheet, sub_d, force, cli):
    """FID is set when the logical switch is created. FID changes not supported in this script. See _execute_cli(). """
    try:
        if switch_obj is not None:
            fid, new_fid = str(switch_obj.r_fid()), str(sub_d['parameter'])
            if fid != new_fid:
                buf_l = [
                    'FID changing not supported by this script.',
                    'Current   : ' + brcddb_switch.best_switch_name(switch_obj, fid=True),
                    'Requested : ' + 'FID: ' + new_fid,
                ]
                brcdapi_log.log(buf_l + _standard_error(sheet, sub_d['row'], None), echo=True)
                switch_obj.r_get('tracker_d')['config_fail'] += 1
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return False


def _switch_banner(session, switch_obj, sheet, sub_d, force, cli):
    """Sets the switch banner. See _execute_cli() for parameters."""

    try:
        banner = sub_d['parameter']
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
            brcdapi_log.log(buf_l + _standard_error(sheet, sub_d['row'], None), echo=True)
        sub_d['parameter'] = valid_banner

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
            sub_d['row'],
            'ERROR: Failed to set Login Banner (' + valid_banner + ')'
        )

    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return False


def _switch_type(session, switch_obj, sheet, sub_d, force, cli):
    """Switch type is set when the switch is created. Changing it is not supported. See _execute_cli(). """
    try:
        switch_type = switch_obj.c_switch_type().replace('default', 'open')
        if switch_type != sub_d['parameter']:
            buf_l = [
                'Changing the switch type is not supported by this script.',
                'Current   : ' + switch_type,
                'Requested : ' + sub_d['parameter'],
                ]
            brcdapi_log.log(buf_l + _standard_error(sheet, sub_d['row'], None), echo=True)
            switch_obj.r_get('tracker_d')['config_fail'] += 1
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return False


def _switch_name_mode(session, switch_obj, sheet, sub_d, force, cli):
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
    global _switch_name_mode_conv_d

    try:
        switch_d = switch_obj.r_get('switch_d')
        if sub_d['parameter'] is None:
            return False

        # Make sure the port name mode is valid.
        port_name_mode = _switch_name_mode_conv_d.get(sub_d['parameter'])
        if port_name_mode is None:
            buf_l = [
                'ERROR: Parameter, ' + sub_d['parameter'] + ' for ' + sub_d['user_key'] + ' is invalid.',
                'Valid options are: ' + ', '.join([str(k) for k in _switch_name_mode_conv_d.keys()]) + '.',
            ]
            brcdapi_log.log(buf_l + _standard_error(sheet, sub_d['row'], None), echo=True)
            return False

        if port_name_mode == switch_obj.r_get(brcdapi_util.bfc_portname_mode):
            return False

        # Prepare the content
        content_d = None

        # If the port name mode is "dynamic", check the port name format and build the content
        if port_name_mode == 'dynamic':
            port_name_format_d = None

            # Find and validate Port Name Format
            for d in switch_d['data_l']:
                if d['key'] == 'port_name_format':
                    port_name_format_d = d
                    break
            if port_name_format_d is None:
                buf_l = [
                    'ERROR: ' + sub_d['user_key'] + '  is ' + sub_d['parameter'] + ' which requires',
                    'Port Name Format, but a row with Port Name Format was not found.'
                ]
                brcdapi_log.log(buf_l + _standard_error(sheet, switch_d['row'], None), echo=True)
                switch_obj.r_get('tracker_d')['config_fail'] += 1
                return False
            port_name_format = port_name_format_d['parameter']
            if port_name_format is None or len(port_name_format) == 0:
                buf_l = ['ERROR: Port Name Format cannot be empty.']
                brcdapi_log.log(buf_l + _standard_error(sheet, port_name_format_d['row'], None), echo=True)
                switch_obj.r_get('tracker_d')['config_fail'] += 1
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
                sub_d,
                'running/' + brcdapi_util.bfc_port_uri,
                content_d,
                'ERROR: Failed to set ' + sub_d['user_key'] + ' (' + sub_d['key'] + ')',
                )

    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return False


def _dup_wwn(session, switch_obj, sheet, sub_d, force, cli):
    """Duplicate WWN (enforce login) handling. See _execute_cli(). """
    try:
        if sub_d['parameter'] is None:
            return False
        if sub_d['parameter'] == switch_obj.r_get(brcdapi_util.bfc_fport_enforce_login):
            return False

        if switch_obj.r_is_enabled():
            buf_l = ['ERROR: The switch must be disabled to modify ' + sub_d['user_key'] + ' handling.',]
            brcdapi_log.log(buf_l + _standard_error(sheet, sub_d['row'], None), echo=True)
            switch_obj.r_get('tracker_d')['config_fail'] += 1
            return False

        content_d = {'f-port-login-settings': {'enforce-login-string': sub_d['parameter']}}
        _send_request(
            session,
            switch_obj,
            sheet,
            sub_d,
            'running/' + brcdapi_util.bfcfp_uri,
            content_d,
            'ERROR: Failed to set ' + sub_d['user_key'] + ' (' + sub_d['key'] + ')',
            )

    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return _change_parameters(session, switch_obj, sheet, sub_d, force, cli)

#####################################################
#                                                   #
#  Switch Functions That Require Special Handling   #
#                                                   #
#####################################################


def _switch_name(session, switch_obj, sheet, sub_d, force, cli):
    """Set the switch user-friendly name. See _execute_cli() for parameters."""
    try:
        switch_name = sub_d['parameter']
        if not isinstance(switch_name, str):
            return False

        valid_name = brcdapi_util.valid_switch_name(switch_name)
        if brcddb_switch.best_switch_name(switch_obj) != valid_name:
            buf_l = _invalid_characters(switch_name, valid_name)
            if len(buf_l) > 0:
                buf_l.insert(0, 'WARNING: The switch name was modified as follows:')
                brcdapi_log.log(buf_l + _standard_error(sheet, sub_d['row'], None), echo=True)
            content_d = {'user-friendly-name': valid_name}
            _process_api_response(
                brcdapi_switch.fibrechannel_switch(session, switch_obj.r_fid(), content_d, switch_obj.r_obj_key()),
                switch_obj,
                sheet,
                sub_d['row'],
                'ERROR: Failed to set switch user-friendly name.'
            )
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return False


def _switch_did(session, switch_obj, sheet, sub_d, force, cli):
    """Set the switch Domain ID. See _execute_cli() for parameters."""
    try:
        switch_did = switch_obj.r_did()
        if switch_did is None or switch_did != sub_d['parameter']:
            # Is the switch enabled?
            if switch_obj.r_is_enabled():
                buf = 'ERROR: Switch must be disabled to change the DID.'
                brcdapi_log.log([buf] + _standard_error(sheet, sub_d['row'], None), echo=True)
                switch_obj.r_get('tracker_d')['config_fail'] += 1
            else:
                content_d = {'domain-id': sub_d['parameter']}
                _process_api_response(
                    brcdapi_switch.fibrechannel_switch(session, switch_obj.r_fid(), content_d, switch_obj.r_obj_key()),
                    switch_obj,
                    sheet,
                    sub_d['row'],
                    'ERROR: Failed to set switch Domain-ID.'
                )

    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return False


def _switch_fab_principal(session, switch_obj, sheet, sub_d, force, cli):
    """Set this switch as the fabric principal. See _execute_cli() for parameters."""
    global _bfc_fabric

    try:
        # Does fabric priority need to be enabled?
        switch_d = switch_obj.r_get('switch_d')
        new_fab_principal = sub_d['parameter']
        if not isinstance(new_fab_principal, bool):
            return False
        current_fab_principal = switch_obj.r_get(brcdapi_util.bfc_principal_en, False)
        if not new_fab_principal and not current_fab_principal:
            return False  # It's off on the worksheet and off on the switch. The priority doesn't matter.

        # Get the desired fabric priority
        current_fab_priority = switch_obj.r_get(brcdapi_util.bfc_principal_pri, 'None')
        new_fab_priority = None
        # Find the priority
        for data_d in switch_d['data_l']:
            if data_d['key'] == 'fab_priority':
                new_fab_priority = data_d.get('parameter')
                break
        if new_fab_principal and new_fab_priority is None:
            buf_l = ['ERROR: Fabric Principal Priority is required to set the Fabric Principal.']
            brcdapi_log.log(buf_l + _standard_error(sheet, sub_d['row'], None), echo=True)
            switch_obj.r_get('tracker_d')['config_fail'] += 1
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
        _send_request(session, switch_obj, sheet, sub_d, _bfc_fabric, content_d, e_buf)

    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return False


def _switch_fabric_name(session, switch_obj, sheet, sub_d, force, cli):
    """Set the fabric user-friendly name. See _execute_cli() for parameters."""
    try:
        if brcddb_fabric.best_fab_name(switch_obj) != sub_d['parameter']:
            content_d = {'fabric-user-friendly-name': sub_d['parameter']}
            _process_api_response(
                brcdapi_switch.fibrechannel_switch(session, switch_obj.r_fid(), content_d, switch_obj.r_obj_key()),
                switch_obj,
                sheet,
                sub_d['row'],
                'ERROR: Failed to set switch user-friendly name.'
            )
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return False


def _configure_switch(session, switch_obj, sub_d, force, cli):
    """Set, if necessary, switch configuration parameters. See _execute_cli() for parameters."""
    if switch_obj is None:
        return False  # The error message was printed elsewhere
    switch_name = brcddb_switch.best_switch_name(switch_obj, did=True, fid=True, wwn=True)

    # Perform switch configuration actions
    switch_d = switch_obj.r_get('switch_d')
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
                switch_wwn = switch_obj.r_obj_key()
                proj_obj = _refresh_project(
                    session,
                    switch_obj.r_project_obj(),
                    desc='Interim step in _configure_chassis'
                )
                switch_obj = proj_obj.r_switch_obj(switch_wwn)
        except KeyError:
            buf_l = [
                'ERROR: Invalid key: ' + str(d['user_key']) + ' (' + str(d.get('key', '?')) + ')',
                'Line: ' + str(inspect.currentframe()),
                'Switch: ' + switch_name
            ]
            buf_l.extend(_standard_error(sheet, d.get('row', 0), None))
            brcdapi_log.exception(buf_l, echo=True)
            switch_obj.r_get('tracker_d')['config_fail'] += 1
        except ForceError:
            return False  # The error was already reported.
        except BaseException as e:
            buf_l = ['Sheet: ' + str(sheet), 'Switch: ' + switch_name, pprint.pformat(d), pprint.pformat(sub_d), str(e)]
            if class_util.get_simple_class_type(switch_obj, all_types=True) == 'SwitchObj':
                switch_obj.r_get('tracker_d')['config_fail'] += 1
            else:
                buf_l.append('Invalid switch object: ' + str(type(switch_obj)))
            brcdapi_log.exception(buf_l, echo=True)

    return False


def _enable_cup(session, switch_obj, sheet, sub_d, force, cli):
    """Enable CUP if it should be enabled. See _execute_cli() for parameters."""

    try:
        # Do we need to enable CUP?
        if sub_d['parameter'] is None:
            return False
        if switch_obj.r_get(brcdapi_util.ficon_cup_en, False) == sub_d['parameter']:
            return False

        switch_type = switch_obj.c_switch_type()
        if switch_type == 'ficon':
            buf = 'ERROR: Failed to set ' + sub_d['user_key'] + ' (' + sub_d['key'] + '). This usually happens when '
            buf += 'the license has not been installed.'
            _send_request(
                session,
                switch_obj,
                sheet,
                sub_d,
                brcdapi_util.ficon_cup_uri,
                dict(cup={'fmsmode-enabled': sub_d['parameter']}),
                buf,
                )
        else:
            buf_l = ['Can only enable CUP on switches configured as "FICON". Switch type is: ' + switch_type]
            brcdapi_log.log(buf_l + _standard_error(sheet, sub_d['row'], None), echo=True)
            switch_obj.r_get('tracker_d')['config_fail'] += 1
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return False


def _evaluate_scc(switch_obj, scc_wwn_l):
    """Determines if the SCC_POLICY needs to be created or modified. Copy and pasted from scc_policy.py

    :param switch_obj: Switch object
    :type switch_obj: brcddb.class.switch.SwitchObj
    :param scc_wwn_l: SCC_POLICY membership
    :type scc_wwn_l: list
    :return: Search for "_evaluate_scc" in scc_policy.py for details
    :rtype: dict
    """
    # full_scc_wwn_d is so that I don't have to spin the list everytime. As a practical matter, this list will be so
    # small that the performance difference will be insignificant. I just did this out of force of habit. Rather than
    # back it out after I tested the code, I left it in and added this comment.
    full_scc_wwn_d = dict()
    for wwn in scc_wwn_l:
        full_scc_wwn_d[wwn] = True

    scc_policy_d = dict(
        create_bool=False,
        fabwide_bool=False,
        add_l=list(),
        remove_l=list(),
        defined='not_attempted',  # See above
        activated='not_attempted'  # See as above
    )

    # Determine if the policy needs to be created, pushed to the fabric, and what members to add and remove.
    defined_scc_l = switch_obj.r_defined_scc(list())
    if len(defined_scc_l) == 0:
        scc_policy_d['create_bool'] = True
        scc_policy_d['fabwide_bool'] = True
        scc_policy_d['add_l'] = scc_wwn_l
    else:
        defined_scc_d = dict()
        for wwn in defined_scc_l:
            defined_scc_d[wwn] = True
        scc_policy_d['add_l'] = [wwn for wwn in scc_wwn_l if wwn not in defined_scc_d]
        scc_policy_d['remove_l'] = [wwn for wwn in defined_scc_l if wwn not in full_scc_wwn_d]
        if len(switch_obj.r_active_scc(list())) == 0:
            scc_policy_d['fabwide_bool'] = True

    return scc_policy_d


def _scc(session, switch_obj, sheet, sub_d, force, cli):
    """Set the SCC policy, if there is one. See _execute_cli() for parameters."""

    try:
        # Is there anything to do?
        switch_d = switch_obj.r_get('switch_d')
        if not isinstance(sub_d['parameter'], str):
            return False
        parameter_l = [b for b in sub_d['parameter'].strip().replace(' ', '').split(',') if len(b) > 0]
        if len(parameter_l) == 0:
            return False  # Some white space was added to the cell but nothing else if we get here.

        # Restricted to FICON switches only. See "Important Programming Note" in the module header for an explanation.
        switch_type = str(switch_obj.c_switch_type())
        if switch_type != 'ficon':
            switch_obj.r_get('tracker_d')['config_fail'] += 1
            buf_l = [
                'WARNING: An SCC policy is only supported with FICON fabrics. Switch type',
                'is: ' + switch_type + '. No action taken.',
            ]
            brcdapi_log.log(buf_l + _standard_error(sheet, switch_d['row'], None), echo=True)
            return False

        # Figure out what WWNs should be in the policy
        wwn_l = [switch_obj.r_obj_key()]  # Always our own switch
        for wwn in parameter_l:
            if wwn == '*':
                wwn_l.extend([str(b) for b in switch_obj.r_fabric_obj().r_switch_keys()])
            elif gen_util.is_wwn(wwn, full_check=True):
                wwn_l.append(wwn)
            else:
                brcdapi_log.log(
                    ['ERROR: Invalid WWN: ' + wwn] + _standard_error(sheet, switch_d['row'], None),
                    echo=True
                )
                switch_obj.r_get('tracker_d')['config_fail'] += 1
        if len(wwn_l) == 0:
            return False  # Some white space was added to the cell but nothing else if we get here.
        wwn_l = gen_util.remove_duplicates(wwn_l)
        wwn_l.sort()  # I don't think the order matters, but just in case... I also do this in scc_policy.py

        # Determine if the policy needs to be created and with what WWNs
        scc_policy_d = _evaluate_scc(switch_obj, wwn_l)

        # Update the SCC policy
        # If the SCC_POLICY doesn't exist, create it with the membership list
        if scc_policy_d['create_bool']:
            obj = brcdapi_rest.operations_request(
                session,
                'operations/security-acl-policy',
                'POST',
                {
                    'security-policy-parameters': {
                        'policy-name': 'SCC_POLICY',
                        'members': dict(member=scc_policy_d['add_l']),
                        'action': 'create',
                    }
                },
                fid=switch_obj.r_fid()
            )
            if fos_auth.is_error(obj):
                switch_obj.r_get('tracker_d')['config_fail'] += 1
                brcdapi_log.log(
                    [
                        'ERROR: Failed to create SCC Policy. FOS Error:',
                        ' ' + fos_auth.formatted_error_msg(obj).replace('\n', ' \n')
                    ],
                    echo=True
                )
            else:
                switch_obj.r_get('tracker_d')['config_success'] += 1

        # Add all the WWNs that need to be added.
        elif len(scc_policy_d['add_l']) > 0:
            obj = brcdapi_rest.operations_request(
                session,
                'operations/security-acl-policy',
                'POST',
                {
                    'security-policy-parameters': {
                        'policy-name': 'SCC_POLICY',
                        'members': dict(member=scc_policy_d['add_l']),
                        'action': 'add',
                    }
                },
                fid=switch_obj.r_fid()
            )
            if fos_auth.is_error(obj):
                switch_obj.r_get('tracker_d')['config_fail'] += 1
                brcdapi_log.log(
                    [
                        'ERROR: Failed to update the SCC Policy. FOS Error:',
                        ' ' + fos_auth.formatted_error_msg(obj).replace('\n', ' \n')
                    ],
                    echo=True
                )
            else:
                switch_obj.r_get('tracker_d')['config_success'] += 1

    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return False


#####################################
#                                   #
# Case statements for _ficon_zone() #
#                                   #
#####################################

def _ficon_zone_all(fabric_obj):
    """Adds zoning that contains a single zone will all port except ICL ports to the fabric object.

    :param fabric_obj: Fabric object
    :type fabric_obj: brcddb.classes.fabric.FabricObj
    :return: Name of zone configuration created.
    :rtype: str
    """
    zonecfg = brcddb_fabric.unique_zonecfg_name(fabric_obj, 'ficon_zonecfg')
    brcddb_fabric.ficon_zone_fab_obj(
        fabric_obj, brcddb_fabric.ficon_zone_all(fabric_obj, zonecfg)
    )

    return zonecfg


def _ficon_zone_all_f(fabric_obj):
    """Adds zoning that contains a single zone will all F-Ports to the fabric object.

    :param fabric_obj: Fabric object
    :type fabric_obj: brcddb.classes.fabric.FabricObj
    :return: Name of zone configuration created.
    :rtype: str
    """
    zonecfg = brcddb_fabric.unique_zonecfg_name(fabric_obj, 'ficon_zonecfg')
    brcddb_fabric.ficon_zone_fab_obj(
        fabric_obj, brcddb_fabric.ficon_zone_all_f(fabric_obj, zonecfg)
    )

    return zonecfg


def _ficon_zone_by_device(fabric_obj):
    """Adds zoning that contains zones by device to the fabric object.

    :param fabric_obj: Fabric object
    :type fabric_obj: brcddb.classes.fabric.FabricObj
    :return: Name of zone configuration created.
    :rtype: str
    """
    zonecfg = brcddb_fabric.unique_zonecfg_name(fabric_obj, 'ficon_zonecfg')
    brcddb_fabric.ficon_zone_fab_obj(
        fabric_obj,
        brcddb_fabric.ficon_zone_by_device(fabric_obj, zonecfg, brcddb_fabric.rnid_groups(fabric_obj))
    )

    return zonecfg


_zone_action_d = dict(all=_ficon_zone_all, all_f=_ficon_zone_all_f, device=_ficon_zone_by_device)


def _ficon_zone(session, switch_obj, sheet, sub_d, force, cli):
    """Enable CUP if it should be enabled. See _execute_cli() for parameters."""
    global _zone_action_d

    try:
        # Is there anything to do?
        switch_d = switch_obj.r_get('switch_d')
        if not isinstance(sub_d['parameter'], str):
            return False
        switch_type = str(switch_obj.c_switch_type())
        if switch_type != 'ficon':
            switch_obj.r_get('tracker_d')['config_fail'] += 1
            buf_l = [
                'WARNING: FICON Zone is only supported with FICON fabrics. Switch type',
                'is: ' + switch_type + '. No action taken.',
            ]
            brcdapi_log.log(buf_l + _standard_error(sheet, sub_d['row'], None), echo=True)
            return False

        # Add the zone for the zone action to the fabric object
        fabric_obj = switch_obj.r_fabric_obj()
        try:
            zonecfg = _zone_action_d[sub_d['parameter']](fabric_obj)
        except KeyError:
            switch_obj.r_get('tracker_d')['config_fail'] += 1
            buf_l = [
                'ERROR: Invalid zone action, "' + sub_d['parameter'] + '".',
                'Line: ' + str(inspect.currentframe()),
                'No action taken.',
            ]
            brcdapi_log.log(buf_l + _standard_error(sheet, sub_d['row'], None), echo=True)
            return False

        brcddb_api_zone.replace_zoning(
            session,
            fabric_obj,
            switch_obj.r_fid(),
            None if fabric_obj.r_eff_zone_cfg_obj() is None else zonecfg
        )

        switch_obj.r_get('tracker_d')['config_success'] += 1

    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

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


def _chassis_enable_disable(session, chassis_obj, sheet, sub_d, force, cli):
    """Enables or disables the chassis. See _execute_cli() for parameters."""
    global _chassis_uri, _ENABLE_WAIT

    try:
        # Enable
        if sub_d['parameter'] == 'enable':
            if chassis_obj.r_is_enabled():
                return False

            obj = _send_request(
                session,
                chassis_obj,
                sheet,
                sub_d,
                _chassis_uri,
                dict(chassis={'chassis-enabled': True}),
                'ERROR: Could not enable the chassis.',
            )
            if fos_auth.is_error(obj):
                return False
            time.sleep(_ENABLE_WAIT)
            return True

        # Disable
        if sub_d['parameter'] == 'disable':
            if not chassis_obj.r_is_enabled():
                return False

            if not force:
                buf = 'ERROR: Cannot disable chassis. -force not specified.'
                brcdapi_log.log([buf] + _standard_error(sheet, sub_d['row'], None), echo=True)
                chassis_obj.r_get('tracker_d')['config_fail'] += 1
                return False

            # If we got this far, all is good. Send the request
            _send_request(
                session,
                chassis_obj,
                sheet,
                sub_d,
                _chassis_uri,
                dict(chassis={'chassis-enabled': False}),
                'ERROR: Could not disable the chassis.',
            )
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

        return False

    # If we got this far, the parameter is invalid
    buf = 'ERROR: Invalid parameter, ' + sub_d['parameter'] + '. Valid parameters are: Enable and Disable.'
    brcdapi_log.log([buf] + _standard_error(sheet, sub_d['row'], None), echo=True)
    chassis_obj.r_get('tracker_d')['config_fail'] += 1
    raise ForceError


def _chassis_motd(session, chassis_obj, sheet, sub_d, force, cli):
    """Sets the chassis "Message of the Day". See _execute_cli() for parameters."""

    try:
        # Is there anything to change?
        motd = sub_d['parameter']
        if not isinstance(motd, str):
            return False
        motd = motd.replace('\r\n', '\n')
        # As of FOS 9.1.1d, brcdapi_util.bc_motd incorrectly returned the chassis name.
        if motd == chassis_obj.r_get(brcdapi_util.bc_motd):
            return False

        # Remove any invalid characters from the MOTD specified in the workbook
        valid_motd = brcdapi_util.valid_chassis_motd(motd)
        buf_l = _invalid_characters(motd, valid_motd)
        if len(buf_l) > 0:
            buf_l.insert(0, 'WARNING: The MOTD contained invalid characters. It was modified as follows:')
            buf_l.extend(_standard_error(sheet, sub_d['row'], None))
            brcdapi_log.log(buf_l, echo=True)
        sub_d['parameter'] = valid_motd
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    # Send the change
    return _change_parameters(session, chassis_obj, sheet, sub_d, force, cli)


def _chassis_web_tools(session, chassis_obj, sheet, sub_d, force, cli):
    """Enable/disables WebTools. See _execute_cli() for parameters.

    I think WebTools is always enabled and that brocade_chassis/management-interface-configuration/webtools-enabled
    is obsolete. Since I'm not sure, I read brocade_chassis/management-interface-configuration. If webtools-enabled
    is present, I try to change it. Otherwise, ignore it. I removed this option from the workbooks. I left this code in
    just in case it's ever needed in the future."""
    global _parameters_d

    try:
        if chassis_obj.r_get(_parameters_d[sub_d['key']]) is None:
            return False
    except BaseException as e:
        brcdapi_log.exception(['Sheet: ' + str(sheet), pprint.pformat(sub_d), str(e)], echo=True)

    return _change_parameters(session, chassis_obj, sheet, sub_d, force, cli)


def _config_logical_switches(session, chassis_obj, sheet, sub_d, force, cli):
    """Creates logical switches and assigns ports. See _execute_cli() for parameters.

    port_map_d: If a switch already exists, it may contain ports that need to be moved to another logical switch. The
    easy thing to do would be to put those ports in the default switch and then put them in whatever logical switch
    they belong in when that switch is processed. Moving ports is very inefficient. port_map_d is used to determine
    where all the ports belong, so that they only need to be moved once.

    Key is the FID where the port is moving to ("to FID"). Value is a dictionary whose key is the FID where the port
    currently resides ("from FID"). The value is a list of ports in the "from FID" that need to be moved to the
    "to FID."

    pending_move_d: Key is the port number. Value is the "from FID", which is the FID the port is currently in. This
    dictionary only contains ports that need to be moved.
    """
    global _tracking_template_d

    refresh_flag = False
    state_l = ['Setup']  # Used for error reporting

    try:
        # Is there anything to change?
        if not sub_d['parameter']:
            return refresh_flag

        # Setup
        chassis_d = chassis_obj.r_get('chassis_d')
        online_port_l, non_existent_port_l, non_existent_fid_l, api_move_fail_l = list(), list(), list(), list()
        default_fid = chassis_obj.r_default_switch_fid()

        # Create whatever switches need to be created
        state_l.append('Create logical switches')
        switch_d_l = [d for d in chassis_d['switch_d'].values() if chassis_obj.r_switch_obj_for_fid(d['fid']) is None]
        for switch_d in switch_d_l:

            # Some switch settings are contingent on other parameters. param_d simplifies digging out other switch data.
            param_d = dict()
            for data_d in switch_d['data_l']:
                param_d[data_d['key']] = data_d['parameter']

            # Create the logical switch
            state_l.append('Creating FID ' + str(switch_d['fid']))
            brcdapi_log.log('Creating FID ' + str(switch_d['fid']), echo=True)
            obj = brcdapi_switch.create_switch(
                session,
                switch_d['fid'],
                True if param_d.get('switch_type', 'open') == 'base' else False,
                True if param_d.get('switch_type', 'open') == 'ficon' else False
            )
            _process_api_response(obj, chassis_obj, sheet, 0, 'ERROR: Could not create the switch.')
            refresh_flag = True

        if refresh_flag:
            state_l.append('Refresh')
            proj_obj = _refresh_project(session, chassis_obj.r_project_obj(), desc='Post switch create')
            chassis_obj = proj_obj.r_chassis_obj(session.get('chassis_wwn'))
            refresh_flag = False

        # Get a map of where all the ports should go
        state_l.append('Setup switch_port_map_d (map of where ports go.')
        error_online_l = list()  # Error message for ports that could not be moved because they were online.
        error_no_fid_l = list()  # Error messages for port that could not be moved because the fid doesn't exist.
        error_exist_l = list()  # Error messages for ports that do not exist in the chassis
        # switch_port_map_d: Key: FID where port is moving to. Value: dict. Key: FID where ports are moving from. Value:
        # list of ports to be moved.
        switch_port_map_d = dict()  # See comment above
        for switch_obj in chassis_obj.r_switch_objects():
            switch_port_map_d[switch_obj.r_fid()] = dict()
        for switch_fid, switch_d in chassis_d['switch_d'].items():
            switch_obj = chassis_obj.r_switch_obj_for_fid(switch_fid)
            if switch_obj is None:
                continue  # There was an error, which was reported elsewhere, creating the switch.
            switch_name = brcddb_switch.best_switch_name(switch_obj, fid=True)  # Used for error reporting

            # Find any ports that don't belong in this switch and move to where it belongs
            state_l.append(switch_name + ' - Find ports that do not belong in this switch')
            for port_obj in switch_obj.r_port_objects():
                port_num = port_obj.r_obj_key()
                port_d = port_obj.r_get(
                    'port_d',
                    dict(sheet='Unknown', row='?', fid=0, tracker_d=_tracking_template_d.copy())
                )
                if switch_fid != default_fid and port_d['fid'] != port_obj.r_fid():
                    # The port doesn't belong in this switch
                    to_fid = port_d['fid']
                    if chassis_obj.r_switch_obj_for_fid(to_fid) is None:
                        # This port belongs in a switch that doesn't exist, so put it in the default switch.
                        error_no_fid_l.append('  ' + port_num + ', FID: ' + str(to_fid))
                        port_obj.r_get('tracker_d')['config_fail'] += 1
                        to_fid = default_fid
                    port_l = switch_port_map_d[to_fid].get(port_obj.r_fid())
                    if not isinstance(port_l, list):
                        port_l = list()
                        switch_port_map_d[to_fid][port_obj.r_fid()] = port_l
                    port_l.append(port_num)

            # Add any ports defined in the workbook that aren't already in this switch to switch_port_map_d
            state_l.append(switch_name + ' - Add ports from the workbook to the map')
            for port_d in [d for d in chassis_d['port_d'].values() if d['fid'] == switch_fid]:
                port_obj = chassis_obj.r_port_obj(port_d['port_key'])
                if port_obj is None:
                    error_exist_l.append('  ' + port_d['port_key'] + ', Switch: ' + switch_name)
                    continue
                if switch_fid == port_obj.r_fid():
                    continue  # The port is already in this switch.
                if len(port_obj.r_login_keys()) > 0 and not force:
                    # The port doesn't belong in this switch, but something is logged in and -force was not specified
                    error_online_l.append('  ' + port_obj.r_obj_key() + ', Switch: ' + switch_name)
                    port_obj.r_switch_obj().r_get('tracker_d')['config_fail'] += 1
                else:
                    # Move the port to the FID it belongs in if the FID exists. Otherwise, move it to the default FID
                    from_fid = port_obj.r_fid()
                    to_fid = default_fid if chassis_obj.r_switch_obj_for_fid(from_fid) is None else port_d['fid']
                    if to_fid != from_fid:
                        port_l = switch_port_map_d[to_fid].get(port_obj.r_fid())
                        if port_l is None:
                            port_l = list()
                            switch_port_map_d[to_fid][port_obj.r_fid()] = port_l
                        port_l.append(port_obj.r_obj_key())

        # Report errors
        state_l.append('Report errors')
        for d in [
            dict(l=error_exist_l, m=['', 'Ports not moved because they don\'t exist']),
            dict(l=error_online_l, m=['', 'Online ports that were not moved.']),
            dict(l=error_no_fid_l, m=['', 'Ports not moved because FID doesn\'t exist'])
        ]:
            if len(d['l']) > 0:
                brcdapi_log.log([''] + d['m'] + d['l'], echo=True)

        # Add/Move ports
        state_l.append('Add/Move ports')
        config_errors, config_success = 0, 0
        for to_fid, from_fid_d in switch_port_map_d.items():
            for from_fid, port_l in from_fid_d.items():
                refresh_flag = True
                success_l, fault_l = brcdapi_switch.add_ports(
                    session,
                    to_fid,
                    from_fid,
                    ports=[p for p in port_l if 'ge' not in p.lower()],
                    ge_ports=[p for p in port_l if 'ge' in p.lower()],
                    echo=True
                )
                config_success, config_errors = config_success + len(success_l), config_errors + len(fault_l)
                api_move_fail_l.extend(fault_l)

        # Process alerts
        state_l.append('Process alerts')
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
        state_l.append('Update the Tracker')
        chassis_obj.r_get('tracker_d')['config_success'] += config_success
        chassis_obj.r_get('tracker_d')['config_fail'] += config_errors

        # Update the project object
        if refresh_flag:
            state_l.append('Refresh after port moves')
            proj_obj = _refresh_project(session, chassis_obj.r_project_obj(), desc='Interim step in _configure_chassis')
            chassis_obj = proj_obj.r_chassis_obj(session.get('chassis_wwn'))

        # Configure the switches
        state_l.append('Configure switches')
        for fid, switch_d in chassis_d['switch_d'].items():
            state_l.append('Configuring FID ' + str(fid))
            switch_obj = chassis_obj.r_switch_obj_for_fid(fid)
            if _configure_switch(session, switch_obj, switch_d, force, cli):
                refresh_flag = True

    except BaseException as e:
        buf_l = ['Sheet: ' + str(sheet), 'States Processed']
        buf_l.extend(['  ' + b for b in state_l])
        buf_l.append('refresh_flag: ' + str(refresh_flag))
        buf_l.append('Python error: ' + str(e))
        brcdapi_log.exception(buf_l, echo=True)

    return refresh_flag


_chassis_config_d = dict(  # See brcddb.report.utils._conv_parameters_d for explanation of keys
    cli=_execute_cli,  # CLI
    enable=_chassis_enable_disable,  # Enable/Disable
    chassis_name=_chassis_name,  # Chassis Name
    fcr=_chassis_fcr,  # FCR
    msg_of_day=_chassis_motd,  # Message Of The Day
    shell_to=_change_parameters,  # Shell Timeout
    session_to=_change_parameters,  # Session Timeout
    tcp_to=_change_parameters,  # TCP Timeout Level
    max_rest=_change_parameters,  # Max REST Sessions
    web_tools=_chassis_web_tools,  # Web Tools
    config_switches=_config_logical_switches,  # Configure Switches
)


def _configure_chassis(session, chassis_obj, force, cli):
    """Set chassis parameters, create and configure logical switches, move and configure ports

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param chassis_obj: Chassis object
    :type chassis_obj: brcddb.classes.chassis.ChassisObj
    :param force: True: Perform disabled. False: Do not perform any disable requests.
    :type force: bool
    :param cli: True: Execute all CLI. False: Do not execute any CLI
    :type cli: bool
    :return: The most current project objects
    :rtype: brcddb.classes.project.ProjectObj
    """
    global _chassis_config_d

    # Initialization
    proj_obj = chassis_obj.r_project_obj()
    brcdapi_log.log('Configuring chassis: ' + brcddb_chassis.best_chassis_name(chassis_obj), echo=True)
    chassis_d = chassis_obj.r_get('chassis_d')
    if not isinstance(chassis_d, dict):
        brcdapi_log.exception('Programming error: chassis_obj missing chassis_d. All processing halted.', echo=True)
        raise ForceError

    # Process the Chassis sheet
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
            buf_l = [
                'ERROR: Invalid key: ' + str(d['user_key']) + ' (' + str(d['key']) + ')',
                'Line: ' + str(inspect.currentframe()),
                ]
            brcdapi_log.exception(buf_l, echo=True)
            chassis_obj.r_get('tracker_d')['config_fail'] += 1
        except ForceError:
            return  # The error was already reported.
        except BaseException as e:
            buf_l = ['Programming error encountered. All processing halted.']
            buf_l.extend(_standard_error(chassis_d['sheet'], d['row'], None))
            buf_l.append(str(e))
            brcdapi_log.exception(buf_l, echo=True)

    return proj_obj


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
    global _tracking_template_d

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

    # Login
    brcdapi_log.log('Attempting login', echo=True)
    session = api_int.login(args_d['id'], args_d['pw'], args_d['ip'])
    if fos_auth.is_error(session):  # Errors are sent to the log in api_int.login()
        return brcddb_common.EXIT_STATUS_API_ERROR

    try:
        # Read some basic chassis information
        brcdapi_log.log('Initial data capture', echo=True)
        start_proj_obj = _refresh_project(session, None, desc='Initial data read')
        if start_proj_obj.r_is_any_error():  # Error details are logged in api_int.get_batch()
            return brcddb_common.EXIT_STATUS_API_ERROR
        chassis_obj = start_proj_obj.r_chassis_obj(session.get('chassis_wwn'))

        # Add tracking and the data read from the worksheets to the chassis and switch objects
        chassis_obj.s_new_key('chassis_d', chassis_d)
        chassis_obj.s_new_key('tracker_d', _tracking_template_d.copy())
        for fid, switch_d in chassis_d['switch_d'].items():
            switch_obj = chassis_obj.r_switch_obj_for_fid(fid)
            if switch_obj is not None:
                switch_obj.s_new_key('switch_d', switch_d)
                switch_obj.s_new_key('tracker_d', _tracking_template_d.copy())
        for port, port_d in chassis_d['port_d'].items():
            port_obj = chassis_obj.r_port_obj(port)
            if port_obj is not None:
                port_obj.s_new_key('port_d', port_d)
                port_obj.s_new_key('tracker_d', _tracking_template_d.copy())

        # Make the configuration changes
        proj_obj = _configure_chassis(session, chassis_obj, args_d['force'], args_d['cli'])

        # Enable any ports that need to be enabled.
        reserve_port_l = list()
        for switch_obj in proj_obj.r_switch_objects():
            enable_port_l = list()
            for port_obj in switch_obj.r_port_objects():
                port_d = port_obj.r_get('port_d')
                end_enable = str(port_d.get('end_enable')) if isinstance(port_d, dict) else 'None'
                if end_enable == 'enable':
                    enable_port_l.append(port_obj.r_obj_key())
            # for port_obj in switch_obj.r_port_objects():
            #     port_d = port_obj.r_get('port_d')
            #     if port_obj.r_is_enabled() or not isinstance(port_d, dict) or port_d['end_enable'] != 'enable':
            #         continue
            #     if port_obj.r_is_pod_license():
            #         enable_port_l.append(port_obj.r_obj_key())
            #     else:  # Unreserved ports cannot be enabled
            #         reserve_port_l.append('  ' + port_obj.r_obj_key())
            #         port_obj.r_get('tracker_d')['config_fail'] += 1
            if len(enable_port_l) > 0:
                port_obj = switch_obj.r_port_obj(enable_port_l[0])  # Just for error reporting
                port_d = port_obj.r_get('port_d', dict())
                obj = brcdapi_port.enable_port(session, switch_obj.r_fid(), enable_port_l, persistent=False, best=True)
                _process_api_response(
                    obj,
                    port_obj,
                    port_d.get('sheet', 'Unknown'),
                    port_d.get('row', '?'),
                    'ERROR: Could not enable port'
                )
                port_obj.r_get('tracker_d')['config_fail' if fos_auth.is_error(obj) else 'config_success'] += 1

        # Log any ports that could not be enabled because the port is not reserved.
        if len(reserve_port_l) > 0:
            reserve_port_l.insert(0, 'Could not enable the following ports because the POD has not been reserved')
            brcdapi_log.log(reserve_port_l, echo=True)

        end_proj_obj = _refresh_project(session, start_proj_obj, desc='Final refresh in switch_config.py')

    except ForceError:
        pass  # Error messages are displayed elsewhere when this happens.
    except BaseException as e:
        buf_l = ['ERROR: Programming error encountered:', str(e)]
        brcdapi_log.exception(buf_l, echo=True)

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

    return max(ec_l)


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
