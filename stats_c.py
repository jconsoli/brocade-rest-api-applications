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
:mod:`stats_c` - Collects port statistics at a user specified interval

**Overview**

Initially collects switch and name server information plus the first sample. This is done to make it so that ports can
be associated with what is logged in. From there after, only port statistics are gathered. All data collected from the
switch is stored in a standard brcddb project. The initial switch is stored with it's WWN as is normal; however, each
additional sample is stored with the WWN and the sample number appended.

This script is pretty simple. It doesn't log out and re-login between polls so the poll cycle has to be short enough
such that the switch doesn't automatically log you out. I believe the default logout for a switch login via the API is
5 minutes. The poll cycle is a best effort in that a sleep is introduced that is calculated by:

sleep = poll cycle time - (poll finish time - poll start time)

epoch time of the server where the script is run is used for the formula above. The accuracy of the poll cycle will
depend on several factors, most notably networking delays and CPU activity. The time stamp of the data comes from the
time stamp returned with the switch response.Keep in mind that most data centers use a time clock server which is often
UTC. As of this writing, time-generated returned with the port statistics was the time on the switch when the request
was made, not when the statistics were captured by FOS. For Gen6 & Gen7, FOS polls the port statistics every 2 seconds
so the accuracy of the timestamp is within 2 seconds.

Only fibre channel port statistics are collected at this time. A JSON dump of the counters (only differences of
cumulative counters are stored, which are most of the counters) in a plain text file. Use stats_g.py to convert to an
Excel Workbook

Control-C is supported so data collection can be terminated without incident prior to the maximum number of samples
being collected.

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 1.x.x     | 03 Jul 2019   | Experimental                                                                      |
    | 2.x.x     |               |                                                                                   |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.0     | 19 Jul 2020   | Initial Launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.1     | 29 Sep 2020   | Used standard date format                                                         |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.2     | 09 Jan 2021   | Open log file.                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.3     | 13 Feb 2021   | Added # -*- coding: utf-8 -*-                                                     |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.4     | 14 Nov 2021   | Changed _MIN_POLL_TIME to 2.1 and added collection of brocade-interface. This was |
    |           |               | primarily to capture average-receive-frame-size and average-transmit-frame-size.  |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2019, 2020, 2021 Jack Consoli'
__date__ = '14 Nov 2021'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '3.0.4'

import sys
import os
import signal
import time
import datetime
import argparse
import brcddb.brcddb_project as brcddb_project
import brcdapi.log as brcdapi_log
import brcdapi.pyfos_auth as pyfos_auth
import brcdapi.brcdapi_rest as brcdapi_rest
import brcddb.brcddb_common as brcddb_common
import brcddb.util.copy as brcddb_copy
import brcddb.util.file as brcddb_file
import brcddb.api.interface as brcddb_int
import brcdapi.util as brcdapi_util

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = False
_DEBUG_IP = 'xx.xx.xx.xx'
_DEBUG_ID = 'admin'
_DEBUG_PW = 'password'
_DEBUG_SEC = 'self'  # 'none'
_DEBUG_FID = 2
_DEBUG_SUPPRESS = False
_DEBUG_VERBOSE = False
_DEBUG_POLL_TIME = None
_DEBUG_M = 4
_DEBUG_O = 'test/stats.json'
_DEBUG_LOG = '_logs'
_DEBUG_NL = False
"""_MIN_POLL is the minimum time in seconds the command line will accept. It is actually the time to sleep between each
request for statistical data. Additional comments regarding the poll cycles are in the Overview section in the module
header. Picking a sleep time that results in a poll that guarantees the poll cycle of FOS is impossible. This is why
0.1 is added. Keep in mind that if you poll a switch twice within the same internal switch poll cycle, all the
statistical counters will be the same as the previous poll but the time stamp will be different."""
_MIN_POLL = 2.1  # See comments above
_EXCEPTION_MSG = 'This normally occurs when data collection is terminated with Control-C keyboard interrupt or a '\
    'network error occured. All data collected up to this point will be saved.'
_DEFAULT_POLL_INTERVAL = 10  # Default poll interval, -p
_DEFAULT_MAX_SAMPLE = 100  # Default number of samples, -m
_proj_obj = None  # Project object (brcddb.classes.project.ProjectObj)
_session = None  # Session object returned from brcdapi.pyfos_auth.login()
_out_f = None  # Name of output file for plain text copy of _proj_obj
_base_switch_obj = None  # First switch object, brcddb.classes.switch.SwitchObj
_switch_obj = list()  # List of switch objects containing the statistic samples.

# URIs
_uris = (
    # Don't forget that if NPIV is enabled, there may be multiple logins per port. I took the liberty of assuming you
    # may also want to know other information such as the name of the switch a port is in, alias of attached login,
    # zone the logins are in,
    'brocade-fibrechannel-switch/fibrechannel-switch',  # Switch name, DID, etc...
    'brocade-interface/fibrechannel',  # Base port information
    # 'media-rdp',  # SFP data
)
_uris_2 = (  # Execute if there is a fabric principal
    # 'brocade-fibrechannel-configuration/port-configuration',  # Port configuration
    'brocade-name-server/fibrechannel-name-server',  # Name server login registration information
    'brocade-fibrechannel-configuration/zone-configuration',  # Alias and zoning associated with login
    'brocade-zone/defined-configuration',
    'brocade-zone/effective-configuration',
    'brocade-fdmi/hba',  # FDMI node data
    'brocade-fdmi/port',  # FDMI port data
)


def _wrap_up(exit_code):
    """Write out the collected data in JSON to a plain text file.

    :param exit_code: Initial exit code
    :type exit_code: int
    """
    global _proj_obj, _session, _out_f, _switch_obj, _base_switch_obj

    ec = exit_code
    if _session is not None:
        try:
            obj = brcdapi_rest.logout(_session)
            if pyfos_auth.is_error(obj):
                brcdapi_log.log(pyfos_auth.formatted_error_msg(obj), True)
        except:  # Bare because I'm not debugging other libraries or FOS API errors.
            brcdapi_log.log('Logout failure. ' + _EXCEPTION_MSG, True)
        _session = None

    try:
        _proj_obj.s_new_key('base_switch_wwn', _base_switch_obj.r_obj_key())
        _proj_obj.s_new_key('switch_list', [obj.r_obj_key() for obj in _switch_obj])
        plain_copy = dict()
        brcddb_copy.brcddb_to_plain_copy(_proj_obj, plain_copy)
        brcddb_file.write_dump(plain_copy, _out_f)
    except:  # This shouldn't be bare, but what?
        pass
    return ec


def _signal_handler(sig, frame):
    os._exit(_wrap_up())  # Yes, I should call subprocess.Popen() to clean up, but this is easy.


def parse_args():
    """Parses the module load command line

    :return ip_addr: IP address
    :rtype ip_addr: str
    :return id: User ID
    :rtype id: str
    :return pw: Password
    :rtype pw: str
    :return http_sec: Type of HTTP security
    :rtype http_sec: str
    :return suppress_flag: True - suppress all print to STD_OUT
    :rtype suppress_flag: bool
    :return fid: Fabric ID in chassis specified by -ip where the zoning information is to copied to.
    :rtype fid: int
    :return suppress_flag: True - suppress all print to STD_OUT
    :rtype suppress_flag: bool
    :return report_name: Name of Excel report. Must include the appendix '.xlsx'
    :rtype report_name: str
    """
    global _DEBUG, _DEBUG_IP, _DEBUG_ID, _DEBUG_PW, _DEBUG_SEC, _DEBUG_FID, _DEBUG_SUPPRESS
    global _DEBUG_POLL_TIME, _DEBUG_M, _DEBUG_O, _DEBUG_VERBOSE, _DEBUG_LOG, _DEBUG_NL

    if _DEBUG:
        return _DEBUG_IP, _DEBUG_ID, _DEBUG_PW, _DEBUG_SEC, _DEBUG_FID, _DEBUG_SUPPRESS, _DEBUG_POLL_TIME, _DEBUG_M, \
               _DEBUG_O, _DEBUG_VERBOSE, _DEBUG_LOG, _DEBUG_NL
    buf = 'Collect port statistics at a specified poll interval. Use Control-C to stop data collection and write report'
    parser = argparse.ArgumentParser(description=buf)
    parser.add_argument('-ip', help='Required. IP address', required=True)
    parser.add_argument('-id', help='Required. User ID', required=True)
    parser.add_argument('-pw', help='Required. Password', required=True)
    buf = '(Optional) \'CA\' or \'self\' for HTTPS mode. Default is HTTP'
    parser.add_argument('-s', help=buf, required=False,)
    buf = 'Required. Name of output file where raw data is to be stored. ".json" extension is automatically appended.'
    parser.add_argument('-o', help=buf, required=True)
    buf = '(Optional) Virtual Fabric ID (1 - 128) of switch to read statistics from. Default is 128'
    parser.add_argument('-fid', help=buf, type=int, required=False)
    buf = '(Optional) No arguments. Suppress all library generated output to STD_IO except the exit code. Useful with'\
          ' batch processing'
    parser.add_argument('-sup', help=buf, action='store_true', required=False)
    buf = '(Optional) Polling interval in seconds. Default is '\
          + str(_DEFAULT_POLL_INTERVAL) + '. The minimum is ' + str(_MIN_POLL) + ' seconds.'
    parser.add_argument('-p', help=buf, type=float, required=False)
    buf = '(Optional) Samples are collected until this maximum is reached or a Control-C keyboard interrupt is '\
          'received. Default: ' + str(_DEFAULT_MAX_SAMPLE)
    parser.add_argument('-m', help=buf, type=int, required=False)
    buf = '(Optional) No arguments. Enable debug logging'
    parser.add_argument('-d', help=buf, action='store_true', required=False)
    buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The log '\
          'file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
    parser.add_argument('-log', help=buf, required=False,)
    buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
    parser.add_argument('-nl', help=buf, action='store_true', required=False)
    args = parser.parse_args()
    return args.ip, args.id, args.pw, args.s, args.fid, args.sup, args.p, args.m, args.o, args.d, args.log, args.nl


def _stats_diff(old_obj, new_obj):
    """Builds a structure that looks like 'brocade-interface/fibrechannel-statistics' but just the differences

    :param old_obj: Previous list returned from 'brocade-interface/fibrechannel-statistics'
    :type old_obj: dict
    :param new_obj: New list returned from 'brocade-interface/fibrechannel-statistics'
    :type new_obj: dict
    :return: Port statistics differences in the format returned from 'brocade-interface/fibrechannel-statistics'
    :rtype: dict
    """
    new_list = list()
    ret_obj = {'fibrechannel-statistics': new_list}

    # I'm not sure if it's a guarantee to get the ports in the same order but I need to account for a port going offline
    # anyway so the code below creates a map (dict) of old ports to their respective stats
    old_ports = dict()
    for port in old_obj.get('fibrechannel-statistics'):
        old_ports.update({port.get('name'): port})

    # Get the differences
    for port in new_obj.get('fibrechannel-statistics'):
        if port is None:
            break  # This can happen when the user Control-C out. I have no idea why, but I've seen it happen
        new_stats = dict()
        port_num = port.get('name')
        old_stats = old_ports.get(port_num)
        if old_stats is None:
            new_stats = port
        else:
            for k, v in port.items():
                if k not in ('sampling-interval', 'time-generated') and 'rate' not in k and isinstance(v, (int, float)):
                    new_stats.update({k: v - old_stats.get(k)})
                elif isinstance(v, dict):
                    d1 = dict()
                    for k1, v1 in v.items():
                        d1.update({k1: v1 - v.get(k1)})
                    new_stats.update({k: d1})
                else:
                    new_stats.update({k: v})
        new_list.append(new_stats)
    return ret_obj


def pseudo_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    global _DEBUG, _DEFAULT_POLL_INTERVAL, _DEFAULT_MAX_SAMPLE, _proj_obj, _session, _out_f, _switch_obj, _base_switch_obj
    global __version__, _uris, _uris_2

    signal.signal(signal.SIGINT, _signal_handler)

    # Get user input
    ip, user_id, pw, sec, fid, s_flag, pct, max_p, _out_f, vd, log, nl = parse_args()
    if not nl:
        brcdapi_log.open_log(log)
    if vd:
        brcdapi_rest.verbose_debug = True
    if s_flag:
        brcdapi_log.set_suppress_all()
    default_text = ' (default)'
    sec = 'none' if sec is None else sec
    ml = ['WARNING!!! Debug is enabled'] if _DEBUG else list()
    ml.append(os.path.basename(__file__) + ' version: ' + __version__)
    ml.append('IP Address:    ' + brcdapi_util.mask_ip_addr(ip))
    ml.append('User ID:       ' + user_id)
    ml.append('FID:           ' + str(fid))
    if max_p is None:
        max_p = _DEFAULT_MAX_SAMPLE
        ml.append('Samples:       ' + str(max_p) + default_text)
    else:
        ml.append('Samples:       ' + str(max_p))
    if pct is None:
        pct = _DEFAULT_POLL_INTERVAL
        ml.append('Poll Interval: ' + str(pct) + default_text)
    else:
        ml.append('Poll Interval: ' + str(pct) + ' (defaulting to ' + str(_MIN_POLL) + ')' if pct < _MIN_POLL else '')
    ml.append('Output File:   ' + _out_f)
    brcdapi_log.log(ml, True)
    x = len('.json')
    if len(_out_f) < x or _out_f[len(_out_f)-x] != '.json':
        _out_f += '.json'

    # Create project
    _proj_obj = brcddb_project.new('Port_Stats', datetime.datetime.now().strftime('%d %b %Y %H:%M:%S'))
    _proj_obj.s_python_version(sys.version)
    _proj_obj.s_description('Port statistics')

    # Login
    _session = brcddb_int.login(user_id, pw, ip, sec, _proj_obj)
    if pyfos_auth.is_error(_session):
        brcdapi_log.log(pyfos_auth.formatted_error_msg(_session), True)
        return brcddb_common.EXIT_STATUS_ERROR

    try:  # I always put all code after login in a try/except in case of a code bug or network error, I still logout
        # Capture the initial switch and port information along with the first set of statistics.
        brcdapi_log.log('Capturing initial data', True)
        brcddb_int.get_batch(_session, _proj_obj, _uris, fid)  # Captured data is put in _proj_obj
        chassis_obj = _proj_obj.r_chassis_obj(_session.get('chassis_wwn'))
        if chassis_obj.r_is_vf_enabled():
            if fid is None:
                fid = 128
            _base_switch_obj = chassis_obj.r_switch_obj_for_fid(fid)
        else:
            _base_switch_obj = chassis_obj.r_switch_objects()[0]
        if _base_switch_obj is None:
            brcdapi_log.log('Switch for FID ' + str(fid) + ' not found. ', True)
            return _wrap_up(brcddb_common.EXIT_STATUS_ERROR)
        base_switch_wwn = _base_switch_obj.r_obj_key()
        if _base_switch_obj.r_fabric_key() is None:
            _base_switch_obj.s_fabric_key(base_switch_wwn)  # Fake out a fabric principal if we don't have one
            _proj_obj.s_add_fabric(base_switch_wwn)
        brcddb_int.get_batch(_session, _proj_obj, _uris_2, fid)  # Captured data is put in _proj_obj
        time.sleep(5)  # Somewhat arbitrary time. Don't want a throttling delay if the poll interval is very short

        # Get the first sample
        stats_buf = 'brocade-interface/fibrechannel-statistics'
        last_time = time.time()
        last_stats = brcddb_int.get_rest(_session, stats_buf, _base_switch_obj, fid)
        for p in last_stats.get('fibrechannel-statistics'):
            _base_switch_obj.r_port_obj(p.get('name')).s_new_key('fibrechannel-statistics', p)

        # Now start collecting the port and interface statistics
        for i in range(0, max_p):
            x = pct - (time.time() - last_time)
            time.sleep(_MIN_POLL if x < _MIN_POLL else x)
            switch_obj = _proj_obj.s_add_switch(base_switch_wwn + '-' + str(i))
            last_time = time.time()
            obj = brcddb_int.get_rest(_session, 'brocade-interface/fibrechannel', switch_obj, fid)
            if not pyfos_auth.is_error(obj):
                for p in obj.get('fibrechannel'):
                    switch_obj.s_add_port(p.get('name')).s_new_key('fibrechannel', p)
                obj = brcddb_int.get_rest(_session, stats_buf, switch_obj, fid)
            if pyfos_auth.is_error(obj):  # We typically get here when the login times out or network fails.
                brcdapi_log.log('Error encountered. Data collection limited to ' + str(i) + ' samples.',
                                True)
                _wrap_up(brcddb_common.EXIT_STATUS_ERROR)
                return brcddb_common.EXIT_STATUS_ERROR
            obj = brcddb_int.get_rest(_session, stats_buf, switch_obj, fid)
            if pyfos_auth.is_error(obj):  # We typically get here when the login times out or network fails.
                brcdapi_log.log('Error encountered. Data collection limited to ' + str(i) + ' samples.',
                                True)
                _wrap_up(brcddb_common.EXIT_STATUS_ERROR)
                return brcddb_common.EXIT_STATUS_ERROR

            for p in _stats_diff(last_stats, obj).get('fibrechannel-statistics'):
                switch_obj.s_add_port(p.get('name')).s_new_key('fibrechannel-statistics', p)
            _switch_obj.append(switch_obj)
            last_stats = obj

        return _wrap_up(brcddb_common.EXIT_STATUS_OK)

    except:
        brcdapi_log.log('Error capturing statistics. ' + _EXCEPTION_MSG, True)
        return _wrap_up(brcddb_common.EXIT_STATUS_ERROR)


##################################################################
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
