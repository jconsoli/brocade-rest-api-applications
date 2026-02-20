#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright 2023, 2024, 2025, 2026 Jack Consoli.  All rights reserved.

**License**

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may also obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.

The license is free for single customer use (internal applications). Use of this module in the production,
redistribution, or service delivery for commerce requires an additional license. Contact jack_consoli@yahoo.com for
details.

**Description**

Collects port statistics at a user specified interval

Initially collects switch and name server information plus the first sample. This is done to make it so that ports can
be associated with what is logged in. From thereafter, only port statistics are gathered. All data collected from the
switch is stored in a standard brcddb project. The initial switch is stored with it's WWN as is normal; however, each
additional sample is stored with the WWN and the sample number appended.

This script is pretty simple. It doesn't log out and re-login between polls so the poll cycle has to be short enough
such that the switch doesn't automatically log you out. I believe the default logout for a switch login via the API is
5 minutes. To maintain the poll cycle a sleep is introduced that is calculated by:

sleep = poll cycle time - (poll finish time - poll start time)

epoch time of the server where the script is run is used for the formula above. The accuracy of the poll cycle will
depend on several factors, most notably networking delays and CPU activity. The time stamp of the data comes from the
time stamp returned with the switch response.Keep in mind that most data centers use a time clock server which is often
UTC. As of this writing, time-generated returned with the port statistics was the time on the switch when the request
was made, not when the statistics were captured by FOS. For Gen6 & Gen7, FOS polls the port statistics every 2 seconds
so the accuracy of the timestamp is within 2 seconds. A new parameter, time-refreshed, was added in one of the 9.x
released, but to maintain support with older versions of FOS, time-generated is still used. Given that the minimum
interval is 2.1 sec, this is moot.

Only fibre channel port statistics are collected at this time. A JSON dump of the counters (only differences of
cumulative counters are stored, which are most of the counters) in a plain text file. Use stats_g.py to convert to an
Excel Workbook

Control-C is supported so data collection can be terminated without incident prior to the maximum number of samples
being collected.

**Version Control**

+-----------+---------------+---------------------------------------------------------------------------------------+
| Version   | Last Edit     | Description                                                                           |
+===========+===============+=======================================================================================+
| 4.0.0     | 04 Aug 2023   | Re-Launch                                                                             |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.1     | 06 Mar 2024   | Set verbose debug via brcdapi.brcdapi_rest.verbose_debug()                            |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.2     | 03 Apr 2024   | Added version numbers of imported libraries.                                          |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.3     | 16 Jun 2024   | Improved help messages.                                                               |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.4     | 29 Oct 2024   | Added debug capabilities.                                                             |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.5     | 06 Dec 2024   | Fixed spelling mistake in message.                                                    |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.6     | 25 Aug 2025   | Use brcddb.util.util.get_import_modules to dynamically determined imported libraries. |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.7     | 19 Oct 2025   | Updated comments only.                                                                |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.8     | 20 Feb 2026   | Added ability to poll multiple switches.                                              |
+-----------+---------------+---------------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2024, 2025, 2026 Jack Consoli'
__date__ = '20 Feb 2026'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack_consoli@yahoo.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '4.0.8'

import http.client
import sys
import os
import signal
import datetime
import collections
import time
import copy
import brcdapi.gen_util as gen_util
import brcdapi.util as brcdapi_util
import brcdapi.log as brcdapi_log
import brcdapi.fos_auth as fos_auth
import brcdapi.brcdapi_rest as brcdapi_rest
import brcdapi.file as brcdapi_file
import brcdapi.excel_util as excel_util
import brcdapi.port as brcdapi_port
import brcddb.brcddb_common as brcddb_common
import brcddb.brcddb_project as brcddb_project
import brcddb.util.copy as brcddb_copy
import brcddb.api.interface as brcddb_int
import brcddb.classes.util as class_util

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
# _STAND_ALONE: True: Executes as a standalone module taking input from the command line. False: Does not automatically
# execute. This is useful when importing this module into another module that calls psuedo_main().
_STAND_ALONE = True  # See note above
_DEBUG = False  # True: skip the sleep between sample collection. Useful when simulating in brcdapi.brcdapi_restapi.py

"""_MIN_POLL is the minimum time in seconds the command line will accept. It is actually the time to sleep between each
request for statistical data. Additional comments regarding the poll cycles are in the Overview section in the module
header. Picking a sleep time that results in a poll that guarantees the poll cycle of FOS is impossible. This is why
0.1 is added. Keep in mind that if you poll a switch twice within the same internal switch poll cycle, all the
statistical counters will be the same as the previous poll but the time stamp will be different."""
_MIN_POLL = 2.1  # See comments above
_MIN_SLEEP = 0.2  # Minimum time to sleep between poll cycles. This is somewhat arbitrary and may not be necessary.
_MAX_POLL = 3600  # 1 hour. I believe the maximum API login time without any activity is 2 hours.
_EXCEPTION_MSG = 'This normally occurs when data collection is terminated with Control-C keyboard interrupt or a '\
    'network error occurred. All data collected up to this point will be saved.'
_DEFAULT_POLL_INTERVAL = 10.0  # Default poll interval, -p
_DEFAULT_MAX_SAMPLE = 100  # Default number of samples, -m
_MIN_SAMPLES = 5  # A somewhat arbitrary minimum number of samples.

_p_help = 'Optional. Polling interval in seconds. Fractions of a second are supported, so this may be an integer or '
_p_help += 'floating point number. Default: ' + str(_DEFAULT_POLL_INTERVAL) + ' sec. Minimum: ' + str(_MIN_POLL)
_p_help += ' sec. Maximum: ' + str(_MAX_POLL) + ' sec. If the poll time is >= to the HTTP connection timeout, 15 sec '
_p_help += 'when this was written, disable the HTTP timeout. The HTTP connection timeout is determined after login. '
_p_help += 'Program execution will halt if the poll time exceeds the HTTP connection timeout. To disable the HTTP '
_p_help += 'connection timeout: "py app_config.py -https_dis"'
_m_help = 'Optional. Number of samples to collect. Default: ' + str(_DEFAULT_MAX_SAMPLE) + '. Minimum: '
_m_help += str(_MIN_SAMPLES) + '. Maximum: None.'
_input_d = collections.OrderedDict()
_input_d.update(
    i=dict(h='Required. Name of workbook containing login credentials and FID number for switches to be polled. '
             '".xlsx" extension is automatically appended.'),
    o=dict(h='Required. Name of output file where raw data is to be stored. ".json" extension is automatically '
             'appended.'),
    p=dict(r=False, t='float', d=_DEFAULT_POLL_INTERVAL, h=_p_help),
    m=dict(r=False, t='int', d=_DEFAULT_MAX_SAMPLE, h=_m_help),
    clr=dict(r=False, t='bool', d=False, h='Optional. Clear stats before starting.')
)
_input_d.update(gen_util.parseargs_log_d.copy())
_input_d.update(gen_util.parseargs_debug_d.copy())

# URIs
_uris_0 = (
    # Chassis information is automatically determined after login
    'running/' + brcdapi_util.bcmic_uri,  # Management interface configuration
    'running/' + brcdapi_util.bfs_uri,  # Switch name, DID, etc...
)
_uris_1 = (
    'running/' + brcdapi_util.bifc_uri,  # Base port information + average frame size
    'running/' + brcdapi_util.bfc_port_uri,  # Port configuration
    'running/' + brcdapi_util.bns_uri,  # Name server login registration information
    'running/' + brcdapi_util.bz_def,  # Defined zone database
    'running/' + brcdapi_util.bz_eff,  # Effective zone database
    'running/' + brcdapi_util.fdmi_hba,  # FDMI node data
    'running/' + brcdapi_util.fdmi_port,  # FDMI port data
)
_port_statistics = 'running/' + brcdapi_util.bifc_stats

_skip_list_l = brcddb_copy.default_skip_list.copy()
_skip_list_l.extend(
    [
        'stats_c/session',
    ]
)

# Debug
_debug_d = {
    '0/0': {
        'out-frames': dict(i=0, v=(100, 122, 200, 150, 110, 0)),
        'in-frames': dict(i=0, v=(5000, 2000, 2200, 1530, 1100, 4500))
    },
    '0/1': {
        'out-frames': dict(i=0, v=(150, 222, 180, 150, 110, 0)),
        'in-frames': dict(i=0, v=(3000, 2000, 2200, 1530, 1100, 4500))
    },
}


def _debug_values(obj):
    """Used for debug only. Inserts fake values for port statistics

    :param obj: Port statistics collected from FOS
    :type obj: dict
    :return: Modified port statistics, if applicable
    :rtype: dict
    """
    global _DEBUG, _debug_d

    if _DEBUG and not fos_auth.is_error(obj):
        r_obj = copy.deepcopy(obj)
        for r_obj_d in [d for d in r_obj['fibrechannel-statistics'] if d['name'] in _debug_d]:
            port = r_obj_d['name']
            for key in _debug_d[port].keys():
                r_obj_d[key] += _debug_d[port][key]['v'][_debug_d[port][key]['i']]
                x = _debug_d[port][key]['i'] + 1
                _debug_d[port][key]['i'] = 0 if x >= len(_debug_d[port][key]['v']) else x
        return r_obj

    return obj


def _login(proj_obj):
    """Login to all chassis

    :param proj_obj: The project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :return: Exit code. See exit codes in brcddb.brcddb_common
    :rtype: int
    """
    switch_poll_d = proj_obj.rs_key('stats_c', dict())
    for d in switch_poll_d.values():
        try:
            d['session'] = brcddb_int.login(d['user_id'], d['pw'], d['ip_addr'], d['security'], proj_obj)
            if fos_auth.is_error(d['session']):
                brcdapi_log.log(
                    [
                        'Login failed for ' + brcdapi_util.mask_ip_addr(d.get('ip_addr')) + '. Error is:',
                        fos_auth.formatted_error_msg(d['session'])
                    ],
                    echo=True
                )
                ec = brcddb_common.EXIT_STATUS_ERROR
        except (KeyboardInterrupt, http.client.CannotSendRequest, http.client.ResponseNotReady):
            brcdapi_log.log('Control-C. Terminating data collection.', echo=True)
            return brcddb_common.EXIT_STATUS_ERROR
        except BaseException as e:
            brcdapi_log.log(
                [
                    'Error logging in to switch at ' + brcdapi_util.mask_ip_addr(d.get('ip_addr')),
                    'Error is:',
                    class_util.format_obj(e)
                ],
                echo=True
            )
            return brcddb_common.EXIT_STATUS_ERROR

    return brcddb_common.EXIT_STATUS_OK


def _initial_capture(proj_obj, args_d):
    """Capture basic chassis and switch info. Add "stats_c" tracking to applicable objects.
    
    :param proj_obj: The project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :param args_d: Conditioned command line input.
    :type args_d: dict
    :return ec: Exit code. See exit codes in brcddb.brcddb_common
    :rtype ec: int
    :return last_poll_time: Epoch time for initial stats poll
    :rtype last_poll_time: float
    """
    switch_poll_d, chassis_obj = proj_obj.r_get('stats_c'), None
    
    # Capture chassis information
    brcdapi_log.log('Capturing chassis information', echo=True)
    for d in switch_poll_d.values():
        brcddb_int.get_batch(d['session'], proj_obj, _uris_0)  # Captured data is put in proj_obj
        chassis_obj = proj_obj.r_chassis_obj(d['session']['chassis_wwn'])

        # Make sure the poll cycle does not exceed the timeout.
        keep_alive_to = chassis_obj.r_get(brcdapi_util.bc_https_ka_to)
        if chassis_obj.r_get(brcdapi_util.bc_https_ka) and keep_alive_to <= (args_d['p'] + 0.5):
            buf = 'The keep alive time (' + str(keep_alive_to) + ') must be at least 0.5 seconds longer than the '
            buf += ' poll cycle (' + str(args_d['p']) + '). Consider using "py app_config.py -https_dis" to disable'
            buf += ' the REST interface timeout.'
            brcdapi_log.log(buf, echo=True)
            return brcddb_common.EXIT_STATUS_INPUT_ERROR, 0.0
    
        # Resolve FID numbers into a list of FIDs.
        fid_l = chassis_obj.r_fid_list()
        fid_l.sort()
        if d['FID'] == '*':
            d['fid_l'] = fid_l
        else:
            d['fid_l'] = list()
            for fid in gen_util.range_to_list(str(d['FID'])):
                if fid not in fid_l or fid < 1 or fid > 128:
                    brcdapi_log.log('FID ' + str(fid) + ' is not valid at row ' + str(d['row']), echo=True)
                    return brcddb_common.EXIT_STATUS_INPUT_ERROR, 0.0
                d['fid_l'].append(fid)
    
        # Add stats_c to each port object
        for switch_obj in [chassis_obj.r_switch_obj_for_fid(fid) for fid in d['fid_l']]:
            for port_obj in switch_obj.r_port_objects():
                port_obj.rs_key('stats_c', dict(samples=list()))
    
    # Capture the initial fabric and port information
    brcdapi_log.log('Capturing switch and port configuration information', echo=True)
    for d in switch_poll_d.values():
        if args_d['clr']:
            for fid in d['fid_l']:
                brcdapi_port.clear_stats(
                    d['session'],
                    fid,
                    chassis_obj.r_switch_obj_for_fid(fid).r_port_keys()
                )
        brcddb_int.get_batch(d['session'], proj_obj, _uris_1, fid=d['fid_l'])

    # Add the port statistics to the initial capture.
    brcdapi_log.log('Capturing initial data sample', echo=True)
    last_poll_time = time.time()
    for d in switch_poll_d.values():
        brcddb_int.get_batch(d['session'], proj_obj, _port_statistics, fid=d['fid_l'])

    return brcddb_common.EXIT_STATUS_OK, last_poll_time


def _sample_captures(proj_obj, args_d, last_poll_time):
    """Capture basic chassis and switch info. Add "stats_c" tracking to applicable objects.

    :param proj_obj: The project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :param args_d: Conditioned command line input.
    :type args_d: dict
    :param last_poll_time: Epoch time of the initial poll
    :type last_poll_time: float
    :return: Exit code. See exit codes in brcddb.brcddb_common
    :rtype: int
    """
    switch_poll_d, sample_count, ec = proj_obj.r_get('stats_c'), 1, brcddb_common.EXIT_STATUS_OK

    while True:

        # Temporary storage for port statistics. Key is the switch WWN.
        switch_d = dict()

        # Wait for next poll cycle
        if not _DEBUG:
            time.sleep(min(_MIN_SLEEP, time.time() + args_d['p'] - last_poll_time))

        brcdapi_log.log('Capturing data sample ' + str(sample_count), echo=True)
        last_poll_time = time.time()
        for d in switch_poll_d.values():
            chassis_obj = proj_obj.r_chassis_obj(d['session']['chassis_wwn'])
            for fid in d['fid_l']:
                obj = _debug_values(brcdapi_rest.get_request(d['session'], _port_statistics, fid))
                if fos_auth.is_error(obj):
                    brcdapi_log.log(
                        [
                            'Error collecting stats for ' + brcdapi_util.mask_ip_addr(d['ip_addr']),
                            fos_auth.formatted_error_msg(obj)
                        ],
                        echo=True)
                switch_d[chassis_obj.r_switch_obj_for_fid(fid).r_obj_key()] = obj

        # Add the stats to the port objects. Doing this data collection to minimize time gap between each switch
        for switch_wwn, obj_d in switch_d.items():
            switch_obj = proj_obj.r_switch_obj(switch_wwn)
            for port_stats_d in obj_d['fibrechannel-statistics']:
                try:
                    switch_obj.r_port_obj(port_stats_d['name']).r_get('stats_c')['samples'].append(port_stats_d)
                except (KeyError, TypeError):
                    pass  # If a port was added or removed, just ignore it.

        # Are we done?
        sample_count += 1
        if sample_count > args_d['m']:
            brcdapi_log.log('Data collection complete.', echo=True)
            break

    return ec


def _logout(proj_obj):
    """Logout of all chassis

    :param proj_obj: The project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :return: Exit code. See exit codes in brcddb.brcddb_common
    :rtype: int
    """
    ec = brcddb_common.EXIT_STATUS_OK

    switch_poll_d = proj_obj.r_get('stats_c')
    for d in switch_poll_d.values():
        el = brcddb_int.logout(d['session'])
        if len(el) > 0:
            if el[0] != 'API logout succeeded' or len(el) > 1:
                el.insert(0, 'Error logging out of ' + brcdapi_util.mask_ip_addr(d.get('ip_addr')))
                brcdapi_log.log(el, echo=True)
                ec = brcddb_common.EXIT_STATUS_API_ERROR

    return ec


def _write_db(proj_obj, db_name):
    """Converts the project object to standard Python data structures and write to a JSON file.
    :param proj_obj: The project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :param db_name: File name to be written to
    :type db_name: str
    """
    ec = brcddb_common.EXIT_STATUS_OK

    brcdapi_log.log('Saving project to: ' + db_name, echo=True)
    proj_obj.s_new_key('stats_c', dict(), f=True)  # Effectively deletes stats_c.
    plain_copy = dict()
    brcddb_copy.brcddb_to_plain_copy(proj_obj, plain_copy)
    try:
        brcdapi_file.write_dump(plain_copy, db_name)
        brcdapi_log.log('Save complete', echo=True)
    except FileNotFoundError:
        brcdapi_log.log('Input file, ' + db_name + ', not found', echo=True)  # I don't think this can happen
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    except FileExistsError:
        brcdapi_log.log('Folder in ' + db_name + ' does not exist', echo=True)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    except PermissionError:
        brcdapi_log.log('Permission error writing ' + db_name, echo=True)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    return ec


def pseudo_main(switch_l, args_d):
    """Basically the main(). Did it this way so that it can easily be used as a standalone module or called externally.

    :param switch_l: List of switch login credentials read from input file, -i
    :type switch_l: list
    :param args_d: Conditioned command line input.
    :type args_d: dict
    :return: Exit code. See exit codes in brcddb.brcddb_common
    :rtype: int
    """
    global _uris_0, _MIN_SLEEP, _port_statistics
    
    ec, last_poll_time, switch_poll_d = brcddb_common.EXIT_STATUS_OK, 0, dict()

    signal.signal(signal.SIGINT, brcdapi_rest.control_c)

    # Create the project
    proj_obj = brcddb_project.new('Port_Stats', datetime.datetime.now().strftime('%d %b %Y %H:%M:%S'))
    proj_obj.s_python_version(sys.version)
    proj_obj.s_description('Port statistics')
    proj_obj.s_new_key('stats_c', switch_poll_d)

    # Consolidate the list of switches to poll
    row, el = 2, list()
    for d in switch_l:
        error_flag = False
        sub_switch_poll_d = switch_poll_d.get(d['ip_addr'])
        if sub_switch_poll_d is None:
            sub_switch_poll_d = d.copy()
            sub_switch_poll_d['input_fid'] = list()
            switch_poll_d[d['ip_addr']] = sub_switch_poll_d
            for key in ['ip_addr', 'pw', 'user_id']:
                if not isinstance(sub_switch_poll_d.get(key), str):
                    el.append(key + ' at row ' + str(row) + ' in ' + args_d['i'] + ' missing or invalid')
                    error_flag = True
            if error_flag:
                sub_switch_poll_d[d['ip_addr']] = sub_switch_poll_d
            else:
                sub_switch_poll_d['input_fid'] = d.get('FID')
        if not isinstance(d.get('FID'), (str, int)):
            el.append('FID at row ' + str(row) + ' in ' + args_d['i'] + ' missing or invalid')
        sub_switch_poll_d['row'] = row
        row += 1
    if len(el) > 0:
        brcdapi_log.log(el, echo=True)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Login
    if ec == brcddb_common.EXIT_STATUS_OK:
        ec = _login(proj_obj)

    try:  # I always put all code after login in a try/except in case of a code bug or network error, I still logout

        # Initial data capture and setup
        if ec == brcddb_common.EXIT_STATUS_OK:
            ec, last_poll_time = _initial_capture(proj_obj, args_d)
        
        # Start polling
        if ec == brcddb_common.EXIT_STATUS_OK:
            ec = _sample_captures(proj_obj, args_d, last_poll_time)

    except (KeyboardInterrupt, http.client.CannotSendRequest, http.client.ResponseNotReady):
        ec = brcddb_common.EXIT_STATUS_OK
    except BaseException as e:
        brcdapi_log.log(
            ['Error capturing statistics. ' + _EXCEPTION_MSG, 'Exception: '] + class_util.format_obj(e),
            echo=True
        )
        ec = brcddb_common.EXIT_STATUS_ERROR

    # Logout
    logout_ec = _logout(proj_obj)

    # Write out the DB file
    if ec == brcddb_common.EXIT_STATUS_OK:
        ec = _write_db(proj_obj, args_d['o'])
    else:
        brcdapi_log.log(args_d['o'] + ' project not written due to previous errors.', echo=True)

    return logout_ec if ec == brcddb_common.EXIT_STATUS_OK else ec


def _get_input():
    """Parses the module load command line

    :return: Exit code. See exit codes in brcddb.brcddb_common
    :rtype: int
    """
    global __version__, _input_d, _MIN_POLL, _MAX_POLL, _MIN_SAMPLES

    ec, switch_l = brcddb_common.EXIT_STATUS_OK, None

    # Get command line input
    buf = 'Collect port statistics at a specified poll interval. Use Control-C to stop data collection and write report'
    try:
        args_d = gen_util.get_input(buf, _input_d)
    except TypeError:
        return brcddb_common.EXIT_STATUS_INPUT_ERROR  # gen_util.get_input() already posted the error message.

    # Set up logging
    brcdapi_rest.verbose_debug(args_d['d'])
    brcdapi_log.open_log(
        folder=args_d['log'],
        suppress=args_d['sup'],
        no_log=args_d['nl'],
        version_d=brcdapi_util.get_import_modules()
    )

    # Is the poll interval valid?
    args_p_help = ''
    if args_d['p'] < _MIN_POLL or args_d['p'] > _MAX_POLL:
        args_p_help = ' **ERROR**: Must be between ' + str(_MIN_POLL) + ' and ' + str(_MAX_POLL) + ' seconds'
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Are the number of samples valid?
    args_m_help = ''
    if args_d['m'] < _MIN_SAMPLES:
        args_m_help = ' **ERROR**: Must be >= ' + str(_MIN_SAMPLES)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Read the login credentials file
    args_i_help = ''
    input_file = brcdapi_file.full_file_name(args_d['i'], '.xlsx')
    try:
        switch_l = excel_util.parse_parameters(sheet_name='parameters', hdr_row=0, wb_name=input_file)['content']
    except FileNotFoundError:
        args_i_help = ' **ERROR**: Not found.'
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    except FileExistsError:
        args_i_help = ' **ERROR**: File path does not exist.'
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Command line feedback
    ml = [
        os.path.basename(__file__) + ', ' + __version__,
        'Credentials file, -i: ' + args_d['i'] + args_i_help,
        'Output File, -o:      ' + args_d['o'],
        'Samples, -m:          ' + str(args_d['m']) + args_m_help,
        'Poll Interval, -p:    ' + str(args_d['p']) + args_p_help,
        'Log, -log:            ' + str(args_d['log']),
        'No log, -nl:          ' + str(args_d['nl']),
        'Debug, -d:            ' + str(args_d['d']),
        'Suppress, -sup:       ' + str(args_d['sup']),
        '',
    ]
    brcdapi_log.log(ml, echo=True)
    args_d['o'] = brcdapi_file.full_file_name(args_d['o'], '.json')
    args_d['i'] = input_file

    return ec if ec != brcddb_common.EXIT_STATUS_OK else pseudo_main(switch_l, args_d)


##################################################################
#
#                    Main Entry Point
#
###################################################################
if _DOC_STRING:
    print('_DOC_STRING is True. No processing')
    exit(brcddb_common.EXIT_STATUS_OK)

if _STAND_ALONE:
    _ec = _get_input()
    brcdapi_log.close_log(['', 'Processing Complete. Exit code: ' + str(_ec)], echo=True)
    exit(_ec)
