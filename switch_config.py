#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020, 2021, 2022 Jack Consoli.  All rights reserved.
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

$ToDo running/brocade-fibrechannel-switch/fibrechannel-switch/principal (0 for no, 1 for yes)

To set it:

PATCH running/brocade-fibrechannel-configuration/fabric

principal-selection-enabled - boolean
principal-priority - hex value. See options for fabricprincipal -priority

Look for insistent-domain-id-enabled

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
    | 1.0.3     | 16 Nov 2021   | Fixed call to brcdapi.port.enable_ports()                                         |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.4     | 31 Dec 2021   | Use brcddb.util.file.full_file_name()                                             |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.5     | 28 Apr 2022   | Used full URI                                                                     |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.6     | 26 May 2022   | Disabled debug mode (_DEBUG)                                                      |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.7     | 22 Jun 2022   | Replaced CLI port address binding with API based port address binding introduced  |
    |           |               | in FOS 9.1.                                                                       |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.8     | 25 Jul 2022   | Added module version number to output.                                            |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.9     | 14 Oct 2022   | Fixed case when there is no chassis configuration worksheet.                      |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2020, 2021, 2022 Jack Consoli'
__date__ = '14 Oct 2022'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '1.0.9'

import argparse
import sys
import datetime
import os
import brcdapi.log as brcdapi_log
import brcdapi.switch as brcdapi_switch
import brcdapi.brcdapi_rest as brcdapi_rest
import brcdapi.fos_auth as fos_auth
import brcdapi.port as brcdapi_port
import brcdapi.util as brcdapi_util
import brcdapi.file as brcdapi_file
import brcdapi.gen_util as gen_util
import brcddb.brcddb_common as brcddb_common
import brcddb.report.utils as report_utils
import brcddb.util.util as brcddb_util
import brcddb.api.interface as api_int
import brcddb.brcddb_project as brcddb_project
import brcddb.brcddb_port as brcddb_port
import brcddb.brcddb_switch as brcddb_switch

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = False  # When True, use _DEBUG_xxx instead of passed arguments
_DEBUG_ip = '10.155.2.69'
_DEBUG_id = 'admin'
_DEBUG_pw = 'Pass@word1!'
_DEBUG_sec = 'self'
_DEBUG_i = 'config/sac_test'
_DEBUG_force = False
_DEBUG_sup = False
_DEBUG_echo = True
_DEBUG_d = False
_DEBUG_log = '_logs'
_DEBUG_nl = False

_basic_capture_kpi_l = [
    # 'running/brocade-fabric/fabric-switch',  Done automatically in brcddb.api.interface.get_chassis()
    'running/brocade-fibrechannel-switch/fibrechannel-switch',
    'running/brocade-interface/fibrechannel',
]
_switch_d_bfs_fs_to_api = dict(  # Conversion table for brocade-fibrechannel-switch/fibrechannel-switch
    did='domain-id',
    switch_name='user-friendly-name',
    fab_name='fabric-user-friendly-name',  # The fabric name is set and read in the switch parameters. IDK why
    banner='banner',
)
_switch_d_bfc_fab_to_api = dict(  # Conversion table for brocade-fibrechannel-configuration/fabric
    idid='insistent-domain-id-enabled',
    p_fab_enable='principal-selection-enabled',
    p_fab_priority='principal-priority',
)
_switch_d_bfc_sw_config_to_api = dict(  # Conversion table for brocade-fibrechannel-configuration/switch-configuration
    xisl='xisl-enabled',
)
# Below is used in _configure_ports. I did it this way so that additional parameters can easily be added in the future.
_config_ports_d = dict(port_name='user-friendly-name')


def _configure_chassis(session, chassis_d):
    """Configure, create if necessary, a logical switch

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param chassis_d: Switch object as returned from report_utils.parse_switch_file()
    :type chassis_d: dict
    :return: Completion code - see brcddb.common
    :rtype: int
    """
    if chassis_d is None:
        return brcddb_common.EXIT_STATUS_OK  # No chassis level changes to make
    for kpi, content in chassis_d.items():
        tl = kpi.split('/')
        content_d = {tl[len(tl)-1]: content} if tl[0] == 'running' else content
        obj = brcdapi_rest.send_request(session, kpi, 'PATCH', content_d)
        if fos_auth.is_error(obj):
            brcdapi_log.exception(['Error processing ' + kpi + 'Error is: ', fos_auth.formatted_error_msg(obj)],
                                  echo=True)
            return brcddb_common.EXIT_STATUS_API_ERROR

    return brcddb_common.EXIT_STATUS_OK


def _configure_ports(session, fid, port_d, enable_flag):
    """Configure ports with running/brocade-interface/fibrechannel

    :param session: Session object returned from brcdapi.fos_auth.login()
    :type session: dict
    :param fid: Logical FID number for switch with ports. Use None if switch is not VF enabled.
    :type fid: int
    :param port_d: Port dictionary as returned from brcddb.report.utils.parse_switch_file()
    :type port_d: dict
    :param enable_flag: If True, enable all ports
    :type enable_flag: bool
    """
    global _config_ports_d

    # Figure out which ports need to be configured
    ec, content_l = brcddb_common.EXIT_STATUS_OK, list()
    for port, val_d in port_d.items():
        d = {'name': port, 'is-enabled-state': True} if enable_flag else dict(name=port)
        for k, v in _config_ports_d.items():
            buf = val_d.get(k)
            if buf is not None:
                d.update({v: buf})
        if len(d) > 1:
            content_l.append(d)

    # Update port configurations on the switch
    if len(content_l) > 0:
        obj = brcdapi_rest.send_request(session,
                                         'running/brocade-interface/fibrechannel',
                                         'PATCH',
                                         {'fibrechannel': content_l},
                                         fid)
        if fos_auth.is_error(obj):
            brcdapi_log.exception(['Error configuring ports for FID ' + str(fid), fos_auth.formatted_error_msg(obj)],
                                  True)
            ec = brcddb_common.EXIT_STATUS_API_ERROR

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
    switch_d.update(not_found_ports=list(), online_ports=list(), remove_ports=list(), add_ports=dict())
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

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
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
    brcdapi_log.log(buf, echo=True)
    base = True if switch_d['switch_type'] == 'base' else False
    ficon = True if switch_d['switch_type'] == 'ficon' else False
    obj = brcdapi_switch.create_switch(session, fid, base, ficon, echo=echo)
    if fos_auth.is_error(obj):
        switch_d['err_msgs'].append('Error creating FID ' + str(fid))
        brcdapi_log.exception([switch_d['err_msgs'][len(switch_d['err_msgs']) - 1], fos_auth.formatted_error_msg(obj)],
                        True)
        return brcddb_common.EXIT_STATUS_ERROR

    # re-read the chassis and logical switch data to pick up the switch we just created.
    session.pop('chassis_wwn', None)
    api_int.get_batch(session, chassis_obj.r_project_obj(), _basic_capture_kpi_l, None)
    return chassis_obj.r_switch_obj_for_fid(fid)


def _config_fab_and_switch(session, switch_d, echo):
    """Add and remove ports from a logical switch

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param switch_d: Switch object as returned from report_utils.parse_switch_file()
    :type switch_d: dict
    :param echo: If True, echo switch configuration details to STD_OUT
    :type echo: bool
    """
    global _switch_d_bfs_fs_to_api, _switch_d_bfc_fab_to_api, _switch_d_bfc_sw_config_to_api

    # Load common use stuff into local variables
    ec = brcddb_common.EXIT_STATUS_OK
    fid = switch_d['fid']
    idid = False if switch_d['switch_type'] == 'ficon' else switch_d['idid']

    # Set switch configuration parameters for brocade-fibrechannel-switch/fibrechannel-switch.
    sub_content = dict()
    for k, v in _switch_d_bfs_fs_to_api.items():
        v_buf = switch_d[k]
        if v_buf is not None:
            if k == 'banner':
                v_buf = gen_util.valid_banner.sub('-', v_buf)
                if switch_d[k] != switch_d[k]:
                    buf = 'Invalid characters in banner for FID ' + str(fid) + '. Replaced invalid characters with "-"'
                    switch_d['err_msgs'].append(buf)
                    brcdapi_log.log(buf, echo=True)
            sub_content.update({v: v_buf})
    if switch_d['switch_type'] == 'ficon':
        sub_content.update({'in-order-delivery-enabled': True, 'dynamic-load-sharing': 'two-hop-lossless-dls'})

    # Send the changes for brocade-fibrechannel-switch/fibrechannel-switch.
    obj = brcdapi_switch.fibrechannel_switch(session, fid, sub_content, None, echo)
    if fos_auth.is_error(obj):
        # in-order-delivery-enabled and dynamic-load-sharing not supported in pre-FOS 9.0 so just try it again
        if 'in-order-delivery-enabled' in sub_content or 'dynamic-load-sharing' in sub_content:
            sub_content.pop('in-order-delivery-enabled', None)
            sub_content.pop('dynamic-load-sharing', None)
            obj = brcdapi_switch.fibrechannel_switch(session, fid, sub_content, None, echo)
            if fos_auth.is_error(obj):
                brcdapi_log.exception(['Failed to configure FID ' + str(fid), fos_auth.formatted_error_msg(obj)],
                                      echo=True)
                ec = brcddb_common.EXIT_STATUS_API_ERROR
            else:
                buf = 'Setting "in-order-delivery-enabled" and "dynamic-load-sharing" not supported in this FOS '\
                      'version. These features must be set manually.'
                brcdapi_log.log(buf)
        else:
            ml = ['Failed to set all switch parameters. Error from FOS is:', fos_auth.formatted_error_msg(obj)]
            switch_d['err_msgs'].extend(ml)
            brcdapi_log.log(ml, echo=True)

    # Set the fabric parameters: brocade-fibrechannel-configuration/switch-configuration
    # Allow XISL is enabled by default. If the switch already exists and someone is trying to enable it, there is no
    # logic below to check for the current state. Some API calls return an error if something is being set to the same
    # state. As a future, I should check to see if that's the case here and if so, check to current setting.
    if not switch_d['xisl']:
        obj = brcdapi_rest.send_request(session,
                                        'running/brocade-fibrechannel-configuration/switch-configuration',
                                        'PATCH',
                                        {'switch-configuration': {_switch_d_bfc_sw_config_to_api['xisl']: False}},
                                        fid)
        if fos_auth.is_error(obj):
            switch_d['err_msgs'].append('Failed to disable XISL')
            ml = ['Failed to disable XISL for FID ' + str(fid),
                  fos_auth.formatted_error_msg(obj),
                  'Enabling and disabling of XISLs via the API was not supported until FOS v9.0.',
                  'Unless there are other error messages, all other operations are or will be completed as expected.']
            brcdapi_log.exception(ml, echo=True)
            ec = brcddb_common.EXIT_STATUS_API_ERROR

    # Build running/brocade-fibrechannel-configuration/fabric
    sub_content_d = dict()
    if idid:
        sub_content_d.update({_switch_d_bfc_fab_to_api['idid']: True})
    if switch_d.get('p_fab_enable') is not None and switch_d['p_fab_enable']:
        sub_content_d.update({_switch_d_bfc_fab_to_api['p_fab_enable']: True,
                              _switch_d_bfc_fab_to_api['p_fab_priority']: switch_d.get('p_fab_priority')})
    if len(sub_content_d) > 0:
        obj = brcdapi_rest.send_request(session,
                                        'running/brocade-fibrechannel-configuration/fabric',
                                        'PATCH',
                                        {'fabric': sub_content_d},
                                        fid)
        if fos_auth.is_error(obj):
            switch_d['err_msgs'].append('Failed to set insistent domain id')
            brcdapi_log.exception(['Failed to set insistent domain id for FID ' + str(fid),
                             fos_auth.formatted_error_msg(obj)], echo=True)
            ec = brcddb_common.EXIT_STATUS_API_ERROR

    return ec


def _add_remove_ports(session, switch_obj, switch_d, force, echo):
    """Add and remove ports from a logical switch

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param switch_obj: Chassis object
    :type switch_obj: brcddb.classes.switch.SwitchObj
    :param switch_d: Switch object as returned from report_utils.parse_switch_file()
    :type switch_d: dict
    :param force: Move the port whether it's online or not.
    :type force: bool
    :param echo: If True, echo switch configuration details to STD_OUT
    :type echo: bool
    :return: Ending status. See brcddb.common
    :rtype: int
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
        brcdapi_log.log(ml, echo=True)
    default_fid = chassis_obj.r_default_switch_fid()

    # Remove ports - $ToDo brcdapi_switch.add_ports doesn't remove GE ports
    obj = brcdapi_switch.add_ports(session, default_fid, fid, switch_d['remove_ports'], None, echo)
    if fos_auth.is_error(obj):
        ml = ['Error moving ports from FID ' + str('fid') + ' to ' + str(default_fid),
              fos_auth.formatted_error_msg(obj)]
        brcdapi_log.exception(ml, echo=True)
        ec = brcddb_common.EXIT_STATUS_ERROR

    # Add ports
    for from_fid, port_d in switch_d['add_ports'].items():
        obj = brcdapi_switch.add_ports(session, fid, from_fid, port_d['ports'], port_d['ge_ports'], echo)
        if fos_auth.is_error(obj):
            ml = ['Error moving ports from FID ' + from_fid + ' to ' + str(fid),
                  fos_auth.formatted_error_msg(obj)]
            brcdapi_log.exception(ml, echo=True)
            ec = brcddb_common.EXIT_STATUS_ERROR

    return ec


def _bind_address_to_port(session, switch_obj, switch_d, force, echo):
    """Binds the addresses to the port

    WARNING: force has not yet been implemented. The assumption is that the port is disabled.

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param switch_obj: Chassis object
    :type switch_obj: brcddb.classes.switch.SwitchObj
    :param switch_d: Switch object as returned from report_utils.parse_switch_file()
    :type switch_d: dict
    :param force: Disable the port and bind the address regardless of the state of port binding or other port state.
    :type force: bool
    :param echo: If True, echo switch configuration details to STD_OUT
    :type echo: bool
    :return: Ending status. See brcddb.common
    :rtype: int
    """
    port_d = dict()
    for port_num, d in switch_d['ports'].items():
        port_d.update({port_num: '0x' + d['port_addr'] + '00'})
    if len(port_d) > 0:
        obj = brcdapi_switch.bind_addresses(session, brcddb_switch.switch_fid(switch_obj), port_d, echo)
        if fos_auth.is_error(obj):
            ml = ['Errors encountered binding port address for FID ' + str(brcddb_switch.switch_fid(switch_obj)),
                  fos_auth.formatted_error_msg(obj)]
            brcdapi_log.exception(ml, echo=True)
            return brcddb_common.EXIT_STATUS_ERROR

    return brcddb_common.EXIT_STATUS_OK


def _enable_switch(session, fid, echo):
    """Enable switch

    :param session: Session object returned from brcdapi.fos_auth.login()
    :type session: dict
    :param fid: Fabric ID
    :type fid: int
    :param echo: If True, echo switch configuration details to STD_OUT
    :type echo: bool
    """
    obj = brcdapi_switch.fibrechannel_switch(session, fid, {'is-enabled-state': True}, None, echo)
    if fos_auth.is_error(obj):
        brcdapi_log.exception(['Failed to enable FID ' + str(fid), fos_auth.formatted_error_msg(obj)], echo=True)
        return brcddb_common.EXIT_STATUS_API_ERROR

    return brcddb_common.EXIT_STATUS_OK


def _enable_ports(session, fid, port_l, echo):
    """Enable ports

    :param session: Session object returned from brcdapi.fos_auth.login()
    :type session: dict
    :param fid: Fabric ID
    :type fid: int
    :param port_l: Ports in s/p notation to enable
    :type port_l: list
    :param echo: If True, echo switch configuration details to STD_OUT
    :type echo: bool
    """
    if len(port_l) > 0:
        obj = brcdapi_port.enable_port(session, fid, port_l, echo)
        if fos_auth.is_error(obj):
            brcdapi_log.exception(['Failed to enable ports on FID ' + str(fid), fos_auth.formatted_error_msg(obj)],
                                  True)
            return brcddb_common.EXIT_STATUS_API_ERROR

    return brcddb_common.EXIT_STATUS_OK


def _configure_switch(session, proj_obj, switch_d, force, echo):
    """Configure, create if necessary, a logical switch

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param proj_obj: Project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :param switch_d: Switch object as returned from report_utils.parse_switch_file()
    :type switch_d: dict
    :param force: Move the port whether it's online or not.
    :type force: bool
    :param echo: If True, echo switch configuration details to STD_OUT
    :type echo: bool
    :return: Error code - see brcddb.common
    :rtype: int
    """
    global _basic_capture_kpi_l

    r_status = [brcddb_common.EXIT_STATUS_OK]

    # See if the FID already exists. If not, create the switch
    fid = switch_d['fid']
    chassis_obj = proj_obj.r_chassis_obj(session.get('chassis_wwn'))
    if chassis_obj is None:
        switch_d['err_msgs'].append('Error reading logical switch information from chassis')
        brcdapi_log.exception(switch_d['err_msgs'][len(switch_d['err_msgs'])-1], echo=True)
        return brcddb_common.EXIT_STATUS_ERROR
    switch_obj = chassis_obj.r_switch_obj_for_fid(fid)
    if switch_obj is None:
        switch_obj = _create_switch(session, chassis_obj, switch_d, echo)
        if switch_obj is None:
            switch_d['err_msgs'].append('Could not read switch data for FID ' + str(fid))
            brcdapi_log.log(switch_d['err_msgs'][len(switch_d['err_msgs']) - 1], echo=True)
            return brcddb_common.EXIT_STATUS_ERROR
        switch_d.update(created=True)
    else:
        switch_d.update(created=False)
    switch_d.update(switch_obj=switch_obj)

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
        ec = _bind_address_to_port(session, switch_obj, switch_d, force, echo)
        r_status.append(ec)
        if ec != brcddb_common.EXIT_STATUS_OK:
            switch_d['err_msgs'].append('Failed to bind all addresses. Check the log for details')

    # Enable switch
    if switch_d['enable_switch']:
        ec = _enable_switch(session, fid, echo)
        r_status.append(ec)
        if ec != brcddb_common.EXIT_STATUS_OK:
            switch_d['err_msgs'].append('Failed to enable switch. Check the log for details')

    # Configure ports
    r_status.append(_configure_ports(session, switch_d['fid'], switch_d['ports'], switch_d['enable_ports']))

    # Pick the first non-OK error code to return
    ec = brcddb_common.EXIT_STATUS_OK
    for ec in r_status:
        if ec != brcddb_common.EXIT_STATUS_OK:
            break
    return ec


def _print_summary(switch_d_list):
    """Enable switch

    :param switch_d_list: List of switch dictionaries
    :type switch_d_list: list
    """
    ml = ['\nSummary', '_______']
    for switch_d in switch_d_list:
        ml.append('\nFID: ' + str(switch_d.get('fid')))
        ml.append('  Switch Name:            ' + brcddb_switch.best_switch_name(switch_d.get('switch_obj'), wwn=True))
        ml.append('  Switch Created:         ' + str(switch_d.get('created')))
        try:
            ml.append('  Ports Added:            ' + str(len(switch_d['ports'].keys())))
            ml.append('  Ports Removed:          ' + str(len(switch_d['remove_ports'])))
            ml.append('  Online Ports Not Moved: ' + str(len(switch_d['online_ports'])))
            ml.append('  Ports Not Found:        ' + str(len(switch_d['not_found_ports'])))
        except:
            pass  # We should never get here but I'm not changing working code.
        err_msgs = gen_util.convert_to_list(switch_d.get('err_msgs'))
        if len(err_msgs) > 0:
            ml.append('  Error Messages:         ')
            ml.extend(['    ' + buf for buf in err_msgs])
    brcdapi_log.log(ml, echo=True)


def _get_input():
    """Retrieves the command line input, reads the input Workbook, and minimally validates the input

    :return ip: Switch IP address
    :rtype ip: str
    :return out_file: Name of output file
    :rtype out_file: str
    :return s_flag: Suppress flag
    :rtype s_flag: bool
    """
    global _DEBUG, _DEBUG_ip, _DEBUG_id, _DEBUG_pw, _DEBUG_sec, _DEBUG_i, _DEBUG_force, _DEBUG_sup, _DEBUG_echo,\
        _DEBUG_d, _DEBUG_log, _DEBUG_nl

    if _DEBUG:
        args_ip, args_id, args_pw, args_s, args_i, args_force, args_sup, args_echo, args_d, args_log, args_nl = \
            _DEBUG_ip, _DEBUG_id, _DEBUG_pw, _DEBUG_sec, _DEBUG_i, _DEBUG_force, _DEBUG_sup, _DEBUG_echo, \
            _DEBUG_d, _DEBUG_log, _DEBUG_nl
    else:
        buf = 'Reads a switch configuration workbook and configures each logical switch accordingly. See '\
              'X6_X7-4_Switch_Configuration.xlsx, X6_X7-8_Switch_Configuration.xlsx, and '\
              'Fixed_Port_Switch_Configuration.xlsx.'
        parser = argparse.ArgumentParser(description=buf)
        parser.add_argument('-ip', help='(Optional) IP address', required=True)
        parser.add_argument('-id', help='(Optional) User ID', required=True)
        parser.add_argument('-pw', help='(Optional) Password', required=True)
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
        args_ip, args_id, args_pw, args_s, args_i, args_force, args_sup, args_echo, args_d, args_log, args_nl = \
            args.ip, args.id, args.pw, args.s, args.i, args.force, args.sup, args.echo, args.d, args.log, args.nl

    # Set up the logging options
    if args_sup:
        brcdapi_log.set_suppress_all()
    if not args_nl:
        brcdapi_log.open_log(args_log)
    if args_d:
        brcdapi_rest.verbose_debug = True

    return args_ip, args_id, args_pw, args_s if args_s else 'none', args_i, args_force, args_echo


def pseudo_main():
    """Basically the main().

    :return: Exit code
    :rtype: int
    """
    global _DEBUG

    # Get and validate command line input.
    ec = brcddb_common.EXIT_STATUS_OK
    ip, user_id, pw, sec, file, force, echo = _get_input()
    file = brcdapi_file.full_file_name(file, '.xlsx')
    ml = ['switch_config.py: ' + __version__,
          'File, -i:         ' + file,
          'IP address, -ip:  ' + brcdapi_util.mask_ip_addr(ip),
          'ID, -id:          ' + str(user_id),
          's, -s:            ' + sec,
          'force, -force     ' + str(force),
          'echo, -echo       ' + str(echo)]
    if _DEBUG:
        ml.insert(0, 'WARNING!!! Debug is enabled')
    brcdapi_log.log(ml, echo=True)

    # Read in the Workbook, generate the portaddress --bind commands, and configure the switch(es)
    chassis_d, switch_d_list = report_utils.parse_switch_file(file)
    switch_d = session = proj_obj = None

    try:

        # Login
        session = api_int.login(user_id, pw, ip, sec, proj_obj)
        if fos_auth.is_error(session):  # Errors are sent to the log in api_int.login()
            return brcddb_common.EXIT_STATUS_API_ERROR

        # Get a project object
        proj_obj = brcddb_project.new('Create_LS', datetime.datetime.now().strftime('%d %b %Y %H:%M:%S'))
        proj_obj.s_python_version(sys.version)
        proj_obj.s_description('Creating logical switches from ' + os.path.basename(__file__))

        # Read some basic chassis information. Primarily to see if defined switches and ports already exist
        api_int.get_batch(session, proj_obj, _basic_capture_kpi_l, None)
        if proj_obj.r_is_any_error():  # Error details are logged in api_int.get_batch()
            return brcddb_common.EXIT_STATUS_API_ERROR

        # Make chassis updates
        ec = _configure_chassis(session, chassis_d)

        # Create and/or modify the logical switches
        for switch_d in switch_d_list:
            switch_d.update(err_msgs=list())

            # Create the logical switch
            if switch_d['switch_flag']:
                ec = _configure_switch(session, proj_obj, switch_d, force, echo)
                if len(switch_d['err_msgs']) > 0:
                    buf_l = ['Errors creating switch. Switch name: ' + str(switch_d.get('switch_name')) + ' DID: ' +
                             str(switch_d.get('did'))]
                    buf_l.extend('  ' + b for b in switch_d['err_msgs'])
                    brcdapi_log.log(buf_l, echo=True)

    except BaseException as e:
        buf = 'Programming error encountered. Exception: ' + str(e)
        if isinstance(switch_d, dict) and isinstance(switch_d.get('err_msgs'), list):
            switch_d['err_msgs'].append(buf)
        brcdapi_log.log(buf, echo=True)
        ec = brcddb_common.EXIT_STATUS_ERROR

    # Logout and display a summary report
    if session is not None:
        obj = brcdapi_rest.logout(session)
        if fos_auth.is_error(obj):
            brcdapi_log.exception(fos_auth.formatted_error_msg(obj), echo=True)
            ec = brcddb_common.EXIT_STATUS_API_ERROR
    if ip is not None:
        _print_summary(switch_d_list)

    return ec


###################################################################
#
#                    Main Entry Point
#
###################################################################
if _DOC_STRING:
    print('_DOC_STRING is True. No processing')
    exit(brcddb_common.EXIT_STATUS_OK)

_ec = pseudo_main()
brcdapi_log.close_log('Processing complete. Exit status: ' + str(_ec))
exit(_ec)
