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

Example on how to capture port statistics and add them to your own database

Similar to api_examples.stats_to_db. The difference is that this module relies on the brcddb methods. Using these
methods make it easier to capture data for multiple switches and provide port descriptions based on what is logged in to
the port.

Comments from api_examples.stats_to_db:

For any database to work, the keys must be unique. Since multiple switches can have the same port and in environments
with multiple fabrics, it's possible to have the same fibre channel address. In this example, a unique key is a hash
of the switch WWN and port number. Note that the switch WWN will always be unique.

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
| 4.0.3     | 16 Jun 2024   | Removed unused debug variables.                                                       |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.4     | 06 Dec 2024   | Updated comments only.                                                                |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.5     | xx xxx 2026   | Use brcddb.util.util.get_import_modules to dynamically determined imported libraries. |
+-----------+---------------+---------------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2023, 2024, 2025, 2026 Jack Consoli'
__date__ = 'xx xxx 2025'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack_consoli@yahoo.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Development'
__version__ = '4.0.5'

import os
import datetime
import brcdapi.gen_util as gen_util
import brcdapi.util as brcdapi_util
import brcdapi.brcdapi_rest as brcdapi_rest
import brcdapi.fos_auth as fos_auth
import brcdapi.log as brcdapi_log
import brcdapi.file as brcdapi_file
import brcddb.brcddb_project as brcddb_project
import brcddb.brcddb_common as brcddb_common
import brcddb.api.interface as api_int
import brcddb.brcddb_port as brcddb_port

_DOC_STRING = False  # Should always be False. Prohibits any actual I/O. Only useful for building documentation
# _STAND_ALONE: True: Executes as a standalone module taking input from the command line. False: Does not automatically
# execute. This is useful when importing this module into another module that calls psuedo_main().
_STAND_ALONE = True  # See note above

_input_d = dict(
    i=dict(h='Required. Input CSV file of switch login credentials. The file must be a CSV plain text file in the '
             'format: User ID,Password,Address,Security. Security is either CA or self for HTTPS access and none for '
             'HTTP. If Security is omitted, none (HTTP) is assumed. Don\'t forget to include the file extension. The '
             'file extension is not assumed.'),
    fid=dict(r=False,
             h='(Optional) CSV list of FIDs to capture logical switch specific data. The default is to automatically '
               'determine all logical switch FIDs defined in the chassis.')
)
_input_d.update(gen_util.parseargs_log_d.copy())

_kpi_l = (
    # 'running/brocade-fabric/fabric-switch',  Done automatically in brcddb.api.interface._get_chassis()
    'running/brocade-fibrechannel-switch/fibrechannel-switch',
    'running/brocade-interface/fibrechannel',  # Basic port information
    'running/brocade-interface/fibrechannel-statistics',  # Statistics
    'running/brocade-media/media-rdp',  # SFP data
    'running/brocade-fdmi/hba',  # Node data for what's attached. Used for port description
    'running/brocade-name-server/fibrechannel-name-server',  # Login data. Used for port description
    # 'running/brocade-ficon/rnid',  # To capture RNID data for FICON (mainframe) environments
)


def _db_add(key_0, key_1, key_2, val):
    """Stubbed out method to add key value pairs to your database

    :param key_0: First key
    :type key_0: str
    :param key_1: Second key
    :type key_1: str
    :param key_2: Third key
    :type key_2: str
    :param val: Value associated with the keys
    :type val: str, int, float
    """
    key_list = [key.replace(':', '_').replace('/', '_') for key in (key_0, key_1, key_2)]
    # If you are new to Python, above is equivalent to:
    # key_list = list()
    # for key in (key_0, key_1, key_2):
    #     key_list.append(key.replace(':', '_').replace('/', '_'))
    # It's probably better to do the equivalent of the key.replace above with a compiled regex but for the few usec it
    # may save, this is good enough for a simple example.

    # You might want to make sure you are adding a valid value to your database.
    if not isinstance(val, (str, int, float)):
        brcdapi_log.log('Invalid value type, ' + str(type(val)) + ', for key: ' + '/'.join(key_list), True)
        return
    # It's probably a good idea to make sure the keys are valid as well. In this example, we're only going to convert
    # ':' (used in the switch WWN) and '/' (used in the port number) to an underscore, '_'. There may be other
    # characters, such as '-', that are not valid database keys that you will need to modify.

    brcdapi_log.log('Adding key: ' + '/'.join(key_list) + ', Value: ' + str(val), True)


def _add_data_to_db(proj_obj):
    """Captures data from switch and adds it to the project object

    :param proj_obj: The project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    """
    for switch_obj in proj_obj.r_switch_objects():
        switch_wwn = switch_obj.r_obj_key()
        for port_obj in switch_obj.r_port_objects():
            port_num = port_obj.r_obj_key()
            # brcddb_port.port_best_desc(port_obj) returns a description of what's attached to the port
            port_desc = brcddb_port.port_best_desc(port_obj)
            port_desc = '(nothing attached)' if port_desc == '' else '(' + port_desc + ')'
            port_desc = port_obj.r_obj_key() + ' ' + port_desc
            _db_add(switch_wwn, port_num, '_description', port_desc)
            # Now add all the individual port configuration parameters, statistics, and SFP info.
            for kpi in ('fibrechannel', 'fibrechannel-statistics', 'media-rdp'):
                d = port_obj.r_get(kpi)
                if isinstance(d, dict):  # It could be None if no ports or no SFPs in the logical switch
                    for k, v in d.items():
                        #  I think 'neighbor' is the only type that fails the test below.
                        if isinstance(v, (str, int, float)):  # Note that bool is a subtype of int.
                            _db_add(switch_wwn, port_num, k, v)


def _capture_data(proj_obj, kpi_l, fid_l, user_id, pw, ip_addr, sec):
    """Captures data from switch and adds it to the project object

    :param proj_obj: The project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :param kpi_l: List of KPIs to GET
    :type kpi_l: list, tuple
    :param fid_l: FID, or list of FIDs for logical switch level requests. If None, execute requests for all FIDs.
    :type fid_l: int, list, tuple, None
    :param user_id: User ID
    :type user_id: str
    :param pw: Password
    :type pw: str
    :param ip_addr: IP address
    :type ip_addr: str
    :param sec: If 'CA' or 'self', uses https to login. Otherwise, http.
    :type sec: None, str
    :return: Status code
    :type: int
    """
    # Login
    session = api_int.login(user_id, pw, ip_addr, sec, proj_obj)
    if fos_auth.is_error(session):
        return brcddb_common.EXIT_STATUS_API_ERROR  # api_int.login() prints the error message detail.

    ec = brcddb_common.EXIT_STATUS_OK

    # Capture the data
    api_int.get_batch(session, proj_obj, kpi_l, fid_l)
    if proj_obj.r_is_any_error():
        brcdapi_log.log('Errors encountered. Search the log for "ERROR:".', True)

    # Logout
    obj = brcdapi_rest.logout(session)
    if fos_auth.is_error(obj):
        brcdapi_log.log(fos_auth.formatted_error_msg(obj), True)
        ec = brcddb_common.EXIT_STATUS_API_ERROR

    return ec


def _parse_login_credentials(in_file):
    """Reads a CSV list of switch login credentials from a file and parses into a Python dict

    :param in_file: Input file with CSV list of login credentials
    :type in_file: str
    :return: List of dictionaries with the following keys: ip, id, pw, sec
    :rtype: list
    """
    # Read the file with login credentials and format into a list of dictionaries
    rl = list()
    file_content = brcdapi_file.read_file(in_file, remove_blank=True, rc=True)
    for mod_line in file_content:
        params = mod_line.replace(' ', '').split(',')
        if len(params) == 3:
            params.append('none')
        if len(params) == 4:
            rl.append(dict(id=params[0], pw=params[1], ip=params[2], sec=params[3]))
        else:
            brcdapi_log.log('Missing parameters in input file. Line:\n' + mod_line, True)

    return rl


def pseudo_main(in_file, fid_l):
    """Basically the main(). Did it this way so that it can easily be used as a standalone module or called externally.

    :param in_file: Name of login credentials file
    :type in_file: str
    :param fid_l: FIDs to collect statistics from
    :type fid_l: list, None
    :return: Exit code
    :rtype: int
    """
    global _kpi_l
    
    # Read the file with the login credentials
    switch_list = _parse_login_credentials(in_file)

    # Create a project object
    proj_obj = brcddb_project.new("Captured_data", datetime.datetime.now().strftime('%d %b %Y %H:%M:%S'))

    # Poll all the switches
    ec_l = list()
    for switch in switch_list:  # Collect the data for each switch
        ec_l.append(_capture_data(proj_obj, _kpi_l, fid_l, switch['id'], switch['pw'], switch['ip'], switch['sec']))

    # Build cross-references. This associates name server logins with a physical port. It is necessary in this example
    # because what is attached to the port is used as the port description added to the database.
    brcdapi_log.log('Building cross references', True)
    brcddb_project.build_xref(proj_obj)

    # Add the data to your database
    brcdapi_log.log('Adding data to database', True)
    _add_data_to_db(proj_obj)

    # Return the first error status encountered
    for ec in ec_l:
        if ec != brcddb_common.EXIT_STATUS_OK:
            return ec
    return brcddb_common.EXIT_STATUS_OK  # If we get this far, everything was good


def _get_input():
    """Parses the module load command line

    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    global __version__, _input_d

    ec = brcddb_common.EXIT_STATUS_OK

    # Get command line input
    buf = 'This is intended as a programming example only but the method _db_add() could be easily modified to ' \
          'use as a stand-alone module to launch periodically to capture statistics and add them to a custom ' \
          'database. It illustrates how to capture port statistics and additional information that is typical of ' \
          'a custom script to capture statistics and add them to a database.'
    args_d = gen_util.get_input(buf, _input_d)

    # Set up logging
    brcdapi_log.open_log(
        folder=args_d['log'],
        suppress=args_d['sup'],
        no_log=args_d['nl'],
        version_d=brcdapi_util.get_import_modules()
    )

    # Is the FID or FID range valid?
    args_fid_l = gen_util.range_to_list(args_d['fid']) if isinstance(args_d['fid'], str) else None
    args_fid_help = brcdapi_util.validate_fid(args_fid_l)
    if len(args_fid_help) > 0:
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Command line feedback
    ml = [
        os.path.basename(__file__) + ', ' + __version__,
        'Login credentials file, -i: ' + args_d['i'],
        'Fabric ID, -fid:            ' + args_d['fid'],
        'Log, -log:                  ' + str(args_d['log']),
        'No log, -nl:                ' + str(args_d['nl']),
        'Debug, -d:                  ' + str(args_d['d']),
        'Suppress, -sup:             ' + str(args_d['sup']),
        '',
    ]
    brcdapi_log.log(ml, echo=True)

    return ec if ec != brcddb_common.EXIT_STATUS_OK else \
        pseudo_main(brcdapi_file.full_file_name(args_d['i'], '.json'), args_fid_l)


###################################################################
#
#                    Main Entry Point
#
###################################################################
if _DOC_STRING:
    print('_DOC_STRING is True. No processing')
    exit(0)

if _STAND_ALONE:
    _ec = _get_input()
    brcdapi_log.close_log(['', 'Processing Complete. Exit code: ' + str(_ec)], echo=True)
    exit(_ec)
