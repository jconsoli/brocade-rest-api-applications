#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019, 2020 Jack Consoli.  All rights reserved.
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
:mod:`stats_clear` - Clears all statistical counters

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 1.0.0     | 01 Feb 2021   | Initial Launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.1     | 13 Feb 2021   | Added # -*- coding: utf-8 -*-                                                     |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2021 Jack Consoli'
__date__ = '13 Feb 2021'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '1.0.1'

import argparse
import sys
import os
import datetime

import brcddb.api.interface as api_int
import brcddb.brcddb_project as brcddb_project
import brcdapi.log as brcdapi_log
import brcdapi.brcdapi_rest as brcdapi_rest
import brcdapi.pyfos_auth as pyfos_auth
import brcddb.brcddb_common as brcddb_common

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = False  # When True, use _DEBUG_IP, _DEBUG_ID, _DEBUG_PW, AND _DEBUG_OUTF instead of passed arguments
_DEBUG_IP = '10.8.105.10'
_DEBUG_ID = 'admin'
_DEBUG_PW = 'password'
_DEBUG_SEC = 'self'  # None
_DEBUG_SUPPRESS = False
_DEBUG_FIDS = '128'
_DEBUG_VERBOSE = False

# URIs
chassis_uris = (
    'brocade-fibrechannel-logical-switch/fibrechannel-logical-switch',  # Must have to find switch associated with FID
)


def parse_args():
    """Parses the module load command line

    :param switch_obj: Switch object
    :type obj: brcddb.classes.SwitchObj
    :param sheet_name: Worksheet name.
    :type sheet_name: str
    :return ip: IP address
    :rtype ip: str
    :return id: User ID
    :rtype id: str
    :return pw: User password
    :rtype pw: str
    :return sec: Security - None, CA, or self
    :rtype sec: str
    :return sup: True - Suppress all output.
    :rtype sup: bool
    """
    global _DEBUG_IP, _DEBUG_ID, _DEBUG_PW, _DEBUG_SEC, _DEBUG_SUPPRESS, _DEBUG_FIDS, _DEBUG_VERBOSE

    if _DEBUG:
        return _DEBUG_IP, _DEBUG_ID, _DEBUG_PW, _DEBUG_SEC, _DEBUG_SUPPRESS, _DEBUG_FIDS, _DEBUG_VERBOSE
    parser = argparse.ArgumentParser(description='Clears all statistical counters.')
    parser.add_argument('-ip', help='Required. IP address', required=True)
    parser.add_argument('-id', help='Required. User ID', required=True)
    parser.add_argument('-pw', help='Required. Password', required=True)
    parser.add_argument('-s', help='Optional. \'CA\' or \'self\' for HTTPS mode.', required=False,)
    buf = 'Optional. Suppress all library generated output to STD_IO except the exit code. Useful with batch' \
          'processing'
    parser.add_argument('-sup', help=buf, action='store_true', required=False)
    buf = 'Optional. Specify a FID or CSV list of FIDs. Do not use spaces when specifying a CSV list of FIDs. If ' \
          'not specified, all FIDs are automatically determined and statics cleared from all ports from all FIDs'
    parser.add_argument('-fid', help=buf, required=False)
    parser.add_argument('-d', help='Enable debug logging', action='store_true', required=False)
    args = parser.parse_args()
    return args.ip, args.id, args.pw, args.s, args.sup, args.fid, args.d


def clear_stats(session, switch_obj):
    """Clear all statistical counters associated with a switch

    :param session: Session object returned from brcdapi.pyfos_auth.login()
    :type session: dict
    :param switch_obj: Switch object
    :type switch_obj: brcddb.classes.SwitchObj
    :return: Ending status code
    :rtype: int
    """
    ec = brcddb_common.EXIT_STATUS_OK
    stats_list = [
        dict(ports=switch_obj.r_port_keys(), content='fibrechannel-statistics'),
        dict(ports=switch_obj.r_ge_port_keys(), content='gigabitethernet-statistics')
    ]
    for stats in stats_list:
        if len(stats.get('ports')) > 0:
            pl = list()
            fid = switch_obj.r_get('brocade-fibrechannel-logical-switch/fibrechannel-logical-switch/fabric-id')
            content = {stats.get('content'): pl}
            for p in stats.get('ports'):
                d = dict()
                d.update({'name': p})
                d.update({'reset-statistics': 1})
                pl.append(d)
            obj = brcdapi_rest.send_request(session, 'brocade-interface/fibrechannel-statistics', 'PATCH', content, fid)
            if pyfos_auth.is_error(obj):
                brcdapi_log.log(pyfos_auth.obj_error_detail(obj), True)
                ec = brcddb_common.EXIT_STATUS_ERROR

    return ec


def psuedo_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    ec = brcddb_common.EXIT_STATUS_OK

    # Get the user input
    ml = ['WARNING!!! Debug is enabled'] if _DEBUG else list()
    ip, user_id, pw, sec, s_flag, fid, vd, log, nl = parse_args()
    if not nl:
        brcdapi_log.open_log(log)
    if vd:
        brcdapi_rest.verbose_debug = True
    if s_flag:
        brcdapi_log.set_suppress_all()
    if sec is None:
        sec = 'none'
    fid_list = None if fid is None else [int(i) for i in fid.split(',')]
    ml.extend([
        'IP address: ' + ip,
        'User ID:    ' + user_id,
        'Security:   ' + sec,
        'Surpress:   ' + str(s_flag),
        'FID:        ' + 'Automatic' if fid is None else fid])
    brcdapi_log.log(ml, True)

    # Create the project
    proj_obj = brcddb_project.new('Captured_data', datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
    proj_obj.s_python_version(sys.version)
    proj_obj.s_description('Unused ports to disable')

    # Login
    session = api_int.login(user_id, pw, ip, sec, proj_obj)
    if pyfos_auth.is_error(session):
        brcdapi_log.log(pyfos_auth.formatted_error_msg(session), True)
        return brcddb_common.EXIT_STATUS_ERROR

    # Capture data - stats are cleared on a per port basis so this is needed to determine what the ports are.
    try:  # I always put all code after login in a try/except so that if I have a code bug, I still logout
        brcdapi_log.log('Capturing data', True)
        api_int.get_batch(session, proj_obj, chassis_uris, list(), fid_list)  # Captured data is put in proj_obj
        chassis_obj = proj_obj.r_chassis_obj(session.get('chassis_wwn'))

        # Clear stats on each switch
        for switch_obj in chassis_obj.r_switch_objects():
            fid = switch_obj.r_get('brocade-fibrechannel-logical-switch/fibrechannel-logical-switch/fabric-id')
            if fid_list is None or fid in fid_list:
                temp_ec = clear_stats(session, switch_obj)
                ec = temp_ec if ec != brcddb_common.EXIT_STATUS_OK else ec
    except:
        brcdapi_log.exception('Programming error encountered', True)
        ec = brcddb_common.EXIT_STATUS_ERROR

    # Logout
    obj = brcdapi_rest.logout(session)
    if pyfos_auth.is_error(obj):
        brcdapi_log.log(pyfos_auth.formatted_error_msg(obj), True)
        return brcddb_common.EXIT_STATUS_ERROR

    return ec

##################################################################
#
#                    Main Entry Point
#
###################################################################


if _DOC_STRING:
    print('_DOC_STRING is True. No processing')
else:
    ec = psuedo_main()
    brcdapi_log.close_log(str(ec), True)
    exit(ec)
