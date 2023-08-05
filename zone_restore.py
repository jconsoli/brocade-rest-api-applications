#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2023 Consoli Solutions, LLC.  All rights reserved.
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
:mod:`zone_restore` - Sets the zone configuration DB to that of a previously captured zone DB

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 4.0.0     | 04 Aug 2023   | Re-Launch                                                                         |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2023 Consoli Solutions, LLC'
__date__ = '04 August 2023'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack_consoli@yahoo.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '4.0.0'

import argparse
import brcdapi.log as brcdapi_log
import brcdapi.fos_auth as fos_auth
import brcdapi.brcdapi_rest as brcdapi_rest
import brcdapi.util as brcdapi_util
import brcdapi.file as brcdapi_file
import brcddb.brcddb_project as brcddb_project
import brcddb.brcddb_common as brcddb_common
import brcddb.brcddb_fabric as brcddb_fabric
import brcddb.api.interface as api_int
import brcddb.api.zone as api_zone

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = False   # When True, use _DEBUG_xxx below instead of parameters passed from the command line.
_DEBUG_ip = 'xx.xxx.xx.xx'
_DEBUG_id = 'admin'
_DEBUG_pw = 'password'
_DEBUG_sec = 'self'
_DEBUG_i = '_capture_2022_10_23_08_20_34/combined'
_DEBUG_fid = 128
_DEBUG_wwn = '10:00:c4:f5:7c:2d:a6:20'
_DEBUG_a = False
_DEBUG_scan = False
_DEBUG_cli = 'test/cli'
_DEBUG_sup = False
_DEBUG_d = False
_DEBUG_log = '_logs'
_DEBUG_nl = False

_kpis_for_capture = ('running/brocade-fibrechannel-switch/fibrechannel-switch',
                     'running/brocade-interface/fibrechannel',
                     'running/brocade-zone/defined-configuration',
                     'running/brocade-zone/effective-configuration',
                     'running/brocade-fibrechannel-configuration/zone-configuration',
                     'running/brocade-fibrechannel-configuration/fabric')
_ZONE_KPI_FILE = '_zone_merge_kpis.txt'

_control_tables = {
    'FabricObj': {
        '/_(obj_key|project_obj|alerts|base_logins|port_map|eff_zone_objs|switch_keys|login_objs)': dict(skip=True),
        '/_(fdmi_node_objs|fdmi_port_objs|flags|port_map|flags|reserved_keys)': dict(skip=True),
        '/brocade-zone/(.*)': dict(skip=True),  # Everything in brocade-zone is already in the object
    },
    'ZoneCfgObj': {
        '/_(obj_key|project_obj|alerts|flags|fabric_key|reserved_keys)': dict(skip=True),
    },
    'ZoneObj': {
        '/_(obj_key|project_obj|alerts|flags|fabric_key|reserved_keys)': dict(skip=True),
    },
    'AliasObj': {
        '/_(obj_key|project_obj|alerts|flags|fabric_key|reserved_keys)': dict(skip=True),
    },
}

_MAX_ZONE_MEM = 4
_MAX_LINES = 20
_cli_hdr_0 = ['########################################################',
              '#                                                      #']
_cli_hdr_1 = ['#                                                      #',
              '########################################################',
              '']


def _scan_fabrics(proj_obj):
    """Scan the project for each fabric and list the fabric WWN, FID , and zone configurations

    :param proj_obj: Project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :return: Status code
    :rtype: int
    """
    ec = brcddb_common.EXIT_STATUS_OK

    # Prepare the fabric display
    ml = ['', 'Fabric Scan (* indicates the effective zone config)', '']
    for fab_obj in proj_obj.r_fabric_objects():
        eff_zonecfg = fab_obj.r_defined_eff_zonecfg_key()
        ml.append(brcddb_fabric.best_fab_name(fab_obj, wwn=True))
        ml.append('  FID:         ' + ', '.join([str(fid) for fid in brcddb_fabric.fab_fids(fab_obj)]))
        for buf in fab_obj.r_zonecfg_keys():
            if isinstance(eff_zonecfg, str) and eff_zonecfg == buf:
                ml.append('  Zone Config: ' + '*' + buf)
            elif buf != '_effective_zone_cfg':
                ml.append('  Zone Config: ' + buf)
        ml.append('')

    # Wrap up and print fabric information
    if len(ml) == 0:
        ml.append('No fabrics specified.')
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    brcdapi_log.log(ml, echo=True)

    return ec


def _cli_commands(fab_obj):
    """Generate CLI commands

    :param fab_obj: Fabric object
    :type fab_obj: brcddb.classes.fabric.FabricObj
    :return: Status code
    :rtype: int
    """
    global _cli_hdr_0, _cli_hdr_1

    ec, rl = brcddb_common.EXIT_STATUS_OK, list()
    control_l = (
        dict(disp='#                 Aliases                              #',
             cmd='alicreate',
             add='aliadd',
             obj_l=fab_obj.r_alias_objects(),
             zone_flag=False),
        dict(disp='#                 Zones                                #',
             cmd='zonecreate',
             add='zoneadd',
             obj_l=fab_obj.r_zone_objects(),
             zone_flag=True),
        dict(disp='#           Zone Configurations                        #',
             cmd='cfgcreate',
             add='cfgadd',
             obj_l=fab_obj.r_zonecfg_objects(),
             zone_flag=False)
    )

    # Generate the CLI commands
    for control_d in control_l:

        # Add the header
        rl.extend(_cli_hdr_0)
        rl.append(control_d['disp'])
        rl.extend(_cli_hdr_1)

        line = 0
        for obj in control_d['obj_l']:
            if obj.r_obj_key() == '_effective_zone_cfg':
                continue

            # Figure out what the command parameters are
            buf, add_buf, name_start, name_end, add_mem_buf = control_d['cmd'], control_d['add'], ' "', '", ', ''
            mem_l = obj.r_members()
            if control_d['zone_flag']:
                zone_type = obj.r_type()
                if zone_type == brcddb_common.ZONE_TARGET_PEER:
                    continue
                if zone_type == brcddb_common.ZONE_USER_PEER:
                    # Add a line space if necessary
                    if line >= _MAX_LINES:
                        rl.append('')
                        line = 0
                    else:
                        line += 1
                    name_start = ' --peerzone "'
                    name_end = '" -members '
                    rl.append(buf + name_start + obj.r_obj_key() + '" -principal "' + ';'.join(obj.r_pmembers()) + '"')
                    buf = add_buf + name_start + obj.r_obj_key() + name_end
                else:
                    buf += name_start + obj.r_obj_key() + name_end
            else:
                buf += name_start + obj.r_obj_key() + name_end

            # Add the members
            mem_len = len(mem_l)
            i, x = 0, min(_MAX_ZONE_MEM, mem_len)

            # Add a line space if necessary
            if line >= _MAX_LINES:
                rl.append('')
                line = 0
            else:
                line += 1

            rl.append(buf + '"' + ';'.join(mem_l[i:x]) + '"')
            i = x
            while i < mem_len:
                x = i + min(_MAX_ZONE_MEM, mem_len)

                # Add a line space if necessary
                if line >= _MAX_LINES:
                    rl.append('')
                    line = 0
                else:
                    line += 1

                rl.append(add_buf + name_start + obj.r_obj_key() + name_end + '"' + ';'.join(mem_l[i:x]) + '"')
                i = x
        rl.append('')

    return rl


def parse_args():
    """Parses the module load command line
    
    :return: file
    :rtype: str
    """
    global _DEBUG, _DEBUG_ip, _DEBUG_id, _DEBUG_pw, _DEBUG_sec, _DEBUG_fid, _DEBUG_i, _DEBUG_wwn, _DEBUG_a,\
        _DEBUG_scan, _DEBUG_cli, _DEBUG_d, _DEBUG_sup, _DEBUG_log, _DEBUG_nl

    if _DEBUG:
        return _DEBUG_ip, _DEBUG_id, _DEBUG_pw, _DEBUG_sec, _DEBUG_fid, _DEBUG_i, _DEBUG_wwn, _DEBUG_a, _DEBUG_scan, \
               _DEBUG_cli, _DEBUG_d, _DEBUG_sup, _DEBUG_log, _DEBUG_nl
    buf = 'Sets the zone database to that of a previous capture. Although typically used to restore a zone database, '\
          'this module can be used to set the zone database to that of any fabric.'
    parser = argparse.ArgumentParser(description=buf)
    buf = 'Required unless generating CLI output, -cli, or scanning, -scan. '
    parser.add_argument('-ip', help=buf + 'IP address', required=False)
    parser.add_argument('-id', help=buf + 'User ID', required=False)
    parser.add_argument('-pw', help=buf + 'Password', required=False)
    parser.add_argument('-s', help='(Optional) "none" for HTTP, default, or "self" for HTTPS mode.', required=False,)
    buf = 'Optional with -scan, otherwise required. Fabric ID of logical switch whose DB is be restored from the '\
          'fabric specified with the -wwn parameter.'
    parser.add_argument('-fid', help=buf, required=False)
    buf = 'Required. Captured data file from the output of capture.py, combine.py, or multi_capture.py.'
    parser.add_argument('-i', help=buf, required=True)
    buf = 'Optional with -scan, otherwise required. Fabric WWN whose zone DB is to be read and set in the fabric '\
          'specified with the -fid parameter. Keep in mind that if the fabric was rebuilt, it may have a different WWN.'
    parser.add_argument('-wwn', help=buf, required=False)
    buf = 'Optional. Specifies the zone zone configuration to activate. If not specified, no change is made to the '\
          'effective configuration. If a zone configuration is in effect and this option is not specified, the '\
          'effective zone may result in the defined zone configuration being inconsistent with the effective zone '\
          'configuration.'
    parser.add_argument('-a', help=buf, required=False)
    buf = 'Optional. No parameters. Scan switch if login credentials supplied and captured data file for fabric '\
          'information.'
    parser.add_argument('-scan', help=buf, action='store_true', required=False)
    buf = 'Optional. Name of file for CLI commands. When specified, -ip, -id, -pw, and -s are ignored.'
    parser.add_argument('-cli', help=buf, required=False)
    buf = 'Optional. Suppress all output to STD_IO except the exit code and argument parsing errors. Useful with '\
          'batch processing where only the exit status code is desired. Messages are still printed to the log file'\
          '. No operands.'
    parser.add_argument('-sup', help=buf, action='store_true', required=False)
    buf = '(Optional) No parameters. When set, a pprint of all content sent and received to/from the API, except ' \
          'login information, is printed to the log.'
    parser.add_argument('-d', help=buf, action='store_true', required=False)
    buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The log ' \
          'file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
    parser.add_argument('-log', help=buf, required=False, )
    buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
    parser.add_argument('-nl', help=buf, action='store_true', required=False)
    args = parser.parse_args()
    return args.ip, args.id, args.pw, args.s, args.fid, args.i, args.wwn, args.a, args.scan, args.cli, args.d, \
           args.sup, args.log, args.nl


def _get_input():
    """Retrieves the command line input, reads the input Workbook, and validates the input

    :return ec: Error code from brcddb.brcddb_common
    :rtype ec: int
    :return sl: List of switches to poll as read from the input Workbook
    :rtype sl: list
    :return pl: List of project files to combine
    :rtype pl: list
    :return cfg_name: Name of zone configuration file to create
    :rtype cfg_name: str, None
    :return a_cfg: Activation flag. If True, activate the zone configuration specified by cfg_name
    :rtype a_cfg: bool
    :return t_flag: Test flag. If True, test only. Do not make any changes
    :rtype t_flag: bool
    :return scan_flag: Scan flag. If True, scan files and switches for fabric information
    :rtype scan_flag: bool
    :return cli_file: Name of file for CLI commands
    :rtype cli_file: None, str
    :return addl_parms: Additional parameters (logging and debug flags) to pass to multi_capture.py
    :rtype addl_parms: list
    """
    global _DEBUG, __version__

    # Initialize the return variables
    ec = brcddb_common.EXIT_STATUS_OK
    addl_parms = list()

    # Get and validate the user input
    ip, user_id, pw, sec, fid, cfile, wwn, zone_cfg, scan_flag, cli_file, d_flag, s_flag, log, nl = parse_args()
    if s_flag:
        addl_parms.append('-sup')
        brcdapi_log.set_suppress_all()
    if nl:
        addl_parms.append('-nl')
    else:
        brcdapi_log.open_log(log)
    if log is not None:
        addl_parms.extend(['-log', log])
    if d_flag:
        addl_parms.append('-d')
        brcdapi_rest.verbose_debug = True
    buf = ''
    if isinstance(fid, int):
        buf = ' INVALID. Must be an integer in the range of 1-128' if fid < 0 or fid > 128 else ''
    ml = ['WARNING!!! Debug is enabled'] if _DEBUG else list()
    ml.append('zone_restore.py version: ' + __version__)
    ml.append('IP address, -ip:         ' + brcdapi_util.mask_ip_addr(ip))
    ml.append('ID, -id:                 ' + str(user_id))
    ml.append('HTTPS, -s:               ' + str(sec))
    ml.append('FID, -fid:               ' + str(fid) + buf)
    ml.append('Input file, -i:          ' + cfile)
    ml.append('WWN, -wwn:               ' + str(wwn))
    ml.append('Activate zone cfg, -a:   ' + str(zone_cfg))
    ml.append('Scan, -scan:             ' + str(scan_flag))
    ml.append('CLI file, -cli:          ' + str(cli_file))
    brcdapi_log.log(ml, echo=True)
    if len(buf) > 0:
        return brcddb_common.EXIT_STATUS_INPUT_ERROR
    if sec is None:
        sec = 'none'
    ml = list()
    if cli_file is None and not scan_flag:
        if ip is None:
            ml.append('  IP address (-ip)')
        if user_id is None:
            ml.append('  User ID (-id)')
        if pw is None:
            ml.append('  Password (-pw)')
        if fid is None:
            ml.append('  FID (-fid)')
        if len(buf) > 0:
            ml.append('  FID ' + buf)
        if wwn is None:
            ml.append('  Fabric WWN (-wwn)')
        if len(ml) > 0:
            ml.insert(0, 'Missing the following required parameters:')
            ml.append('Use the -h option for additional help.')
            brcdapi_log.log(ml, echo=True)
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    cfile = brcdapi_file.full_file_name(cfile, '.json')
    cli_file = brcdapi_file.full_file_name(cli_file, '.txt')

    return ec, ip, user_id, pw, sec, scan_flag, fid, cfile, wwn, zone_cfg, scan_flag, addl_parms, cli_file


def pseudo_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code. See exit codes in brcddb.brcddb_common
    :rtype: int
    """
    global __version__
    global _DEBUG_id, _DEBUG_pw, _DEBUG_ip

    ec, ip, user_id, pw, sec, scan_flag, fid, cfile, wwn, zone_cfg, scan_flag, addl_parms, cli_file = _get_input()

    if ec != brcddb_common.EXIT_STATUS_OK:
        return ec

    # Read the project file
    proj_obj = brcddb_project.read_from(cfile)
    if proj_obj is None:
        return brcddb_common.EXIT_STATUS_ERROR

    fab_obj = proj_obj.r_fabric_obj(wwn)
    if scan_flag:
        return _scan_fabrics(proj_obj)
    elif fab_obj is None:
        brcdapi_log.log(wwn + ' does not exist in ' + cfile + '. Try using the -scan option', echo=True)
        return brcddb_common.EXIT_STATUS_INPUT_ERROR

    if isinstance(cli_file, str):
        try:
            with open(cli_file, 'w') as f:
                f.write('\n'.join(_cli_commands(fab_obj)))
            f.close()
        except FileNotFoundError:
            brcdapi_log.log(['', 'Folder in path ' + cli_file + ' does not exist.', ''], echo=True)
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
        except PermissionError:
            brcdapi_log.log(['', 'Permission error writing ' + cli_file + '.', ''], echo=True)
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

        return ec

    # Login
    session = api_int.login(user_id, pw, ip, sec, proj_obj)
    if fos_auth.is_error(session):
        brcdapi_log.log(fos_auth.formatted_error_msg(session), echo=True)
        return brcddb_common.EXIT_STATUS_ERROR

    try:
        # Make the zoning change
        brcdapi_log.log('Sending zone updates to FID ' + str(fid), echo=True)
        obj = api_zone.replace_zoning(session, fab_obj, fid)
        if fos_auth.is_error(obj):
            brcdapi_log.log(fos_auth.formatted_error_msg(obj), echo=True)
        else:
            brcdapi_log.log('Zone restore completed successfully.', echo=True)

        # Activate the zone configuration
        if zone_cfg is not None:
            brcdapi_log.log('Enabling zone configuration ' + zone_cfg + ', fid: ' + str(fid), echo=True)
            api_zone.enable_zonecfg(session, fab_obj, fid, zone_cfg)

    except BaseException as e:
        brcdapi_log.log(['', 'Software error.', 'Exception: ' + str(e)], echo=True)

    # Logout
    obj = brcdapi_rest.logout(session)
    if fos_auth.is_error(obj):
        brcdapi_log.log(fos_auth.formatted_error_msg(obj), echo=True)

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
