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
:mod:`capture` - Reads all information for all FIDs in a chassis and parses that data into brcddb objects.

**Description**

Except for login and logout, only performs GET operations. The KPIs to GET are specified by a command line parameter.
The options are:

    * A user supplied list of KPIs
    * All requests the chassis supports
    * A default list which are the resources the report.py module uses

The process is as follows:

    * GET the data
    * Add the data to the appropriated brcddb class using brcdapi.util.uri_map.area to determine which class
    * Once all data is captured, convert the brcddb.classes.project.ProjectObj to a plain dict and JSON dump to a file.

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 3.0.0     | 19 Jul 2020   | Initial Launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.1-5   | 13 Mar 2021   | Clean up. No functional changes.                                                  |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.6     | 17 Apr 2021   | Added ability to access IODF path information via z/OS libraries.                 |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.7     | 14 May 2021   | Added automatic extensions.                                                       |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.8     | 14 Nov 2021   | Deprecated pyfos_auth                                                             |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.9     | 31 Dec 2021   | Account for all json output file names                                            |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2019, 2020, 2021 Jack Consoli'
__date__ = '31 Dec 2021'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '3.0.9'

import argparse
import sys
import datetime
import brcddb.brcddb_project as brcddb_project
import brcdapi.log as brcdapi_log
import brcdapi.util as brcdapi_util
import brcdapi.brcdapi_rest as brcdapi_rest
import brcddb.util.copy as brcddb_copy
import brcddb.util.file as brcddb_file
import brcddb.api.interface as api_int
import brcdapi.fos_auth as brcdapi_auth
import brcddb.brcddb_common as brcddb_common
import brcddb.util.util as brcddb_util

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_WRITE = True  # Should always be True. Used for debug only. Prevents the output file from being written when False
_DEBUG = False   # When True, use _DEBUG_xxx below instead of parameters passed from the command line.
_DEBUG_IP = '10.xxx.x.xxx'
_DEBUG_OUTF = 'test/x118'
_DEBUG_ID = 'admin'
_DEBUG_PW = 'password'
_DEBUG_SEC = 'self'
_DEBUG_SUPPRESS = False
_DEBUG_VERBOSE = True
_DEBUG_C = None
_DEBUG_FID = None
_DEBUG_LOG = '_logs'
_DEBUG_NL = False

_report_kpi_l = (
    # 'brocade-fabric/fabric-switch',  Done automatically in brcddb.api.interface._get_chassis()
    'brocade-fibrechannel-switch/fibrechannel-switch',
    'brocade-fibrechannel-switch/topology-domain',
    'brocade-fibrechannel-switch/topology-route',
    'brocade-interface/fibrechannel',
    'brocade-interface/fibrechannel-statistics',
    # 'brocade-interface/logical-e-port',
    'brocade-media/media-rdp',
    'brocade-fabric/access-gateway',
    'brocade-fibrechannel-routing/routing-configuration',
    'brocade-fibrechannel-routing/lsan-zone',
    'brocade-fibrechannel-routing/lsan-device',
    'brocade-fibrechannel-routing/edge-fabric-alias',
    'brocade-zone/defined-configuration',
    'brocade-zone/effective-configuration',
    'brocade-zone/fabric-lock',
    'brocade-fdmi/hba',
    'brocade-fdmi/port',
    'brocade-name-server/fibrechannel-name-server',
    'brocade-fabric-traffic-controller/fabric-traffic-controller-device',
    'brocade-fibrechannel-configuration/switch-configuration',
    'brocade-fibrechannel-configuration/f-port-login-settings',
    'brocade-fibrechannel-configuration/port-configuration',
    'brocade-fibrechannel-configuration/zone-configuration',
    'brocade-fibrechannel-configuration/fabric',
    'brocade-fibrechannel-configuration/chassis-config-settings',
    'brocade-fibrechannel-configuration/fos-settings',
    'brocade-ficon/cup',
    'brocade-ficon/logical-path',
    'brocade-ficon/rnid',
    'brocade-ficon/switch-rnid',
    'brocade-ficon/lirr',
    'brocade-ficon/rlir',
    'brocade-fru/power-supply',
    'brocade-fru/fan',
    'brocade-fru/blade',
    'brocade-fru/history-log',
    'brocade-fru/sensor',
    'brocade-fru/wwn',
    'brocade-chassis/chassis',
    'brocade-chassis/ha-status',
    'brocade-maps/maps-config',
    'brocade-maps/rule',
    'brocade-maps/maps-policy',
    'brocade-maps/group',
    'brocade-maps/dashboard-rule',
    'brocade-maps/dashboard-history',
    'brocade-maps/dashboard-misc',
    'brocade-maps/system-resources',
    'brocade-maps/paused-cfg',
    'brocade-maps/monitoring-system-matrix',
    'brocade-maps/switch-status-policy-report',
    'brocade-maps/fpi-profile',
    'brocade-time/clock-server',
    'brocade-time/time-zone',
    'brocade-license/license',
)


def _kpi_list(session, c_file):
    """Returns the list of KPIs to capture

    :param session: Session object returned from brcdapi.brcdapi_auth.login()
    :type session: dict
    :param c_file: Name of file with KPIs to read
    :type c_file: str, None
    :return: List of KPIs
    :rtype: list
    """
    kpi_l = _report_kpi_l if c_file is None else brcddb_util.convert_to_list(session.get('supported_uris')) if \
        c_file == '*' else brcddb_file.read_file(c_file)
    rl = list()
    for kpi in kpi_l:
        if kpi in brcdapi_util.uri_map:
            if 'GET' in brcdapi_util.uri_map[kpi]['methods'] and \
                    brcdapi_util.uri_map[kpi]['area'] != brcdapi_util.NULL_OBJ:
                rl.append(kpi)
        else:
            brcdapi_log.log(':UNKNOWN KPI: ' + kpi, True)
    return rl


def parse_args():
    """Parses the module load command line

    :return ip_addr: IP address
    :rtype ip_addr: str
    :return id: User ID
    :rtype id: str
    :return pw: Password
    :rtype pw: str
    :return file: Name of output file
    :rtype file: str
    :return http_sec: Type of HTTP security
    :rtype http_sec: str
    :return suppress_flag: True - suppress all print to STD_OUT
    :rtype suppress_flag: bool
    """
    global _DEBUG_IP, _DEBUG_ID, _DEBUG_PW, _DEBUG_OUTF, _DEBUG_SEC, _DEBUG_SUPPRESS, _DEBUG_VERBOSE, _DEBUG_C
    global _DEBUG_FID, _DEBUG_LOG, _DEBUG_NL, _DEBUG

    if _DEBUG:
        return _DEBUG_IP, _DEBUG_ID, _DEBUG_PW, _DEBUG_OUTF, _DEBUG_SEC, _DEBUG_SUPPRESS, _DEBUG_VERBOSE, _DEBUG_C, \
               _DEBUG_FID, _DEBUG_LOG, _DEBUG_NL
    parser = argparse.ArgumentParser(description='Capture (GET) requests from a chassis')
    parser.add_argument('-f', help='Output file for captured data', required=True)
    parser.add_argument('-ip', help='IP address', required=True)
    parser.add_argument('-id', help='User ID', required=True)
    parser.add_argument('-pw', help='Password', required=True)
    parser.add_argument('-s', help='\'CA\' or \'self\' for HTTPS mode.', required=False,)
    buf = '(Optional) Name of file with list of KPIs to capture. Use * to capture all data the chassis supports. The '\
          'default is to capture all KPIs required for the report.'
    parser.add_argument('-c', help=buf, required=False,)
    buf = '(Optional) CSV list of FIDs to capture logical switch specific data. The default is to automatically '\
          'determine all logical switch FIDs defined in the chassis.'
    parser.add_argument('-fid', help=buf, required=False)
    buf = '(Optional) No parameters. Suppress all library generated output to STD_IO except the exit code. Useful '\
          'with batch processing'
    parser.add_argument('-sup', help=buf, action='store_true', required=False)
    buf = '(Optional) No parameters. When set, a pprint of all content sent and received to/from the API, except '\
          'login information, is printed to the log.'
    parser.add_argument('-d', help=buf, action='store_true', required=False)
    buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The log ' \
          'file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
    parser.add_argument('-log', help=buf, required=False, )
    buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
    parser.add_argument('-nl', help=buf, action='store_true', required=False)
    args = parser.parse_args()
    return args.ip, args.id, args.pw, args.f, args.s, args.sup, args.d, args.c, args.fid, args.log, args.nl


def pseudo_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    ip, user_id, pw, outf, sec, s_flag, vd, c_file, fid, log, nl = parse_args()
    if vd:
        brcdapi_rest.verbose_debug = True
    if s_flag:
        brcdapi_log.set_suppress_all()
    if not nl:
        brcdapi_log.open_log(log)
    if sec is None:
        sec = 'none'
    fid_l = None if fid is None else fid.split(',')
    ml = ['WARNING!!! Debug is enabled'] if _DEBUG else list()
    ml.append('IP:          ' + brcdapi_util.mask_ip_addr(ip, True))
    ml.append('ID:          ' + user_id)
    ml.append('security:    ' + sec)
    ml.append('Output file: ' + outf)
    ml.append('KPI file:    ' + str(c_file))
    ml.append('FID List:    ' + str(fid))
    brcdapi_log.log(ml, True)
    outf = brcddb_file.full_file_name(outf, '.json')

    # Create project
    proj_obj = brcddb_project.new("Captured_data", datetime.datetime.now().strftime('%d %b %Y %H:%M:%S'))
    proj_obj.s_python_version(sys.version)
    proj_obj.s_description("This is a test")

    # Login
    session = api_int.login(user_id, pw, ip, sec, proj_obj)
    if brcdapi_auth.is_error(session):
        return brcddb_common.EXIT_STATUS_API_ERROR

    # Collect the data
    try:
        api_int.get_batch(session, proj_obj, _kpi_list(session, c_file), fid_l)
        if proj_obj.r_is_any_error():
            brcdapi_log.log('Errors encountered. Search the log for "ERROR:".', True)
    except BaseException as e:
        brcdapi_log.exception('Programming error encountered. Exception is: ' + str(e), True)

    # Logout
    obj = brcdapi_rest.logout(session)
    if brcdapi_auth.is_error(obj):
        brcdapi_log.log(brcdapi_auth.formatted_error_msg(obj), True)

    # Dump the database to a file
    if _WRITE:
        brcdapi_log.log('Saving project to: ' + outf, True)
        plain_copy = dict()
        brcddb_copy.brcddb_to_plain_copy(proj_obj, plain_copy)
        brcddb_file.write_dump(plain_copy, outf)
        brcdapi_log.log('Save complete', True)

    return proj_obj.r_exit_code()


###################################################################
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
