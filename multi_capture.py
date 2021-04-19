#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019, 2020, 2021 Jack Consoli.  All rights reserved.
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
:mod:`multi_capture` - Captures all switch data from a list and generates a report.

This is effectively an intelligent batch file that does the following:

    * Create a folder for the collected data.
    * Start capture.py for each chassis specified in a passed chassis list
    * Start combine.py once the data capture completes
    * Start report.py once the combine completes

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 3.0.0     | 19 Jul 2020   | Initial Launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.4     | 17 Apr 2021   | Miscellaneous bug fixes.                                                          |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2019, 2020, 2021 Jack Consoli'
__date__ = '17 Apr 2021'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '3.0.4'

import argparse
import datetime
import os
import subprocess

import brcdapi.log as brcdapi_log
import brcdapi.brcdapi_rest as brcdapi_rest
import brcddb.util.file as brcddb_file
import brcddb.brcddb_common as brcddb_common

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = False   # When True, use _DEBUG_xxx below instead of parameters passed from the command line.
_DEBUG_I = 'mtest.txt'
_DEBUG_F = None
_DEBUG_SFP = 'sfp_rules_r7.xlsx'
_DEBUG_IOCP = 'test_iocp'
_DEBUG_r = True
_DEBUG_c = None
_DEBUG_SUP = False  # If true, all logging to STD_OUT is suppressed
_DEBUG_VERBOSE = False
_DEBUG_LOG = '_logs'
_DEBUG_NL = False


def parse_args():
    """Parses the module load command line when launching from stand-alone desk top application

    :return f: Name of output file, if specified, for JSON dump
    :rtype f: str, None
    :return i: Name of input CSV file
    :rtype i: str
    :return r: Name of report, if specified.
    :rtype r: str, None
    """
    global _DEBUG_I, _DEBUG_F, _DEBUG_SFP, _DEBUG_IOCP, _DEBUG_r, _DEBUG_c, _DEBUG_SUP, _DEBUG_VERBOSE, _DEBUG_LOG, \
        _DEBUG_NL

    if _DEBUG:
        return _DEBUG_I, _DEBUG_F, _DEBUG_SFP, _DEBUG_IOCP, _DEBUG_r, _DEBUG_c, _DEBUG_SUP, _DEBUG_VERBOSE, _DEBUG_LOG,\
               _DEBUG_NL
    buf = 'Capture all report data from multiple chassis and optionally generate a report.'
    parser = argparse.ArgumentParser(description=buf)
    buf = 'Required. Input CSV file of switch login credentials. The file must be a CSV plain text file in the format: '
    buf += 'User ID,Password,Address,Security. Security is either CA or self for HTTPS access and none for HTTP. If'
    buf += ' Security is omitted, none (HTTP) is assumed'
    parser.add_argument('-i', help=buf, required=True)
    buf = 'Optional. Folder name where captured data is to be placed. If not specified, a folder with the default name'\
          ' _capture_yyyy_mmm_dd is created. The individual switch data is put in this folder with the switch name. '\
          'Also created in this folder is a file named combined.json which is output of combine.py and report.xlsx.'
    parser.add_argument('-f', help=buf, required=False)
    buf = 'Optional. Name of the Excel Workbook with SFP thresholds. This is the same file used as input to '\
          'applications.maps_config. This is useful for checking SFPs against the new recommended MAPS rules before '\
          'implementing them or filling in missing rules. Only used if -r is specified.'
    parser.add_argument('-sfp', help=buf, required=False)
    buf = 'Optional. Name of folder with IOCP files. All files in this folder must be IOCP files (build I/O '\
          'configuration statements from HCD) and must begin with the CEC serial number followed by \'_\'. Leading 0s '\
          'are not required. Example, for a CEC with serial number 12345: 12345_M90_iocp.txt'
    parser.add_argument('-iocp', help=buf, required=False)
    parser.add_argument('-r', help='Optional. Generates a report.', action='store_true', required=False)
    buf = '(Optional) Name of file with list of KPIs to capture. Use * to capture all data the chassis supports. The ' \
          'default is to capture all KPIs required for the report.'
    parser.add_argument('-c', help=buf, required=False,)
    buf = 'Suppress all library generated output to STD_IO except the exit message. Useful with batch processing'
    parser.add_argument('-sup', help=buf, action='store_true', required=False)
    parser.add_argument('-d', help='Enable debug logging', action='store_true', required=False)
    buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The log '\
          'file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
    parser.add_argument('-log', help=buf, required=False,)
    buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
    parser.add_argument('-nl', help=buf, action='store_true', required=False)
    args = parser.parse_args()
    return args.i, args.f, args.sfp, args.iocp, args.r, args.c, args.sup, args.d, args.log, args.nl


def psuedo_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    global _DEBUG

    addl_parms_all = list()
    addl_parms_capture = list()
    addl_parms_report = list()

    # Get and parse the input data
    ml = ['WARNING!!! Debug is enabled'] if _DEBUG else list()
    ml.append(os.path.basename(__file__) + ' version: ' + __version__)
    in_file, folder, sfp, iocp, report_flag, kpi_file, s_flag, vd, log, nl = parse_args()
    if kpi_file is not None:
        addl_parms_capture.extend(['-c', kpi_file])
    if vd:
        brcdapi_rest.verbose_debug = True
        addl_parms_capture.append('-d')
        addl_parms_report.append('-d')
    if s_flag:
        brcdapi_log.set_suppress_all()
        addl_parms_all.append('-sup')
    if nl:
        addl_parms_all.append('-nl')
    else:
        brcdapi_log.open_log(log)
        if log is not None:
            addl_parms_all.extend(['-log', log])
    if iocp is not None:
        addl_parms_report.extend(['-iocp', iocp])
    ml.append('Input file:    ' + in_file)
    if folder is None:
        folder = '_capture_' + datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        ml.append('Output Folder: (Automatic) ' + folder)
    else:
        ml.append('Output Folder: ' + folder)
    ml.append('SFP:           ' + str(sfp))
    ml.append('IOCP:          ' + str(iocp))
    ml.append('Report:        ' + str(report_flag))
    ml.append('KPI File:      ' + str(kpi_file))
    ml.append('Suppress:      ' + str(s_flag))
    ml.append('Verbose Debug: ' + str(vd))
    brcdapi_log.log(ml, True)

    # Read the file with login credentials and perform some basic validation
    switch_list = list()
    file_content = brcddb_file.read_file(in_file)
    i = 0
    for mod_line in file_content:
        params = mod_line.replace(' ', '').split(',')
        if len(params) == 3:
            params.append('none')
        if len(params) >= 4:
            l = params[2].split('.')
            params.append('capture_' + str(l[len(l) - 1]) + '_' + str(i))
            switch_list.append(params)
            i += 1
        else:
            i += 1
            brcdapi_log.log('Missing parameters in input file:\nLine ' + str(i) + ': ' + mod_line, True)

    # Create the folder
    os.mkdir(folder)

    # Kick off all the data captures
    pid_l = list()
    for l in switch_list:
        brcdapi_log.log('Starting: ' + l[4])
        params = ['python.exe', 'capture.py', '-f', folder + '/' + l[4] + '.txt']
        i = 0
        for buf in ('-id', '-pw', '-ip', '-s'):
            params.append(buf)
            params.append(l[i])
            i += 1
        params.extend(addl_parms_capture)
        params.extend(addl_parms_all)
        if _DEBUG:
            brcdapi_log.log(' '.join(params), True)
        pid_l.append(subprocess.Popen(params))

    # Below waits for all processes to complete before generating the report.
    pid_done = [p.wait() for p in pid_l]
    for i in range(0, len(pid_done)):
        brcdapi_log.log('Completed: ' + switch_list[i][4] + '. Ending status: ' + str(pid_done[i]), True)

    # Combine the captured data
    brcdapi_log.log('Combining captured data. This may take several seconds', True)
    param = ['python.exe', 'combine.py', '-i', folder, '-o', 'combined.json']
    params.extend(addl_parms_all)
    if _DEBUG:
        brcdapi_log.log(' '.join(params), True)
    ec = subprocess.Popen(param).wait()
    brcdapi_log.log('Combine completed with status: ' + str(ec), True)

    # Generate the report
    if report_flag and ec == brcddb_common.EXIT_STATUS_OK:
        brcdapi_log.log('Data collection complete. Generating report.', True)
        param = ['python.exe', 'report.py', '-i', folder + '/combined.json', '-o', folder + '/report.xlsx']
        param.extend(addl_parms_report)
        params.extend(addl_parms_all)
        if _DEBUG:
            brcdapi_log.log(' '.join(params), True)
        ec = subprocess.Popen(param).wait()

    return ec

###################################################################
#
#                    Main Entry Point
#
###################################################################


_ec = brcddb_common.EXIT_STATUS_OK
if _DOC_STRING:
    print('_DOC_STRING is True. No processing')
else:
    _ec = psuedo_main()
    brcdapi_log.close_log(str(_ec), True)
exit(_ec)
