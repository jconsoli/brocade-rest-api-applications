#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright 2023, 2024 Consoli Solutions, LLC.  All rights reserved.

**License**

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may also obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.

The license is free for single customer use (internal applications). Use of this module in the production,
redistribution, or service delivery for commerce requires an additional license. Contact jack@consoli-solutions.com for
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
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2023, 2024 Consoli Solutions, LLC'
__date__ = '06 Dec 2024'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack@consoli-solutions.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '4.0.5'

import os
import collections
import brcdapi.log as brcdapi_log
import brcdapi.file as brcdapi_file
import brcdapi.excel_util as excel_util
import brcdapi.gen_util as gen_util
import brcdapi.port as brcdapi_port
import brcddb.brcddb_project as brcddb_project
import brcddb.apps.report as brcddb_report
import brcddb.report.zone as zone_report
import brcddb.brcddb_common as brcddb_common
import brcddb.brcddb_bp as brcddb_bp
import brcddb.app_data.alert_tables as al
import brcddb.util.iocp as brcddb_iocp
import brcddb.util.obj_convert as brcddb_conv
import brcddb.brcddb_port as brcddb_port
import brcddb.util.search as brcddb_search

_version_d = dict(
    brcdapi_log=brcdapi_log.__version__,
    gen_util=gen_util.__version__,
    brcdapi_file=brcdapi_file.__version__,
    brcddb_common=brcddb_common.__version__,
    excel_util=excel_util.__version__,
    brcdapi_port=brcdapi_port.__version__,
    brcddb_project=brcddb_project.__version__,
    brcddb_report=brcddb_report.__version__,
    zone_report=zone_report.__version__,
    brcddb_bp=brcddb_bp.__version__,
    al=al.__version__,
    brcddb_iocp=brcddb_iocp.__version__,
    brcddb_conv=brcddb_conv.__version__,
    brcddb_port=brcddb_port.__version__,
    brcddb_search=brcddb_search.__version__,
)

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
# _STAND_ALONE: True: Executes as a standalone module taking input from the command line. False: Does not automatically
# execute. This is useful when importing this module into another module that calls psuedo_main().
_STAND_ALONE = True  # See note above

# debug input (for copy and paste into Run->Edit Configurations->script parameters):
# -i test/test_output -bp bp -sfp sfp_rules_r12 -r -c * -nm -log _logs

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


def _filter_wwn(obj, filter_val, search):
    """Returns a list of port objects with logins that have WWNs matching the search criteria"""

    return brcddb_conv.obj_extract(
        brcddb_search.match_test(
            brcddb_conv.obj_extract(obj, 'LoginObj'),
            dict(k='_obj_key', t=search, v=filter_val, i=True)),
        'PortObj')


def _filter_alias(obj, filter_val, search):
    """Returns a list of port objects with logins that have aliases matching the search criteria"""
    return brcddb_conv.obj_extract(
        brcddb_search.match_test(brcddb_conv.obj_extract(obj, 'AliasObj'),
                                 dict(k='_obj_key', t=search, v=filter_val, i=True)),
        'PortObj'
    )


def _filter_switch_port(obj, filter_val, search):
    """Returns a list of port objects for the switch(es) and port(s) specified in filter_val"""
    switch_l, rl = list(), list()
    tl = filter_val.split(';') if isinstance(filter_val, str) else list()
    if len(tl) >= 2:
        for switch in tl[0].split(','):
            switch_l.extend([obj.r_switch_obj(switch)] if gen_util.is_wwn(switch)
                            else brcddb_project.switch_obj_for_user_name(obj, switch, match_type=search))
        port_l = brcdapi_port.port_range_to_list(tl[1])
        for switch_obj in switch_l:
            rl.extend([switch_obj.r_port_obj(p) for p in port_l if switch_obj.r_port_obj(p) is not None])
    else:
        brcdapi_log.exception('Invalid filter_val. Type: ' + str(type(filter_val)) + ', Val: ' + str(filter_val),
                              echo=True)

    return rl


def _filter_switch_port_name(obj, filter_val, search):
    """Returns a list of port objects for the switch(es) and port(s) specified in filter_val"""
    switch_l, rl = list(), list()
    tl = filter_val.split(';') if isinstance(filter_val, str) else list()
    if len(tl) >= 2:
        for switch in tl[0].split(','):
            switch_l.extend([obj.r_switch_obj(switch)] if gen_util.is_wwn(switch)
                            else brcddb_project.switch_obj_for_user_name(obj, switch))
        for switch_obj in switch_l:
            for name in tl[1].split(','):
                rl.extend(brcddb_port.port_objects_for_name(switch_obj, name, search=search))
    else:
        brcdapi_log.exception('Invalid filter_val. Type: ' + str(type(filter_val)) + ', Val: ' + str(filter_val),
                              echo=True)

    return rl


def _filter_zone(obj, filter_val, search):
    """Returns a list of alias objects in obj"""
    return brcddb_conv.obj_extract(
        brcddb_search.match_test(
            brcddb_conv.obj_extract(obj, 'ZoneObj'),
            dict(k='_obj_key', t=search, v=filter_val, i=True)),
        'PortObj'
    )


_group_filter_list = {'WWN': _filter_wwn,
                      'Alias': _filter_alias,
                      'switch;port': _filter_switch_port,
                      'switch;port_name': _filter_switch_port_name,
                      'Zone': _filter_zone}


def _groups(proj_obj, group_l, file):
    """Parses the group definition file

    :param proj_obj: Project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :param group_l: List of groups defined in -group workbook
    :type group_l: list
    :param file: File name of group definition file, -group. Only used for error reporting.
    :type file: str
    :return: Dictionary whose key is the group name and the value is a list of login objects
    :rtype: dict
    """
    ml, ungrouped_initiator_l, ungrouped_target_l = list(), list(), list()
    grouped_d, group_d = dict(), collections.OrderedDict()

    if len(group_l) > 0:

        # Find the column headers
        col_d = excel_util.find_headers(group_l[0])
        for key in ('Group', 'Filter', 'Operand', 'Operator'):
            if key not in col_d:
                ml.append(key + ' missing in ' + file)
        if len(ml) > 0:
            brcdapi_log.log(ml, echo=True)
            return group_d

        # Figure out what's in each group
        row = 1
        for row_l in group_l[1:]:
            row += 1
            group = row_l[col_d['Group']]
            if not isinstance(group, str) or len(group) == 0:
                continue
            group = group.strip()  # This is read from a user created Workbook, so remove any accidental white space
            operand = row_l[col_d['Operand']]
            if isinstance(operand, str):
                operand = operand.strip()  # This is read from a user created Workbook, Remove accidental white space
            g_filter = row_l[col_d['Filter']]
            if not isinstance(g_filter, str) or g_filter not in _group_filter_list:
                ml.append('Unknown Filter, ' + str(g_filter) + ', at row ' + str(row))
            sub_group_d = group_d.get(group)
            if sub_group_d is None:
                sub_group_d = dict(group_wwn_d=dict(), port_obj_l=list())
                group_d.update({group: sub_group_d})
            sub_group_d['port_obj_l'].extend(
                _group_filter_list[g_filter](proj_obj, operand, row_l[col_d['Operator']]))

        # Zone groups are typically used for storage enclosures. It's not uncommon to use standard zones with multiple
        # target WWNs in the same zone. Below probably could have been more efficient. I didn't think of this until
        # after the first test, so I just shoe horned it in. It adds a dictionary of WWNs that are part of the group.
        # This dictionary is used in the report zone page to skip logins zoned to this group that are already part of
        # the group.
        for sub_group_d in group_d.values():
            for port_obj in sub_group_d['port_obj_l']:
                for wwn in port_obj.r_login_keys():
                    sub_group_d['group_wwn_d'].update({wwn: True})
                # Keep track of ports already grouped:
                grouped_d.update({port_obj.r_switch_key()+port_obj.r_obj_key(): True})

    # Another after thought: find all the logins that are not grouped and get all groups by RNID Sequence number
    # rnid_d: Key is the generic device type. Value is a dict whose key is the sequence number. Value is list of port
    # objects. Sorting by generic device type was done to display groups in order of the device type.
    rnid_d = dict()  # See comment above
    for port_obj in [obj for obj in proj_obj.r_port_objects() if obj.r_is_online()]:

        # Mainframe Groups
        port_rnid_d = port_obj.r_get('rnid')
        if isinstance(port_rnid_d, dict):
            generic_type = brcddb_iocp.generic_device_type(port_rnid_d.get('type-number'))
            port_rnid_seq = port_rnid_d.get('sequence-number', '000000000000')

            # Get the generic device type dictionary from rnid_d. If it hasn't been added yet, add it.
            generic_type_d = rnid_d.get(generic_type)
            if not isinstance(generic_type_d, dict):
                generic_type_d = dict()
                rnid_d.update({generic_type: generic_type_d})

            # Get the port object list for this sequence number
            port_obj_l = generic_type_d.get(port_rnid_seq)
            if not isinstance(port_obj_l, list):
                port_obj_l = list()
                generic_type_d.update({port_rnid_seq: port_obj_l})

            # Add the port object
            port_obj_l.append(port_obj)

        elif not bool(grouped_d.get(port_obj.r_switch_key()+port_obj.r_obj_key())):
            login_obj_l = port_obj.r_login_objects()
            if len(login_obj_l) > 0:
                fc4_features = login_obj_l[0].r_get('brocade-name-server/fibrechannel-name-server/fc4-features')
                if isinstance(fc4_features, str):
                    if 'initiator' in fc4_features.lower():
                        ungrouped_initiator_l.append(port_obj)
                    else:
                        ungrouped_target_l.append(port_obj)

    # Sort out the mainframe groups in order of storage followed by CHPID
    for key in ('DASD', 'Tape', 'CUP', 'CTC', 'Switch', 'IDG', 'Test', 'UNKN', 'CPU'):
        for sub_key, port_obj_l in rnid_d.get(key, dict()).items():
            if len(port_obj_l) > 0:
                group_d[key + '_' + sub_key] = dict(mf_group=key, port_obj_l=port_obj_l)

    # Are there any missing CPUs?
    missing_cpu_l, missing_cpu_d = list(), dict()
    for port_obj in proj_obj.r_port_objects():
        port_rnid_d = port_obj.r_get('rnid')
        if isinstance(port_rnid_d, dict):
            if brcddb_iocp.generic_device_type(port_rnid_d.get('type-number')) == 'CPU':
                sn = port_rnid_d.get('sequence-number', '').upper()
                if sn not in rnid_d['CPU'] and sn not in missing_cpu_d:
                    missing_cpu_d[sn] = True
                    missing_cpu_l.append(port_obj)

    group_d[zone_report.UNGROUPED_TARGET] = dict(port_obj_l=ungrouped_target_l)
    group_d[zone_report.UNGROUPED_INITIATOR] = dict(port_obj_l=ungrouped_initiator_l)
    group_d[zone_report.MISSING_CPU] = dict(port_obj_l=missing_cpu_l)
    return group_d


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
    brcddb_bp.best_practice(bp_rules, sfp_rules, al.AlertTable.alertTbl, proj_obj)

    # Get the groups, -group.
    brcdapi_log.log('Building groups')
    el, group_l = list(), list()
    if group_file is not None:  # Group file
        el, group_l = excel_util.read_workbook(group_file, dm=3, sheets='parameters')
        if len(el) > 0:
            brcdapi_log.log(el, echo=True)
            return brcddb_common.EXIT_STATUS_INPUT_ERROR
        try:
            group_l = group_l[0]['al']
            if len(group_l) < 2:
                brcdapi_log.log('No Filters defined in ' + group_file, echo=True)
                return brcddb_common.EXIT_STATUS_INPUT_ERROR
        except (IndexError, KeyError):
            brcdapi_log.log('"parameters" sheet not found in ' + group_file, echo=True)
            return brcddb_common.EXIT_STATUS_INPUT_ERROR
    group_d = _groups(proj_obj, group_l, group_file)

    # Generate the report
    brcddb_report.report(proj_obj, outf, group_d)
    _custom_report(proj_obj, custom_parms)

    return brcddb_common.EXIT_STATUS_ERROR if proj_obj.r_is_any_error() else brcddb_common.EXIT_STATUS_OK


def _get_input():
    """Parses the module load command line

    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    global __version__, _input_d, _version_d

    # Get command line input
    args_d = gen_util.get_input('Creates a general report in Excel ', _input_d)

    # Set up logging
    brcdapi_log.open_log(folder=args_d['log'], suppress=args_d['sup'], no_log=args_d['nl'], version_d=_version_d)

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
