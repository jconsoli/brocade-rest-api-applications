#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019, 2020, 2021, 2022, 2023 Jack Consoli.  All rights reserved.
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
    | 3.0.5     | 14 May 2021   | Permitted input from Excel Workbook instead of just a CSV file.                   |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.6     | 14 Nov 2021   | Do not pass -d to report.py. Better help message for -r option.                   |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.7     | 16 Nov 2021   | Automatically append ".json to output file names. Fixed missing SFP rules         |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.8     | 31 Dec 2021   | Use brcddb.util.file.full_file_name()                                             |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.9     | 28 Apr 2022   | Added additional help messages.                                                   |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.1.0     | 22 Jun 2022   | Improved error messaging.                                                         |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.1.1     | 24 Oct 2022   | Improved error messaging and add Control-C to exit                                |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.1.2     | 09 May 2023   | Added -bp parameter for report.                                                   |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2019, 2020, 2021, 2022, 2023 Jack Consoli'
__date__ = '09 May 2023'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '3.1.2'

import signal
import argparse
import datetime
import os
import subprocess
import brcdapi.log as brcdapi_log
import brcdapi.brcdapi_rest as brcdapi_rest
import brcdapi.excel_util as excel_util
import brcdapi.file as brcdapi_file
import brcddb.brcddb_common as brcddb_common

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = False   # When True, use _DEBUG_xxx below instead of parameters passed from the command line.
_DEBUG_i = 'test_copy'
_DEBUG_f = None
_DEBUG_sfp = 'sfp_rules_r10'
_DEBUG_iocp = None  # 'test_iocp'
_DEBUG_r = False
_DEBUG_c = None
_DEBUG_bp = 'bp'
_DEBUG_sup = False  # If true, all logging to STD_OUT is suppressed
_DEBUG_d = None
_DEBUG_log = '_logs'
_DEBUG_nl = False


def parse_args():
    """Parses the module load command line when launching from stand-alone desk top application

    :return i: Name of input file, Excel workbook with login credentials. See multi_capture_example.xlsx
    :rtype i: str
    :return f: Name of log folder. None if not specified.
    :rtype f: str, None
    :return sfp: Name of SFP rules file. None if not specified.
    :rtype sfp: str, None
    :return iocp: Name of folder containing IOCP files. None if not specified.
    :rtype iocp: str, None
    :return r: If True, generate a report.
    :rtype r: bool
    :return c: Custom report parameters passed to _custom_report(). Typically not used.
    :rtype c: str, None
    :return sup: If True, suppress echo of messages to STD_OUT.
    :rtype sup: bool
    :return d: Debug flag. When True, a pprint of all I/O is sent to the log and console
    :rtype d: bool
    :return log: Folder for the log file. None if not specified.
    :rtype log: bool
    :return nl: No log. When True, a log file is not created.
    :rtype nl: bool
    """
    global _DEBUG_i, _DEBUG_f, _DEBUG_sfp, _DEBUG_iocp, _DEBUG_r, _DEBUG_c, _DEBUG_bp, _DEBUG_sup, _DEBUG_d, _DEBUG_log
    global _DEBUG_nl

    if _DEBUG:
        return _DEBUG_i, _DEBUG_f, _DEBUG_sfp, _DEBUG_iocp, _DEBUG_r, _DEBUG_c, _DEBUG_bp, _DEBUG_sup, _DEBUG_d, \
               _DEBUG_log, _DEBUG_nl
    buf = 'Capture all report data from multiple chassis and optionally generate a report.'
    parser = argparse.ArgumentParser(description=buf)
    buf = 'Required. Excel file of switch login credentials. See multi_capture_example.xlsx. ".xlsx" is automatically '\
          'appended if no extension is specified.'
    parser.add_argument('-i', help=buf, required=True)
    buf = 'Optional. Folder name where captured data is to be placed. If not specified, a folder with the default name'\
          ' _capture_yyyy_mmm_dd_hh_mm_ss is created. The individual switch data is put in this folder with the switch'\
          ' name. A file named combined.json, output of combine.py, and report.xlsx, output of report.py, is '\
          'added to this folder.'
    parser.add_argument('-f', help=buf, required=False)
    buf = 'Optional. Name of the Excel Workbook with best practice checks. This parameter is passed to report.py if '\
          '-r is specified. Otherwise it is not used. ".xlsx" is automatically appended.'
    parser.add_argument('-bp', help=buf, required=False)
    buf = 'Optional. Name of the Excel Workbook with SFP thresholds. This parameter is passed to report.py if -r is ' \
          'specified. Otherwise it is not used. ".xlsx" is automatically appended.'
    parser.add_argument('-sfp', help=buf, required=False)
    buf = 'Optional. Name of folder with IOCP files. All files in this folder must be IOCP files (build I/O '\
          'configuration statements from HCD) and must begin with the CEC serial number followed by \'_\'. Leading 0s '\
          'are not required. Example, for a CPC with serial number 12345: 12345_M90_iocp.txt'
    parser.add_argument('-iocp', help=buf, required=False)
    buf = '(Optional). No parameters. When specified, generates a report. See -f option for location. The name of the '\
          'report is "report_yyyy_mm_dd_hh_mm_ss.xlsx"'
    parser.add_argument('-r', help=buf, action='store_true', required=False)
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
    return args.i, args.f, args.sfp, args.iocp, args.r, args.c, args.bp, args.sup, args.d, args.log, args.nl


def psuedo_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    global _DEBUG

    signal.signal(signal.SIGINT, brcdapi_rest.control_c)

    addl_parms_all, addl_parms_capture, addl_parms_report = list(), list(), list()

    # Get and parse the input data
    ml = ['WARNING!!! Debug is enabled'] if _DEBUG else list()
    ml.append(os.path.basename(__file__) + ' version: ' + __version__)
    in_file, folder, sfp, iocp, report_flag, kpi_file, bp_file, s_flag, vd, log, nl = parse_args()
    if kpi_file is not None:
        addl_parms_capture.extend(['-c', kpi_file])
    if vd:
        brcdapi_rest.verbose_debug = True
        addl_parms_capture.append('-d')
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
    date_str = '_' + datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    if folder is None:
        folder = '_capture' + date_str
        ml.append('Output Folder: (Automatic) ' + folder)
    else:
        ml.append('Output Folder: ' + folder)
    ml.append('SFP, -sfp:           ' + str(sfp))
    ml.append('Best Practices, -bp: ' + str(bp_file))
    ml.append('IOCP, -iocp:         ' + str(iocp))
    ml.append('Report, -r:          ' + str(report_flag))
    ml.append('KPI File, -c:        ' + str(kpi_file))
    ml.append('Suppress, -sup:      ' + str(s_flag))
    ml.append('Verbose Debug, -d:   ' + str(vd))
    brcdapi_log.log(ml, echo=True)

    # Read the file with login credentials and perform some basic validation
    ml, switch_parms = list(), list()
    if sfp is not None:
        addl_parms_report.extend(['-sfp', sfp])
    if bp_file is not None:
        addl_parms_report.extend(['-bp', bp_file])
    file = brcdapi_file.full_file_name(in_file, '.xlsx')
    row = 1
    try:
        for d in excel_util.parse_parameters(sheet_name='parameters', hdr_row=0, wb_name=file)['content']:
            row += 1
            buf = brcdapi_file.full_file_name(d['name'].split('/').pop().split('\\').pop(), '.json')  # Just file name
            switch_parms.append(['-id', d['user_id'],
                                 '-pw', d['pw'],
                                 '-ip', d['ip_addr'],
                                 '-s', 'none' if d['security'] is None else d['security'],
                                 '-f', folder + '/' + buf])
    except FileNotFoundError:
        ml.extend(['', file + ' not found.'])
    except AttributeError:
        ml.extend(['',
                   'Invalid login credentials in row ' + str(row) + ' in ' + file,
                   'This typically occurs when cells are formatted with no content. Try deleting any unused rows.'])
    except KeyboardInterrupt:
        ml.extend(['', 'Processing terminated with Control-C from keyboard'])

    # Create the folder
    if len(ml) == 0:
        try:
            os.mkdir(folder)
        except FileExistsError:
            ml.extend(['', 'Folder ' + folder + ' already exists.'])
        except FileNotFoundError:
            ml.extend(['', folder + ' contains a path that does not exist.'])
    if len(ml) > 0:
        brcdapi_log.log(ml, echo=True)
        return brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Kick off all the data captures
    try:
        pid_l = list()
        for temp_l in switch_parms:
            params = ['python.exe', 'capture.py'] + temp_l + addl_parms_capture + addl_parms_all
            if _DEBUG:
                brcdapi_log.log(' '.join(params), echo=True)
            pid_l.append(subprocess.Popen(params))

        # Below waits for all processes to complete before generating the report.
        pid_done = [p.wait() for p in pid_l]
        for i in range(0, len(pid_done)):
            brcdapi_log.log('Completed switch capture at index ' + str(i) + '. Ending status: ' + str(pid_done[i]),
                            echo=True)
    except KeyboardInterrupt:
        brcdapi_log.log(['Processing terminating with Control-C from keyboard.',
                         'WARNING: This module starts other capture sessions which must be terminated individually'],
                        echo=True)


    # Combine the captured data
    try:
        brcdapi_log.log('Combining captured data. This may take several seconds', echo=True)
        params = ['python.exe', 'combine.py', '-i', folder, '-o', 'combined.json'] + addl_parms_all
        if _DEBUG:
            brcdapi_log.log('DEBUG: ' + ' '.join(params), echo=True)
        ec = subprocess.Popen(params).wait()
        brcdapi_log.log('Combine completed with status: ' + str(ec), echo=True)

        # Generate the report
        if report_flag and ec == brcddb_common.EXIT_STATUS_OK:
            brcdapi_log.log('Data collection complete. Generating report.', echo=True)
            buf = folder + '/report_' + date_str + '.xlsx'
            params = ['python.exe', 'report.py', '-i', folder + '/combined.json', '-o', buf]
            params.extend(addl_parms_report + addl_parms_all)
            if _DEBUG:
                brcdapi_log.log('DEBUG: ' + ' '.join(params), echo=True)
            ec = subprocess.Popen(params).wait()
    except KeyboardInterrupt:
        brcdapi_log.log('Processing terminating with Control-C from keyboard.', echo=True)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    return ec

###################################################################
#
#                    Main Entry Point
#
###################################################################


if _DOC_STRING:
    print('_DOC_STRING is True. No processing')
    exit(brcddb_common.EXIT_STATUS_OK)

_ec = psuedo_main()
brcdapi_log.close_log('Processing complete. Exit code: ' + str(_ec))
exit(_ec)
