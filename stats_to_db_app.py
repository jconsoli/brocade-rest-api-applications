#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2021, 2022 Jack Consoli.  All rights reserved.
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
:mod:`stats_to_db_app` - Example on how to capture port statistics and add them to your own database

**Description**

  Simlimar to api_examples.stats_to_db. The difference is that this module relies on the brcddb methods. Using these
  methods make it easier to capture data for multiple switches and provide port descriptions based on what is logged in
  to the port.

  Comments from api_examples.stats_to_db:

  For any database to work, the keys must be unique. Since multiple switches can have the same port and in environments
  with multiple fabrics, it's possible to have the same fibre channel address. In this example, a unique key is a hash
  of the switch WWN and port number. Note that the switch WWN will always be unique.

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 1.0.0     | 27 Feb 2021   | Initial Launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.1     | 28 Feb 2021   | Build cross-references before generating port descriptions.                       |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.2     | 31 Dec 2021   | Updated comments. No functional changes.                                          |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.3     | 28 Apr 2022   | Adjusted for new URI format.                                                      |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2021, 2022 Jack Consoli'
__date__ = '28 Apr 2022'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '1.0.3'

import datetime
import argparse
import brcddb.brcddb_project as brcddb_project
import brcdapi.brcdapi_rest as brcdapi_rest
import brcdapi.fos_auth as fos_auth
import brcdapi.log as brcdapi_log
import brcdapi.file as brcdapi_file
import brcddb.brcddb_common as brcddb_common
import brcddb.api.interface as api_int
import brcddb.brcddb_port as brcddb_port

_DOC_STRING = False  # Should always be False. Prohibits any actual I/O. Only useful for building documentation
_DEBUG = False   # When True, use _DEBUG_xxx below instead of command line input
_DEBUG_i = 'test_csv.txt'
_DEBUG_fid = None
_DEBUG_d = False  # When True, all content and responses are formatted and printed (pprint).
_DEBUG_log = '_logs'
_DEBUG_nl = False

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


def parse_args():
    """Parses the module load command line

    :return: ip, id, pw, file
    :rtype: (str, str, str, str
    """
    global _DEBUG_i, _DEBUG_fid, _DEBUG_d, _DEBUG_log, _DEBUG_nl

    if _DEBUG:
        return _DEBUG_i, _DEBUG_fid, _DEBUG_d, _DEBUG_log, _DEBUG_nl

    buf = 'This is intended as a programming example only but the method _db_add() could be easily modified to ' \
          'use as a stand-alone module to launch periodically to capture statistics and add them to a custom ' \
          'database. It illustrates how to capture port statistics and additional information that is typical of ' \
          'a custom script to capture statistics and add them to a database.'
    parser = argparse.ArgumentParser(description=buf)
    buf = 'Required. Input CSV file of switch login credentials. The file must be a CSV plain text file in the '\
          'format: User ID,Password,Address,Security. Security is either CA or self for HTTPS access and none for '\
          'HTTP. If Security is omitted, none (HTTP) is assumed. Don\'t forget to include the file extension. The '\
          'file extension is not assumed.'
    parser.add_argument('-i', help=buf, required=True)
    buf = '(Optional) CSV list of FIDs to capture logical switch specific data. The default is to automatically ' \
          'determine all logical switch FIDs defined in the chassis.'
    parser.add_argument('-fid', help=buf, required=False)
    buf = '(Optional) Enable debug logging. Prints the formatted data structures (pprint) to the log and console.'
    parser.add_argument('-d', help=buf, action='store_true', required=False)
    buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The ' \
          'log file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
    parser.add_argument('-log', help=buf, required=False, )
    buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
    parser.add_argument('-nl', help=buf, action='store_true', required=False)
    args = parser.parse_args()
    return args.i, args.fid, args.d, args.log, args.nl


def pseudo_main():
    """Basically the main(). Did it this way to use with IDE
    :return: Exit code
    :rtype: int
    """
    global _kpi_l
    
    # Get the command line input
    ml = ['WARNING!!! Debug is enabled'] if _DEBUG else list()
    in_file, fid_str, vd, log, nl = parse_args()
    if vd:
        brcdapi_rest.verbose_debug = True
    if not nl:
        brcdapi_log.open_log(log)
    ml.append('FID: ' + str(fid_str))
    fid_l = None if fid_str is None else fid_str.split(',')
    brcdapi_log.log(ml, True)

    # Read the file with the login credentials
    switch_list = _parse_login_credentials(in_file)

    # Create a project object
    proj_obj = brcddb_project.new("Captured_data", datetime.datetime.now().strftime('%d %b %Y %H:%M:%S'))

    # Poll all the switches
    ec_l = list()
    for switch in switch_list:  # Collect the data for each switch
        ec_l.append(_capture_data(proj_obj, _kpi_l, fid_l, switch['id'], switch['pw'], switch['ip'], switch['sec']))

    # Build cross references. This associates name server logins with a physical port. It is necessary in this example
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
    return ec  # If we get this far, everything was good


###################################################################
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
