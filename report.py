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

Creates a report in Excel Workbook format from a brcddb project

**Version Control**

+-----------+---------------+---------------------------------------------------------------------------------------+
| Version   | Last Edit     | Description                                                                           |
+===========+===============+=======================================================================================+
| 4.0.0     | 04 Aug 2023   | Re-Launch                                                                             |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.1     | 06 Mar 2024   | Improved error messaging.                                                             |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.2     | 09 Mar 2024   | Addd input parameters to the project object                                           |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.3     | 03 Apr 2024   | Added version numbers of imported libraries.                                          |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.4     | 16 Jun 2024   | Improved help messages. Added -sheet input parameter.                                 |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.5     | 06 Dec 2024   | Remove extraneous white space from user input in Workbook                             |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.6     | 26 Dec 2024   | Updated comments only.                                                                |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.7     | 25 Aug 2025   | Use brcddb.util.util.get_import_modules to dynamically determined imported libraries. |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.8     | 19 Oct 2025   | Updated comments only.                                                                |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.9     | 04 Dec 2025   | Fix bug when no CPUs are logged in to a FICON logical switch.                         |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.1.0     | 20 Feb 2026   | Moved reading and parsing of the groups file to brcddb.report.utils.groups()          |
+-----------+---------------+---------------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2024, 2025, 2026 Jack Consoli'
__date__ = '20 Feb 2026'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack_consoli@yahoo.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '4.1.0'

import os
import brcdapi.log as brcdapi_log
import brcdapi.file as brcdapi_file
import brcdapi.excel_util as excel_util
import brcdapi.gen_util as gen_util
import brcdapi.util as brcdapi_util
import brcddb.util.util as brcddb_util
import brcddb.brcddb_project as brcddb_project
import brcddb.apps.report as brcddb_report
import brcddb.report.utils as report_utils
import brcddb.brcddb_common as brcddb_common
import brcddb.brcddb_bp as brcddb_bp
import brcddb.app_data.alert_tables as al
import brcddb.util.iocp as brcddb_iocp

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
# _STAND_ALONE: True: Executes as a standalone module taking input from the command line. False: Does not automatically
# execute. This is useful when importing this module into another module that calls psuedo_main().
_STAND_ALONE = True  # See note above

# Input parameter definitions
_input_d = dict(
    i=dict(h='Required. Name of input file generated by capture.py, combine.py, or multi_capture.py. Extension '
             '".json" is automatically added if no extension present.'),
    o=dict(h='Required. Name of report file. ".xlsx" is automatically appended.'),
    bp=dict(r=False,
            h='Optional. Name of the Excel Workbook with best practice checks. This parameter is passed to report.py '
              'if -r is specified. Otherwise, it is not used. ".xlsx" is automatically appended.'),
    sheet=dict(r=False, d='active', h='Optional. Specifies the sheet name in -bp to read. The default is "active".'),
    sfp=dict(r=False,
             h='Optional. Name of the Excel Workbook with SFP thresholds. This parameter is passed to report.py if -r '
               'is specified. Otherwise, it is not used. ".xlsx" is automatically appended.'),
    group=dict(r=False, h='Optional. Name of Excel file containing group definitions. See group.xlsx for an example.'),
    iocp=dict(r=False,
              h='Optional. Name of folder with IOCP files. All files in this folder must be IOCP files (build I/O '
                'configuration statements from HCD) and must begin with the CEC serial number followed by \'_\'. '
                'Leading 0s are not required. Example, for a CPC with serial number 12345: 12345_M90_iocp.txt'),
    c=dict(r=False,
           h='"options" parameter passed to _custom_report(). This is only useful for developers who have modified '
             '_custom_report().'),
)
_input_d.update(gen_util.parseargs_log_d.copy())


def _custom_report(proj_obj, options):
    """Modified as needed for custom reports. Intended for programmers customizing this script

    :param proj_obj: Project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :param options: As passed in via the shell
    :type options: str, None
    """
    return


def _rnid_summary(proj_obj):
    """Modified as needed for custom reports. Intended for programmers customizing this script

    :param proj_obj: Project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    """

    # Categorize the RNID data by type, then serial number
    rnid_sum_d = dict()  # Key is the generic device type. Value is a dict: keys are sn. The value a count of logins
    for port_obj in proj_obj.r_port_objects():
        rnid_d = port_obj.r_get('rnid')
        if isinstance(rnid_d, dict):
            try:
                key = brcddb_iocp.dev_type_desc(rnid_d['type-number'])
                rnid_seq_d = rnid_sum_d.get(key)
                if not isinstance(rnid_seq_d, dict):
                    rnid_seq_d = dict()
                    rnid_sum_d[key] = rnid_seq_d
                sn = rnid_d['sequence-number']
                if sn in rnid_seq_d:
                    rnid_seq_d[sn] += 1
                else:
                    rnid_seq_d[sn] = 1
            except KeyError:
                pass  # Just in case the RNID data is incomplete

    # Format the output text
    rnid_l = list()  # Formatted text for report output
    for k, d in rnid_sum_d.items():
        rnid_l.extend(['', '**' + k + '**'])
        for seq, val in d.items():
            rnid_l.append(str(seq) + ': ' + str(val))

    # Print the RNID report
    if len(rnid_l) > 0:
        rnid_l.insert(0, '')
        rnid_l.insert(0, 'RNID SUMMARY')
        rnid_l.append('')
        brcdapi_log.log(rnid_l, echo=True)

    return


def pseudo_main(proj_obj, outf, bp_rules, sfp_rules, group_file, iocp, custom_parms):
    """Basically the main(). Did it this way so that it can easily be used as a standalone module or called externally.

    :param proj_obj: Project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :param outf: Output file name, -o
    :type outf: str
    :param bp_rules: Best practice rules file, -bp
    :type bp_rules: str, None
    :param sfp_rules: Name of SFP rules file, -sfp
    :type sfp_rules: str, None
    :param group_file: Name of group file
    :type group_file: None, str
    :param iocp: Name of folder containing IOCP files, -iocp
    :type iocp: str, None
    :param custom_parms: Custom report parameters passed to _custom_report(), -c. Typically not used.
    :type custom_parms: str, None
    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    # Perform all pre-processing (parse IOCPs, build references, ...)
    brcdapi_log.log('Building cross-references', echo=True)
    brcddb_project.build_xref(proj_obj)
    brcddb_project.add_custom_search_terms(proj_obj)
    brcdapi_log.log('Performing mainframe checks', echo=True)
    for file in brcdapi_file.read_directory(iocp):
        brcddb_iocp.parse_iocp(proj_obj, iocp + '/' + file)
    brcdapi_log.log('Building mainframe device groups', echo=True)
    brcddb_iocp.build_rnid_table(proj_obj)
    brcdapi_log.log('Analyzing project for best practices', echo=True)

    # Get the groups, -group.
    group_d, el = report_utils.groups(proj_obj, group_file)
    if len(el) > 0:
        brcdapi_log.log(el, echo=True)
        proj_obj.s_user_error_flag()
    brcddb_util.add_to_obj(proj_obj, 'report_app/group_d', group_d)

    # Add best practice alerts to the appropriate objects
    brcddb_bp.best_practice(bp_rules, sfp_rules, al.AlertTable.alertTbl, proj_obj)

    # Generate the report
    brcddb_report.report(proj_obj, outf, group_d)
    _custom_report(proj_obj, custom_parms)

    # Display a summary of RNID data
    _rnid_summary(proj_obj)

    return brcddb_common.EXIT_STATUS_ERROR if proj_obj.r_is_any_error() else brcddb_common.EXIT_STATUS_OK


def _get_input():
    """Parses the module load command line

    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    global __version__, _input_d

    # Get command line input
    args_d = gen_util.get_input('Creates a general report in Excel ', _input_d)

    # Set up logging
    brcdapi_log.open_log(
        folder=args_d['log'],
        suppress=args_d['sup'],
        no_log=args_d['nl'],
        version_d=brcdapi_util.get_import_modules()
    )

    # Command line feedback
    ml = [os.path.basename(__file__) + ', ' + __version__,
          'In file, -i:                 ' + args_d['i'],
          'Out file, -o:                ' + args_d['o'],
          'SFP rules file, -sfp:        ' + str(args_d['sfp']),
          'Best practice, -bp:          ' + str(args_d['bp']),
          'Best practice sheet, -sheet: ' + str(args_d['sheet']),
          'Zone groups, -group:         ' + str(args_d['group']),
          'IOCP, -iocp:                 ' + str(args_d['iocp']),
          'Custom, -c:                  ' + str(args_d['c']),
          'Log, -log:                   ' + str(args_d['log']),
          'No log, -nl:                 ' + str(args_d['nl']),
          'Suppress, -sup:              ' + str(args_d['sup']),
          '',]
    brcdapi_log.log(ml, echo=True)

    # Get full file names
    in_file = brcdapi_file.full_file_name(args_d['i'], '.json')
    out_file = brcdapi_file.full_file_name(args_d['o'], '.xlsx')
    bp_file = brcdapi_file.full_file_name(args_d['bp'], '.xlsx')
    sfp_file = brcdapi_file.full_file_name(args_d['sfp'], '.xlsx')
    group_file = brcdapi_file.full_file_name(args_d['group'], '.xlsx')

    # Read the project file, -i
    try:
        proj_obj = brcddb_project.read_from(in_file)
        if proj_obj is None:  # Error messages are sent to the log in brcddb_project.read_from() if proj_obj is None
            return brcddb_common.EXIT_STATUS_INPUT_ERROR
    except FileNotFoundError:
        brcdapi_log.log('Input file, ' + in_file + ', not found', echo=True)
        return brcddb_common.EXIT_STATUS_INPUT_ERROR
    except FileExistsError:
        brcdapi_log.log('Folder in ' + in_file + ' does not exist', echo=True)
        return brcddb_common.EXIT_STATUS_INPUT_ERROR
    proj_obj.s_description('\n'.join(ml))

    return pseudo_main(proj_obj, out_file, bp_file, sfp_file, group_file, args_d['iocp'], args_d['c'])


##################################################################
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
