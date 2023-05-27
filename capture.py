#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020, 2021, 2022, 2023 Jack Consoli.  All rights reserved.
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
    | 3.1.0     | 28 Apr 2022   | Relocated libraries                                                               |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.1.1     | 04 Sep 2022   | Added module and version number to user feedback.                                 |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.1.2     | 24 Oct 2022   | Added ability to control-C out of data capture.                                   |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.1.3     | 27 May 2023   | Enabled brocade-maps/dashboard-xxx collection                                     |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2019, 2020, 2021, 2022, 2023 Jack Consoli'
__date__ = '27 May 2023'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '3.1.3'

import http.client
import signal
import argparse
import sys
import datetime
import brcddb.brcddb_project as brcddb_project
import brcdapi.log as brcdapi_log
import brcdapi.util as brcdapi_util
import brcdapi.brcdapi_rest as brcdapi_rest
import brcdapi.file as brcdapi_file
import brcddb.util.copy as brcddb_copy
import brcddb.api.interface as api_int
import brcdapi.fos_auth as brcdapi_auth
import brcddb.brcddb_common as brcddb_common

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_WRITE = True  # Should always be True. Used for debug only. Prevents the output file from being written when False
_DEBUG = False   # When True, use _DEBUG_xxx below instead of parameters passed from the command line.
_DEBUG_ip = 'xx.xxx.x.xx'
_DEBUG_f = 'test/test_output'
_DEBUG_id = 'admin'
_DEBUG_pw = 'password'
_DEBUG_s = 'self'
_DEBUG_sup = False
_DEBUG_d = True
_DEBUG_c = None  # 'test/test_kpis.txt'
_DEBUG_fid = None
_DEBUG_log = '_logs'
_DEBUG_nl = False

_report_kpi_l = (
    # 'running/brocade-fabric/fabric-switch',  Done automatically in brcddb.api.interface._get_chassis()
    # 'running/brocade-logging/audit-log',  # $ToDo Fix this
    'running/brocade-logging/error-log',
    'running/brocade-fibrechannel-switch/fibrechannel-switch',
    'running/brocade-fibrechannel-switch/topology-domain',
    'running/brocade-fibrechannel-switch/topology-route',
    'running/brocade-interface/fibrechannel',
    'running/brocade-interface/fibrechannel-statistics',
    # 'running/brocade-interface/logical-e-port',
    'running/brocade-media/media-rdp',
    # 'running/brocade-fabric/access-gateway',
    'running/brocade-fibrechannel-routing/routing-configuration',
    'running/brocade-fibrechannel-routing/lsan-zone',
    'running/brocade-fibrechannel-routing/lsan-device',
    'running/brocade-fibrechannel-routing/edge-fabric-alias',
    'running/brocade-zone/defined-configuration',
    'running/brocade-zone/effective-configuration',
    'running/brocade-zone/fabric-lock',
    'running/brocade-fdmi/hba',
    'running/brocade-fdmi/port',
    'running/brocade-name-server/fibrechannel-name-server',
    'running/brocade-fabric-traffic-controller/fabric-traffic-controller-device',
    'running/brocade-fibrechannel-configuration/switch-configuration',
    'running/brocade-fibrechannel-configuration/f-port-login-settings',
    'running/brocade-fibrechannel-configuration/port-configuration',
    'running/brocade-fibrechannel-configuration/zone-configuration',
    'running/brocade-fibrechannel-configuration/fabric',
    'running/brocade-fibrechannel-configuration/chassis-config-settings',
    'running/brocade-fibrechannel-configuration/fos-settings',
    'running/brocade-ficon/cup',
    'running/brocade-ficon/logical-path',
    'running/brocade-ficon/rnid',
    'running/brocade-ficon/switch-rnid',
    'running/brocade-ficon/lirr',
    'running/brocade-ficon/rlir',
    'running/brocade-fru/power-supply',
    'running/brocade-fru/fan',
    'running/brocade-fru/blade',
    'running/brocade-fru/history-log',
    'running/brocade-fru/sensor',
    'running/brocade-fru/wwn',
    'running/brocade-chassis/chassis',
    'running/brocade-chassis/ha-status',
    # 'running/brocade-maps/maps-config',
    # 'running/brocade-maps/rule',
    # 'running/brocade-maps/maps-policy',
    # 'running/brocade-maps/group',
    'running/brocade-maps/dashboard-rule',
    'running/brocade-maps/dashboard-history',
    'running/brocade-maps/dashboard-misc',
    # 'running/brocade-maps/system-resources',
    # 'running/brocade-maps/paused-cfg',
    # 'running/brocade-maps/monitoring-system-matrix',
    # 'running/brocade-maps/switch-status-policy-report',
    # 'running/brocade-maps/fpi-profile',
    'running/brocade-time/clock-server',
    'running/brocade-time/time-zone',
    'running/brocade-license/license',
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
    global _report_kpi_l

    kpi_l = _report_kpi_l if c_file is None else brcdapi_util.uris_for_method(session, 'GET', uri_d_flag=False) if \
        c_file == '*' else brcdapi_file.read_file(c_file)

    rl = list()
    for kpi in kpi_l:
        uri_d = brcdapi_util.uri_d(session, kpi)
        if uri_d is not None:
            if 'GET' in uri_d['methods'] and uri_d['area'] != brcdapi_util.NULL_OBJ:
                rl.append(kpi)
        else:
            # Different versions of FOS support different KPIs so log it but don't pester the operator with it.
            brcdapi_log.log(':UNKNOWN KPI: ' + kpi)
    return rl


def _get_input():
    """Parses the module load command line

    :return ec: Error code
    :rtype ec: int
    :return args_ip: IP address
    :rtype args_ip: str
    :return args_id: User ID
    :rtype args_id: str
    :return args_pw: Password
    :rtype args_pw: str
    :return args_f: Name of output file
    :rtype args_f: str
    :return args_s: Type of HTTP security. Should be 'none' or 'self'
    :rtype args_s: str
    :return args_c: Name of file containing URIs to GET.
    :rtype args_c: str, None
    :return args_fid: CSV list of FIDs to capture data for
    :rtype args_fid: list, None
    """
    global _DEBUG_ip, _DEBUG_id, _DEBUG_pw, _DEBUG_f, _DEBUG_s, _DEBUG_sup, _DEBUG_d, _DEBUG_c
    global _DEBUG_fid, _DEBUG_log, _DEBUG_nl, _DEBUG

    ec = brcddb_common.EXIT_STATUS_OK

    if _DEBUG:
        args_ip, args_id, args_pw, args_f, args_s, args_sup, args_d, args_c, args_fid, args_log, args_nl = \
            _DEBUG_ip, _DEBUG_id, _DEBUG_pw, _DEBUG_f, _DEBUG_s, _DEBUG_sup, _DEBUG_d, _DEBUG_c, _DEBUG_fid, \
            _DEBUG_log, _DEBUG_nl
    else:
        parser = argparse.ArgumentParser(description='Capture (GET) requests from a chassis')
        parser.add_argument('-f', help='Output file for captured data', required=True)
        parser.add_argument('-ip', help='IP address', required=True)
        parser.add_argument('-id', help='User ID', required=True)
        parser.add_argument('-pw', help='Password', required=True)
        parser.add_argument('-s', help='\'CA\' or \'self\' for HTTPS mode.', required=False,)
        buf = '(Optional) Name of file with list of KPIs to capture. Use * to capture all data the chassis supports. '\
              'The default is to capture all KPIs required for the report.'
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
        buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The ' \
              'log file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
        parser.add_argument('-log', help=buf, required=False, )
        buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
        parser.add_argument('-nl', help=buf, action='store_true', required=False)
        args = parser.parse_args()

        args_ip, args_id, args_pw, args_f, args_s, args_sup, args_d, args_c, args_fid, args_log, args_nl = \
            args.ip, args.id, args.pw, args.f, args.s, args.sup, args.d, args.c, args.fid, args.log, args.nl

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
        'capture.py version: ' + __version__,
        'IP:          ' + brcdapi_util.mask_ip_addr(args_ip, keep_last=True),
        'ID:          ' + args_id,
        'security:    ' + args_s + ' UNSUPPORTED HTTPS method!' if ec != brcddb_common.EXIT_STATUS_OK else '',
        'Output file: ' + args_f,
        'KPI file:    ' + str(args_c),
        'FID List:    ' + str(args_fid)
    ]
    if _DEBUG:
        ml.insert(0, 'WARNING!!! Debug is enabled')
    brcdapi_log.log(ml, echo=True)


    return ec, args_ip, args_id, args_pw, brcdapi_file.full_file_name(args_f, '.json'),\
           'none' if args_s is None else args_s, args_c, None if args_fid is None else args_fid.split(',')


def pseudo_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    global __version__

    signal.signal(signal.SIGINT, brcdapi_rest.control_c)

    ec, ip, user_id, pw, outf, sec, c_file, fid_l = _get_input()
    if ec != brcddb_common.EXIT_STATUS_OK:
        return ec

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
    except KeyboardInterrupt:
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
        brcdapi_log.log('Processing terminated by user.', echo=True)
    except RuntimeError:
        ec = brcddb_common.EXIT_STATUS_API_ERROR
        brcdapi_log.log('Programming error encountered. See previous message', echo=True)
    except BaseException as e:
        ec = brcddb_common.EXIT_STATUS_ERROR
        e_buf = str(e, errors='ignore') if isinstance(e, (bytes, str)) else str(type(e))
        brcdapi_log.log('Programming error encountered. Exception is: ' + e_buf, echo=True)

    # Logout
    try:
        obj = brcdapi_rest.logout(session)
        if brcdapi_auth.is_error(obj):
            brcdapi_log.log(['Logout failed. Error is:', brcdapi_auth.formatted_error_msg(obj)], echo=True)
        else:
            brcdapi_log.log('Logout succeeded', echo=True)
    except (http.client.CannotSendRequest, http.client.ResponseNotReady):
        brcdapi_log.log(['Could not logout. You may need to terminate this session via the CLI',
                         'mgmtapp --showsessions, mgmtapp --terminate'], echo=True)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Dump the database to a file
    if _WRITE and ec == brcddb_common.EXIT_STATUS_OK:
        brcdapi_log.log('Saving project to: ' + outf, echo=True)
        plain_copy = dict()
        brcddb_copy.brcddb_to_plain_copy(proj_obj, plain_copy)
        brcdapi_file.write_dump(plain_copy, outf)
        brcdapi_log.log('Save complete', echo=True)

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
brcdapi_log.close_log(['', 'Processing Complete. Exit code: ' + str(_ec)], echo=True)
exit(_ec)
