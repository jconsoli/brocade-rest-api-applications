#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2023 Consoli Solutions, LLC.  All rights reserved.
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
:mod:`search` - Contains several examples of how to perform searches of the brcddb objects

This module illustrates how to use the searching and built in reporting features of the brcddb libraries. Some of the
examples are practical but the primary intent is to illustrate how to use the tools. It is set up to make it easy to
pick examples of interest either to simply look at the output or to set break points to examine the code and data.
Unless edited for a specific function, as a stand-alone utility this module serves no useful purpose.

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 4.0.0     | 04 Aug 2023   | Re-Launch                                                                         |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2023 Consoli Solutions, LLC'
__date__ = '04 August 2023'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack_consoli@yahoo.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '4.0.0'

import argparse
import json
import brcddb.brcddb_project as brcddb_project
import brcdapi.log as brcdapi_log
import brcdapi.gen_util as gen_util
import brcdapi.excel_util as excel_util
import brcddb.brcddb_common as brcddb_common
import brcddb.classes.util as brcddb_class_util
import brcddb.util.util as brcddb_util
import brcdapi.file as brcdapi_file
import brcddb.util.search as brcddb_search
import brcddb.util.obj_convert as brcddb_conv
import brcddb.report.chassis as report_chassis
import brcddb.report.fabric as report_fabric
import brcddb.report.login as report_login
import brcddb.report.port as report_port
import brcddb.report.switch as report_switch
import brcddb.report.zone as report_zone

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = False  # When True, use the values below instead of reading from the command line
_DEBUG_i = '_capture_2021_11_16_11_27_27/combined'
_DEBUG_f = 's/test'
_DEBUG_eh = False
_DEBUG_log = '_logs'
_DEBUG_nl = False
_DEBUG_v = False

_wb = None                               # Object for the Excel workbook used for example output
_report_name = None  # Name of report
_working_obj_l = list()
_report_display = dict()
_sheet_index = 0                         # Most examples add a worksheet to the Excel workbook. This indicates where.

_eh = (
    '',
    'Extended description of filter file, -f. See examples in the "s" folder.',
    '',
    'The filter file is a list of actions in the form of dictionaries as follows:',
    '',
    'def_report  dict  Optional. Defines the output report as follows',
    '',
    '    name  str   Name of the Excel workbook. ".xlsx" is automatically',
    '                appended.',
    '',
    '    xxxx  list  Where "xxxx" is a user defined report display format. The',
    '                value is a list of object keys to display. This list is passed',
    '                directly to the report page methods in brcddb.report. This',
    '                is only relevant to report pages that accept a that a display',
    '                table which are: chassis, switch, port, and login.'
    '',
    'object      str   The search.py utility maintains a list of brcddb objects to',
    '                  operate on. It is preloaded with the project object defined',
    '                  with the -i parameter. Objects are extracted/converted with',
    '                  this option by specifying one of the simple object types in',
    '                  brcddb.classes.util.simple_class_type',
    '',
    'print       dict  Optional. Instructs search.py to print the results to the.',
    '                  console as follows:',
    '',
    '    title   str   Optional. Printed before printing any results.',
    '',
    '    disp    str   Optional. What to display for each object. See "replace"',
    '',
    '    replace list  Optional. List of dictionaries. Each dictionary is as',
    '                  follows:',
    '                  t    The text in disp to be replaced with the value in "r"',
    '                  r    The key to a value in the working object list that',
    '                       the text in "t" is replaced with.',
    '',
    '    total   str   Optional. Prints this text to the console followed by the',
    '                  number of matches found.',
    '',
    'report      dict  Optional. "def_report" must be defined if using this option.',
    '                  Instructs search.py to insert a worksheet into the workbook',
    '                  as follows:',
    '',
    '    disp    str   Optional. Must be one of the predefined display options,',
    '                  see "xxxx" in "def_report". If omitted, the default display',
    '                  for the object type is used. See',
    '                  brcddb.app_data.report_tables',
    '',
    '    index   int   Optional. Sheet index where the worksheet is to be inserted.',
    '                  If omitted, the default is 0.',
    '',
    '    name    str   Required. Name of the worksheet',
    '',
    '    title   str   Optional. Title to be inserted at the top of the worksheet',
    '',
    '    type  str   The type of report (worksheet) to generate. Typically,',
    '                searching only makes sense when searching for ports or logins',
    '                so only "port" or "login" makes sense but the coding for all'
    '                report types was easy so all are available. Valid types are:',
    '',
    '        alias    brcddb.report.zone.alias_page()',
    '',
    '        chassis  brcddb.report.chassis.chassis_page()',
    '',
    '        fabric   brcddb.report.fabric.fabric_page()',
    '',
    '        login    brcddb.report.login.login_page()',
    '',
    '        ntarget  brcddb.report.zone.non_target_zone_page()',
    '',
    '        port     brcddb.report.port.port_page()',
    '',
    '        switch   brcddb.report.switch.switch_page()',
    '',
    '        target   brcddb.report.zone.target_zone_page()',
    '',
    '        zone     brcddb.report.zone.zone_page()',
    '',
    'test        dict  Defines a test to be performed passed to',
    '                  brcddb.util.search.match_test()',
    '',
)


##################################################################
#
# Case actions for _print_act().
#
###################################################################
def _print_title(obj):
    buf = obj.get('title')
    if buf is not None:
        brcdapi_log.log(buf, True)


def _print_disp(obj):
    global _working_obj_l

    disp = gen_util.convert_to_list(obj.get('disp'))
    to_print_l = list()
    for b_obj in _working_obj_l:
        for buf in disp:
            for d in gen_util.convert_to_list(obj.get('replace')):
                buf = buf.replace(d['t'], str(b_obj.r_get(d['r'])))
            to_print_l.append(buf)
    if len(to_print_l) > 0:
        brcdapi_log.log(to_print_l, True)


def _print_total(obj):
    global _working_obj_l

    brcdapi_log.log(obj['total'] + str(len(_working_obj_l)), True)


_print_action_tbl = dict(title=_print_title, disp=_print_disp, total=_print_total)


def _has_sheet_name(obj, buf):
    """Checks to see if there is a sheet name in obj and prints the sheet name being processed to STD_IO and the log.
    
    :param obj: "report" object from the input file
    :type obj: dict
    :param buf: Display text if "name" is found
    :type buf: str
    :return: True if "name" is in the object and the value is a str
    :rtype: bool
    """
    sheet_name = obj.get('name')
    if isinstance(sheet_name, str):
        return True
    if sheet_name is None:
        brcdapi_log.log('"name" missing in "report".', True)
    else:
        brcdapi_log.log('Invalid type, ' + str(type(sheet_name)) + ', for "name" in "report".', True)
    return False
        
        
##################################################################
#
# Case actions for _report_act(). See obj in _has_sheet_name() for input description
#
###################################################################
def _validate_obj_type(obj_l, obj_type):
    type_l = gen_util.remove_duplicates([brcddb_class_util.get_simple_class_type(obj) for obj in obj_l])
    if (len(type_l) == 1 and type_l[0] == obj_type) or len(type_l) == 0:
        return True
    brcdapi_log.log('Invalid report object type. Expected: ' + obj_type + '. Received: ' + ', '.join(type_l), True)
    return False


def _report_alias_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'FabricObj'):
        brcdapi_log.log('Invalid object type for "alias"', True)
        return

    i = 0
    base_sheet_title = str(obj.get('title'))
    for fab_obj in _working_obj_l:
        if i == 0:
            sheet_name = obj['name']
            sheet_title = base_sheet_title
        else:
            sheet_name = obj['name'] + '_' + str(i)
            sheet_title = base_sheet_title + ' (' + str(i) + ')'
        brcdapi_log.log('Creating ' + sheet_name, True)
        report_zone.alias_page(fab_obj, None, _wb, sheet_name, obj.get('index'), sheet_title)
        i += 1


def _report_chassis_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'ChassisObj'):
        brcdapi_log.log('Invalid object type for "chassis"', True)
        return

    i = 0
    base_sheet_title = str(obj.get('title'))
    for chassis_obj in _working_obj_l:
        if i == 0:
            sheet_name = obj['name']
            sheet_title = base_sheet_title
        else:
            sheet_name = obj['name'] if i == 0 else obj['name'] + '_' + str(i)
            sheet_title = base_sheet_title + ' (' + str(i) + ')'
        brcdapi_log.log('Creating ' + sheet_name, True)
        report_chassis.chassis_page(_wb, None, sheet_name, obj.get('index'), sheet_title, chassis_obj, disp)
        i += 1


def _report_fabric_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'FabricObj'):
        brcdapi_log.log('Invalid object type for "fabric"', True)
        return

    i = 0
    base_sheet_title = str(obj.get('title'))
    for fab_obj in _working_obj_l:
        if i == 0:
            sheet_name = obj['name']
            sheet_title = base_sheet_title
        else:
            sheet_name = obj['name'] + '_' + str(i)
            sheet_title = base_sheet_title + ' (' + str(i) + ')'
        brcdapi_log.log('Creating ' + sheet_name, True)
        report_fabric.fabric_page(_wb, None, obj.get('index'), sheet_name, sheet_title, fab_obj)
        i += 1


def _report_login_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'LoginObj'):
        brcdapi_log.log('Invalid object type for "login"', True)
        return

    brcdapi_log.log('Creating ' + obj['name'], True)
    report_login.login_page(_wb, None, obj['name'], obj.get('index'), obj.get('title'), _working_obj_l,
                            in_display=obj.get('disp'), in_login_display_tbl=None, s=True)


def _report_ntarget_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'FabricObj'):
        brcdapi_log.log('Invalid object type for "ntarget"', True)
        return

    i = 0
    base_sheet_title = str(obj.get('title'))
    for fab_obj in _working_obj_l:
        if i == 0:
            sheet_name = obj['name']
            sheet_title = base_sheet_title
        else:
            sheet_name = obj['name'] + '_' + str(i)
            sheet_title = base_sheet_title + ' (' + str(i) + ')'
        brcdapi_log.log('Creating ' + sheet_name, True)
        report_zone.non_target_zone_page(fab_obj, None, _wb, sheet_name, obj.get('index'), sheet_title)
        i += 1


def _report_port_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'PortObj'):
        brcdapi_log.log('Invalid object type for "port"', True)
        return

    brcdapi_log.log('Creating ' + obj['name'], True)
    report_port.port_page(_wb, None, obj['name'], obj.get('index'), obj.get('title'),
                          brcddb_util.sort_ports(_working_obj_l), disp)


def _report_switch_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'SwitchObj'):
        brcdapi_log.log('Invalid object type for "switch"', True)
        return

    brcdapi_log.log('Creating ' + obj['name'], True)
    report_switch.switch_page(_wb, None, obj['name'], obj.get('index'), obj.get('title'), _working_obj_l)


def _report_target_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'FabricObj'):
        brcdapi_log.log('Invalid object type for "target"', True)
        return

    i = 0
    base_sheet_title = str(obj.get('title'))
    for fab_obj in _working_obj_l:
        if i == 0:
            sheet_name = obj['name']
            sheet_title = base_sheet_title
        else:
            sheet_name = obj['name'] + '_' + str(i)
            sheet_title = base_sheet_title + ' (' + str(i) + ')'
        brcdapi_log.log('Creating ' + sheet_name, True)
        report_zone.target_zone_page(fab_obj, None, _wb, sheet_name, obj.get('index'), sheet_title)
        i += 1


def _report_zone_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'FabricObj'):
        brcdapi_log.log('Invalid object type for "zone"', True)
        return

    i = 0
    base_sheet_title = str(obj.get('title'))
    for fab_obj in _working_obj_l:
        if i == 0:
            sheet_name = obj['name']
            sheet_title = base_sheet_title
        else:
            sheet_name = obj['name'] + '_' + str(i)
            sheet_title = base_sheet_title + ' (' + str(i) + ')'
        brcdapi_log.log('Creating ' + sheet_name, True)
        report_zone.zone_page(fab_obj, None, _wb, sheet_name, obj.get('index'), sheet_title)
        i += 1


_report_action_d = dict(
    alias=_report_alias_act,
    chassis=_report_chassis_act,
    fabric=_report_fabric_act,
    login=_report_login_act,
    ntarget=_report_ntarget_act,
    port=_report_port_act,
    switch=_report_switch_act,
    target=_report_target_act,
    zone=_report_zone_act,
)


##################################################################
#
#        Case actions for psuedo_main(), see _action_d
#
###################################################################
def _def_report_act(obj):
    global _wb, _report_name, _report_display

    if not _has_sheet_name(obj, 'workbook'):
        return  # Appropriate error message is logged in _has_sheet_name
    _wb = excel_util.new_report()
    _report_name = brcdapi_file.full_file_name(obj.get('name'), '.xlsx')
    for k, v in obj.items():
        if k != 'name':
            _report_display.update({k: v})


def _object_act(obj):
    global _working_obj_l

    _working_obj_l = brcddb_conv.obj_extract(_working_obj_l, obj)


def _report_act(obj):
    global _report_name, _report_display

    # Validate the users filter file
    if not isinstance(_report_name, str):
        brcdapi_log.log('"report" action found before "def_report" action.', True)
        return
    report_disp = None
    disp = obj.get('disp')
    if disp is not None:
        if not isinstance(disp, str):
            buf = 'Invalid "disp" type, ' + str(type(disp)) + ', in "report" action. The value associated with '
            buf += '"disp" must be a string. Using default display tables.'
            brcdapi_log.log(buf, True)
        else:
            report_disp = _report_display.get(disp)
            if report_disp is None:
                buf = '"disp", ' + disp + ', in "report" action not found in "def_report". Using default display '\
                                          'tables.'
                brcdapi_log.log(buf, True)

    if _has_sheet_name(obj, 'worksheet'):
        obj_type = obj.get('type')
        if obj_type is not None and obj_type in _report_action_d:
            _report_action_d[obj_type](obj, report_disp)
        else:
            brcdapi_log.log('Invalid "type", "' + str(obj.get('type')) + '" in "report" action', True)


def _test_act(obj):
    global _working_obj_l

    _working_obj_l = brcddb_search.match_test(_working_obj_l, obj)


def _print_act(obj):
    for k in ('title', 'disp', 'total'):  # A poor man's ordered dictionary
        _print_action_tbl[k](obj)


_action_d = dict(
    def_report=_def_report_act,
    object=_object_act,
    report=_report_act,
    test=_test_act,
    print=_print_act,
)


def _read_file(file):
    """Reads in a JSON formatted file

    :param file: Name of file to read
    :type file: str
    :return: Parsed object
    :rtype: dict, list
    """
    try:
        obj = brcddb_project.read_from(file)
    except FileNotFoundError:
        brcdapi_log.log(file + ', not found', True)
    if obj is None:
        brcdapi_log.log('Unknown error opening ' + file, True)

    return obj


def _get_input():
    """Parses the module load command line

    :return ec: Status code.
    :rtype ec: int
    :return proj_obj: Project object
    :rtype proj_obj: brcddb.classes.project.ProjectObj
    :return filter_obj: Filter file contents converted to standard Python type
    :rtype filter_obj: dict, list
    """
    global _DEBUG, _DEBUG_i, _DEBUG_f, _DEBUG_eh, _DEBUG_v, _DEBUG_log, _DEBUG_nl

    proj_obj, filter_obj, ml, ec = None, None, list(), brcddb_common.EXIT_STATUS_OK

    if _DEBUG:
        proj_file, filter_file, eh, v_flag, log_file, log_nl = \
            _DEBUG_i, _DEBUG_f, _DEBUG_eh, _DEBUG_v, _DEBUG_log, _DEBUG_nl
        ml.append('WARNING!!! Debug is enabled')
    else:
        parser = argparse.ArgumentParser(description='Convert supportshow output to equivalent capture output.')
        parser.add_argument('-i', help='Required. Name of project file. ".json" is automatically appended',
                            required=False)
        buf = 'Required. Name of filter file. If the file extension is not ".json", a file extension of ".txt" is '\
              'assumed. Invoke with the -eh option for additional help'
        parser.add_argument('-f', help=buf, required=False)
        buf = 'Optional. No parameters. When specified, extended help for the filter file, -f, is displayed and '\
              'processing is terminated.'
        parser.add_argument('-eh', help=buf, action='store_true', required=False)
        buf = 'Optional. No parameters. When specified, attempts to read and convert the filter file, -f, only. No '\
              'other processing is performed.'
        parser.add_argument('-v', help=buf, action='store_true', required=False)
        buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The ' \
              'log file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
        parser.add_argument('-log', help=buf, required=False,)
        buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
        parser.add_argument('-nl', help=buf, action='store_true', required=False)
        args = parser.parse_args()

        proj_file, filter_file, eh, v_flag, log_file, log_nl = args.i, args.f, args.eh, args.v, args.log, args.nl

    if not log_nl:
        brcdapi_log.open_log(log_file)
    if eh:
        ml.extend(_eh)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    else:
        if not v_flag and not isinstance(proj_file, str):
            ml.append('Missing project file, -i')
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
        if not isinstance(filter_file, str):
            ml.append('Missing filter file, -f')
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    if ec == brcddb_common.EXIT_STATUS_OK:

        # Read in the filter file
        x = len('.json')
        if len(filter_file) <= x or filter_file[len(filter_file)-x:].lower() != '.json':
            filter_file = brcdapi_file.full_file_name(filter_file, '.txt')
        try:
            filter_obj = json.loads(''.join(brcdapi_file.read_file(filter_file, remove_blank=True, rc=True)))
        except FileNotFoundError:
            ml.append('Filter file, ' + filter_file + ', not found')
            ec = brcddb_common.EXIT_STATUS_ERROR
        except ValueError:
            ml.append('Improperly formatted JSON in ' + filter_file)
            ec = brcddb_common.EXIT_STATUS_ERROR
        if v_flag:
            if ec == brcddb_common.EXIT_STATUS_OK:
                ml.append('Successfully read ' + filter_file)
            ml.append('Validating filter file only. No other processing performed.')
            ec = brcddb_common.EXIT_STATUS_ERROR

        else:
            # User feedback
            proj_file = brcdapi_file.full_file_name(proj_file, '.json')
            ml.append('Project, -i:     ' + str(proj_file))
            ml.append('filter file, -f: ' + str(filter_file))

            # Read in the project file
            try:
                proj_obj = brcddb_project.read_from(proj_file)
            except FileNotFoundError:
                ml.append('Project file, ' + proj_file + ', not found')
                proj_obj = None
            if proj_obj is None:
                ec = brcddb_common.EXIT_STATUS_ERROR
            else:
                brcddb_project.build_xref(proj_obj)
                brcddb_project.add_custom_search_terms(proj_obj)

    if len(ml) > 0:
        brcdapi_log.log(ml, True)

    return ec, proj_obj, filter_obj


def psuedo_main():
    """Basically the main()."""
    global _wb, _report_name, _working_obj_l

    ec, proj_obj, action_l = _get_input()
    if ec != brcddb_common.EXIT_STATUS_OK:
        return ec
    _working_obj_l.append(proj_obj)

    for action_d in action_l:
        for k, v in action_d.items():
            if k in _action_d:
                _action_d[k](v)
            else:
                brcdapi_log.log('Invalid action item, ' + str(k))

    if _wb is not None and _report_name is not None:
        brcdapi_log.log('Saving ' + _report_name, True)
        excel_util.save_report(_wb, _report_name)

    return brcddb_common.EXIT_STATUS_OK

##################################################################
#
#                    Main Entry Point
#
###################################################################


if _DOC_STRING:
    brcdapi_log.close_log('_DOC_STRING is True. No processing', True)
    exit(brcddb_common.EXIT_STATUS_OK)
else:
    _ec = psuedo_main()
    brcdapi_log.close_log(['', str(_ec)])
    exit(_ec)
