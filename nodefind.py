#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright 2024, 2025, 2026 Jack Consoli.  All rights reserved.

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
| 1.0.5     | 25 Aug 2025   | Use brcddb.util.util.get_import_modules to dynamically determined imported libraries. |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 1.0.6     | 19 Oct 2025   | Updated comments only.                                                                |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 1.0.7     | 20 Feb 2026   | Updated copyright notice.                                                             |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 1.0.8     | 10 Mar 2026   | Removed duplicates in output. Improved help messages.                                 |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 1.0.9     | 01 Aug 2026   | Modified to use new brcddb_switch.best_switch_name() format.                          |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 1.1.0     | 26 Oct 2026   | Added SFP serial numbers.                                                             |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 1.1.1     | 29 Oct 2026   | Added remote (SFP from attached device) SFP serial numbers.                           |
+-----------+---------------+---------------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2024, 2025, 2026 Jack Consoli'
__date__ = '29 Oct 2026'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack_consoli@yahoo.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '1.1.1'

import os
import brcdapi.log as brcdapi_log
import brcdapi.fos_auth as fos_auth
import brcdapi.gen_util as gen_util
import brcdapi.util as brcdapi_util
import brcdapi.excel_util as excel_util
import brcdapi.file as brcdapi_file
import brcddb.brcddb_common as brcddb_common
import brcddb.brcddb_project as brcddb_project
import brcddb.brcddb_switch as brcddb_switch
import brcddb.util.search as brcddb_search
import brcddb.report.login as report_login
import brcddb.report.port as report_port
import brcddb.brcddb_fabric as brcddb_fabric
import brcddb.brcddb_login as brcddb_login
import brcddb.brcddb_port as brcddb_port
import brcddb.app_data.report_tables as brcddb_rt

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
# _STAND_ALONE: True: Executes as a standalone module taking input from the command line. False: Does not automatically
# execute. This is useful when importing this module into another module that calls psuedo_main().
_STAND_ALONE = True  # See note above

_search_type_d = dict(wild='wild', regex_m='regex-m', regex_s='regex-s', exact='exact')
_search_type_l = [str(_b) for _b in _search_type_d.keys()]

# Input parameter definitions
_input_d = dict(
    i=dict(
        h='Required. Name of input file generated by capture.py, combine.py, or multi_capture.py. ".json" is '
          'automatically appended if not present.'
    ),
    alias=dict(
        r=False,
        d=None,
        h='Optional. CSV list of nodes by alias to search for. Supports regex and wild card searching. The search type '
          'is defined with the -s parameter. WARNING: Some characters may be interpreted as command line separators. '
          'Enclose the -alias parameters in quotes to avoid this problem.'
    ),
    alias_f=dict(
        r=False,
        d=None,
        h='Optional. Performs the same function as -alias. The difference is that the input is read from a plain text '
          'file. The argument therefore is a file name. ".txt" is automatically appended. Multiple files can be '
          'specified with a CSV list. Instead of using a CSV list, each search term is on a new line. Since the search '
          'terms are read from a file instead of the command line, there is no need to enclose search terms in quotes. '
          'Blank lines and comments (“#” and anything thereafter to the end of the line) are removed. If -alias is also'
          ' specified, the parameters specified with -alias are appended to the list of parameters read from this file.'
    ),
    wwn=dict(r=False, d=None, h='Optional. Same as -alias except it is applied to WWNs.'),
    wwn_f=dict(r=False, d=None, h='Optional. Same as -alias_f except it is applied to WWNs.'),
    zone=dict(r=False, d=None, h='Optional. Same as -alias except it is applied to zone names.'),
    zone_f=dict(r=False, d=None, h='Optional. Same as -alias_f except it is applied to zone names.'),
    sfp=dict(r=False, d=None, h='Optional. Same as -alias except it is applied to SFP serial numbers.'),
    sfp_f=dict(r=False, d=None, h='Optional. Same as -alias_f except it is applied to SFP serial numbers.'),
    sn=dict(
        r=False,
        d=None,
        h='Optional. Same as -alias except it is applied to the attached device serial numbers. FDMI data is used for '
          'open systems. The sequence number in RNID data is used for FICON (mainframe). Often, FDMI is a feature that '
          'must be enabled on the HBA. Not all HBAs support FDMI.'
    ),
    sn_f=dict(r=False, d=None, h='Optional. Same as -alias_f except it is applied to attached device serial numbers.'),
    s=dict(
        r=False, d='exact', v=_search_type_l,
        h='Optional. Search type. Options are: ' + ', '.join(_search_type_l) + ' The default is "exact".'
    ),
    r=dict(r=False, h='Optional. Name of Excel report file. ".xlsx" is automatically appended.'),
)
_input_d.update(gen_util.parseargs_log_d.copy())


def _local_report(search_d, sfp_search_d, remote_sfp_search_d, sn_search_d):
    """Create a text report for each search term

    :param search_d: Key is the search term. Value is the list of login objects associated with that search term
    :type search_d: dict
    :param sfp_search_d: Key is the search term. Value is the list of port objects associated with that search term
    :type sfp_search_d: dict
    :param remote_sfp_search_d: For remote SFPs. Same data structure as sfp_search_d.
    :type remote_sfp_search_d: dict
    :param sn_search_d: Same as sfp_search_d except the search is performed on attached device serial numbers.
    :type sn_search_d: dict
    :rtype: None
    """
    report_l = [dict(p1='')]

    # Nodes (logins)
    report_l.extend([dict(p1='Node Find Results'), dict(p1='_________________')])
    for k, obj_l in search_d.items():
        report_l.extend([dict(p1=''), dict(p1=str(k))])
        if len(obj_l) == 0:
            report_l.extend([dict(b1_char='  '), dict(b1='Not found.')])
            continue
        for login_obj in obj_l:
            port_obj = login_obj.r_port_obj()
            if port_obj is None:
                buf = 'Port not found for ' + login_obj.r_obj_key()
                buf += '. This typically occurs when there was an incomplete data capture.'
                report_l.extend([dict(b1_char='  '), dict(b1=buf)])
                continue
            report_l.extend([
                dict(b1_char='  Switch:  '),
                dict(b1=brcddb_switch.best_switch_name(port_obj, wwn=True, fid=True, did=True)),
                dict(b1_char='  Port:    '),
                dict(b1=brcddb_port.port_best_desc(port_obj, port_num=True, port_name=True, sn=True)),
                dict(b1_char='  Login:   '),
                dict(b1=brcddb_login.best_login_name(login_obj.r_fabric_obj(), login_obj.r_obj_key(), flag=True)),
                dict(p1=''),
                ])

    # SFPs (Ports)
    for d in [
        dict(  # Switch SFPs
            hdr_l=[dict(p1=''), dict(p1='SFP Find Results'), dict(p1='_________________')],
            search_d=sfp_search_d,
            sfp='SFP S/N:        ',
            sfp_sn=brcdapi_util.sfp_sn
        ),
        dict(  # Remote SFPs
            hdr_l=[
                dict(p1=''),
                dict(p1='Remote (Attached Device) SFP Find Results'),
                dict(p1='_________________________________________')
            ],
            search_d=remote_sfp_search_d,
            sfp='Remote SFP S/N: ',
            sfp_sn=brcdapi_util.sfp_remote_sn
        ),
    ]:
        report_l.extend(d['hdr_l'])
        for k, obj_l in d['search_d'].items():
            report_l.extend([dict(p1=''), dict(p1=str(k))])
            if len(obj_l) == 0:
                report_l.append(dict(b1_char='                  ', b1='Not found.'))
                continue
            for port_obj in obj_l:
                try:
                    login_name = \
                        brcddb_login.best_login_name(port_obj.r_fabric_obj(), port_obj.r_login_keys()[0], flag=True)
                except IndexError:
                    login_name = 'Nothing logged in'
                report_l.extend([
                    dict(b1_char='  Login:          '),
                    dict(b1=login_name),
                    dict(b1_char='  Switch:         '),
                    dict(b1=brcddb_switch.best_switch_name(port_obj, wwn=True, fid=True, did=True)),
                    dict(b1_char='  Port:           '),
                    dict(b1=brcddb_port.port_best_desc(port_obj, port_num=True, port_name=True, sn=True)),
                    dict(b1_char='  ' + d['sfp']),
                    dict(b1=port_obj.r_get(d['sfp_sn'], '')),
                    dict(p1=''),
                    ])

    # Serial Numbers (by port for attached devices)
    report_l.extend([dict(p1=''), dict(p1='SN Find Results'), dict(p1='________________')])
    for k, obj_l in sn_search_d.items():
        report_l.extend([dict(p1=''), dict(p1=str(k))])
        if len(obj_l) == 0:
            report_l.append(dict(b1_char='                  ', b1='Not found.'))
            continue
        for port_obj in obj_l:
            report_l.extend([
                dict(b1_char='  Switch:         '),
                dict(b1=brcddb_switch.best_switch_name(port_obj, wwn=True, fid=True, did=True)),
                dict(b1_char='  Port:           '),
                dict(b1=brcddb_port.port_best_desc(port_obj, port_num=True, port_name=True, sn=True)),
                dict(p1=''),
            ])

    report_l.append(dict(p1=''))
    brcdapi_log.log(gen_util.format_text(report_l), echo=True)


def _excel_report(report, search_d, sfp_search_d, remote_sfp_search_d, sn_search_d):
    """Create an Excel report for each search term found

    :param report: Name of report file. If None, a report will not be created
    :type report: str, None
    :param search_d: Key is the search term and value is the list of login objects associated with that search term
    :type search_d: dict
    :param sfp_search_d: Key is the search term and value is the list of port objects associated with that search term
    :type sfp_search_d: dict
    :param remote_sfp_search_d: For remote SFPs. Same data structure as sfp_search_d.
    :type remote_sfp_search_d: dict
    :param sn_search_d: Same as sfp_search_d except the search is performed on attached device serial numbers.
    :type sn_search_d: dict
    :return: True if there was no report to write or the report was successfully created. Otherwise, False.
    :rtype: None
    """

    # Create the workbook
    if not isinstance(report, str):
        return True
    brcdapi_log.log('Creating report: ' + report, echo=True)
    wb = excel_util.new_report()

    # Add the page for serial numbers (by port)
    for d in [
        dict(sheet_name='Attached_Device', hdr='S/N In Attached Device Find Results', search_d=sn_search_d),
        dict(sheet_name='Remote_SFP', hdr='Remote SFP Find Results', search_d=remote_sfp_search_d),
        dict(sheet_name='SFP', hdr='SFP Find Results', search_d=sfp_search_d),
    ]:
        report_obj_l = list()
        for obj_l in d['search_d'].values():
            report_obj_l.extend(obj_l)
        report_port.port_page(
            wb,
            None,
            d['sheet_name'],
            0,
            d['hdr'],
            report_obj_l,
            in_display=brcddb_rt.Port.port_sfp_find_tbl
        )

    # Add the page for logins (for traditional nodefind results)
    report_obj_l = list()
    for obj_l in search_d.values():
        report_obj_l.extend(obj_l)
    report_login.login_page(
        wb,
        None,
        'Node_Find',
        0,
        'Node Find Results',
        report_obj_l)

    # Save the workbook and return
    return excel_util.save_report(wb, report)


def _find_by_alias(proj_obj, search_d, alias_l, search_type):
    """Add login objects matching the search criteria for aliases to search_d. d,i members are not processed.

    :param proj_obj: Project object
    :type proj_obj: brcdapi.class.project.ProjectObj
    :param search_d: Tracking dictionary. Defined in the beginning of psuedo_main().
    :type search_d: dict
    :param alias_l: Nodes by alias to search for
    :type alias_l: list
    :param search_type: Type of search. Can be exact, regex_m, regex_s, or wild
    :type search_type: str
    :return: Nothing
    :rtype: None
    """
    for fab_obj in proj_obj.r_fabric_objects():

        # Find by alias. Doing this one alias at a time to keep track of what was found for each alias
        for alias in alias_l:  # Keep in mind that aliases may be a regex or wild card
            for alias_obj in [
                fab_obj.r_alias_obj(a) for a in brcddb_fabric.aliases_by_name(fab_obj, alias, s_type=search_type)
            ]:
                for login_obj in gen_util.remove_none([fab_obj.r_login_obj(wwn) for wwn in alias_obj.r_members()]):
                    search_d[alias].append(login_obj)


def _find_by_wwn(proj_obj, search_d, wwn_l, search_type):
    """Add login objects matching the search criteria for WWNs to search_d.

    :param proj_obj: Project object
    :type proj_obj: brcdapi.class.project.ProjectObj
    :param search_d: Tracking dictionary. Defined in the beginning of psuedo_main().
    :type search_d: dict
    :param wwn_l: Nodes by WWN to search for
    :type wwn_l: list
    :param search_type: Type of search. Can be exact, regex_m, regex_s, or wild
    :type search_type: str
    :return: Nothing
    :rtype: None
    """
    for wwn in wwn_l:
        search_d[wwn].extend(
            brcddb_search.match(
                proj_obj.r_login_objects(),
                '_obj_key',
                wwn,
                ignore_case=True,
                stype=search_type
            )
        )


def _find_by_zone(proj_obj, search_d, zone_l, search_type):
    """Add login objects matching the search criteria for zones to search_d. d,i members are not processed.

    :param proj_obj: Project object
    :type proj_obj: brcdapi.class.project.ProjectObj
    :param search_d: Tracking dictionary. Defined in the beginning of psuedo_main().
    :type search_d: dict
    :param zone_l: Nodes by zone to search for
    :type zone_l: list
    :param search_type: Type of search. Can be exact, regex_m, regex_s, or wild
    :type search_type: str
    :return: Nothing
    :rtype: None
    """
    for fab_obj in proj_obj.r_fabric_objects():
        for zone in zone_l:
            for zone_obj in [
                fab_obj.r_zone_obj(z) for z in brcddb_fabric.zone_by_name(fab_obj, zone, s_type=search_type)
            ]:
                zone_wwn_l = list()
                for mem in zone_obj.r_members():
                    alias_obj = fab_obj.r_alias_obj(mem)
                    zone_wwn_l.extend([mem] if alias_obj is None else alias_obj.r_members())  # None if mem is WWN
                    for login_obj in gen_util.remove_none([fab_obj.r_login_obj(wwn) for wwn in zone_wwn_l]):
                        search_d[zone].append(login_obj)


def _find_by_sfp(proj_obj, search_d, sfp_l, search_type):
    """Add port objects matching the search criteria for SFPs to search_d.

    :param proj_obj: Project object
    :type proj_obj: brcdapi.class.project.ProjectObj
    :param search_d: Tracking dictionary. Defined in the beginning of psuedo_main().
    :type search_d: dict
    :param sfp_l: SFP serial numbers to search for
    :type sfp_l: list
    :param search_type: Type of search. Can be exact, regex_m, regex_s, or wild
    :type search_type: str
    :return: Nothing
    :rtype: None
    """
    for sfp in sfp_l:
        search_d[sfp].extend(
            brcddb_search.match(
                proj_obj.r_port_objects(),
                brcdapi_util.sfp_sn,
                sfp,
                ignore_case=True,
                stype=search_type
            )
        )


def _find_by_remote_sfp(proj_obj, search_d, sfp_l, search_type):
    """Add port objects matching the search criteria for remote optics to search_d.

    :param proj_obj: Project object
    :type proj_obj: brcdapi.class.project.ProjectObj
    :param search_d: Tracking dictionary. Defined in the beginning of psuedo_main().
    :type search_d: dict
    :param sfp_l: SFP serial numbers to search for
    :type sfp_l: list
    :param search_type: Type of search. Can be exact, regex_m, regex_s, or wild
    :type search_type: str
    :return: Nothing
    :rtype: None
    """
    for sfp in sfp_l:
        search_d[sfp].extend(
            brcddb_search.match(
                proj_obj.r_port_objects(),
                brcdapi_util.sfp_remote_sn,
                sfp,
                ignore_case=True,
                stype=search_type
            )
        )


def _find_by_sn(proj_obj, search_d, sn_l, search_type):
    """Add port objects matching the search criteria for SFPs to search_d.

    :param proj_obj: Project object
    :type proj_obj: brcdapi.class.project.ProjectObj
    :param search_d: Tracking dictionary. Defined in the beginning of psuedo_main().
    :type search_d: dict
    :param sn_l: Attached device serial numbers to search for
    :type sn_l: list
    :param search_type: Type of search. Can be exact, regex_m, regex_s, or wild
    :type search_type: str
    :return: Nothing
    :rtype: None
    """
    for sn in sn_l:
        search_d[sn].extend(
            brcddb_search.match(
                proj_obj.r_port_objects(),
                brcdapi_util.fdmi_node_sn,  # Open systems
                sn,
                ignore_case=True,
                stype=search_type
            )
        )
        search_d[sn].extend(
            brcddb_search.match(
                proj_obj.r_port_objects(),
                'rnid/sequence-number',  # FICON
                sn,
                ignore_case=True,
                stype=search_type
            )
        )


def psuedo_main(proj_obj, alias_l, wwn_l, zone_l, sfp_l, sn_l, search_type, report):
    """Basically the main().

    :param proj_obj: Project object
    :type proj_obj: brcdapi.class.project.ProjectObj
    :param alias_l: Nodes by alias to search for
    :type alias_l: list
    :param wwn_l: Nodes by WWN to search for
    :type wwn_l: list
    :param zone_l: Nodes by zone to search for
    :type zone_l: list
    :param sfp_l: SFPs by serial number to search for.
    :type sfp_l: list
    :param sn_l: Attached device by serial number to search for.
    :type sn_l: list
    :param search_type: Type of search. Can be exact, regex_m, regex_s, or wild
    :type search_type: str
    :param report: Name of Excel report.
    :type report: None,str
    :return: Status code. See EXIT_STATUS_* in brcddb.brcddb_common.py for details
    :rtype: int
    """
    # Initialize tracking data structures
    # search_d: Key is the search term. Used for alias, wwn, and zone. The content is a list of login objects matching
    # the search criteria.
    # sfp_search_d: The content is a list of port objects with SFPs matching the search criteria.
    search_d, sfp_search_d, remote_sfp_search_d, sn_search_d = dict(), dict(), dict(), dict()
    for buf in alias_l + wwn_l + zone_l:
        search_d[buf] = list()
    for buf in sfp_l:
        sfp_search_d[buf] = list()
        remote_sfp_search_d[buf] = list()
    for buf in sn_l:
        sn_search_d[buf] = list()

    # Search for the matching login objects and port objects
    _find_by_alias(proj_obj, search_d, alias_l, search_type)
    _find_by_wwn(proj_obj, search_d, wwn_l, search_type)
    _find_by_zone(proj_obj, search_d, zone_l, search_type)
    _find_by_sfp(proj_obj, sfp_search_d, sfp_l, search_type)
    _find_by_remote_sfp(proj_obj, remote_sfp_search_d, sfp_l, search_type)
    _find_by_sn(proj_obj, sn_search_d, sn_l, search_type)

    # Create the reports and return
    for key, mem_l in search_d.items():
        search_d[key] = gen_util.remove_duplicates(mem_l)
    for key, mem_l in sfp_search_d.items():
        sfp_search_d[key] = gen_util.remove_duplicates(mem_l)
    _local_report(search_d, sfp_search_d, remote_sfp_search_d, sn_search_d)

    return brcddb_common.EXIT_STATUS_OK \
        if _excel_report(report, search_d, sfp_search_d, remote_sfp_search_d, sn_search_d) \
        else brcddb_common.EXIT_STATUS_ERROR


def _get_input():
    """Parses the module load command line

    :return ec: Status code.
    :rtype ec: int
    """
    global __version__, _input_d, _search_type_d

    ec = brcddb_common.EXIT_STATUS_OK

    # Get command line input
    buf = 'Searches a project file for a node by WWN. Aliases and zone members are converted to WWNs. Wild card and '\
          'regex matching/searching is supported. The type of searching, -s, is applied to all input. Typically, only '\
          'one type of input (-alias, -alias_f, -wwn, -wwn_f, -zone, -zone_f, -sfp, -sfp_f) is used, but any '\
          'combination of inputs is supported. The output is a logical OR of all inputs. To simplify copy and paste, '\
          'duplicates are removed.'
    try:
        args_d = gen_util.get_input(buf, _input_d)
    except TypeError:
        return brcddb_common.EXIT_STATUS_INPUT_ERROR  # gen_util.get_input() already posted the error message.

    # Set up logging
    brcdapi_log.open_log(
        folder=args_d['log'],
        suppress=args_d['sup'],
        no_log=args_d['nl'],
        version_d=brcdapi_util.get_import_modules()
    )

    # Read in the project file
    args_i_help = ''
    proj_obj = brcddb_project.read_from(brcdapi_file.full_file_name(args_d['i'], '.json'))
    if fos_auth.is_error(proj_obj):
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
        args_i_help = ' ERROR: See below for details.'

    # Command line feedback
    ml = [
        '',
        os.path.basename(__file__) + ', ' + __version__,
        'Project, -i:          ' + args_d['i'] + args_i_help,
        'Alias, -alias:        ' + str(args_d['alias']),
        'Alias file, -alias_f: ' + str(args_d['alias_f']),
        'WWN, -wwn:            ' + str(args_d['wwn']),
        'WWN file, -wwn_f:     ' + str(args_d['wwn_f']),
        'Zone, -zone:          ' + str(args_d['zone']),
        'Zone file, -zone_f:   ' + str(args_d['zone_f']),
        'SFP, -sfp:            ' + str(args_d['sfp']),
        'SFP file, -sfp_f:     ' + str(args_d['sfp_f']),
        'SN, -sn:              ' + str(args_d['sn']),
        'SN file, -sn_f:       ' + str(args_d['sn_f']),
        'Search type, -s:      ' + str(args_d['s']),
        'Report, -r:           ' + str(args_d['r']),
        'Log, -log:            ' + str(args_d['log']),
        'No log, -nl:          ' + str(args_d['nl']),
        'Suppress, -sup:       ' + str(args_d['sup']),
        '',
    ]

    if ec is not brcddb_common.EXIT_STATUS_OK:
        ml.append(fos_auth.formatted_error_msg(proj_obj))
        brcdapi_log.log(ml, echo=True)
        return ec

    # Add the description and build cross-references in the project object
    proj_obj.s_description('\n'.join(ml))
    brcddb_project.build_xref(proj_obj)

    # Get the lists of things to search for.
    search_d = dict(alias=list(), wwn=list(), zone=list(), sfp=list(), sn=list())
    for key in search_d.keys():
        if isinstance(args_d[key], str):
            search_d[key].extend([b.strip() for b in gen_util.convert_to_list(args_d[key].split(','))])
        file_key = key + '_f'
        if isinstance(args_d[file_key], str):
            for file in [brcdapi_file.full_file_name(b.strip(), '.txt', dot=True) for b in args_d[file_key].split(',')]:
                content_l = brcdapi_file.read_file(file, remove_blank=True, rc=True)
                if isinstance(content_l, list):
                    search_d[key].extend([b.strip() for b in content_l])
                else:
                    ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Validate the WWNs and aliases
    if max([len(search_d[k]) for k in ('alias', 'wwn', 'zone', 'sfp', 'sn')]) == 0:
        ml.append('Nothing to search for.')
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    elif args_d['s'] == 'exact':
        check_d = dict(alias=gen_util.is_valid_zone_name, wwn=gen_util.is_wwn, zone=gen_util.is_valid_zone_name)
        for key, action in check_d.items():
            for mem in [b for b in search_d[key] if not action(b)]:
                buf = mem + ', is not valid a valid ' + mem.upper() if mem == 'wwn' else mem
                ml.append(buf + ' for exact match. Re-run with -h and review the -s options.')
                ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    brcdapi_log.log(ml, echo=True)

    # Command line feedback and process. IDK why I didn't just pass search_d to psuedo_main().
    return ec if ec != brcddb_common.EXIT_STATUS_OK else \
        psuedo_main(
            proj_obj,
            gen_util.remove_duplicates(gen_util.remove_none(search_d['alias'])),
            gen_util.remove_duplicates(gen_util.remove_none(search_d['wwn'])),
            gen_util.remove_duplicates(gen_util.remove_none(search_d['zone'])),
            gen_util.remove_duplicates(gen_util.remove_none(search_d['sfp'])),
            gen_util.remove_duplicates(gen_util.remove_none(search_d['sn'])),
            _search_type_d[args_d['s']],
            brcdapi_file.full_file_name(args_d['r'], '.xlsx'),
        )


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
