#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright 2023, 2024, 2025, 2026 Jack Consoli.  All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may also obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.

The license is free for single customer use (internal applications). Use of this module in the production,
redistribution, or service delivery for commerce requires an additional license. Contact jack_consoli@yahoo.com for
details.

**Outstanding**

    ToDo - Put in single file. Finish all LS configuration first.
    ToDo - Remove: WWN Based persistent PID and Allow XISL Use in base switch configure
    ToDo - Add port configurations to columns in workbook
    ToDo - Bug fix: -base and -ficon is missing in the lscfg command string

**Description**

Reads a switch configuration workbook and creates the CLI commands necessary to create and configure logical switches.

**Notes**

    *   Intended for internal Broadcom use only
    *   In case you are wondering why this is more complicated than it needs to be: To fulfill a need for FOS switch
        configuration commands switch_config.py was modified to generate CLI instead of making API calls to a switch.
        Since switch_config.py already used the brcddb libraries which uses data constructs specific to the API,
        continuing to use them was an expedient.
    *   There was also a need to check and validate the workbooks before attempting to make switch changes via the API
        so rather than add a test option to switch_config.py, this module is used.

**Version Control**

+-----------+---------------+---------------------------------------------------------------------------------------+
| Version   | Last Edit     | Description                                                                           |
+===========+===============+=======================================================================================+
| 1.0.0     | 25 Aug 2025   | Initial launch                                                                        |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 1.0.1     | 19 Oct 2025   | Updated comments only.                                                                |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 1.0.2     | 20 Feb 2026   | Updated copyright notice.                                                             |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 1.0.3     | 10 Mar 2026   | Added port configuration commands from the CLI column.                                |
+-----------+---------------+---------------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2024, 2025, 2026 Jack Consoli'
__date__ = '10 Mar 2026'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack_consoli@yahoo.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '1.0.3'

import os
import collections
import brcdapi.log as brcdapi_log
import brcdapi.port as brcdapi_port
import brcdapi.gen_util as gen_util
import brcdapi.util as brcdapi_util
import brcdapi.file as brcdapi_file
import brcddb.brcddb_common as brcddb_common
import brcddb.report.utils as report_utils

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation

# Input parameter definitions
_input_d = dict(
    i=dict(h='Required. File name of Excel Workbook to read.'),
    o=dict(h='Required. File name prefix for FOS commands. One output file is generated for each logical switch. The '
             'file name for each logical switch is this prefix appended with "_fid.txt"'),
)
_input_d.update(gen_util.parseargs_log_d.copy())

_fc_switch = 'running/brocade-fibrechannel-switch/'
_fc_config = 'running/brocade-fibrechannel-configuration/'
_fc_ficon = 'running/brocade-ficon/'
_MAX_ZONE_MEM = 10
_MAX_LINES = 20
_preamble_l = [
    '# WARNINGS:',
    '#   * Not responsible for errors.',
    '#   * These steps are intended for new installs. Many of them are disruptive.',
    '#   * Carefully check the switch configuration before putting it into production.',
    '#   * Except for the chassis name, these instructions are limited to logical',
    '#     switch and port configuration only.',
    '',
    '# NOTES:',
    '#   * In all examples, the -f option, force, suppresses "are you sure" questions.',
    '#   * Copy and paste has some odd behavior sometimes. Make sure what you pasted matches what you copied.',
    '#   * You can copy multiple lines of commands and paste into an SSH session but do not copy and paste ',
    '#     beyond a blank line. If you encounter a blank line, let all previous commands complete before',
    '#     continuing',
    '#   * Insistent Domain ID is automatically set for ficon switches and therefore, setting it is not an',
    '#     option in the configure command.',
    '',
]
_chassis_config_l = [
    '########################################################',
    '#                                                      #',
    '#            Chassis Configuration                     #',
    '#                                                      #',
    '########################################################',
    '',
    '# Make sure virtual fabrics (VF) is enabled',
    '',
    'fosconfig --show',
    '',
    '# If Virtual Fabric is not enabled:',
    '',
    'chassisdisable -force',
    '',
    'fosconfig --enable vf',
    '',
    'chassisenable',
    '',
]
_switch_configuration_0_l = [
    '',
    '########################################################',
    '#                                                      #',
    '#    Create Logical Switch With Basic Configuration    #',
    '#                                                      #',
    '########################################################',
    ''
]
_validate_l = [
    '',
    '########################################################',
    '#                                                      #',
    '#                  Validation                          #',
    '#                                                      #',
    '########################################################',
    '',
    '# NOTE: In-order delivery is a legacy setting that is no longer required.',
    '',
    '# Command                         Description',
    '#-----------------------------------------------------------------------------',
    '# secpolicyshow                   Should contain all switch WWNs in the fabric',
    '# fddcfg -showall                 Should be: Fabric Wide Consistency Policy:- "SCC:S"',
    '# aptpolicy                       1 - PBR (deprecated), 2 - DBR, 3 - EBR (FiDR)',
    '#                                 The aptpolicy must be the same in all switches.',
    '# configshow | grep -i ididmode   Should be fabric.ididmode:1',
    '# configshow | grep -i hifmode    Should be fabric.hifmode:1',
    '# configshow | grep -i wwnpidmode Should be fabric.wwnPidMode:0',
    '',
    'secpolicyshow',
    'fddcfg --showall',
    'aptpolicy',
    '',
    'configshow | grep -i ididmode',
    '',
    'configshow | grep -i hifmode',
    '',
    'configshow | grep -i wwnpidmode',
    '',
    '# If any of the validation checks fail, the easiest solution is to simply delete the logical',
    '# switch and start over. To delete the logical switch: "lscfg --delete fid", where fid is the',
    '# Fabric ID number.',
    '',
    ]
_cup_l = [
    '# Enable CUP',
    '',
    'ficoncupset fmsmode enable',
    '',
    '# Validate the CUP settings.',
    '# ficoncupshow MIHPTO             Should be 180',
    '# ficoncupshow fmsmode            Must be enabled',
    '# ficoncupshow modereg            Make sure Active=Saved Mode (ASM) bit is set.',
    '#                                 POSC UAM ASM DCAM ACP HCP',
    '#                                 ------------------------------',
    '#                                 1    0   1   0    1   0',
    '',
    'ficoncupshow MIHPTO',
    'ficoncupshow fmsmode',
    'ficoncupshow modereg',
    '',
]
_switch_configuration_1_l = [
    '# The configure command has multiple interactive sections. Some of the response below may be',
    '# the default in which case you can just click on "enter" to accept the default. For any',
    '# parameter not explicitly defined below, accept the default by pressing the "enter" key.',
    '# Change only these settings (the order may be different on your switch):',
    '',
    'configure',
    '',
    '# Fabric parameters: yes',
]
_switch_configuration_2_l = [
    '# Accept all other settings by simply pressing the enter key.',
    '',
]
_port_configuration_l = [
    '',
    '########################################################',
    '#                                                      #',
    '#               Port Configuration                     #',
    '#                                                      #',
    '########################################################',
    '',
    '# Some ports may already be reserved. Ignore error messages to that effect.',
]
_zoning_l = [
    '',
    '########################################################',
    '#                                                      #',
    '#                     Zoning                           #',
    '#                                                      #',
    '########################################################',
    '',
    '# Consider replacing these generic zone object names. Zone object names are used',
    '# in multiple places so make sure all are replaced. For FICON switches, it is',
    '# assumed that all ports should be in the zone. If that assumption is incorrect,',
    '# you will need to adjust these commands accordingly.'
    '',
]
_enable_l = [
    '',
    '########################################################',
    '#                                                      #',
    '#               Enable Commands                        #',
    '#                                                      #',
    '########################################################',
    '',
]
_aptpolicy_d = {'default': list(), 'device-based': ['aptpolicy 2', ''], 'exchange-based': ['aptpolicy 3', '']}


def _chassis_commands(chassis_d):
    """Generate the chassis commands

    :param chassis_d: Chassis object as returned from report_utils.parse_switch_file()
    :type chassis_d: dict
    :return: List of chassis configuration commands
    :rtype: list
    """
    global _chassis_config_l

    cmd_l = _chassis_config_l.copy()
    try:
        chassis_name = chassis_d['running/brocade-chassis/chassis']['chassis-user-friendly-name']
        cmd_l.extend(['# Chassis Name', '', 'chassisname ' + chassis_name, ''])
    except (KeyError, TypeError):
        pass

    return cmd_l


def _configuration_checks(switch_d_l):
    """Some basic chassis configuration checks.

    :param switch_d_l: List of switch object as returned from report_utils.parse_switch_file()
    :type switch_d_l: list
    :return: Error messages. List is empty if no errors found
    :rtype: list
    """
    rl, base_l = list(), list()

    # Note: duplicate FID checking is done in brcddb.report.utils.parse_switch_file() so there is no need to do it here.
    for switch_d in switch_d_l:
        switch_did = gen_util.get_key_val(switch_d, _fc_switch+'fibrechannel-switch/domain-id')

        if switch_d['switch_info']['switch_type'] == 'base':
            base_l.append(switch_d)  # Used to check for, and report if necessary, duplicate base switches

        # Does the domain ID in the switch definition match the domain ID in the port worksheets?
        # When written, rl_index will always be 0 here. This was set up so that message could be added to rl prior to
        # getting here.
        rl_index = len(rl)
        for port_d in switch_d['port_d'].values():
            port_did = port_d.get('did')
            if isinstance(port_did, int) and port_did != switch_did:
                rl.append('  ' + port_d['port'] + ' DID: ' + str(port_did))
        if len(rl) > rl_index:
            buf = 'The switch DID, ' + str(switch_did) + ', for ' + switch_d['switch_info']['sheet_name'] +\
                  ' does not match the DID for the following ports:'
            rl.insert(rl_index, buf)

        # Does the banner contain any invalid characters?
        banner = gen_util.get_key_val(switch_d, _fc_switch+'fibrechannel-switch/banner')
        if isinstance(banner, str):
            v_banner = gen_util.valid_banner.sub('-', banner)
            if banner != v_banner:
                # Fix and report the issue. Note that by reporting the error to the log rather than rl allows the
                # script to continue running. This isn't a big enough problem to halt processing.
                gen_util.add_to_obj(switch_d, _fc_switch+'fibrechannel-switch/banner', v_banner)
                buf = 'Invalid characters in banner for FID on ' + switch_d['switch_info']['sheet_name'] + \
                      '. Replaced invalid characters with "-"'
                brcdapi_log.log(buf, echo=True)

    # Check for > 1 base switch
    if len(base_l) > 1:
        rl.append('Multiple base switches defined:')
        rl.extend(['  ' + switch_d['switch_info']['sheet_name'] for switch_d in base_l])

    return rl


def _switch_commands(switch_d):
    """Generate the commands to create a logical switch

    :param switch_d: Switch object as returned from report_utils.parse_switch_file()
    :type switch_d: dict
    :return: List of logical switch configuration commands
    :rtype: list
    """
    global _switch_configuration_0_l, _switch_configuration_1_l, _switch_configuration_2_l, _aptpolicy_d, _fc_config

    fid = str(switch_d['switch_info']['fid'])
    xisl = '' if bool(gen_util.get_struct_from_obj(switch_d, _fc_config+'switch-configuration/xisl-enabled')) \
        else ' -lisldisable'

    # Get a list of ports by slot for this switch. Ordered to simplify adding ports to slots by port range
    port_l = brcdapi_port.sort_ports([str(k) for k in switch_d['port_d'].keys()])
    slot_d = collections.OrderedDict()
    for port in port_l:
        temp_l = port.split('/')
        d = slot_d.get(temp_l[0])
        if d is None:
            d = dict(p=list(), ge=list())
            slot_d.update({temp_l[0]: d})
        if 'ge' in temp_l[1].lower():
            d['ge'].append(int(temp_l[1].lower().replace('ge', '')))
        else:
            d['p'].append(int(temp_l[1]))
    switch_d.update(_slot_d=slot_d)  # To save the time of figuring this out again when configuring the ports

    # Create the logical switch
    cmd_l = _switch_configuration_0_l.copy()
    if len(xisl) > 0:
        cmd_l.extend(['# WARNING: The "-lisldisable" option was added in FOS v9.1. If the command below',
                      '# fails, retry without the "-lisldisable" and disable XISL in the next step.',
                      ''])
    buf = '' if 'open' in switch_d['switch_info']['switch_type'] else ' -' + switch_d['switch_info']['switch_type']
    cmd_l.extend(['lscfg --create ' + fid + xisl + buf + ' -force', '', 'setcontext ' + fid, '', 'switchdisable', ''])
    aptpolicy = gen_util.get_key_val(switch_d, _fc_switch+'fibrechannel-switch/advanced-performance-tuning-policy')
    if aptpolicy is not None:
        cmd_l.extend(_aptpolicy_d[aptpolicy])
    cmd_l.extend(_switch_configuration_1_l)
    switch_did = gen_util.get_key_val(switch_d, _fc_switch+'fibrechannel-switch/domain-id')
    switch_idid = bool(gen_util.get_key_val(switch_d, _fc_config+'fabric/insistent-domain-id-enabled'))
    switch_port_name = gen_util.get_key_val(switch_d, _fc_config+'port-configuration/portname-mode')
    switch_xisl = bool(gen_util.get_key_val(switch_d, _fc_config+'switch-configuration/xisl-enabled'))
    switch_dup_wwn = gen_util.get_key_val(switch_d, _fc_config+'f-port-login-settings/enforce-login')
    configure_l = [dict(t='#   * Domain: ', a=str(switch_did), o=''),
                   dict(t='#   * WWN Based persistent PID: ', a='no', o=''),
                   dict(t='#   * Allow XISL Use: ',
                        a='yes' if switch_xisl else 'no (you will be asked to confirm)',
                        o=''),
                   dict(t='#   * Insistent Domain ID Mode: ',
                        a='yes' if switch_idid else 'no',
                        o=' (not an option for FICON)'),
                   dict(t='#   * Disable Default PortName: ',
                        a='no' if switch_port_name == 'default' else 'yes',
                        o=''),
                   dict(t='#   * Dynamic Portname: ', a='on' if switch_port_name == 'dynamic' else 'off', o='')]
    if switch_dup_wwn != 0:
        configure_l.append(dict(t='#   * Enforce FLOGI/FDISC login: ', a=str(switch_dup_wwn), o=''))
    for d in configure_l:
        cmd_l.append(d['t'] + d['a'] + d['o'])
    cmd_l.extend(_switch_configuration_2_l)

    # Final FICON configuration and checks
    if switch_d['switch_info']['switch_type'] == 'ficon':
        if bool(gen_util.get_key_val(switch_d, _fc_ficon+'cup/fmsmode-enabled')):
            cmd_l.extend(_cup_l)
        # FICON switches haven't always been configured properly so check
        cmd_l.extend(_validate_l)

    # Set the ports to be moved to the default configuration
    i = 0
    cmd_l.extend(['# Set the ports to be moved to the default port configuration.', ''])
    for slot, d in slot_d.items():
        slot_str = '' if slot == '0' else slot + '/'
        for port in d['p']:
            cmd_l.append('portcfgdefault ' + slot_str + str(port))
            if i >= _MAX_LINES:
                cmd_l.append('')
                i = 0
            else:
                i += 1
        for port in d['ge']:
            cmd_l.append('portcfgdefault ' + slot_str + str(port))
            if i >= _MAX_LINES:
                cmd_l.append('')
                i = 0
            else:
                i += 1
    cmd_l.append('')

    # Add the ports
    for slot, d in slot_d.items():
        slot_str = '' if slot == '0' else ' -slot ' + slot
        for port_range in gen_util.int_list_to_range(d['p']):
            cmd_l.extend(['lscfg --config ' + fid + slot_str + ' -port ' + port_range + ' -force', ''])
        for port_range in gen_util.int_list_to_range(d['ge']):
            cmd_l.extend(['lscfg --config ' + fid + slot_str + ' -port ge' + port_range + ' -force', ''])

    cmd_l.extend(['# Set the remaining switch parameters.', ''])

    # Switch parameters
    buf = gen_util.get_key_val(switch_d, _fc_switch+'fibrechannel-switch/fabric-user-friendly-name')
    if isinstance(buf, str) and len(buf) > 0:
        cmd_l.append('fabricname --set ' + buf)
    buf = gen_util.get_key_val(switch_d, _fc_switch+'fibrechannel-switch/user-friendly-name')
    if isinstance(buf, str) and len(buf) > 0:
        cmd_l.append('switchname ' + buf)
    buf = gen_util.get_key_val(switch_d, _fc_switch+'fibrechannel-switch/banner')
    if isinstance(buf, str) and len(buf) > 0:
        cmd_l.append('bannerset "' + buf + '"')
    cmd_l.extend(['',
                  '# Below is not supported on all switch types. If you get an error, ignore it',
                  '',
                  'creditrecovmode --be_losync on',
                  ''])

    return cmd_l


def _port_commands(switch_d):
    """Generate the port configuration commands

    :param switch_d: Switch object as returned from report_utils.parse_switch_file()
    :type switch_d: dict
    :return: List of port configuration commands
    :rtype: list
    """
    global _port_configuration_l, _MAX_LINES

    cmd_l = list()

    # Reserve ports
    for slot, d in switch_d['_slot_d'].items():
        if slot != '0':
            break
        for port_range in gen_util.int_list_to_range(d['p']):
            cmd_l.append('license --reserve -port ' + port_range)
        for port_range in gen_util.int_list_to_range(d['ge']):
            cmd_l.append('license --reserve -port ge' + port_range)
        cmd_l.append('')

    # Port address binding
    if switch_d['switch_info']['bind']:
        start_addr = 0
        for slot, d in switch_d['_slot_d'].items():
            for port_range in gen_util.int_list_to_range(d['p']):
                buf = '' if slot == '0' else slot + '/'
                buf += port_range + ' ' + gen_util.pad_string(hex(start_addr)[2:], 2, '0') + '00'
                cmd_l.append('portaddress --bind ' + buf)
                start_addr += len(gen_util.range_to_list(port_range))
        cmd_l.append('')

    # Port names
    i, pd = 0, switch_d['port_d']
    for buf in ['portname ' + pd[k]['port'] + ' -n "' + pd[k]['port_name'] + '"' for k in
                brcdapi_port.sort_ports([str(k) for k in pd.keys()])
                if isinstance(pd[k]['port_name'], str) and len(pd[k]['port_name']) > 0]:
        if i >= _MAX_LINES:
            cmd_l.append('')
            i = 0
        else:
            i += 1
        cmd_l.append(buf)

    return _port_configuration_l + cmd_l if len(cmd_l) > 0 else cmd_l


def _enable_commands(switch_d):
    """Generate the switch and port enable commands if applicable

    :param switch_d: Switch object as returned from report_utils.parse_switch_file()
    :type switch_d: dict
    :return: List of enable commands
    :rtype: list
    """
    global _enable_l

    cmd_l = list()
    if switch_d['switch_info']['enable_switch']:
        cmd_l.extend(['switchenable', ''])
    if switch_d['switch_info']['enable_ports']:
        index_l = [d['index'] for d in switch_d['port_d'].values() if isinstance(d['index'], int)]
        if len(index_l) > 0:
            buf = 'portcfgpersistentenable' if switch_d['switch_info']['switch_type'] == 'ficon' else 'portenable'
            cmd_l.append(buf + ' -i ' + str(min(index_l)) + '-' + str(max(index_l)) + ' -f')

    return _enable_l + cmd_l if len(cmd_l) > 0 else cmd_l


def _zone_commands(switch_d):
    """Generates commands to create one large d,i zone if the switch is defined as ficon.

    :param switch_d: Switch object as returned from report_utils.parse_switch_file()
    :type switch_d: dict
    :return: List of enable commands
    :rtype: list
    """
    global _zoning_l, _MAX_ZONE_MEM

    if switch_d['switch_info']['switch_type'] != 'ficon':
        return list()
    cmd_l = _zoning_l.copy()

    # Get a zone name and figure out what the members should be
    zone_name = 'zone_switch_' + hex(gen_util.get_key_val(switch_d, _fc_switch+'fibrechannel-switch/domain-id'))[2:]
    # The order doesn't matter but most people like to see it sorted
    di_l = brcdapi_port.sort_ports([str(d['did']) + '/' + str(d['index']) for d in switch_d['port_d'].values()
                                    if d.get('did') is not None])
    if len(di_l) == 0:
        cmd_l.extend(['# There are no ports in this switch to zone', ''])
        return cmd_l
    di_l = [b.replace('/', ',') for b in di_l]

    # Create the zone and add the members
    len_di_l = len(di_l)
    i, x = 0, min(_MAX_ZONE_MEM, len_di_l)
    cmd_l.append('zonecreate "' + zone_name + '", "' + ';'.join(di_l[i:x]) + '"')
    i = x
    while i < len_di_l:
        x = i + min(_MAX_ZONE_MEM, len_di_l)
        cmd_l.append('zoneadd "' + zone_name + '", "' + ';'.join(di_l[i:x]) + '"')
        i = x

    # Add the zone configuration
    cfg_name = zone_name + '_cfg'
    cmd_l.extend(['', 'cfgcreate "' + cfg_name + '", "' + zone_name + '"', 'defzone --noaccess', ''])
    cmd_l.extend(['cfgsave -force', '', 'cfgenable  ' + cfg_name + ' -force', ''])

    return cmd_l


_switch_actions = (_switch_commands, _port_commands, _enable_commands, _zone_commands)


def pseudo_main(file_prefix, chassis_d, switch_d_l):
    """Basically the main().

    :param file_prefix: Prefix for CLI output files
    :type file_prefix: str
    :param chassis_d: Chassis definitions from brcddb.report.utils.parse_switch_file()
    :type chassis_d: dict
    :param switch_d_l: List of switch definitions from brcddb.report.utils.parse_switch_file()
    :type switch_d_l: list
    :return: Exit code
    :rtype: int
    """
    global _preamble_l, _validate_l, _switch_actions

    ec = brcddb_common.EXIT_STATUS_OK

    # Create the switch configuration output files
    brcdapi_log.log('Creating content', echo=True)
    for switch_d in switch_d_l:

        # Create the CLI for the switch configuration
        cmd_l = _preamble_l + _chassis_commands(chassis_d)
        for action in _switch_actions:
            cmd_l.extend(action(switch_d))
        cmd_l.append('')

        # Write the file
        file = file_prefix + '_' + str(switch_d['switch_info']['fid']) + '.txt'
        brcdapi_log.log('Writing file: ' + file, echo=True)
        el = brcdapi_file.write_file(file, cmd_l)
        if len(el) > 0:
            brcdapi_log.log(el, echo=True)
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    return ec


def _get_input():
    """Retrieves the command line input, reads the input Workbook, and minimally validates the input

    :return ip: Switch IP address
    :rtype ip: str
    :return out_file: Name of output file
    :rtype out_file: str
    :return s_flag: Suppress flag
    :rtype s_flag: bool
    """
    global __version__, _input_d

    # Get command line input
    buf = 'Reads a switch configuration workbook and generates FOS CLI commands to configure each logical switch.'
    try:
        args_d = gen_util.get_input(buf, _input_d)
    except TypeError:
        return brcddb_common.EXIT_STATUS_INPUT_ERROR  # gen_util.get_input() already posted the error message.

    # Set up logging
    brcdapi_log.open_log(
        folder=args_d['log'],
        suppress=args_d['sup'],
        no_log=args_d['nl'],
        version_d=brcdapi_util.get_import_modules()
    )
    
    # User feedback
    ml = ['',
          os.path.basename(__file__) + ', ' + __version__,
          'switch_config.py:    ' + __version__,
          'File, -i:            ' + args_d['i'],
          'Out file prefix, -o: ' + args_d['o'],
          ]
    brcdapi_log.log(ml, echo=True)

    # Read and validate the switch configuration workbook
    brcdapi_log.log('Reading ' + args_d['i'], echo=True)
    error_l, chassis_d, switch_d_l = report_utils.parse_switch_file(brcdapi_file.full_file_name(args_d['i'], '.xlsx'))
    if len(error_l) == 0:
        if chassis_d is None and len(switch_d_l) == 0:
            error_l.append('Nothing to configure')
    else:
        error_l.extend(_configuration_checks(switch_d_l))
    if len(error_l) > 0:
        brcdapi_log.log(error_l, echo=True)

    return brcddb_common.EXIT_STATUS_INPUT_ERROR if len(error_l) > 0 else \
        pseudo_main(args_d['i'], args_d['o'], switch_d_l)


###################################################################
#
#                    Main Entry Point
#
###################################################################
if _DOC_STRING:
    print('_DOC_STRING is True. No processing')
    exit(brcddb_common.EXIT_STATUS_OK)

_ec = _get_input()
brcdapi_log.close_log('Processing complete. Exit code: ' + str(_ec), echo=True)
exit(_ec)
