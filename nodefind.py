#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright 2024 Consoli Solutions, LLC.  All rights reserved.

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

Performs a node find in a project

**Version Control**

+-----------+---------------+---------------------------------------------------------------------------------------+
| Version   | Last Edit     | Description                                                                           |
+===========+===============+=======================================================================================+
| 1.0.0     | 03 Apr 2024   | Initial launch                                                                        |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 1.0.1     | 15 May 2024   | Added -zone and -zone_f options for searching by zone.                                |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 1.0.2     | 16 Jun 2024   | Improved help messages.                                                               |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 1.0.3     | 20 Oct 2024   | PEP8 cleanup                                                                          |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 1.0.4     | 06 Dec 2024   | Updated comments only.                                                                |
+-----------+---------------+---------------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2024 Consoli Solutions, LLC'
__date__ = '06 Dec 2024'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack@consoli-solutions.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '1.0.4'

import os
import brcdapi.log as brcdapi_log
import brcdapi.gen_util as gen_util
import brcdapi.excel_util as excel_util
import brcdapi.file as brcdapi_file
import brcddb.brcddb_common as brcddb_common
import brcddb.brcddb_project as brcddb_project
import brcddb.brcddb_switch as brcddb_switch
import brcddb.util.search as brcddb_search
import brcddb.report.login as report_login
import brcddb.brcddb_fabric as brcddb_fabric
import brcddb.brcddb_login as brcddb_login
import brcddb.brcddb_port as brcddb_port
_version_d = dict(
    brcdapi_log=brcdapi_log.__version__,
    gen_util=gen_util.__version__,
    excel_util=excel_util.__version__,
    brcdapi_file=brcdapi_file.__version__,
    brcddb_common=brcddb_common.__version__,
    brcddb_project=brcddb_project.__version__,
    brcddb_switch=brcddb_switch.__version__,
    brcddb_search=brcddb_search.__version__,
    report_login=report_login.__version__,
    brcddb_fabric=brcddb_fabric.__version__,
    brcddb_login=brcddb_login.__version__,
    brcddb_port=brcddb_port.__version__,
)

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
# _STAND_ALONE: True: Executes as a standalone module taking input from the command line. False: Does not automatically
# execute. This is useful when importing this module into another module that calls psuedo_main().
_STAND_ALONE = True  # See note above

_search_type_d = dict(wild='wild', regex_m='regex-m', regex_s='regex-s', exact='exact')
_search_type_l = [str(_b) for _b in _search_type_d.keys()]

# Input parameter definitions
_input_d = dict(
    i=dict(h='Required. Name of input file generated by capture.py, combine.py, or multi_capture.py. ".json" is '
             'automatically appended if not present.'),
    alias=dict(r=False, d=None,
               h='Optional. CSV list of nodes by alias to search for. Supports regex and wild card searching. '
                 'WARNING: Most regex searches must be encapsulated in quotes. Otherwise, the command line interpreter '
                 'gets confused and exits with an error message. Often, the error message states that the -i parameter '
                 'is missing even though it was entered on the command line.'),
    alias_f=dict(r=False, d=None,
                 h='Optional. A CSV list of plain text files containing the aliases to search for. The default file '
                   'extension is ".txt". The content is the same as -alias except that each alias should be on a '
                   'separate line and quotations should not be used. Quotes are only to keep the command line '
                   'interpreter from getting confused. Comments and blank lines are ignored. Parameters specified '
                   'with -alias and -alias_f are combined to create a single list of aliases.'),
    wwn=dict(r=False, d=None,
             h='Optional. CSV list of nodes by WWN to search for. Supports regex and wild card searching. If the '
               'regex contains a comma, don\'t forget to encapsulate it with quotes.'),
    wwn_f=dict(r=False, d=None,
               h='Optional. Same as -alias_f except it is applied to WWNs.'),
    zone=dict(r=False, d=None,
              h='Optional. CSV list of nodes contained in a zone to search for. Regex and wild card '
                'searching is performed on the zone name, not the zone members. If the regex contains a comma, don\'t '
                'forget to encapsulate it with quotes. Domain-index (d,i) members, used for FICON, are ignored.'),
    zone_f=dict(r=False, d=None,
                h='Optional. Same as -alias_f except it is applied to zones.'),
    s=dict(r=False, d='exact', v=_search_type_l,
           h='Optional. Search type. Options are: ' + ', '.join(_search_type_l) + ' The default is "exact".'),
    r=dict(r=False, h='Optional. Name of Excel report file. ".xlsx" is automatically appended.'),
)
_input_d.update(gen_util.parseargs_log_d.copy())

_wb = None  # Object for the Excel workbook used for output
_proj_obj = None  # Project object
_report_name = None  # Name of report
_working_obj_l = list()
_report_display = dict()
_sheet_index = 0  # Most examples add a worksheet to the Excel workbook. This indicates where.
_MAX_LINE_LEN = 72  # Used to control how long help messages can be.


def _local_report(search_d):
    """Create a text report for each search term

    :param search_d: Key is the search term and value is the list of login objects associated with that search term
    :type search_d: dict
    :rtype: None
    """
    ml = ['', 'Node Find Results', '_________________']
    for k, login_obj_l in search_d.items():
        ml.extend(['', str(k)])
        if len(login_obj_l) == 0:
            ml.append('  Not found.')
        for login_obj in login_obj_l:
            port_obj = login_obj.r_port_obj()
            if port_obj is None:
                ml.append('  Port not found for ' + login_obj.r_obj_key() +
                          '. This typically occurs when there was an incomplete data capture.')
                continue
            login_name = brcddb_login.best_login_name(login_obj.r_fabric_obj(), login_obj.r_obj_key(), flag=True)
            switch_name = brcddb_switch.best_switch_name(port_obj.r_switch_obj(), wwn=True, fid=True, did=True)
            ml.extend([
                '  Name:        ' + login_name,
                '  Switch:      ' + switch_name,
                '  Port:        ' + brcddb_port.best_port_name(port_obj, port_num=True),
                '  Description: ' + brcddb_port.port_best_desc(port_obj),
                '',
                ])
    brcdapi_log.log(
        ml, echo=True)


def _excel_report(report, search_d):
    """Create an Excel report for each search term found

    :param report: Name of report file. If None, a report will not be created
    :type report: str, None
    :param search_d: Key is the search term and value is the list of login objects associated with that search term
    :type search_d: dict
    :rtype: None
    """
    if report is None:
        return
    wb = excel_util.new_report()
    sheet_name = 'Node Find Results'
    report_obj_l = list()
    for k, login_obj_l in search_d.items():
        report_obj_l.extend(login_obj_l)
    report_login.login_page(wb, None, sheet_name, 0, sheet_name, report_obj_l)

    try:
        excel_util.save_report(wb, report)
    except FileNotFoundError:
        brcdapi_log.log('Folder in ' + report + ' not found.')
    except PermissionError:
        buf = ('Permission denied writing ' + report +
               '. This typically happens when the file is open in another application')
        brcdapi_log.log(buf, echo=True)


def psuedo_main(proj_obj, alias_l, wwn_l, zone_l, search_type, report):
    """Basically the main().

    :param proj_obj: Project object
    :type proj_obj: brcdapi.class.project.ProjectObj
    :param alias_l: Nodes by alias to search for
    :type alias_l: list
    :param wwn_l: Nodes by WWN to search for
    :type wwn_l: list
    :param zone_l: Nodes by zone to search for
    :type zone_l: list
    :param search_type: Type of search. Can be exact, regex_m, regex_s, or wild
    :type search_type: str
    :param report: Name of Excel report.
    :type report: None,str
    :return: Status code.
    :rtype: int
    """

    # Initialize tracking data structures
    search_d = dict()
    for buf in alias_l + wwn_l + zone_l:
        search_d.update({buf: list()})

    # Find each item - nodefind
    for fab_obj in proj_obj.r_fabric_objects():

        # Find by alias. Doing this one alias at a time to keep track of what was found for each alias
        for alias in alias_l:  # Keep in mind that aliases may be a regex or wild card
            for alias_obj in [fab_obj.r_alias_obj(a) for a in
                              brcddb_fabric.aliases_by_name(fab_obj, alias, s_type=search_type)]:
                for wwn in alias_obj.r_members():
                    login_obj = fab_obj.r_login_obj(wwn)
                    if login_obj is not None:
                        search_d[alias].append(login_obj)

        # Find by WWN. Doing this one WWN at a time to keep track of what was found for each WWN. Keep in mind that
        # WWNs may be a regex or wild card
        for wwn in wwn_l:
            search_d[wwn].extend(brcddb_search.match(fab_obj.r_login_objects(), '_obj_key', wwn, True, search_type))

        # Find by zone - Similar to find by alias but keep in mind that the member may be a WWN.
        # d,i zone members are not processed
        for zone in zone_l:
            for zone_obj in [fab_obj.r_zone_obj(z) for z in
                             brcddb_fabric.zone_by_name(fab_obj, zone, s_type=search_type)]:
                zone_wwn_l = list()
                for mem in zone_obj.r_members():
                    alias_obj = fab_obj.r_alias_obj(mem)
                    if alias_obj is None:
                        zone_wwn_l.append(mem)  # assume it's a WWN. If not, fab_obj.r_login_obj() returns None
                    else:
                        zone_wwn_l.extend([wwn for wwn in alias_obj.r_members()])
                    for wwn in zone_wwn_l:
                        login_obj = fab_obj.r_login_obj(wwn)
                        if login_obj is not None:
                            search_d[zone].append(login_obj)

    # Create the reports
    _local_report(search_d)
    _excel_report(report, search_d)

    return brcddb_common.EXIT_STATUS_OK


def _get_input():
    """Parses the module load command line

    :return ec: Status code.
    :rtype ec: int
    """
    global __version__, _input_d, _version_d, _search_type_d

    ec = brcddb_common.EXIT_STATUS_OK

    # Get command line input
    buf = 'Searches a project file for a node by WWN. Aliases and zone members are converted to WWNs. Wild card and '\
          'regex matching/searching is supported. The type of searching, -s, is applied to all input. Typically, only '\
          'one type of input (-alias, -alias_f, -wwn, -wwn_f, -zone, and -zone_f) is used, but any combination of '\
          'inputs is supported. To simplify copy and paste, duplicates in the resulting lists of aliases (-alias + '\
          '-alias_f), WWNs (-wwn + -wwn_f), and zones (-zone and -zone_f) are removed.'
    try:
        args_d = gen_util.get_input(buf, _input_d)
    except TypeError:
        return brcddb_common.EXIT_STATUS_INPUT_ERROR  # gen_util.get_input() already posted the error message.

    # Set up logging
    brcdapi_log.open_log(folder=args_d['log'], suppress=args_d['sup'], no_log=args_d['nl'], version_d=_version_d)

    # Read in the project file
    proj_obj, args_i_help = None, ''
    try:
        proj_obj = brcddb_project.read_from(brcdapi_file.full_file_name(args_d['i'], '.json'))
        if proj_obj is None:  # Error messages are sent to the log in brcddb_project.read_from() if proj_obj is None
            return brcddb_common.EXIT_STATUS_INPUT_ERROR
        brcddb_project.build_xref(proj_obj)
    except FileNotFoundError:
        args_i_help = ' not found'
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    except FileExistsError:
        args_i_help = ' folder does not exist.'
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Command line feedback
    ml = ['',
          os.path.basename(__file__) + ', ' + __version__,
          'Project, -i:          ' + args_d['i'] + args_i_help,
          'Alias, -alias:        ' + str(args_d['alias']),
          'Alias file, -alias_f: ' + str(args_d['alias_f']),
          'WWN, -wwn:            ' + str(args_d['wwn']),
          'WWN file, -wwn_f:     ' + str(args_d['wwn_f']),
          'Zone, -zone:          ' + str(args_d['zone']),
          'Zone file, -zone_f:   ' + str(args_d['zone_f']),
          'Search type, -s:      ' + str(args_d['s']),
          'Report, -r:           ' + str(args_d['r']),
          'Log, -log:            ' + str(args_d['log']),
          'No log, -nl:          ' + str(args_d['nl']),
          'Suppress, -sup:       ' + str(args_d['sup']),]
    proj_obj.s_description('\n'.join(ml))
    ml.append('')

    # Get the lists of aliases and WWNs to work on.
    alias_l = list() if args_d['alias'] is None else gen_util.convert_to_list(args_d['alias'].split(','))
    wwn_l = list() if args_d['wwn'] is None else gen_util.convert_to_list(args_d['wwn'].split(','))
    zone_l = list() if args_d['zone'] is None else gen_util.convert_to_list(args_d['zone'].split(','))
    for d in (dict(f=args_d['alias_f'], l=alias_l),
              dict(f=args_d['wwn_f'], l=wwn_l),
              dict(f=args_d['zone_f'], l=zone_l)):
        if isinstance(d['f'], str):
            for file in d['f'].split(','):
                try:
                    d['l'].extend(brcdapi_file.read_file(brcdapi_file.full_file_name(file, '.txt', dot=True)))
                except FileNotFoundError:
                    ml.append(str(file) + ' does not exist')
                    ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
                except FileExistsError:
                    ml.append('A folder in ' + str(file) + ' does not exist')
                    ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Validate the WWNs and aliases
    if len(alias_l) + len(wwn_l) + len(zone_l) == 0:
        ml.append('No nodes to search for.')
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    elif args_d['s'] == 'exact':
        for wwn in wwn_l:
            if not gen_util.is_wwn(wwn):
                ml.append(wwn + ', is not valid a valid WWN for exact match. Re-run with -h and review the -s options.')
                ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
        for alias in alias_l:
            if not gen_util.is_valid_zone_name(alias):
                ml.append(alias + ', is not a valid alias for exact match. Re-run with -h and review the -s options.')
                ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
        for zone in zone_l:
            if not gen_util.is_valid_zone_name(zone):
                ml.append(zone + ', is not a valid zone for exact match. Re-run with -h and review the -s options.')
                ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    brcdapi_log.log(ml, echo=True)

    # Command line feedback and process
    return ec if ec != brcddb_common.EXIT_STATUS_OK else \
        psuedo_main(proj_obj,
                    gen_util.remove_duplicates(gen_util.remove_none(alias_l)),
                    gen_util.remove_duplicates(gen_util.remove_none(wwn_l)),
                    gen_util.remove_duplicates(gen_util.remove_none(zone_l)),
                    _search_type_d[args_d['s']],
                    brcdapi_file.full_file_name(args_d['r'], '.xlsx'))


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
