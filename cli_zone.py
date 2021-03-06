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
:mod:`cli_zone` - Reads a list of CLI commands from a file and converts those commands to an equivalent brcddb object

**Overview**

Using the API as a replacement for an SSH CLI session isn't useful; however, since there are numerous CLI zoning
scripts, this was a useful tool to test brcddb.apps.zone.py. This module was posted for those familiar with the CLI to
use as an example with the following caveats and features:

    * d,i zones are not parsed properly
    * Includes common error checking
    * Takes advantage of all brcddb.apps.zone.py features (test mode, suppress output, zone from saved container)
    * Processes made up command, zonecleanup, which was used to test the zone cleanup feature of brcddb.apps.zone.py
    * Unsupported commands: zoneobjectexpunge, zoneobjectrename, zoneobjectreplace, defzone

**Inputs**

+-------+-----------+-----------------------------------------------------------------------------------------------+
| Input | Required  | Description                                                                                   |
+=======+===========+===============================================================================================+
| -ip   | Yes       | Chassis IP address. Only required if chassis access is required.                              |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| -id   | Yes       | Chassis IP address. Only required if chassis access is required.                              |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| -pw   | Yes       | Chassis IP address. Only required if chassis access is required.                              |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| -s    | No        | Security: CA or self for HTTPS mode. Do specify for HTTP access. Only required if chassis     |
|       |           | access is required.                                                                           |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| -cli  | Yes       | Name of plain text file with CLI commands                                                     |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| -fab  | Maybe     | WWN of fabric principal switch. Only used if -i is specified                                  |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| -fid  | Yes       | Virtual Fabric ID (1 - 128) of fabric in chassis specified by the -ip argument. Only used if  |
|       |           | -ip is specified.                                                                             |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| -i    | No        | When specified, instead of capturing data from the chassis specified with -ip, data is read   |
|       |           | from this file. It must be in the format of a file generated by capture.py or combine.py.     |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| -t    | No        | Test mode. Flag only. No arguments. When specified, zoning is not pushed to the chassis.      |
|       |           | Useful for validating the commands specified in the -cli file.                                |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| -f    | No        | Force. Flag only. No arguments. Ignore warnings and push changes to the fabric.               |
+-------+-----------+-----------------------------------------------------------------------------------------------+
| -sup  | No        | Suppress all output to STD_IO except the exit code. Useful with batch processing where only   |
|       |           | the exit status code is desired. Messages are still printed to the log file.                  |
+-------+-----------+-----------------------------------------------------------------------------------------------+

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 3.0.0     | 01 Nov 2020   | Initial Launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.1     | 09 Jan 2021   | Open log file.                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.2     | 13 Feb 2021   | Added # -*- coding: utf-8 -*-                                                     |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.3     | 31 Dec 2021   | Make all exception clauses explicit.                                              |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.4     | 28 Apr 2022   | Relocated libraries.                                                              |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2020, 2021, 2022 Jack Consoli'
__date__ = '28 Apr 2022'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '3.0.4'

import argparse
import brcdapi.log as brcdapi_log
import brcdapi.brcdapi_rest as brcdapi_rest
import brcdapi.util as brcdapi_util
import brcdapi.gen_util as gen_util
import brcdapi.file as brcdapi_file
import brcddb.brcddb_common as brcddb_common
import brcddb.apps.zone as brcddb_zone
import brcddb.util.util as brcddb_util

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = False
_DEBUG_ip = 'xx.xxx.x.xxx'
_DEBUG_id = 'admin'
_DEBUG_pw = 'Password'
_DEBUG_sec = 'none'
_DEBUG_cli = 'test/zone_test_1.txt'
_DEBUG_fid = 1
_DEBUG_t = False
_DEBUG_f = True
_DEBUG_b = True
_DEBUG_sup = False
_DEBUG_d = False
_DEBUG_log = '_logs'
_DEBUG_nl = False


def parse_args():
    """Parses the module load command line

    :return: file
    :rtype: str
    """
    global _DEBUG_ip, _DEBUG_id, _DEBUG_pw, _DEBUG_sec, _DEBUG_cli, _DEBUG_fid, _DEBUG_t, _DEBUG_f, _DEBUG_sup,\
        _DEBUG_d, _DEBUG_b, _DEBUG_log, _DEBUG_nl

    if _DEBUG:
        return _DEBUG_ip, _DEBUG_id, _DEBUG_pw, _DEBUG_sec, _DEBUG_cli, _DEBUG_fid, _DEBUG_t, _DEBUG_f,\
               _DEBUG_b, _DEBUG_sup, _DEBUG_d, _DEBUG_log, _DEBUG_nl

    else:
        parser = argparse.ArgumentParser(description='Convert CLI zoning commands to API calls or brcddb object file.')
        parser.add_argument('-ip', help='IP address', required=False)
        parser.add_argument('-id', help='User ID', required=False)
        parser.add_argument('-pw', help='Password', required=False)
        parser.add_argument('-s', help='\'CA\' or \'self\' for HTTPS mode.', required=False,)
        parser.add_argument('-cli', help='Name of plain text file with CLI commands', required=True)
        buf = 'Virtual Fabric ID (1 - 128) of fabric in chassis specified by the -ip argument. Only used if -ip '
        buf += 'is specified'
        parser.add_argument('-fid', help=buf, type=int, required=True)
        buf = 'Test mode. No arguments. When specified, Zoning is not pushed to the chassis. Useful for validating '\
              'the commands specified in the -cli file.'
        parser.add_argument('-t', help=buf, action='store_true', required=False)
        buf = 'Force. No arguments. When specified, ignore warnings and, when creating objects, overwrite it if it'\
              ' already exists.'
        parser.add_argument('-f', help=buf, action='store_true', required=False)
        buf = 'Bulk zone. No arguments. When specified, the zone database is rebuilt with whatever changes are in the'\
              ' CLI file, specified by -cli, and completely replaces the zone database. WARNING: The effective zone '\
              'configuration is not re-established automatically with this option.'
        parser.add_argument('-b', help=buf, action='store_true', required=False)
        buf = 'Suppress all library generated output to STD_IO except the exit code. Useful with batch processing'
        parser.add_argument('-sup', help=buf, action='store_true', required=False)
        parser.add_argument('-d', help='Enable debug logging', action='store_true', required=False)
        buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The ' \
              'log file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
        parser.add_argument('-log', help=buf, required=False, )
        buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
        parser.add_argument('-nl', help=buf, action='store_true', required=False)
        args = parser.parse_args()
        return args.ip, args.id, args.pw, args.s, args.cli, args.fid, args.t, args.f, args.b, args.sup, args.d, \
               args.log, args.nl


def _format_fault(obj, line_num, file_content):
    """Formats a fault into printable text

    :param obj: Dictionary as defined in Return 'changes"
    :type obj: dict
    :param line_num: Line number
    :type line_num: int
    :return: Formatted text
    :rtype: str
    """
    try:
        buf = str(file_content[line_num])
    except BaseException as e:
        buf = 'Unknown exception: ' + str(e)
    msg_l = [
        '',
        'Line:    ' + str(line_num + 1),
        'Input:   ' + buf,
        'changed: ' + str(obj.get('changed')),
        'fail:    ' + str(obj.get('fail')),
        'io:      ' + str(obj.get('io')),
        'Status:  ' + str(obj.get('status')),
        'Reason:  ' + str(obj.get('reason')),
        'err_msg:',
    ]
    msg_l.extend(['  ' + buf for buf in gen_util.convert_to_list(obj.get('err_msg'))])
    return '\n'.join(msg_l)


def pseudo_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    # Get and validate the input parameters. Add all input arguments to the log
    ip, user_id, pw, sec, cli_file, fid, t_flag, f_flag, b_flag, s_flag, vd, log, nl = parse_args()
    if not nl:
        brcdapi_log.open_log(log)
    if vd:
        brcdapi_rest.verbose_debug = True
    content = {
        'fid': fid,
        'ip-addr': ip,
        'id': user_id,
        'pw': pw,
        'sec': sec,
        'force': False if f_flag is None else f_flag,
        'test': False if t_flag is None else t_flag,
        'bulk': False if b_flag is None else b_flag,
    }

    if s_flag:
        brcdapi_log.set_suppress_all()
    ml = list()
    if _DEBUG:
        ml.append('WARNING!!! Debug is enabled')
    ml.append('IP:          ' + brcdapi_util.mask_ip_addr(ip, True))
    ml.append('ID:          ' + user_id)
    ml.append('CLI file:    ' + cli_file)
    ml.append('FID:         ' + str(fid))
    ml.append('Test flag:   ' + str(t_flag))
    ml.append('Force flag:  ' + str(f_flag))
    ml.append('Bulk flag:   ' + str(b_flag))
    brcdapi_log.log(ml, True)

    # Read in the CLI file, condition the input strings and send it
    ml = list()
    try:
        file_contents = brcdapi_file.read_file(cli_file)
    except FileNotFoundError:
        ml.extend(['', 'File ' + cli_file + ' not found. Did you remember the file extension?'])
    except PermissionError:
        ml.extend(['', 'You do not have permission to read ' + cli_file])
    if len(ml) > 0:
        brcdapi_log.log(ml, True)
        return brcddb_common.EXIT_STATUS_INPUT_ERROR

    content.update(changes=brcddb_util.parse_cli(file_contents))
    if t_flag:
        content.update(test=True)
    response = brcddb_zone.send_zoning(content)

    # General information
    ec = brcddb_common.EXIT_STATUS_OK
    total_changes = total_failures = total_io = i = 0
    for obj in response:
        if isinstance(obj, dict):  # obj is None for blank or commented our lines in the input
            if obj.get('changed'):
                total_changes += 1
            if obj.get('fail'):
                total_failures += 1
                brcdapi_log.log(_format_fault(obj, i, file_contents), True)
                ec = brcddb_common.EXIT_STATUS_ERROR
            if obj.get('io'):
                total_io += 1
        i += 1
    ml = [
        '',
        'Summary:',
        'Total Changes  : ' + str(total_changes),
        'Total Failures : ' + str(total_failures),
        'Total I/O      : ' + str(total_io)
    ]
    brcdapi_log.log(ml, True)

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
brcdapi_log.close_log('\nProcessing Complete. Exit code: ' + str(_ec))
exit(_ec)
