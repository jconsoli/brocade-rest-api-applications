#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020, 2021 Jack Consoli.  All rights reserved.
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
:mod:`switch_config.py` -

**Description**

    Although FOS doesn't care what order the port bind commands are in, humans like to see them in port order. I'm not
    using the brcddb.class objects for anything but since there is a utility to sort the port objects by port number,
    I'm leveraging that to sort the ports. Note that you can't just do a .sort() on the list because it does an ASCII
    sort which isn't how you expect the numerical values in s/p to be sorted.

    Adding the ports to the logical switch in sorted order will also result in the default addresses being in order.
    This is useful if you are not going to force the address by binding specified addresses to the ports. The fabric
    only cares that the port addresses are unique but again, humans like to see everything in order.

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 1.0.0     | 31 Dec 2020   | Initial launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.1     | 09 Jan 2021   | Open log file.                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.2     | 13 Feb 2021   | Added # -*- coding: utf-8 -*-                                                     |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2020, 2021 Jack Consoli'
__date__ = '13 Feb 2021'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '1.0.2'

import argparse
import sys
import datetime
import os
import brcdapi.log as brcdapi_log
import brcdapi.switch as brcdapi_switch
import brcdapi.brcdapi_rest as brcdapi_rest
import brcdapi.pyfos_auth as pyfos_auth
import brcdapi.port as brcdapi_port
import brcdapi.fos_cli as brcdapi_cli
import brcddb.brcddb_common as brcddb_common
import brcddb.report.utils as report_utils
import brcddb.util.util as brcddb_util
import brcddb.api.interface as api_int
import brcddb.brcddb_project as brcddb_project
import brcddb.brcddb_port as brcddb_port
import brcddb.brcddb_switch as brcddb_switch

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = False  # When True, use _DEBUG_xxx instead of passed arguments
_DEBUG_IP = 'xx.x.xxx.xx'
_DEBUG_ID = 'admin'
_DEBUG_PW = 'password'
_DEBUG_SEC = 'self'
_DEBUG_FILE = 'test/G720_FICON_test_r0'
_DEBUG_FORCE = False
_DEBUG_SUPPRESS = False
_DEBUG_ECHO = True
_DEBUG_VERBOSE = False
_DEBUG_LOG = '_logs'
_DEBUG_NL = False


_basic_capture_kpi_l = [
    # 'brocade-fabric/fabric-switch',  Done automatically in brcddb.api.interface._get_chassis()
    'brocade-fibrechannel-switch/fibrechannel-switch',
    'brocade-interface/fibrechannel',
]
_switch_d_to_api = dict(
    did='domain-id',
    switch_name='user-friendly-name',
    fab_name='fabric-user-friendly-name',  # The fabric name is set and read in the switch parameters. IDK why
    banner='banner'
)


def _cli_via_ssh(ip, user_id, pw, fid, cmd_in):
    """Issues CLI commands to the switch.

    Note: As of FOS 9.0.0b, the ability to bind port address was not yet exposed in the API so an SSH session is created
    to issue CLI commands to bind the port addresses.

    :param ip: IP address
    :type ip: str
    :param user_id: User ID
    :type user_id: str
    :param pw: Password
    :type pw: str
    :param fid: Fabric ID
    :type fid: int
    :param cmd_in: List of CLI commands to execute
    :type cmd_in: list, str, None
    :return: Exit code
    :rtype: int
"""
    ec = brcddb_common.EXIT_STATUS_OK
    cmd_l = brcddb_util.convert_to_list(cmd_in)
    if len(cmd_l) == 0:
        return ec

    # Login
    brcdapi_log.log('Attempting SSH login', True)
    el, ssh = brcdapi_cli.login(ip, user_id, pw)
    if len(el) > 0:
        brcdapi_log.log(el, True)
        return brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Send the commands
    # Programmers note: I don't know why setcontext didn't work so I wrapped all the commands in fosexec.
    brcdapi_log.log('Sending CLI commands', True)
    for cmd in ['fosexec --fid ' + str(fid) + ' -cmd "' + buf + '"' for buf in cmd_l]:
        el, ml = brcdapi_cli.send_command(ssh, cmd)
        all_msgs = ml + el
        if len(el) > 0:
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
        brcdapi_log.log(['CLI Send: ' + cmd, 'Response: '] + all_msgs)
        if 'failed' in ''.join(all_msgs).lower():
            brcdapi_log.log('Failed: ' + cmd, True)
            ec = brcddb_common.EXIT_STATUS_ERROR

    # Logout and close the session
    ssh.close()
    brcdapi_log.log('Logout of SSH session')

    return ec


def _ports_to_move(switch_obj, switch_d, force):
    """Determine what ports are where and where they should be moved to and add the following to switch_d

    +-------------------+-------------------------------------------------------------------------------------------|
    | Key               |                                                                                           |
    +===================+===========================================================================================|
    | not_found_ports   | List of ports in s/p notation that should have been added or removed but the port does    |
    |                   | not exist in the chassis.                                                                 |
    +-------------------+-------------------------------------------------------------------------------------------|
    | online_ports      | List of ports in s/p notation that were not moved because they were online                |
    +-------------------+-------------------------------------------------------------------------------------------|
    | remove_ports      | List of ports in s/p notation that need to be removed from the switch                     |
    +-------------------+-------------------------------------------------------------------------------------------|
    | add_ports         | Dictionary: key is from_fid-. Value is dict - key is 'ports' or 'ge_ports', value is list |
    +-------------------+-------------------------------------------------------------------------------------------|

    :param switch_obj: Switch object of the switch being configured
    :type switch_obj: brcddb.classes.switch.SwitchObj
    :param switch_d: Switch object as returned from report_utils.parse_switch_file()
    :type switch_d: dict
    :param force: Move the port whether it's online or not.
    :type force: bool
    """
    switch_d.update(dict(not_found_ports=list(), online_ports=list(), remove_ports=list(), add_ports=dict()))
    chassis_obj = switch_obj.r_chassis_obj()
    switch_pl = switch_obj.r_port_keys()

    for port_type in ('ports', 'ge_ports'):

        if port_type not in switch_d:
            continue

        # Figure out which ports to remove
        for port in [p for p in switch_pl if p not in switch_d[port_type]]:
            port_obj = chassis_obj.r_port_obj(port)
            if port_obj is None:
                switch_d['not_found_ports'].append(port)
            elif not force and port_obj.r_get('fibrechannel/operational-status') is not None and \
                    port_obj.r_get('fibrechannel/operational-status') == 2:
                switch_d['online_ports'].append(brcddb_port.best_port_name(port_obj, True) + ', ' +
                                                brcddb_port.port_best_desc(port_obj))
            else:
                switch_d['remove_ports'].append(port)

        # Figure out what ports to add
        for port in [port for port in switch_d[port_type] if port not in switch_pl]:
            port_obj = chassis_obj.r_port_obj(port)
            if port_obj is None:
                switch_d['not_found_ports'].append(port)
                switch_d['ports'].pop(port)
            elif port_obj.r_get('fibrechannel/operational-status') is not None and \
                    port_obj.r_get('fibrechannel/operational-status') == 2:
                switch_d['online_ports'].append(port)
                switch_d['ports'].pop(port)
            else:
                fid = brcddb_switch.switch_fid(port_obj.r_switch_obj())
                if fid is None:
                    switch_d['not_found_ports'].append(port)  # This should never happen
                    switch_d['ports'].pop(port)
                else:
                    if fid not in switch_d['add_ports']:
                        switch_d['add_ports'].update({fid: dict(ports=list(), ge_ports=list())})
                    switch_d['add_ports'][fid][port_type].append(port)


def _create_switch(session, chassis_obj, switch_d, echo):
    """Creates a logical switch

    :param session: Session object, or list of session objects, returned from brcdapi.pyfos_auth.login()
    :type session: dict
    :param chassis_obj: Chassis object
    :type chassis_obj: brcddb.classes.chassis.ChassisObj
    :param switch_d: Switch object as returned from report_utils.parse_switch_file()
    :type switch_d: dict
    :param echo: If True, echo switch configuration details to STD_OUT
    :type echo: bool
    """
    global _basic_capture_kpi_l

    fid = switch_d['fid']
    buf = 'Creating FID ' + str(fid) + '. This will take about 20 sec per switch + 25 sec per group of 32 ports.'
    brcdapi_log.log(buf, True)
    base = True if switch_d['switch_type'] == 'base' else False
    ficon = True if switch_d['switch_type'] == 'ficon' else False
    obj = brcdapi_switch.create_switch(session, fid, base, ficon, echo)
    if pyfos_auth.is_error(obj):
        switch_d['err_msgs'].append('Error creating FID ' + str(fid))
        brcdapi_log.log([switch_d['err_msgs'][len(switch_d['err_msgs']) - 1], pyfos_auth.formatted_error_msg(obj)],
                        True)
        return brcddb_common.EXIT_STATUS_ERROR

    # re-read the chassis and logical switch data to pick up the switch we just created.
    session.pop('chassis_wwn', None)
    api_int.get_batch(session, chassis_obj.r_project_obj(), _basic_capture_kpi_l, None)
    return chassis_obj.r_switch_obj_for_fid(fid)


def _config_fab_and_switch(session, switch_d, echo):
    """Add and remove ports from a logical switch

    :param session: Session object, or list of session objects, returned from brcdapi.pyfos_auth.login()
    :type session: dict
    :param switch_d: Switch object as returned from report_utils.parse_switch_file()
    :type switch_d: dict
    :param echo: If True, echo switch configuration details to STD_OUT
    :type echo: bool
    """
    global _switch_d_to_api

    # Load common use stuff into local variables
    ec = brcddb_common.EXIT_STATUS_OK
    fid = switch_d['fid']
    idid = False if switch_d['switch_type'] == 'ficon' else switch_d['idid']

    # Set switch configuration parameters.
    sub_content = dict()
    for k, v in _switch_d_to_api.items():
        if switch_d[k] is not None:
            sub_content.update({v: switch_d[k]})
    if switch_d['switch_type'] == 'ficon':
        sub_content.update({'in-order-delivery-enabled': True, 'dynamic-load-sharing': 'two-hop-lossless-dls'})

    # Send the changes.
    obj = brcdapi_switch.fibrechannel_switch(session, fid, sub_content, None, echo)
    if pyfos_auth.is_error(obj):
        # in-order-delivery-enabled and dynamic-load-sharing not supported in pre-FOS 9.0 so just try it again
        sub_content.pop('in-order-delivery-enabled', None)
        sub_content.pop('dynamic-load-sharing', None)
        obj = brcdapi_switch.fibrechannel_switch(session, fid, sub_content, None, echo)
        if pyfos_auth.is_error(obj):
            brcdapi_log.log(['Failed to configure FID ' + str(fid), pyfos_auth.formatted_error_msg(obj)], True)
            ec = brcddb_common.EXIT_STATUS_API_ERROR
        else:
            switch_d['err_msgs'].append('Failed to set in order delivery and dynamic load sharing')
            buf = 'In order delivery and dynamic load sharing not supported via the API in this version of FOS. '\
                  'Remember to set these parameters manually.'
            brcdapi_log.log(buf, True)

    # Set the fabric parameters.
    # XISL (ability to use the base switch for ISLs) is enabled by default so we only need to disable it
    if not switch_d['xisl']:
        obj = brcdapi_rest.send_request(session,
                                        'brocade-fibrechannel-configuration/switch-configuration',
                                        'PATCH',
                                        {'switch-configuration': {'xisl-enabled': False}},
                                        fid)
        if pyfos_auth.is_error(obj):
            switch_d['err_msgs'].append('Failed to disable XISL')
            ml = ['Failed to disable XISL for FID ' + str(fid),
                  pyfos_auth.formatted_error_msg(obj),
                  'Enabling and disabling of XISLs via the API was not supported until FOS v9.0.',
                  'Unless there are other error messages, all other operations are or will be completed as expected.']
            brcdapi_log.log(ml, True)
            ec = brcddb_common.EXIT_STATUS_API_ERROR

    if idid:
        obj = brcdapi_rest.send_request(session,
                                        'brocade-fibrechannel-configuration/fabric',
                                        'PATCH',
                                        {'fabric': {'insistent-domain-id-enabled': True}},
                                        fid)
        if pyfos_auth.is_error(obj):
            switch_d['err_msgs'].append('Failed to set insistent domain id')
            brcdapi_log.log(['Failed to set insistent domain id for FID ' + str(fid),
                             pyfos_auth.formatted_error_msg(obj)], True)
            ec = brcddb_common.EXIT_STATUS_API_ERROR

    return ec


def _add_remove_ports(session, switch_obj, switch_d, force, echo):
    """Add and remove ports from a logical switch

    :param session: Session object, or list of session objects, returned from brcdapi.pyfos_auth.login()
    :type session: dict
    :param switch_obj: Chassis object
    :type switch_obj: brcddb.classes.switch.SwitchObj
    :param switch_d: Switch object as returned from report_utils.parse_switch_file()
    :type switch_d: dict
    :param force: Move the port whether it's online or not.
    :type force: bool
    :param echo: If True, echo switch configuration details to STD_OUT
    :type echo: bool
    """
    # Load common use stuff into local variables
    ec = brcddb_common.EXIT_STATUS_OK
    chassis_obj = switch_obj.r_chassis_obj()
    fid = switch_d['fid']

    # Figure out what ports to add or remove
    _ports_to_move(switch_obj, switch_d, force)

    # Report any ports that could not be moved.
    ml = list()
    for d in [dict(port_l=switch_d['not_found_ports'], m='were not found:'),
              dict(port_l=switch_d['online_ports'], m='are online:')]:
        if len(d['port_l']) > 0:
            ml.append('The following ports were not moved because they ' + d['m'])
            for port in brcddb_util.sp_port_sort(d['port_l']):
                port_obj = chassis_obj.r_port_obj(port)
                if port_obj is not None:
                    ml.append(brcddb_port.best_port_name(port_obj, True) + ', ' + brcddb_port.port_best_desc(port_obj))
                else:
                    ml.append(port)
            ec = brcddb_common.EXIT_STATUS_ERROR
    if len(ml) > 0:
        brcdapi_log.log(ml, True)
    default_fid = chassis_obj.r_default_switch_fid()

    # $ToDo brcdapi_switch.add_ports doesn't remove GE ports
    # Remove ports
    obj = brcdapi_switch.add_ports(session, default_fid, fid, switch_d['remove_ports'], None, echo)
    if pyfos_auth.is_error(obj):
        ml = ['Error moving ports from FID ' + str('fid') + ' to ' + str(default_fid),
              pyfos_auth.formatted_error_msg(obj)]
        brcdapi_log.log(ml, True)
        ec = brcddb_common.EXIT_STATUS_ERROR

    # Add ports
    for from_fid, port_d in switch_d['add_ports'].items():
        obj = brcdapi_switch.add_ports(session, fid, from_fid, port_d['ports'], port_d['ge_ports'], echo)
        if pyfos_auth.is_error(obj):
            ml = ['Error moving ports from FID ' + from_fid + ' to ' + str(fid),
                  pyfos_auth.formatted_error_msg(obj)]
            brcdapi_log.log(ml, True)
            ec = brcddb_common.EXIT_STATUS_ERROR

    return ec


def _enable_switch(session, fid, echo):
    """Enable switch

    :param session: Session object returned from brcdapi.pyfos_auth.login()
    :type session: dict
    :param fid: Fabric ID
    :type fid: int
    :param echo: If True, echo switch configuration details to STD_OUT
    :type echo: bool
    """
    obj = brcdapi_switch.fibrechannel_switch(session, fid, {'is-enabled-state': True}, None, echo)
    if pyfos_auth.is_error(obj):
        brcdapi_log.log(['Failed to enable FID ' + str(fid), pyfos_auth.formatted_error_msg(obj)], True)
        return brcddb_common.EXIT_STATUS_API_ERROR

    return brcddb_common.EXIT_STATUS_OK


def _enable_ports(session, fid, port_l, echo):
    """Enable ports

    :param session: Session object returned from brcdapi.pyfos_auth.login()
    :type session: dict
    :param fid: Fabric ID
    :type fid: int
    :param port_l: Ports in s/p notation to enable
    :type port_l: list
    :param echo: If True, echo switch configuration details to STD_OUT
    :type echo: bool
    """
    if len(port_l) > 0:
        obj = brcdapi_port.enable_port(session, fid, True, port_l, echo)
        if pyfos_auth.is_error(obj):
            brcdapi_log.log(['Failed to enable ports on FID ' + str(fid), pyfos_auth.formatted_error_msg(obj)], True)
            return brcddb_common.EXIT_STATUS_API_ERROR

    return brcddb_common.EXIT_STATUS_OK


def _configure_switch(user_id, pw, session, proj_obj, switch_d, force, echo):
    """Configure, create if necessary, a logical switch

    :param user_id: User ID. Only used if switch_d['bind_commands'] is a list of len > 0
    :type user_id: str, None
    :param pw: Login password. Only used if switch_d['bind_commands'] is a list of len > 0
    :type pw: str
    :param session: Session object, or list of session objects, returned from brcdapi.pyfos_auth.login()
    :type session: dict
    :param proj_obj: Project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :param switch_d: Switch object as returned from report_utils.parse_switch_file()
    :type switch_d: dict
    :param force: Move the port whether it's online or not.
    :type force: bool
    :param echo: If True, echo switch configuration details to STD_OUT
    :type echo: bool
    """
    global _basic_capture_kpi_l

    r_status = [brcddb_common.EXIT_STATUS_OK]

    # Get some basic switch information for the chassis
    api_int.get_batch(session, proj_obj, _basic_capture_kpi_l, None)
    if proj_obj.r_is_any_error():
        switch_d['err_msgs'].append('Error reading logical switch information from chassis')
        brcdapi_log.log(switch_d['err_msgs'][len(switch_d['err_msgs'])-1], True)
        return brcddb_common.EXIT_STATUS_ERROR

    # See if the FID already exists. If not, create the switch
    fid = switch_d['fid']
    chassis_obj = proj_obj.r_chassis_obj(session.get('chassis_wwn'))
    if chassis_obj is None:
        switch_d['err_msgs'].append('Error reading logical switch information from chassis')
        brcdapi_log.exception(switch_d['err_msgs'][len(switch_d['err_msgs'])-1], True)
        return brcddb_common.EXIT_STATUS_ERROR
    switch_obj = chassis_obj.r_switch_obj_for_fid(fid)
    if switch_obj is None:
        switch_obj = _create_switch(session, chassis_obj, switch_d, echo)
        if switch_obj is None:
            switch_d['err_msgs'].append('Could not read switch data for FID ' + str(fid))
            brcdapi_log.log(switch_d['err_msgs'][len(switch_d['err_msgs']) - 1], True)
            return brcddb_common.EXIT_STATUS_ERROR
        switch_d.update(dict(created=True))
    else:
        switch_d.update(dict(created=False))
    switch_d.update(dict(switch_obj=switch_obj))

    # Configure switch and fabric parameters
    ec = _config_fab_and_switch(session, switch_d, echo)
    r_status.append(ec)
    if ec != brcddb_common.EXIT_STATUS_OK:
        switch_d['err_msgs'].append('Failed to configure all switch parameters. Check the log for details')

    # Add/remove ports
    ec = _add_remove_ports(session, switch_obj, switch_d, force, echo)
    r_status.append(ec)
    if ec != brcddb_common.EXIT_STATUS_OK:
        switch_d['err_msgs'].append('Failed to move all ports. Check the log for details')

    # Bind addresses
    if switch_d['bind']:
        ec = _cli_via_ssh(session['ip_addr'], user_id, pw, fid, switch_d.get('bind_commands'))
        r_status.append(ec)
        if ec != brcddb_common.EXIT_STATUS_OK:
            switch_d['err_msgs'].append('Failed to bind all addresses. Check the log for details')

    # Enable switch
    if switch_d['enable_switch']:
        ec = _enable_switch(session, fid, echo)
        r_status.append(ec)
        if ec != brcddb_common.EXIT_STATUS_OK:
            switch_d['err_msgs'].append('Failed to enable switch. Check the log for details')

    # Enable and ports
    if switch_d['enable_ports']:
        ec = _enable_ports(session, fid, switch_d['ports'].keys(), echo)
        r_status.append(ec)
        if ec != brcddb_common.EXIT_STATUS_OK:
            switch_d['err_msgs'].append('Failed to enable all ports. Check the log for details')

    # Pick the first non-OK error code to return
    ec = brcddb_common.EXIT_STATUS_OK
    for ec in r_status:
        if ec != brcddb_common.EXIT_STATUS_OK:
            break
    return ec


def _bind_commands(switch_d):
    """Add a list of CLI commands to bind the ports associated with a switch to switch_d

    :param switch_d: Switch object as returned from report_utils.parse_switch_file()
    :type switch_d: dict
    :return: List of CLI commands to bind the addresses
    :rtype: list
    """
    port_l = brcddb_util.sp_port_sort(switch_d['ports'].keys())  # See module description for why a sorted list
    bl = ['portaddress --bind ' + port + ' ' + switch_d['ports'][port]['port_addr'].upper() + '00' for port in port_l
          if 'port_addr' in switch_d['ports'][port]]
    switch_d.update(dict(bind_commands=[buf.replace('0/', '') if '10/' not in buf else buf for buf in bl]))


def _print_summary(switch_d_list):
    """Enable switch

    :param switch_d_list: List of switch dictionaries
    :type switch_d_list: list
    """
    ml = ['\nSummary', '_______']
    for switch_d in switch_d_list:
        ml.append('\nFID: ' + str(switch_d.get('fid')))
        ml.append('  Switch Name:            ' + brcddb_switch.best_switch_name(switch_d.get('switch_obj'), True))
        ml.append('  Switch Created:         ' + str(switch_d.get('created')))
        try:
            ml.append('  Ports Added:            ' + str(len(switch_d['ports'].keys())))
            ml.append('  Ports Removed:          ' + str(len(switch_d['remove_ports'])))
            ml.append('  Online Ports Not Moved: ' + str(len(switch_d['online_ports'])))
            ml.append('  Ports Not Found:        ' + str(len(switch_d['not_found_ports'])))
        except:
            pass  # We should never get here but I'm not changing working code.
        err_msgs = brcddb_util.convert_to_list(switch_d.get('err_msgs'))
        if len(err_msgs) > 0:
            ml.append('  Error Messages:         ')
            ml.extend(['    ' + buf for buf in err_msgs])
    brcdapi_log.log(ml, True)


def parse_args():
    """Parses the module load command line

    :return ip: Switch IP address
    :rtype ip: str
    :return out_file: Name of output file
    :rtype out_file: str
    :return s_flag: Suppress flag
    :rtype s_flag: bool
    """
    global _DEBUG_IP, _DEBUG_ID, _DEBUG_PW, _DEBUG_SEC, _DEBUG_FILE, _DEBUG_FORCE, _DEBUG_SUPPRESS, _DEBUG_ECHO,\
        _DEBUG_VERBOSE, _DEBUG_LOG, _DEBUG_NL

    if _DEBUG:
        return _DEBUG_IP, _DEBUG_ID, _DEBUG_PW, _DEBUG_SEC, _DEBUG_FILE, _DEBUG_FORCE, _DEBUG_SUPPRESS, _DEBUG_ECHO,\
               _DEBUG_VERBOSE, _DEBUG_LOG, _DEBUG_NL
    buf = 'Reads a X6-8_Slot_48_FICON_Config Excel Workbook and configures each switch accordingly. Use ficon_zone.py '\
          'to configure the zoning. If the IP address, -ip, is specified, the script will attempt to login and make '\
          'the changes. Otherwise, only CLI commands are generated.'
    parser = argparse.ArgumentParser(description=buf)
    parser.add_argument('-ip', help='(Optional) IP address', required=False)
    parser.add_argument('-id', help='(Optional) User ID', required=False)
    parser.add_argument('-pw', help='(Optional) Password', required=False)
    buf = '(Optional) \'CA\' or \'self\' for HTTPS mode. HTTP is used when not specified.'
    parser.add_argument('-s', help=buf, required=False,)
    parser.add_argument('-i', help='(Required) File name of Excel Workbook to read.', required=True)
    buf = '(Optional) No parameters. If specified, move ports even if they are online'
    parser.add_argument('-force', help=buf, action='store_true', required=False)
    buf = '(Optional) Suppress all library generated output to STD_IO except the exit code. Useful with batch ' \
          'processing'
    parser.add_argument('-sup', help=buf, action='store_true', required=False)
    buf = '(Optional) Echoes activity detail to STD_OUT. Recommended because there are multiple operations that ' \
          'can be very time consuming.'
    parser.add_argument('-echo', help=buf, action='store_true', required=False)
    parser.add_argument('-d', help='Enable debug logging', action='store_true', required=False)
    buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The log '\
          'file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
    parser.add_argument('-log', help=buf, required=False,)
    buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
    parser.add_argument('-nl', help=buf, action='store_true', required=False)
    args = parser.parse_args()
    return args.ip, args.id, args.pw, args.s, args.i, args.force, args.sup, args.echo, args.d, args.log, args.nl


def pseudo_main():
    """Basically the main().

    :return: Exit code
    :rtype: int
    """
    global _DEBUG

    # Get and validate command line input.
    ec = brcddb_common.EXIT_STATUS_OK
    ml = list()
    ip, user_id, pw, sec, file, force, s_flag, echo, vd, log, nl = parse_args()
    if vd:
        brcdapi_rest.verbose_debug = True
    if s_flag:
        brcdapi_log.set_suppress_all()
    if not nl:
        brcdapi_log.open_log(log)
    if sec is None:
        sec = 'none'
    if len(file) < len('.xlsx') or file[len(file)-len('.xlsx'):] != '.xlsx':
        file += '.xlsx'  # Add the .xlsx extension to the Workbook if it wasn't specified on the command line
    if ip is not None:
        if user_id is None:
            ml.append('  -user_id')
        if pw is None:
            ml.append('  -pw')
        if len(ml) > 0:
            ml.insert(0, 'The following parameters are required when an IP address is specified:')
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    if _DEBUG:
        ml.insert(0, 'WARNING!!! Debug is enabled')
    if len(ml) > 0:
        brcdapi_log.log(ml, True)
    if ec != brcddb_common.EXIT_STATUS_OK:
        return ec
    echo = False if echo is None else echo

    # Read in the Workbook, generate the portaddress --bind commands, and configure the switch(es)
    switch_d_list = [switch_d for switch_d in report_utils.parse_switch_file(file).values()]
    proj_obj = None
    session = None
    try:
        for switch_d in switch_d_list:
            switch_d.update(dict(err_msgs=list()))

            # Create the bind commands
            _bind_commands(switch_d)
            cli_l = switch_d['bind_commands'].copy()
            i = 0
            while i < len(cli_l):
                cli_l.insert(i, '')
                i += 16
            cli_l.insert(0, '\n# Bind commands for FID ' + str(switch_d['fid']))
            cli_l.append('\n# End bind commands for FID ' + str(switch_d['fid']))
            brcdapi_log.log(cli_l, True)

            # Create the logical switch
            if ip is not None and switch_d['switch_flag']:

                if session is None:  # Login
                    session = api_int.login(user_id, pw, ip, sec, proj_obj)
                    if pyfos_auth.is_error(session):
                        return brcddb_common.EXIT_STATUS_API_ERROR

                if proj_obj is None:  # Create a project object
                    proj_obj = brcddb_project.new('Create_LS', datetime.datetime.now().strftime('%d %b %Y %H:%M:%S'))
                    proj_obj.s_python_version(sys.version)
                    proj_obj.s_description('Creating logical switches from ' + os.path.basename(__file__))

                ec = _configure_switch(user_id, pw, session, proj_obj, switch_d, force, echo)

    except:
        switch_d['err_msgs'].append('Programming error encountered.')
        brcdapi_log.log(switch_d['err_msgs'][len(switch_d['err_msgs']) - 1], True)
        ec = brcddb_common.EXIT_STATUS_ERROR

    # Logout and create and print a summary report
    if session is not None:
        obj = brcdapi_rest.logout(session)
        if pyfos_auth.is_error(obj):
            brcdapi_log.log(pyfos_auth.formatted_error_msg(obj), True)
            ec = brcddb_common.EXIT_STATUS_API_ERROR
    if ip is not None:
        _print_summary(switch_d_list)

    return ec


###################################################################
#
#                    Main Entry Point
#
###################################################################
_ec = brcddb_common.EXIT_STATUS_OK
if _DOC_STRING:
    print('_DOC_STRING is True. No processing')
else:
    _ec = pseudo_main()
    brcdapi_log.close_log('\nProcessing Complete. Exit code: ' + str(_ec), True)
exit(_ec)
