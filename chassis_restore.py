#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2021, 2022, 2023 Jack Consoli.  All rights reserved.
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
:mod:`chassis_restore` - Restores a switch to a previously captured chassis DB

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 1.0.0     | xx xxx 2023   | Initial launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2023 Jack Consoli'
__date__ = 'xx xxx 2023'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Development'
__version__ = '1.0.0'

import argparse
import collections
import sys
import datetime
import copy
import base64
import brcdapi.log as brcdapi_log
import brcdapi.fos_auth as fos_auth
import brcdapi.brcdapi_rest as brcdapi_rest
import brcdapi.gen_util as gen_util
import brcdapi.util as brcdapi_util
import brcdapi.file as brcdapi_file
import brcdapi.switch as brcdapi_switch
import brcdapi.port as brcdapi_port
import brcddb.brcddb_project as brcddb_project
import brcddb.brcddb_common as brcddb_common
import brcddb.classes.util as class_util
import brcddb.api.interface as api_int
import brcddb.brcddb_chassis as brcddb_chassis
import brcddb.brcddb_switch as brcddb_switch
import brcddb.brcddb_fabric as brcddb_fabric
import brcddb.api.zone as brcddb_zone

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = True   # When True, use _DEBUG_xxx below instead of parameters passed from the command line.
_DEBUG_ip = '10.144.72.15'
_DEBUG_id = 'admin'
_DEBUG_pw = 'AdminPassw0rd!'
_DEBUG_s = 'self'
_DEBUG_i = 'gsh/gsh'
_DEBUG_eh = False
_DEBUG_wwn = None  # '10:00:c4:f5:7c:2d:a6:20'
_DEBUG_scan = False
_DEBUG_p = '*'
_DEBUG_e = True
_DEBUG_sup = False
_DEBUG_d = False
_DEBUG_log = '_logs'
_DEBUG_nl = False

_temp_password = 'Passw0rd!'
_basic_capture_kpi_l = [
    # 'running/brocade-fabric/fabric-switch',  Done automatically in brcddb.api.interface.get_chassis()
    'running/brocade-fibrechannel-switch/fibrechannel-switch',
    'running/brocade-fibrechannel-configuration/switch-configuration',
    'running/brocade-fibrechannel-configuration/port-configuration',
    'running/brocade-interface/fibrechannel',
]
_full_capture_l = _basic_capture_kpi_l.copy()
_restore_parameters = dict(
    c='Chassis. All chassis settings except those specified with "vf" and "s"',
    maps='MAPS. All MAPS custom rules.',
    vf='Virtual Fabric. Set all ports to default. Delete and restore all logical switches.',
    s='Security. Limited to creating non-default users only',
    l='Logging. Does nothing in this release',
    fcr='Fibre Chnnel Routing. Does nothing in this release',
    isl='ISL. Does nothing in this release',
    ficon='FICON. Does nothing in this release',
    fcip='Fibre Channel Over IP. Does nothing in this release',
    p='Port. Does nothing in this release',
    z='Zoning. Restores the zoning configurations for each fabric',
)
_eh = [
    '',
    'Overview',
    '________',
    '',
    'The typical use for this module is for modifying a chassis for:',
    '',
    '  * A service action replacement',
    '  * An upgrade',
    '  * Reallocation of a SAN resource',
    '  * Template'
    '      * It may be useful to configure chassis and switches to use as',
    '        a template and make further modifications via other modules.',
    '',
    'Nomenclature:',
    '',
    '    Restore    Refers to the reference chassis (chassis being',
    '               restored from).',
    '',
    '    Target     Refers to the chassis being rebuilt.',
    '',
    'A capture must be performed from the restore chassis prior to using',
    'this module. It is not necessary to collect all data; however, keep in',
    'mind that what ever data wasn\'t collected can\'t be restored.',
    '',
    'Operation',
    '_________',
    '',
    'A list of actions is acted on. For a description of actions and suggestions,',
    'search this module for _action_l. The intent was to read the list of',
    'actions from a workbook but as of this writing, only the default list is',
    'used.',
    '',
    'A best effort attempt is made to restore the chassis:',
    '',
    '  * All errors are reported but are otherwise ignored. The intent is to',
    '    restore as much as possible.',
    '  * Ports from the previous data capture that do not exist in the chassis',
    '    are ignored',
    '  * Ports that do not exist in the previous data are left in the default switch',
    '',
    'The general process is:'
    '',
    '1.  Read the input file, -i, for the restore chassis',
    '2.  A GET request is issued for each URI associated with \'k\' in the',
    '    action list.'
    '3.  The action list is then processed in order. Typical actions are to',
    '    modify values in the target chassis that differ from the restore chassis'
    '    but action methods can be written to do anything. For a discussion of',
    '    pre-written action methods, search for _action_l.'
    '',
    'Exceptions and Other Notes',
    '__________________________',
    '',
    '  * Existing RBAC users on the target chassis are not modified.',
    '  * If enable, -e, was specified, only those switches and ports that were',
    '    enabled on the restore chassis are enabled on the target chassis.',
    '  * All switch and port configurations are completed before enabling them.',
    '  * All errors are reported but are otherwise ignored. The intent is to',
    '    restore as much as possible.',
    '  * Ports from the previous data capture that do not exist in the target',
    '    chassis are ignored',
    '  * Ports that do not exist in the previous data are left in the default switch',
    '  * Some actions require the affected switch or port to be disabled. The',
    '    recommendation therefore is to leave all switches and ports in the disabled',
    '    state until all configuration actions are complete.',
    '',
    'Parameter, -p, options:',
    '*       All (full restore)',
]
for _key, _buf in _restore_parameters.items():
    _eh.append(gen_util.pad_string(str(_key), 8, ' ', append=True) + _buf)
_eh.append('')


###################################################################
#
#           Support Methods for Branch Actions
#
###################################################################
def _send_request(session, http_method, key, content):
    """Generic method to send requests used by the Branch Actions

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param http_method: HTTP method. PATCH, POST, ...
    :type http_method: str
    :param key: Reference key into _control_d in slash notation.
    :type key: str
    :param content: Content to send to switch. If content is None or empty, nothing is sent to the switch
    :type content: None, dict, list
    :return: List of error messages as str encountered.
    :rtype: list
    """
    el = list()
    if content is None or len(content) == 0:
        return el
    uri = 'running/' + key
    obj = brcdapi_rest.send_request(session, uri, http_method, {key.split('/').pop(): content})
    if fos_auth.is_error(obj):
        el.extend(['Error updating chassis URI:', '  ' + uri, 'FOS error:', fos_auth.formatted_error_msg(obj)])

    return el


def _enable_disable_chassis(session, state, e_text):
    """Disables or Enables the chassis

    :param session: Session object, or list of session objects, returned from brcdapi.fos_auth.login()
    :type session: dict
    :param state: If Ture, enable the chassis. Otherwise, disable the chassis
    :type state: bool
    :param e_text: Text to append to error messages
    :type e_text: str
    :return: List of error messages
    :rtype: list
    """
    el = list()
    obj = _send_request(session, 'PATCH', 'brocade-chassis/chassis', dict(chassis={'chassis-enabled': state}))
    if fos_auth.is_error(obj):
        el.extend(['Error updating chassis URI: brocade-chassis/chassis' + e_text,
                   'FOS error:',
                   fos_auth.formatted_error_msg(obj)])
    return el


def _fmt_errors(to_format, full=False):
    """Formats the standard inputs to the branch actions for error reporting.

    :param to_format: List of objects to format.
    :type to_format: list
    :return: Formatted text in list entries
    :rtype: list
    """
    rl = list()
    for obj in gen_util.convert_to_list(to_format):
        rl.extend(class_util.format_obj(obj, full=full))
    return rl


def _patch_content(r_obj, t_obj, d):
    """ Builds a dictionary with just the differences between the restore object and target object

    :param r_obj: Restore object
    :type r_obj: brcddb.classes.chassis.ChassisObj, brcddb.classes.switch.SwitchObj
    :param t_obj: Restore object
    :type t_obj: brcddb.classes.chassis.ChassisObj, brcddb.classes.switch.SwitchObj
    :param d: Actions to take. This is a dictionary from _control_d
    :type d: dict
    :return: List of error messages as str encountered.
    :rtype: list
    :return content_d: Dictionary differences
    :rtype content_d: dict()
    """
    el = list()
    try:
        rd, content_d, key, rw_d = dict(), dict(), d['k'], d.get('rw')

        # Validate the input
        for obj in (r_obj, t_obj):
            obj_type = str(class_util.get_simple_class_type(obj))
            if obj_type not in ('ChassisObj', 'SwitchObj'):
                el.append('Invalid object type: ' + obj_type + '. ' + d['e'])
        if type(r_obj) != type(t_obj):
            el.append('Object types do not match. ' + d['e'])
        if key is None:
            el.append('Missing k in dictionary for ' + d['e'])
        if not isinstance(rw_d, dict):
            el.append('rw missing in dictionary for ' + d['e'])

        # Figure out the differences
        if len(el) == 0:
            for k, method in rw_d.items():
                r_val, t_val = method(r_obj, d['k'], k), method(t_obj, d['k'], k)
                if r_val is not None:
                    if t_val is None or type(t_val) != type(r_val) or r_val != t_val:
                        content_d.update({k: r_val})

        # Figure out what the return content should be
        if len(content_d) > 0:
            rd.update({key.split('/').pop(): content_d})

    except BaseException as e:
        brcdapi_log.exception(_fmt_errors([d, obj, r_obj, t_obj, e], full=True))
        el.append('Software error. Check the log for "brcdapi library exception call"')

    return el, rd


def _post_content(r_obj, d):
    """Creates a copy of the restore object with just values in d['rw']

    :param r_obj: Restore object
    :type r_obj: brcddb.classes.chassis.ChassisObj, brcddb.classes.switch.SwitchObj
    :param d: Actions to take. This is a dictionary from _control_d
    :type d: dict
    :return: List of error messages as str encountered.
    :rtype: list
    :return content_d: Dictionary differences
    :rtype content_d: dict()
    """
    el = list()
    try:
        rd, content_d, key, rw_d = dict(), dict(), d['k'], d.get('rw')

        # Validate the input
        obj_type = str(class_util.get_simple_class_type(r_obj))
        if obj_type not in ('ChassisObj', 'SwitchObj'):
            el.append('Invalid object type: ' + obj_type + '. ' + d['e'])
        if key is None:
            el.append('Missing k in dictionary for ' + d['e'])
        if not isinstance(rw_d, dict):
            el.append('rw missing in dictionary for ' + d['e'])

        # Figure out what the return content should be
        for key in [k for k, v in rw_d.items() if v]:
            rd.update({key.split('/').pop(): _conv_lookup_act(r_obj, key)})

    except BaseException as e:
        brcdapi_log.exception(_fmt_errors([d, r_obj, e], full=True))
        el.append('Software error. Check the log for "brcdapi library exception call"')

    return el, rd


###################################################################
#
#         Leaf Actions (see rw in _action_l)
#
###################################################################
def _conv_none_act(obj, key, sub_key=None):
    """ Always returns None
    
    :param obj: Chassis or Switch object
    :type obj: brcddb.classes.chassis.ChassisObj, brcddb.classes.switch.SwitchOBj
    :param key: The branch Key in obj to lookup. If just one key, use this and make sub_key None
    :type key: str
    :param sub_key: The leaf name
    :type sub_key: str, None
    :return: Value in obj associated with key
    :rtype: None, str, float, bool, int, list, dict
    """
    return None


def _conv_lookup_act(obj, key, sub_key=None):
    """Simple lookup. See _conv_none_act() for parameters"""
    try:
        full_key = key if sub_key is None else key + '/' + sub_key
        return copy.deepcopy(gen_util.get_key_val(obj, full_key))
    except BaseException as e:
        brcdapi_log.exception(['Key: ' + str(key), 'sub_key: ' + str(sub_key)] + _fmt_errors(obj, full=True), echo=True)
    return None


def _default_user_pw_act(obj, key, sub_key=None):
    """Returns an encoded default new user password: "Passw0rd!". See _conv_none_act() for parameters"""
    global _temp_password
    return base64.b64encode(_temp_password.encode('utf-8')).decode('utf-8')


def _true_act(obj, key, sub_key=None):
    """Returns logical True. See _conv_none_act() for parameters"""
    return True


###################################################################
#
#                        Branch Actions
#
###################################################################
def _data_capture(cd, d):
    """Captures a list of URIs from the target chassis

    :param cd: Session, project info, etc. See local_control_d in pseudo_main()
    :type cd: dict
    :param d: Actions to take. This is a dictionary from _control_d
    :type d: dict
    :return: List of error messages as str encountered.
    :rtype: list
    """
    try:
        el = list()
        if api_int.get_batch(cd['session'], cd['proj_obj'], d['rl']):
            cd['t_chassis_obj'] = cd['proj_obj'].r_chassis_obj(cd['session']['chassis_wwn'])
            cd['fid'] = dict(default=[brcddb_switch.switch_fid(cd['t_chassis_obj'].r_default_switch_obj())],
                             all=cd['t_chassis_obj'].r_fid_list())
            cd['fid'].update(all_non_default=[fid for fid in cd['fid']['all'] if fid not in cd['fid']['default']])
        else:
            el.append('Error(s) capturing data. Check the log for details')
    except BaseException as e:
        brcdapi_log.exception(_fmt_errors([d, cd, e]))
        el.append('Software error. Check the log for "brcdapi library exception call"')
    return el


def _data_clear(cd, d):
    """Clears all data from captured session. See _data_capture() for parameter definitions"""
    try:
        el = list()
        cd['proj_obj'].s_del_chassis(cd['session'].pop('chassis_wwn'))
        try:
            for key in ('t_chassis_obj', 'fid'):
                cd.pop(key)
        except AttributeError:
            pass
    except KeyError:
        pass  # Future proofing. At the time this was written, there would always be a chassis to delete
    except BaseException as e:
        brcdapi_log.exception(_fmt_errors([d, cd, e]))
        el.append('Software error. Check the log for "brcdapi library exception call"')
    return el


def _ports_to_default(cd, d):
    """Sets all ports to the default configuration. See _data_capture() for parameter definitions"""
    el = list()
    try:
        for r_switch_obj in [cd['r_chassis_obj'].r_switch_obj_for_fid(fid) for fid in cd['fid'][d['fid']]]:
            obj = brcdapi_port.default_port_config(cd['session'],
                                                   brcddb_switch.switch_fid(r_switch_obj),
                                                   r_switch_obj.r_port_keys() + r_switch_obj.r_ge_port_keys())
            if fos_auth.is_error(obj):
                el.extend(['Error setting ports to default, FOS error is:', fos_auth.formatted_error_msg(obj)])
    except BaseException as e:
        brcdapi_log.exception(_fmt_errors([d, cd, r_switch_obj, e], full=True))
        el.append('Software error. Check the log for "brcdapi library exception call"')
    return el


def _del_switches(cd, d):
    """Deletes all logical switches. See _data_capture() for parameter definitions"""
    el = list()
    try:
        for fid in cd['fid'][d['fid']]:
            obj = brcdapi_switch.delete_switch(cd['session'], fid, echo=True)
            if fos_auth.is_error(obj):
                el.extend(['Error deleting FID ' + str(fid), fos_auth.formatted_error_msg(obj)])
    except BaseException as e:
        brcdapi_log.exception(_fmt_errors([d, cd, obj, e], full=True))
        el.append('Software error. Check the log for "brcdapi library exception call"')
    return el


def _vf_enable(cd, d):
    """Enable/Disable virtual fabrics. See _data_capture() for parameter definitions"""
    el = list()
    try:
        el, content_d = _patch_content(cd['r_chassis_obj'], cd['t_chassis_obj'], d)
        if len(content_d) > 0:
            el.extend(_enable_disable_chassis(cd['session'], False, '_vf_enable, index: ' + d['e']))  # Disable chassis
            if len(el) == 0:
                # Set VF
                obj = brcdapi_rest.send_request(cd['session'], d['k'], d['m'], content_d)
                if fos_auth.is_error(obj):
                    el.extend(['Error updating chassis URI: ' + d['k'] + ', Index: ' + d['e'],
                               'FOS error:',
                               fos_auth.formatted_error_msg(obj)])
                # Re-enable chassis. Note: If the chassis was disabled from the start, we wouldn't have gotten this far
                el.extend(_enable_disable_chassis(cd['session'], True, '_vf_enable, index: ' + d['e']))
    except BaseException as e:
        brcdapi_log.exception(_fmt_errors([d, cd, obj, e], full=True))
        el.append('Software error. Check the log for "brcdapi library exception call"')
    return el


def _restore_switches(cd, d):
    """Re-creates logical switches. See _data_capture() for parameter definitions"""
    try:
        el, r_chassis_obj, t_chassis_obj = list(), cd['r_chassis_obj'], cd['t_chassis_obj']

        for fid in r_chassis_obj.r_fid_list():
            if t_chassis_obj.r_switch_obj_for_fid(fid) is not None:
                continue  # The LS as already created
            r_switch_obj = r_chassis_obj.r_switch_obj_for_fid(fid)
            # Create the logical switch
            obj = brcdapi_switch.create_switch(cd['session'],
                                               fid,
                                               r_switch_obj.r_is_base(),
                                               r_switch_obj.r_is_ficon(),
                                               echo=True)
            if fos_auth.is_error(obj):
                el.extend(['Error creating ' + brcddb_switch.best_switch_name(r_switch_obj, fid=True, did=True) +d['e'],
                           fos_auth.formatted_error_msg(obj)])
    except BaseException as e:
        brcdapi_log.exception(_fmt_errors([d, cd, r_switch_obj, fid, e], full=True))
        el.append('Software error. Check the log for "brcdapi library exception call"')
    return el


def _restore_ports(cd, d):
    """Add/remove ports. See _data_capture() for parameter definitions"""
    try:
        el, r_chassis_obj, t_chassis_obj = list(), cd['r_chassis_obj'], cd['t_chassis_obj']

        for fid in cd['fid'][d['fid']]:
            rs_obj, ts_obj = r_chassis_obj.r_switch_obj_for_fid(fid), t_chassis_obj.r_switch_obj_for_fid(fid)
            if rs_obj is None:
                el.append('Can\'t add/remove ports to/from FID ' + str(fid) + ' because the FID does not exist in ' +
                          brcddb_chassis.best_chassis_name(r_chassis_obj) + d['e'])
                continue

            # Remove (move to the default switch) any ports that do not belong in the target switch
            obj = brcdapi_switch.add_ports(cd['session'],
                                           fid,
                                           cd['default_fid'],
                                           [p for p in rs_obj.r_port_keys() if ts_obj.r_port_obj(p) is None],
                                           [p for p in rs_obj.r_ge_port_keys() if ts_obj.r_ge_port_obj(p) is None],
                                           echo=True)
            if fos_auth.is_error(obj):
                buf = 'Error adding ports to ' + brcddb_switch.best_switch_name(rs_obj, fid=True, did=True) + d['e']
                brcdapi_log.log([buf, fos_auth.formatted_error_msg(obj)], echo=True)
                el.append(buf)

            # brcdapi_switch.add_ports() needs to know where the ports are moving from so figure that out
            from_fid_d = dict()
            for port_type in ('ge_port', 'port'):
                port_l = rs_obj.r_ge_port_keys() if port_type == 'ge_port' else rs_obj.r_port_keys()
                for port in port_l:
                    port_obj = t_chassis_obj.r_ge_port_obj(port) if port_type == 'ge_port'\
                        else t_chassis_obj.r_port_obj(port)
                    if port_obj is None:
                        el.append('Port ' + port + ' does not exist in ' +
                                  brcddb_chassis.best_chassis_name(t_chassis_obj) + d['e'])
                        continue
                    from_fid = brcddb_switch.switch_fid(port_obj.r_switch_obj())
                    if from_fid not in from_fid_d:
                        from_fid_d.update({from_fid: dict(ge_port=list(), port=list())})
                    from_fid_d[from_fid][port_type].append(port)

            # Now add the ports
            for from_fid, port_d in from_fid_d.items():
                obj = brcdapi_switch.add_ports(cd['session'],
                                               fid,
                                               from_fid,
                                               from_fid_d[from_fid]['port'],
                                               from_fid_d[from_fid]['ge_port'],
                                               echo=True)
                if fos_auth.is_error(obj):
                    buf = 'Error adding ports to ' + brcddb_switch.best_switch_name(rs_obj, fid=True, did=True) + d['e']
                    brcdapi_log.exception(_fmt_errors([buf, fos_auth.formatted_error_msg(obj), from_fid, from_fid_d],
                                                      full=True))
                    el.extend([buf, fos_auth.formatted_error_msg(obj)])
                    continue

            # Bind any addresses that need to be bound
            port_l = list()
            for port_obj in rs_obj.r_port_objects():
                bind_l = port_obj.r_get('fibrechannel/bound-address-list/bound-address')
                if len(bind_l) > 0:
                    port_l.append({port_obj.r_obj_key(): bind_l[0]})

    except BaseException as e:
        brcdapi_log.exception(_fmt_errors(['Software error. Exception:', e]))
        el.append('Software error. Check the log for "brcdapi library exception call"')

    return el


def _none_act(cd, d):
    return list()


def _fibrechannel_switch(cd, d):
    """Actions for brocade-fibrechannel-switch. See _data_capture() for parameter definitions"""
    try:
        el = list()
        brcdapi_log.log('_fibrechannel_switch', echo=True)
        el.append('WIP: _fibrechannel_switch')
    except BaseException as e:
        brcdapi_log.exception(_fmt_errors(['Software error. Exception: ', e]))
        el.append('Software error. Check the log for "brcdapi library exception call"')
    return el


def _trunk_act(cd, d):
    """Re-create trunk groups. See _data_capture() for parameter definitions"""
    try:
        el = list()
        el.apend('WIP: _trunk_act')
    except BaseException as e:
        brcdapi_log.exception(_fmt_errors(['Software error. Exception: ', e]))
        el.append('Software error. Check the log for "brcdapi library exception call"')
    return el
    # rl = [{'trunk-index': d['trunk-index'], 'trunk-members': d['trunk-members']} for d in
    #       gen_util.convert_to_list(d['r_obj'].r_get(d['key']))]
    return None if len(rl) == 0 else rl


def _user_act(cd, d):
    """Re-create non-default users. See _data_capture() for parameter definitions"""
    global _temp_password
    el, content_l = list(), list()
    try:
        key, rw_d, r_chassis_obj, t_chassis_obj = d['k'], d['rw'], cd['r_chassis_obj'], cd['t_chassis_obj']
        t_user_l = gen_util.convert_to_list(cd['t_chassis_obj'].r_get(key))
        if len(t_user_l) > 0:
            existing_user_d = dict(root=True)  # Newer versions of FOS don't support root. Make sure root gets skipped
            for td in gen_util.convert_to_list(t_chassis_obj.r_get(key)):
                existing_user_d.update({td['name']: True})
            for rd in gen_util.convert_to_list(r_chassis_obj.r_get(key)):
                if not bool(existing_user_d.get(rd['name'])):
                    content_d = collections.OrderedDict() if isinstance(rw_d, collections.OrderedDict) else dict()
                    for k in rw_d.keys():
                        content_d.update({k: rw_d[k](rd, k)})
                        if k == 'password':
                            el.append('Created user: ' + str(rw_d.get('name')) + '. Temp password: ' + _temp_password)
                    content_l.append(content_d)
        if len(content_l) > 0:
            return _send_request(cd['session'], d['m'], key, content_l)
    except BaseException as e:
        brcdapi_log.exception(_fmt_errors([d, cd, e], full=True))
        el.append('Software error. Check the log for "brcdapi library exception call"')
    return el


def _zone_restore(cd, d):
    """Restore zoning. See _data_capture() for parameter definitions"""
    el = list()
    for fid in cd['r_chassis_obj'].r_fid_list():
        for fab_obj in cd['t_chassis_obj'].r_fabric_objects():
            fid_l = brcddb_fabric.fab_fids(fab_obj)
            if len(fid_l) == 1:
                if fid == fid_l[0]:
                    obj = brcddb_zone.replace_zoning(cd['session'], fab_obj, fid)
                    if fos_auth.is_error(obj):
                        buf = 'Failed to replace zoning in fabric ' + brcddb_fabric.best_fab_name(fab_obj, fid=True)
                        brcdapi_log.exception(_fmt_errors([buf, fos_auth.formatted_error_msg(obj), fab_obj]), full=True)
                        el.append(buf)
                    else:
                        def_zone = fab_obj.r_defined_eff_zonecfg_key()
                        if isinstance(def_zone, str):
                            obj = brcddb_zone.enable_zonecfg(cd['session'], None, fid, def_zone)
                            if fos_auth.is_error(obj):
                                el.extend(['Failed to enable zone config ' + def_zone,
                                           fos_auth.formatted_error_msg(obj)])
            else:
                el.append('Multiple FIDs in fabric ' + brcddb_fabric.best_fab_name(fab_obj, wwn=True, fid=True) +
                          '. Skipping zone restore on this fabric.')
    return el


def _chassis_update_act(cd, d):
    """Updates that do not have any special considerations. See _data_capture() for parameter definitions"""
    el, content_l = list(), list()
    try:
        key, rw_d, r_chassis_obj, t_chassis_obj = d['k'], d['rw'], cd['r_chassis_obj'], cd['t_chassis_obj']
        r_name, t_name =\
            brcddb_chassis.best_chassis_name(r_chassis_obj), brcddb_chassis.best_chassis_name(t_chassis_obj)
        rd, td = r_chassis_obj.r_get(key), t_chassis_obj.r_get(key)
        if not isinstance(td, dict):
            el.append(key + ' not supported in restore chassis ' + r_name)
        if not isinstance(rd, dict):
            el.append(key + ' not supported in target chassis ' + t_name)
        if len(el) > 0:
            return el
        for k, method in rw_d.items():
            r_val, t_val = method(rd, k), method(td, k)
            if r_val is None:
                el.append(key + '/' + str(k) + ' not supported in restore chassis ' + r_name)
                continue
            if t_val is None:
                el.append(key + '/' + str(k) + ' not supported in target chassis ' + t_name)
                continue
            if d['m'] == 'POST':
                content_l.append({k: r_val})
            elif d['m'] == 'PATCH' and (str(r_val) != str(t_val)):
                content_l.append({k: r_val})
        if len(content_l) > 0:
            return _send_request(cd['session'], d['m'], key, content_l)
    except BaseException as e:
        brcdapi_log.exception(_fmt_errors([d, cd, e], full=True))
        el.append('Software error. Check the log for "brcdapi library exception call"')
    return el


def _switch_update_act(cd, d):
    """Updates that do not have any special considerations. See _data_capture() for parameter definitions"""
    el, content_l = list(), list()
    try:
        key, rw_d, r_chassis_obj, t_chassis_obj = d['k'], d['rw'], cd['r_chassis_obj'], cd['t_chassis_obj']
        for fid in cd['r_chassis_obj'].r_fid_list():
            r_switch_obj, t_switch_obj =\
                r_chassis_obj.r_switch_obj_for_fid(fid), t_chassis_obj.r_switch_obj_for_fid(fid)
            if t_switch_obj is None:
                el.append('FID ' + str(fid) + ' not in ' + brcddb_chassis.best_chassis_name(t_chassis_obj))
                continue
            r_name = brcddb_switch.best_switch_name(r_switch_obj, fid=True)
            t_name = brcddb_switch.best_switch_name(t_switch_obj, fid=True)
            for k, method in rw_d.items():
                r_val, t_val = method(r_switch_obj, key, k), method(t_switch_obj, key, k)
                if r_val is None:
                    el.append(key + '/' + str(k) + ' not supported in restore chassis ' + r_name)
                    continue
                if t_val is None:
                    el.append(key + '/' + str(k) + ' not supported in target chassis ' + t_name)
                    continue
                if d['m'] == 'POST':
                    content_l.append({k: r_val})
                elif d['m'] == 'PATCH' and (str(r_val) != str(t_val)):
                    content_l.append({k: r_val})
            if len(content_l) > 0:
                return _send_request(cd['session'], d['m'], key, content_l)
    except BaseException as e:
        brcdapi_log.exception(_fmt_errors([d, cd, e], full=True))
        el.append('Software error. Check the log for "brcdapi library exception call"')
    return el


def _port_update_act(cd, d):
    """Updates that do not have any special considerations. See _data_capture() for parameter definitions"""
    el = list()
    try:
        key, rw_d, r_chassis_obj, t_chassis_obj = d['k'], d['rw'], cd['r_chassis_obj'], cd['t_chassis_obj']
        for r_switch_obj in r_chassis_obj.r_switch_objects():

            # Find the switch on the target chassis
            fid = brcddb_switch.switch_fid(t_switch_obj)
            t_switch_obj = t_chassis_obj.r_switch_obj_for_fid(fid)
            if t_switch_obj is None:
                buf = 'FID ' + str(fid) + ' does not exist in ' + brcddb_chassis.best_chassis_name(t_chassis_obj)
                buf += '. Ports could not be updated.'
                el.append(buf)
                continue
            r_name = brcddb_switch.best_switch_name(r_switch_obj, fid=True)
            t_name = brcddb_switch.best_switch_name(t_switch_obj, fid=True)

            # Update the ports
            content_l = list()
            port_obj_l = r_switch_obj.r_port_objects() if d['rl'] == 'ports' else r_switch_obj.r_ge_port_objects()
            for port_obj in port_obj_l:
                for k, method in rw_d.items():
                    r_val, t_val = method(r_switch_obj, key, k), method(t_switch_obj, key, k)
                    if r_val is None:
                        el.append(key + '/' + str(k) + ' not supported in restore chassis ' + r_name)
                        continue
                    if t_val is None:
                        el.append(key + '/' + str(k) + ' not supported in target chassis ' + t_name)
                        continue
                    if d['m'] == 'POST':
                        content_l.append({k: r_val})
                    elif d['m'] == 'PATCH' and (str(r_val) != str(t_val)):
                        content_l.append({k: r_val})
            if len(content_l) > 0:
                return _send_request(cd['session'], d['m'], key, content_l)
    except BaseException as e:
        brcdapi_log.exception(_fmt_errors([d, cd, e], full=True))
        el.append('Software error. Check the log for "brcdapi library exception call"')
    return el


def _maps_rule_act(cd, d):
    """Updates for brocade-maps/rule. See _data_capture() for parameter definitions"""
    el, content_l = list(), list()

    try:
        key, rw_d, r_chassis_obj, t_chassis_obj = d['k'], d['rw'], cd['r_chassis_obj'], cd['t_chassis_obj']
        for r_switch_obj in r_chassis_obj.r_switch_objects():

            # Find the switch on the target chassis
            fid = brcddb_switch.switch_fid(t_switch_obj)
            t_switch_obj = t_chassis_obj.r_switch_obj_for_fid(fid)
            if t_switch_obj is None:
                buf = 'FID ' + str(fid) + ' does not exist in ' + brcddb_chassis.best_chassis_name(t_chassis_obj)
                buf += '. Ports could not be updated.'
                el.append(buf)
                continue
            r_name = brcddb_switch.best_switch_name(r_switch_obj, fid=True)
            t_name = brcddb_switch.best_switch_name(t_switch_obj, fid=True)

            # Figure out what custom rules we have first
            rule_lookup_d = dict(
                t=dict(
                    rule_l=[d for d in t_switch_obj.r_get('brocade-maps/rule') if not bool(d.get('is-predefined'))],
                    rule_d=dict()),
                r=dict(
                    rule_l=[d for d in r_switch_obj.r_get('brocade-maps/rule') if not bool(d.get('is-predefined'))],
                    rule_d=dict())
            )
            for custom_rule_d in rule_lookup_d.values():
                for rule_d in custom_rule_d['rule_l']:
                    sub_d = dict()
                    for k, v in rule_d.items():
                        if k != 'name':
                            if k == 'actions':
                                print('LEFT OFF HERE')
                            custom_rule_d['rule_d'].update({k, v})
            for rule_d in [d for d in t_switch_obj.r_get('brocade-maps/rule') if not bool(d.get('is-predefined'))]:
                f
                custom_rule_d.update()
                print()

            # Update the ports
            content_l = list()
            port_obj_l = r_switch_obj.r_port_objects() if d['rl'] == 'ports' else r_switch_obj.r_ge_port_objects()
            for port_obj in port_obj_l:
                for k, method in rw_d.items():
                    r_val, t_val = method(r_switch_obj, key, k), method(t_switch_obj, key, k)
                    if r_val is None:
                        el.append(key + '/' + str(k) + ' not supported in restore chassis ' + r_name)
                        continue
                    if t_val is None:
                        el.append(key + '/' + str(k) + ' not supported in target chassis ' + t_name)
                        continue
                    if d['m'] == 'POST':
                        content_l.append({k: r_val})
                    elif d['m'] == 'PATCH' and (str(r_val) != str(t_val)):
                        content_l.append({k: r_val})
            if len(content_l) > 0:
                return _send_request(cd['session'], d['m'], key, content_l)
    except BaseException as e:
        brcdapi_log.exception(_fmt_errors([d, cd, e], full=True))
        el.append('Software error. Check the log for "brcdapi library exception call"')
    return el




    return el


"""_control_d is a dictionary of dictionaries. The first key is the highest level branch (right after running) and
the second is the next branch level URI. The final dictionary instructs the machine in psuedo_main() how to act on
the URI branch as noted in the table below.

Ordered dictionaries were used because in some cases the order of operations is significant. For example, user IDs must
be created before they can be modified.

Special keys begin with '_'. Special keys are different in that they are not processed as a simple compare and update
differences. Special keys are used to capture, refresh, and create switches. Creating switches and adding ports are
treated as special circumstances abe they have timing and other considerations which are addressed by modules in the
brcdapi library. 

+-------+-----------+-----------------------------------------------------------------------------------------------+
| Key   | Type      | Description                                                                                   |
+=======+===========+===============================================================================================+
| a     | method    | Pointer to method to call when interpreting the branch. If None or not present, the URI is    |
|       |           | put in _full_capture_l, so a GET is performed, but no action is taken.                        |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| e     | str       | Text to append to error messages. Only useful for trouble shooting.                           |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| fid   | str       | 'all' for all logical switches. 'default' for the default switch only. 'all_non_default' for  |
|       |           | logical switches that are not the default. May also be specific FID or CSV list of FIDs or    |
|       |           | range of FIDs. None or not present implies the operation is for a chassis                     |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| k     | str       | KPI (URI not including the leading 'running/' or anything prior). Only used if the action     |
|       |           | method needs to access an API resource. May be a CSV if multiple KPIs are required.           |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| m     | HTTP      | HTTP method                                                                                   |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| rl    | str, list | Data specific to the action method.                                                           |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| p     | None, str | If None, always execute this entry. Otherwise, the entry is only executed if specified with   |
|       |           | the -p option on the command line. See -p options description in _get_input() for details.   |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| rw    | dict      | Dictionary of leaf names that support read and write. The value is a pointer to a method that |
|       |           | interprets the value for the leaf. At the time this was written, there were only two options: |
|       |           |                                                                                               |
|       |           |   _conv_none_act      Always returns None. None is assumed for any leaf not in the            |
|       |           |                       dictionary so this is only useful as a place holder for a leaf you may  |
|       |           |                       want to change at a future date.                                        |
|       |           |                                                                                               |
|       |           |   _conv_lookup_act    A simple deepcopy of what ever the value for the  leaf is.              |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| skip  | bool      | If True, skip this item. Essentially comments out this entry. Set True for all untested       |
|       |           | entries.                                                                                      |
+-------+-----------+-----------------------------------------------------------------------------------------------+

A basic capture (capture_0) is required for to set the ports in the default switch to the default state
(_ports_to_default) or for deleting (_del_switches), creating logical switches (_restore_switches),
and restoring ports (_restore_ports). Data should always be cleared (_data_clear) before capturing (_data_capture) a
fresh set of data. A fresh set of data should always be captured after making changes that may effect other
operations.

For a partial restore, comment out any entries in _control_d you don't want to modify.

The following key/value pairs are added to the dictionaries in _control_d as data is collected:

+-------------------+---------------+-------------------------------------------------------------------------------+
| Key               | Type          | Description                                                                   |
+===================+===============+===============================================================================+
| session           | dict          | Session object returned from brcdapi.fos_auth.login()                         |
+-------------------+---------------+-------------------------------------------------------------------------------+
| r_chassis_obj     | ChassisObj    | Restore from chassis object.                                                  |
+-------------------+---------------+-------------------------------------------------------------------------------+
| t_chassis_obj     | ChassisObj    | Target chassis object.                                                        |
+-------------------+---------------+-------------------------------------------------------------------------------+
| default_fid       | int           | Default FID                                                                   |
+-------------------+---------------+-------------------------------------------------------------------------------+
| fid               | dict          | Key value pairs are:                                                          |
|                   |               |   default         List with one entry, the default switch FID of the restore  |
|                   |               |                   chassis                                                     |
|                   |               |   all             List of all FIDs in the restore chassis                     |
|                   |               |   all_non_default List of all FIDs in the restore chassis except the default  |
|                   |               |                   FID                                                         |
+-------------------+---------------+-------------------------------------------------------------------------------+

WARNING: This is a template with some suggestions. Anything with _conv_none_act or _none_act in most cases is a work
         in progress
"""

_control_d = collections.OrderedDict()
_control_d['_control'] = collections.OrderedDict()
_action_l = [
    # vf: These actions set all ports to the default configuration and delete all non-default logical switches.

    dict(a=_data_capture, rl=_basic_capture_kpi_l, e='Basic Capture 0', p='vf'),
    dict(k='brocade-chassis/chassis', a=_vf_enable, e='_vf_enable', p='vf', rw={'vf-enabled': _conv_lookup_act}),
    # Just set the port in the default switch to the default configuration because the next action, _del_switches,
    # sets all ports in the logical switch to the port defaults before deleting the switch
    dict(a=_ports_to_default, fid='default', e='_ports_to_default', p='vf'),
    dict(a=_del_switches, fid='all_non_default', e='_del_switches', p='vf'),
    dict(a=_data_clear, e='_data_clear 1', p='vf'),
    dict(a=_data_capture, rl=_basic_capture_kpi_l, e='Basic Capture 1', p='vf'),
    dict(k='brocade-fabric/fabric-switch', a=_restore_switches, fid='all_non_default', e='_restore_switches', p='vf'),
    dict(a=_data_clear, e='_data_clear 2', p='vf'),
    dict(a=_data_capture, rl=_basic_capture_kpi_l, e='Basic Capture 2', p='vf'),
    dict(k='brocade-interface/fibrechannel', a=_restore_ports, fid='all_non_default', e='_restore_ports', p='vf'),
    dict(a=_data_clear, e='_data_clear 3', p='vf'),

    # Capture a full set of data before continuing.
    dict(a=_data_capture, rl=_full_capture_l, e='Full Capture'),

    # c: Chassis parameters
    dict(k='brocade-chassis/chassis', a=_chassis_update_act, m='PATCH', p='c', rw={
        'chassis-user-friendly-name': _conv_lookup_act,
        'fcr-enabled': _conv_lookup_act,
        'chassis-enabled': _conv_none_act,
        'shell-timeout': _conv_lookup_act,
        'session-timeout': _conv_lookup_act,
        'tcp-timeout-level': _conv_lookup_act,
    }),
    # Not tested
    dict(k='brocade-chassis/management-interface-configuration', a=_none_act, m='PATCH', p='c', skip=True, rw={
        'rest-enabled,https-protocol-enabled': _conv_lookup_act,
        'max-rest-sessions': _conv_lookup_act,
        'https-keep-alive-enabled': _conv_none_act,
        'cp-name': _conv_lookup_act,
        'interface-name': _conv_lookup_act,
        'auto-negotiate': _conv_lookup_act,
        'speed': _conv_lookup_act,
        'lldp-enabled': _conv_lookup_act,
    }),
    # Not tested
    dict(k='brocade-chassis/management-port-track-configuration', a=_none_act, m='PATCH', p='c', skip=True, rw={
        'tracking-enabled,scan-interval': _conv_lookup_act,
    }),
    dict(k='brocade-chassis/credit-recovery', a=_none_act, m='PATCH', p='c', skip=True, rw={  # Not tested
        'mode': _conv_lookup_act,
        'link-reset-threshold': _conv_lookup_act,
        'fault-option': _conv_lookup_act,
        'backend-credit-loss-enabled': _conv_lookup_act,
        'backend-loss-of-sync-enabled': _conv_lookup_act,
    }),

    # s: Security
    dict(k='brocade-security/user-config', a=_user_act, m='POST', p='s', rw={
        'name': _conv_lookup_act,
        'password': _default_user_pw_act,
        # 'role': _conv_lookup_act,  # In the Rest API Guide but not present in FOS
        'account-description': _conv_lookup_act,
        'account-enabled': _conv_lookup_act,
        'password-change-enforced': _true_act,
        # 'account-locked': _conv_lookup_act,  # FOS defect? I get an error no matter how I set this
        'access-start-time': _conv_lookup_act,
        'access-end-time': _conv_lookup_act,
        'home-virtual-fabric': _conv_lookup_act,
        'chassis-access-role': _conv_lookup_act,
        'virtual-fabric-role-id-list': _conv_lookup_act,
    }),
    dict(k='brocade-security/user-specific-password-cfg', a=_none_act, m='POST', p='s', skip=True),  # Not tested
    dict(k='brocade-security/auth-spec', a=_none_act, m='POST', p='s', skip=True),  # Not tested

    # Logging
    dict(k='brocade-logging/audit', a=_none_act, m='PATCH', p='l', skip=True, rw={  # Not tested
        'audit-enabled': _conv_lookup_act,
        'severity-level': _conv_lookup_act,
        'filter-class-list': _conv_lookup_act,
    }),
    dict(k='brocade-logging/syslog-server', a=_none_act, m='PATCH', p='s', skip=True, rw={  # Not tested
        'server': _conv_lookup_act,
        'port': _conv_lookup_act,
        'secure-mode': _conv_lookup_act,
    }),
    dict(k='brocade-logging/raslog', a=_none_act, m='PATCH', p='s', skip=True, rw={  # Not tested
        'audit-enabled': _conv_lookup_act,
        'severity-level': _conv_lookup_act,
        'filter-class-list': _conv_lookup_act,
    }),
    dict(k='brocade-logging/raslog-module', a=_none_act, m='PATCH', p='s', skip=True, rw={  # Not tested
        'module-id': _conv_lookup_act,
        'log-enabled': _conv_lookup_act,
    }),
    dict(k='brocade-logging/log-quiet-control', a=_none_act, m='PATCH', p='s', skip=True, rw={  # Not tested
        'log-type': _conv_lookup_act,
        'quiet-enabled': _conv_lookup_act,
        'start-time': _conv_lookup_act,
        'end-time': _conv_lookup_act,
        'days-of-week': _conv_lookup_act,
    }),
    dict(k='brocade-logging/log-setting', a=_none_act, m='PATCH', p='s', skip=True, rw={  # Not tested
        'syslog-facility-level': _conv_lookup_act,
        'keep-alive-period': _conv_lookup_act,
        'clear-log': _conv_lookup_act,
    }),
    dict(k='brocade-logging/supportftp', a=_none_act, m='PATCH', p='s', skip=True, rw={  # Not tested
        'host': _conv_lookup_act,
        'user-name': _conv_lookup_act,
        'password': _conv_lookup_act,
        'remote-directory': _conv_lookup_act,
        'auto-enabled': _conv_lookup_act,
        'protocol': _conv_lookup_act,
        'port': _conv_lookup_act,
        'onnectivity-check-interval': _conv_lookup_act,
    }),

    dict(k='brocade-fibrechannel-switch/chassis-config-settings', a=_chassis_update_act, m='PATCH', rl='name', p='c',
         rw={
             'firmware-synchronization-enabled': _conv_lookup_act,
             'http-session-ttl': _conv_lookup_act,
             'ezserver-enabled': _conv_lookup_act,
             'cs-ctl-mode': _conv_lookup_act,
             'sddq-limit': _conv_lookup_act,
             'vtap-qos-compatibility-mode': _conv_lookup_act,
             'secure-mode-enabled': _conv_lookup_act,
             'file-suffix-enabled': _conv_lookup_act,
             # 'custom-index': _conv_lookup_act  # Probably only useful for OEM build out process
         }),

    # Logical Switch Configurations: General
    dict(k='brocade-fibrechannel-switch/fibrechannel-switch', a=_switch_update_act, m='PATCH', rl='name', p='s',
         rw={
             'domain-id': _conv_lookup_act,
             'user-friendly-name': _conv_lookup_act,
             'ip-address': _conv_lookup_act,  # WIP
             'ip-static-gateway-list': _conv_lookup_act,  # WIP
             'subnet-mask': _conv_lookup_act,  # WIP
             'ipfc-address': _conv_lookup_act,  # WIP
             'ipfc-subnet-mask': _conv_lookup_act,  # WIP
             'domain-name': _conv_lookup_act,  # WIP
             'dns-servers': _conv_lookup_act,
             'fabric-user-friendly-name': _conv_lookup_act,
             'ag-mode': _conv_lookup_act,
             'ag-mode-string': _conv_lookup_act,  # WIP
             'banner': _conv_lookup_act,
             'in-order-delivery-enabled': _conv_lookup_act,
             'dynamic-load-sharing': _conv_lookup_act,
             'advanced-performance-tuning-policy': _conv_lookup_act,
             'lacp-system-priority': _conv_lookup_act,
             'switch-persistent-enabled': _conv_lookup_act,
         }),
    dict(k='brocade-fibrechannel-switch/switch-configuration', a=_switch_update_act, m='PATCH', rl='name', p='s', rw={
        'trunk-enabled': _conv_lookup_act,
        'wwn-port-id-mode': _conv_lookup_act,
        'edge-hold-time': _conv_lookup_act,
        'area-mode': _conv_lookup_act,
        'xisl-enabled': _conv_lookup_act,
    }),
    dict(k='brocade-fibrechannel-switch/f-port-login-settings', a=_switch_update_act, m='PATCH', rl='name', p='s', rw={
        'max-logins': _conv_lookup_act,
        'max-flogi-rate-per-switch': _conv_lookup_act,
        'stage-interval': _conv_lookup_act,
        'free-fdisc': _conv_lookup_act,
        'enforce-login': _conv_lookup_act,
        'enforce-login-string': _conv_none_act,
        'max-flogi-rate-per-port': _conv_lookup_act,
    }),
    dict(k='brocade-fibrechannel-switch/port-configuration', a=_switch_update_act, m='PATCH', rl='name', p='s', rw={
        'portname-mode': _conv_lookup_act,
        'dynamic-portname-format': _conv_lookup_act,
        'dynamic-d-port-enabled': _conv_lookup_act,
        'on-demand-d-port-enabled': _conv_lookup_act,
    }),
    dict(k='brocade-fibrechannel-switch/zone-configuration', a=_switch_update_act, m='PATCH', rl='name', p='s', rw={
        'node-name-zoning-enabled': _conv_lookup_act,
        'fabric-lock-timeout': _conv_lookup_act,
    }),
    # Not tested. Below might be done in the vf section when creating logical switches.
    dict(k='brocade-fibrechannel-switch/fabric', a=_switch_update_act, m='PATCH', rl='name', p='s', rw={
        'insistent-domain-id-enabled': _conv_lookup_act,
        'principal-selection-enabled': _conv_lookup_act,
        'principal-priority': _conv_lookup_act,
        'preserved-domain-id-mode-enabled': _conv_lookup_act,
    }),

    # MAPS - Not tested
    dict(k='brocade-maps/rule', a=_maps_rule_act, m='PATCH', p='maps', rw={
        'name': _conv_lookup_act,
        'is-rule-on-rule': _conv_lookup_act,
        'monitoring-system': _conv_lookup_act,
        'time-base': _conv_lookup_act,
        'logical-operator': _conv_lookup_act,
        'threshold-value': _conv_lookup_act,
        'actions': _conv_lookup_act,
        'event-severity': _conv_lookup_act,
        'toggle-time': _conv_lookup_act,
        'quiet-time': _conv_lookup_act,
        'un-quarantine-timeout': _conv_lookup_act,
        'un-quarantine-clear': _conv_lookup_act,
    }),

    # Logical Switch: FCR - Not tested
    dict(k='brocade-fibrechannel-routing/routing-configuration', a=_switch_update_act, m='PATCH', p='fcr', rw={
        'maximum-lsan-count': _conv_lookup_act,
        'backbone-fabric-id': _conv_lookup_act,
        'shortest-ifl': _conv_lookup_act,
        'lsan-enforce-tags': _conv_lookup_act,
        'lsan-speed-tag': _conv_lookup_act,
        'migration-mode': _conv_lookup_act,
        'persistent-translate-domain-enabled': _conv_lookup_act,
    }),
    dict(k='brocade-fibrechannel-routing/edge-fabric-alias', a=_switch_update_act, m='PATCH', p='fcr', rw={
        'edge-fabric-id': _conv_lookup_act,
        'alias-name': _conv_lookup_act,
    }),
    dict(k='brocade-fibrechannel-routing/proxy-config', a=_switch_update_act, m='PATCH', p='fcr', rw={
        'imported-fabric-id': _conv_lookup_act,
        'device-wwn': _conv_lookup_act,
        'proxy-device-slot': _conv_lookup_act,
    }),
    dict(k='brocade-fibrechannel-routing/translate-domain-config', a=_switch_update_act, m='PATCH', p='fcr', rw={
        'imported-fabric-id': _conv_lookup_act,
        'exported-fabric-id': _conv_lookup_act,
        'preferred-translate-domain-id': _conv_lookup_act,
    }),
    dict(k='brocade-fibrechannel-routing/stale-translate-domain', a=_switch_update_act, m='PATCH', p='fcr', rw={
        'imported-fabric-id': _conv_lookup_act,
        'stale-translate-domain-id': _conv_lookup_act,
    }),

    # Logical Switch: Trunking
    dict(k='brocade-fibrechannel-trunk/trunk-area', a=_switch_update_act, m='PATCH', p='fcr', rw={
        'trunk-index': _conv_lookup_act,
    }),

    # Logical Switch: FICON
    dict(k='brocade-ficon/cup', a=_switch_update_act, m='PATCH', p='ficon', rw={
        'fmsmode-enabled': _conv_lookup_act,
        'programmed-offline-state-control': _conv_lookup_act,
        'active-equal-saved-mode': _conv_lookup_act,
        'director-clock-alert-mode': _conv_lookup_act,
        'unsolicited-alert-mode-fru-enabled': _conv_lookup_act,
        'unsolicited-alert-mode-hsc-enabled': _conv_lookup_act,
        'unsolicited-alert-mode-invalid-attach-enabled': _conv_lookup_act,
    }),
    dict(k='brocade-ficon/logical-path', a=_switch_update_act, m='PATCH', p='ficon', rw={
        'link-address': _conv_lookup_act,
        'channel-image-id': _conv_lookup_act,
        'reporting-path-state': _conv_lookup_act,
    }),

    # Logical Switch Port Configurations: FCIP
    dict(k='brocade-interface/extension-ip-interface', a=_switch_update_act, m='PATCH', p='fcip', rw={
        'name': _conv_lookup_act,
        'dp-id': _conv_lookup_act,
        'ip-address': _conv_lookup_act,
        'ip-prefix-length': _conv_lookup_act,
        'mtu-siz': _conv_lookup_act,
        'vlan-id': _conv_lookup_act,
    }),

    # Logical Switch Configurations: LLDP
    dict(k='brocade-lldp/lldp-global', a=_switch_update_act, m='PATCH', p='p', rw={
        'multiplier': _conv_lookup_act,
        'tx-interval': _conv_lookup_act,
        'system-name': _conv_lookup_act,
        'system-description': _conv_lookup_act,
        'enabled-state': _conv_lookup_act,
        'optional-tlvs': _conv_lookup_act,
    }),
    dict(k='brocade-lldp/lldp-profil', a=_switch_update_act, m='PATCH', p='p', rw={
        'name': _conv_lookup_act,
        'multiplier': _conv_lookup_act,
        'tx-interval': _conv_lookup_act,
        'enabled-tlvs': _conv_lookup_act,
    }),

    # Port Configurations: General port configurations
    dict(k='brocade-interface/fibrechannel', a=_port_update_act, rl='ports', m='PATCH', rl='name', p='p', rw={
        'user-friendly-name': _conv_lookup_act,
        'protocol-speed': _conv_lookup_act,
        'g-port-locked': _conv_lookup_act,
        'e-port-disable': _conv_lookup_act,
        'n-port-enabled': _conv_lookup_act,
        'd-port-enable': _conv_lookup_act,
        'persistent-disable': _conv_lookup_act,
        'application-header-enabled': _conv_lookup_act,
        'qos-enabled': _conv_lookup_act,
        'compression-configured': _conv_lookup_act,
        'encryption-enabled': _conv_lookup_act,
        'target-driven-zoning-enable': _conv_lookup_act,
        'sim-port-enabled': _conv_lookup_act,
        'mirror-port-enabled': _conv_lookup_act,
        'credit-recovery-enabled': _conv_lookup_act,
        'f-port-buffers': _conv_lookup_act,
        'e-port-credit': _conv_lookup_act,
        'csctl-mode-enabled': _conv_lookup_act,
        'fault-delay-enabled': _conv_lookup_act,
        'octet-speed-combo': _conv_lookup_act,
        'octet-speed-combo-string': _conv_none_act,  # WIP
        'isl-ready-mode-enabled': _conv_lookup_act,
        'rscn-suppression-enabled': _conv_lookup_act,
        'los-tov-mode-enabled': _conv_lookup_act,
        'los-tov-mode-enabled-string': _conv_none_act,  # WIP
        'npiv-enabled': _conv_lookup_act,
        'npiv-pp-limit': _conv_lookup_act,
        'ex-port-enabled': _conv_lookup_act,
        'fc-router-port-cost': _conv_lookup_act,
        'edge-fabric-id': _conv_lookup_act,
        'preferred-front-domain-id': _conv_lookup_act,
        'fec-enabled': _conv_lookup_act,
        'port-autodisable-enabled': _conv_lookup_act,
        'trunk-port-enabled': _conv_lookup_act,
        'pod-license-state': _conv_lookup_act,
        'disable-reason': _conv_lookup_act,
        'port-peer-beacon-enabled': _conv_lookup_act,
        'clean-address-enabled': _conv_lookup_act,
        'congestion-signal-enabled': _conv_lookup_act,
        'ms-acl-application-server-access': _conv_lookup_act,
        'ms-acl-enhanced-fabric-configuration-server-access': _conv_lookup_act,
        'ms-acl-fabric-configuration-server-access': _conv_lookup_act,
        'ms-acl-fabric-device-management-interface-access': _conv_lookup_act,
        'ms-acl-fabric-zone-server-access': _conv_lookup_act,
        'ms-acl-unzoned-name-server-access': _conv_lookup_act,
        # 'port-generation-number': _conv_none_act,  # Relevant for rebuild?
        # 'port-scn': _conv_none_act,  # Relevant for rebuild?
    }),
    dict(k='brocade-interface/gigabitethernet', a=_port_update_act, rl='ge_ports', m='PATCH', p='p', rw={
        'name': _conv_lookup_act,
        'speed': _conv_lookup_act,
        'protocol-speed': _conv_none_act,
        'persistent-disable': _conv_lookup_act,
        'protocol': _conv_lookup_act,
        'auto-negotiation-enabled': _conv_lookup_act,
        'portchannel-member-timeout': _conv_lookup_act,
        'lldp-profile': _conv_lookup_act,
        'lldp-enabled-state': _conv_lookup_act,
    }),
    dict(k='brocade-interface/portchannel', a=_port_update_act, rl='ports', m='PATCH', p='p', rw={
        'name': _conv_lookup_act,
        'key': _conv_lookup_act,
        'portchannel-type': _conv_lookup_act,
        'admin-state-enabled': _conv_lookup_act,
        'auto-negotiation-enabled': _conv_lookup_act,
        'gigabit-ethernet-member-ports': _conv_lookup_act,
    }),

    # Zoning
    dict(a=_zone_restore, e='_zone_restore', p='z'),
]
for _d in _action_l:
    if 'e' not in _d:
        _d.update(e=str(_d.get('k')))


def _enable(cd):
    """Enable all non-default switches and ports.

    :param cd: Session, project info, etc. See local_control_d in pseudo_main()
    :type cd: dict
    :return: List of error messages as str encountered.
    :rtype: list
    """
    try:
        el = list()
        fid_l = [f for f in cd['r_chassis_obj'].r_fid_list() if f != cd['default_fid']]
        # A logical switch can be busy for up to 10 sec after enabling it so enable all the switches, then the ports
        for fid in fid_l:  # Enable the logical switches
            obj = brcdapi_switch.fibrechannel_switch(cd['session'], fid, {'is-enabled-state': True}, None, False)
            if fos_auth.is_error(obj):
                el.extend(['Failed to enable FID ' + str(fid), fos_auth.formatted_error_msg(obj)])
        for fid in fid_l:  # Enable the ports
            r_switch_obj = cd['r_chassis_obj'].r_switch_obj_for_fid(fid)
            obj = brcdapi_port.enable_port(cd['session'], fid, r_switch_obj.r_port_keys() + r_switch_obj.r_ge_port_keys(),
                                           persistent=True, echo=False)
            if fos_auth.is_error(obj):
                el.extend(['Failed to enable FID ' + str(fid), fos_auth.formatted_error_msg(obj)])
    except BaseException as e:
        brcdapi_log.exception(_fmt_errors(['Software error. Exception:', e]))
        el.append('Software error. Check the log for "brcdapi library exception call"')
    return el


def _get_input():
    """Retrieves the command line input, reads the input Workbook, and validates the input

    :return ec: Error code from brcddb.brcddb_common
    :rtype ec: int
    :return args_ip: IP address of chassis to modify
    :rtype args_ip: str
    :return args_id: Login user ID
    :rtype args_id: str
    :return args_pw: Login password
    :rtype args_pw: str
    :return args_s: 'none' for HTTP or 'self' for HTTPS
    :rtype args_s: str
    :return chassis_obj: Chassis object to restore from
    :rtype chassis_obj: brcddb.classes.chassis.ChassisObj
    :return option_params: Name of workbook to read actions from
    :rtype option_params: str
    :return args_e: If True, enable all non-default switch and ports
    :rtype args_e: bool
    """
    global _DEBUG, __version__, _action_l

    # Initialize the return variables
    proj_obj, chassis_obj, action_l, ec = None, None, list(), brcddb_common.EXIT_STATUS_OK

    # Get shell input
    global _eh, _DEBUG, _DEBUG_ip, _DEBUG_id, _DEBUG_pw, _DEBUG_s, _DEBUG_i, _DEBUG_eh, _DEBUG_scan, _DEBUG_p
    global _DEBUG_e, _DEBUG_d, _DEBUG_sup, _DEBUG_log, _DEBUG_nl

    if _DEBUG:
        args_ip, args_id, args_pw, args_s, args_wwn, args_scan, args_eh, args_p, args_e =\
            _DEBUG_ip, _DEBUG_id, _DEBUG_pw, _DEBUG_s, _DEBUG_wwn, _DEBUG_scan, _DEBUG_eh, _DEBUG_p, _DEBUG_e
        args_i = brcdapi_file.full_file_name(_DEBUG_i, '.json')
        args_d,  args_sup, args_log, args_nl = _DEBUG_d, _DEBUG_sup, _DEBUG_log, _DEBUG_nl
    else:
        parser = argparse.ArgumentParser(description='Restores a chassis configuration to a previous configuration.')
        op_buf = 'Required unless using the -scan or -eh options. '
        parser.add_argument('-ip', help=op_buf + 'IP address', required=False)
        parser.add_argument('-id', help=op_buf + 'User ID', required=False)
        parser.add_argument('-pw', help=op_buf + 'Password', required=False)
        parser.add_argument('-s', help='(Optional) "none" for HTTP, default, or "self" for HTTPS mode.',
                            required=False)
        parser.add_argument('-p', help='Required. Option parameter. Use -eh for details.', required=False)
        buf = 'Captured data file from the output of capture.py, combine.py, or multi_capture.py. ".json" is '\
              'automatically appended.'
        parser.add_argument('-i', help=buf, required=False)
        buf = 'Optional (required if multiple chassis are in the captured data, -i). WWN of chassis in the input file'\
              ', -i, to be restored to the chassis specified with -ip.'
        parser.add_argument('-wwn', help=buf, required=False)
        parser.add_argument('-z', help='Optional. No parameters. Restore zoning as well.', action='store_true',
                            required=False)
        buf = 'Optional. Scan input file, -i, and generate a report with all chassis WWNs. No other processing is ' \
              'performed.'
        parser.add_argument('-scan', help=buf, action='store_true', required=False)
        buf = 'Optional. No parameters. When specified, additional help is displayed. No other processing is performed'
        parser.add_argument('-eh', help=buf, action='store_true', required=False)
        buf = 'No parameters. When specified, all logical switches that were enabled in the restore chassis are '\
              'enabled and all ports that were enabled in the restore chassis are enabled.'
        parser.add_argument('-e', help=buf, action='store_true', required=False)
        buf = 'Optional. Suppress all output to STD_IO except the exit code and argument parsing errors. Useful with ' \
              'batch processing where only the exit status code is desired. Messages are still printed to the log ' \
              'file. No operands.'
        parser.add_argument('-sup', help=buf, action='store_true', required=False)
        buf = '(Optional) No parameters. When set, a pprint of all content sent and received to/from the API, except ' \
              'login information, is printed to the log.'
        parser.add_argument('-d', help=buf, action='store_true', required=False)
        buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The ' \
              'log file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
        parser.add_argument('-log', help=buf, required=False, )
        buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
        parser.add_argument('-nl', help=buf, action='store_true', required=False)
        args = parser.parse_args()
        args_ip, args_id, args_pw, args_s, args_wwn, args_scan, args_eh, args_p, args_e =\
            args.ip, args.id, args.pw, args.s, args.wwn, args.scan, args.eh, args.p, args.e
        args_i = brcdapi_file.full_file_name(args.i, '.json')
        args_d, args_sup, args_log, args_nl = args.d,  args.sup, args.log, args.nl

    # Set up logging
    if args_d:
        brcdapi_rest.verbose_debug = True
    if args_sup:
        brcdapi_log.set_suppress_all()
    if not args_nl:
        brcdapi_log.open_log(args_log)

    # Is the security method valid?
    if args_s is None:
        args_s = 'none'
    elif args_s != 'self' and args_s != 'none':
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
        
    # User feedback
    ml = [
        'chassis_restore.py version: ' + __version__,
        'IP address, -ip:         ' + brcdapi_util.mask_ip_addr(args_ip),
        'ID, -id:                 ' + str(args_id),
        'HTTPS, -s:               ' + str(args_s),
        'Input file, -i:          ' + str(args_i),
        'WWN, -wwn:               ' + str(args_wwn),
        'Option parameters, -p:   ' + str(args_p),
        'Enable, -e:              ' + str(args_e),
        'Scan, -scan:             ' + str(args_scan),
        ]
    if _DEBUG:
        ml.insert(0, 'WARNING!!! Debug is enabled')
    brcdapi_log.log(ml, echo=True)

    # Validate the input.
    ml = list()
    if args_eh:
        ml.extend(_eh)
    elif not args_scan and args_wwn is None:
        for k, v in dict(ip=args_ip, id=args_id, pw=args_pw, i=args_i, p=args_p).items():
            if v is None:
                ml.append('Missing -' + k + '. Re-run with -h or -eh for additional help.')

    if len(ml) == 0:
        # Read the project file
        try:
            proj_obj = brcddb_project.read_from(args_i)
            if proj_obj is None:
                ml.append('File, -i, appears to be corrupted: ' + args_i)
            else:
                chassis_obj_l = proj_obj.r_chassis_objects()
            if args_scan:
                for chassis_obj in chassis_obj_l:
                    ml.append(brcddb_chassis.best_chassis_name(chassis_obj, wwn=True))
                    ml.extend(['  ' + brcddb_switch.best_switch_name(switch_obj, fid=True, did=True)
                               for switch_obj in chassis_obj.r_switch_objects()])
            else:
                if args_wwn is not None:
                    chassis_obj = proj_obj.r_chassis_obj(args_wwn)
                    if chassis_obj is None:
                        ml.append('Could not find a chassis matching ' + args_wwn + ' in ' + args_i)
                else:
                    num_chassis = len(chassis_obj_l)
                    if num_chassis == 0:
                        ml.append('There are no chassis in the input file, -i: ' + args_i)
                    elif num_chassis == 1:
                        chassis_obj = chassis_obj_l[0]
                    else:
                        ml.extend(['Multiple chassis found in ' + args_i,
                                   'Specify with the chassis to restore from using the -wwn option.',
                                   'Re-run with -scan for a list of available chassis.'])
        except (FileExistsError, FileNotFoundError):
            ml.append('Input file, -i, not found: ' + args_i)
            
        # Get the list of actions
        args_p_l = args_p.split(',')
        if '*' in args_p_l:
            action_l = [d for d in _action_l if not bool(d.get('skip'))]
        else:
            error_d = dict()
            for action_d in _action_l:
                if not bool(action_d.get('skip')):
                    for p in args_p_l:
                        if p not in _restore_parameters:
                            if not bool(error_d.get(p)):
                                ml.append('Unknown parameter, ' + p + ', in option parameters, -p')
                                error_d.update({p: True})
                        pl = gen_util.convert_to_list(action_d.get('p'))  # Future proofing to allow lists
                        if len(pl) == 0 or p in pl:  # if 'p' is not specified in the action it is mandatory
                            action_l.append(action_d)
                            break

    if len(ml) > 0:
        ml.insert(0, '')
        brcdapi_log.log(ml, echo=True)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    return ec, args_ip, args_id, args_pw, args_s, chassis_obj, action_l, args_e


def pseudo_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code. See exit codes in brcddb.brcddb_common
    :rtype: int
    """
    global _basic_capture_kpi_l, _full_capture_l

    ec, ip, user_id, pw, sec, r_chassis_obj, action_l, e_flag = _get_input()
    if ec != brcddb_common.EXIT_STATUS_OK:
        return ec
    el = list()

    # Get a project object and some basic info for the chassis to be modified
    proj_obj = brcddb_project.new('Chassis to be modified', datetime.datetime.now().strftime('%d %b %Y %H:%M:%S'))
    proj_obj.s_python_version(sys.version)
    proj_obj.s_description(r_chassis_obj.r_project_obj().r_description())

    # Figure out what data to capture
    for d in action_l:
        key = d.get('k')
        if isinstance(key, str):
            for sub_key in key.split(','):
                if sub_key not in _full_capture_l:
                    _full_capture_l.append('running/' + sub_key)

    # Login
    session = api_int.login(user_id, pw, ip, sec, proj_obj)
    if fos_auth.is_error(session):
        brcdapi_log.log(fos_auth.formatted_error_msg(session), echo=True)
        return brcddb_common.EXIT_STATUS_ERROR
    local_control_d = dict(type='local_control_d', session=session, proj_obj=proj_obj, r_chassis_obj=r_chassis_obj,
                           default_fid=r_chassis_obj.r_default_switch_fid())  # type is used in error reporting

    try:
        for d in action_l:
            brcdapi_log.log('chassis_restore action: ' + d['e'], echo=True)
            el.extend(d['a'](local_control_d, d))
        if e_flag:
            el.extend(_enable(local_control_d))
    except KeyboardInterrupt:
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
        el.append('Processing terminated by user.')
    except RuntimeError:
        ec = brcddb_common.EXIT_STATUS_API_ERROR
        el.append('Programming error encountered while processing ' + str(d.get('e')) + 'See previous message')
    except BaseException as e:
        ec = brcddb_common.EXIT_STATUS_ERROR
        el.extend(_fmt_errors(['Software error while processing:', d.get('e'), 'Exception:', e]))

    # Logout
    obj = brcdapi_rest.logout(session)
    if fos_auth.is_error(obj):
        el.append(fos_auth.formatted_error_msg(obj))

    if len(el) > 0:
        brcdapi_log.log(el, echo=True)

    return ec


##################################################################
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
