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

Contains several examples of how to perform searches of the brcddb objects

This module illustrates how to use the searching and built-in reporting features of the brcddb libraries. Some of the
examples are practical but the primary intent is to illustrate how to use the tools. It is set up to make it easy to
pick examples of interest either to simply look at the output or to set break points to examine the code and data.
Unless edited for a specific function, as a stand-alone utility this module serves no useful purpose.

**Version Control**

+-----------+---------------+---------------------------------------------------------------------------------------+
| Version   | Last Edit     | Description                                                                           |
+===========+===============+=======================================================================================+
| 4.0.0     | 04 Aug 2023   | Re-Launch                                                                             |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.1     | 06 Mar 2024   | Improved help messages.                                                               |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.2     | 20 Oct 2024   | Added version numbers of imported libraries.                                          |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.3     | 06 Dec 2024   | Updated comments only.                                                                |
+-----------+---------------+---------------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2023, 2024 Consoli Solutions, LLC'
__date__ = '06 Dec 2024'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack@consoli-solutions.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '4.0.3'

import os
import json
import brcdapi.log as brcdapi_log
import brcdapi.gen_util as gen_util
import brcdapi.excel_util as excel_util
import brcdapi.file as brcdapi_file
import brcddb.brcddb_common as brcddb_common
import brcddb.brcddb_project as brcddb_project
import brcddb.brcddb_switch as brcddb_switch
import brcddb.classes.util as brcddb_class_util
import brcddb.util.util as brcddb_util
import brcddb.util.search as brcddb_search
import brcddb.util.obj_convert as brcddb_conv
import brcddb.report.chassis as report_chassis
import brcddb.report.fabric as report_fabric
import brcddb.report.login as report_login
import brcddb.report.port as report_port
import brcddb.report.switch as report_switch
import brcddb.report.zone as report_zone
_version_d = dict(
    brcdapi_log=brcdapi_log.__version__,
    gen_util=gen_util.__version__,
    excel_util=excel_util.__version__,
    brcdapi_file=brcdapi_file.__version__,
    brcddb_common=brcddb_common.__version__,
    brcddb_project=brcddb_project.__version__,
    brcddb_switch=brcddb_switch.__version__,
    brcddb_class_util=brcddb_class_util.__version__,
    brcddb_util=brcddb_util.__version__,
    brcddb_search=brcddb_search.__version__,
    brcddb_conv=brcddb_conv.__version__,
    report_chassis=report_chassis.__version__,
    report_fabric=report_fabric.__version__,
    report_login=report_login.__version__,
    report_port=report_port.__version__,
    report_switch=report_switch.__version__,
    report_zone=report_zone.__version__,
)

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
# _STAND_ALONE: True: Executes as a standalone module taking input from the command line. False: Does not automatically
# execute. This is useful when importing this module into another module that calls psuedo_main().
_STAND_ALONE = True  # See note above

_input_d = dict(
    i=dict(r=False,
           h='Required unless using the -eh option. Name of input file generated by capture.py, combine.py, or '
             'multi_capture.py'),
    f=dict(r=False,
           h='Required unless using the -eh option. Name of filter file. If the file extension is not ".json", a file '
             'extension of ".txt" is assumed. Invoke with the -eh option for additional help'),
)
_input_d.update(gen_util.parseargs_eh_d.copy())
_input_d.update(gen_util.parseargs_log_d.copy())

_wb = None  # Object for the Excel workbook used for output
_proj_obj = None  # Project object
_report_name = None  # Name of report
_working_obj_l = list()
_report_display = dict()
_sheet_index = 0  # Most examples add a worksheet to the Excel workbook. This indicates where.
_MAX_LINE_LEN = 72  # Used to control how long help messages can be.

_eh = (
    dict(b=('',
            'Extended description of filter file, -f. See examples in the "s" folder.',
            '',
            'The filter file is a list of actions in the form of dictionaries as follows:',
            '')),
    dict(b='Optional. Defines the output report as follows:', p='def_report  dict  '),
    dict(b=''),
    dict(b='Name of the Excel workbook. ".xlsx" is automatically appended.', p='    name  str   '),
    dict(b=''),
    dict(b='Where "xxxx" is a user defined report display format. The value is a list of object keys to display. This '
           'list is passed directly to the report page methods in brcddb.report. This is only relevant to report pages '
           'that accept a display table. Valid options are: chassis, switch, port, and login.',
         p='    xxxx  list  '),
    dict(b=''),
    dict(b='The search.py utility maintains a list of brcddb objects to operate on. It is preloaded with the project '
           'object defined with the -i parameter. Objects are extracted/converted with this option by specifying one '
           'of the simple object types in brcddb.classes.util.simple_class_type',
         p='object      str   '),
    dict(b=''),
    dict(b='Optional. Instructs search.py to print the results to the console as follows:',
         p='print       dict  '),
    dict(b='Optional. Printed before printing any results.', p='    title   str   '),
    dict(b=''),
    dict(b='Optional. What to display for each object. See "replace"', p='    disp    str   '),
    dict(b=''),
    dict(b='Optional. List of dictionaries. Each dictionary is as follows:', p='    replace list  '),
    dict(b='The text in disp to be replaced with the value in "r"', p='                  t    '),
    dict(b='The key to a value in the working object list that the text in "t" is replaced with.',
         p='                  r    '),
    dict(b=''),
    dict(b='Optional. Prints this text to the console followed by the number of matches found.',
         p='    total   str   '),
    dict(b=''),
    dict(b='Optional. "def_report" must be defined if using this option. Instructs search.py to insert a worksheet '
           'into the workbook as follows:',
         p='report      dict  '),
    dict(b=''),
    dict(b='Optional. Must be one of the predefined display options, see "xxxx" in "def_report". If omitted, the '
           'default display for the object type is used. See brcddb.app_data.report_tables.',
         p='    disp    str   '),
    dict(b=''),
    dict(b='Optional. Sheet index where the worksheet is to be inserted. If omitted, the default is 0.',
         p='    index   int   '),
    dict(b=''),
    dict(b='Required. Name of the worksheet.', p='    name    str   '),
    dict(b=''),
    dict(b='Optional. Title to be inserted at the top of the worksheet', p='    title   str   '),
    dict(b=''),
    dict(b='The type of report (worksheet) to generate. Typically, searching only makes sense when searching for ports '
           'or logins so only "port" or "login" are used but the coding for all report types was easy so all are '
           'available. Valid types are:',
         p='    type  str   '),
    dict(b=''),
    dict(b='brcddb.report.zone.alias_page()', p='        alias    '),
    dict(b=''),
    dict(b='brcddb.report.chassis.chassis_page()', p='        chassis  '),
    dict(b=''),
    dict(b='brcddb.report.fabric.fabric_page()', p='        fabric   '),
    dict(b=''),
    dict(b='brcddb.report.login.login_page()', p='        login    '),
    dict(b=''),
    dict(b='brcddb.report.login.login_page()', p=''),
    dict(b=''),
    dict(b='brcddb.report.zone.non_target_zone_page()', p='        ntarget  '),
    dict(b=''),
    dict(b='brcddb.report.port.port_page()', p='        port     '),
    dict(b=''),
    dict(b='brcddb.report.switch.switch_page()', p='        switch   '),
    dict(b=''),
    dict(b='brcddb.report.zone.target_zone_page()', p='        target   '),
    dict(b=''),
    dict(b='Defines a test to be performed passed to brcddb.util.search.match_test()', p='test        dict  '),
    dict(b=''),
)


##################################################################
#
# Case actions for _print_act().
#
###################################################################
def _print_title(obj):
    buf = obj.get('title')
    if buf is not None:
        brcdapi_log.log(buf, echo=True)


def _print_disp(obj):
    global _working_obj_l

    disp = gen_util.convert_to_list(obj.get('disp'))
    to_print_l = list()
    for b_obj in _working_obj_l:
        for buf in disp:
            for d in gen_util.convert_to_list(obj.get('replace')):
                r_val = str(b_obj.r_get(d['r']))
                if isinstance(d['r'], str) and d['r'] == '_switch':
                    switch_obj = _proj_obj.r_switch_obj(r_val)
                    if switch_obj is not None:
                        r_val = brcddb_switch.best_switch_name(switch_obj, wwn=True, did=True, fid=True)
                buf = buf.replace(d['t'], r_val)
            to_print_l.append(buf)
    if len(to_print_l) > 0:
        brcdapi_log.log(to_print_l, echo=True)


def _print_total(obj):
    global _working_obj_l

    brcdapi_log.log(obj['total'] + str(len(_working_obj_l)), echo=True)


_print_action_tbl = dict(title=_print_title, disp=_print_disp, total=_print_total)


def _has_sheet_name(obj):
    """Checks to see if there is a sheet name in obj and prints the sheet name being processed to STD_IO and the log.
    
    :param obj: "report" object from the input file
    :type obj: dict
    :return: True if "name" is in the object and the value is a str
    :rtype: bool
    """
    sheet_name = obj.get('name')
    if isinstance(sheet_name, str):
        return True
    if sheet_name is None:
        brcdapi_log.log('"name" missing in "report".', echo=True)
    else:
        brcdapi_log.log('Invalid type, ' + str(type(sheet_name)) + ', for "name" in "report".', echo=True)
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
    brcdapi_log.log('Invalid report object type. Expected: ' + obj_type + '. Received: ' + ', '.join(type_l), echo=True)
    return False


def _report_alias_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'FabricObj'):
        brcdapi_log.log('Invalid object type for "alias"', echo=True)
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
        brcdapi_log.log('Creating ' + sheet_name, echo=True)
        report_zone.alias_page(fab_obj, None, _wb, sheet_name, obj.get('index'), sheet_title)
        i += 1


def _report_chassis_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'ChassisObj'):
        brcdapi_log.log('Invalid object type for "chassis"', echo=True)
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
        brcdapi_log.log('Creating ' + sheet_name, echo=True)
        report_chassis.chassis_page(_wb, None, sheet_name, obj.get('index'), chassis_obj, disp)
        i += 1


def _report_fabric_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'FabricObj'):
        brcdapi_log.log('Invalid object type for "fabric"', echo=True)
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
        brcdapi_log.log('Creating ' + sheet_name, echo=True)
        report_fabric.fabric_page(_wb, None, obj.get('index'), sheet_name, sheet_title, fab_obj)
        i += 1


def _report_login_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'LoginObj'):
        brcdapi_log.log('Invalid object type for "login"', echo=True)
        return

    brcdapi_log.log('Creating ' + obj['name'], echo=True)
    report_login.login_page(_wb, None, obj['name'], obj.get('index'), obj.get('title'), _working_obj_l,
                            in_display=obj.get('disp'), in_login_display_tbl=None, s=True)


def _report_ntarget_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'FabricObj'):
        brcdapi_log.log('Invalid object type for "ntarget"', echo=True)
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
        brcdapi_log.log('Creating ' + sheet_name, echo=True)
        report_zone.non_target_zone_page(fab_obj, None, _wb, sheet_name, obj.get('index'), sheet_title)
        i += 1


def _report_port_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'PortObj'):
        brcdapi_log.log('Invalid object type for "port"', echo=True)
        return

    brcdapi_log.log('Creating ' + obj['name'], echo=True)
    report_port.port_page(_wb, None, obj['name'], obj.get('index'), obj.get('title'),
                          brcddb_util.sort_ports(_working_obj_l), disp)


def _report_switch_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'SwitchObj'):
        brcdapi_log.log('Invalid object type for "switch"', echo=True)
        return

    brcdapi_log.log('Creating ' + obj['name'], echo=True)
    report_switch.switch_page(_wb, None, obj['name'], obj.get('index'), obj.get('title'), _working_obj_l)


def _report_target_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'FabricObj'):
        brcdapi_log.log('Invalid object type for "target"', echo=True)
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
        brcdapi_log.log('Creating ' + sheet_name, echo=True)
        report_zone.target_zone_page(fab_obj, None, _wb, sheet_name, obj.get('index'), sheet_title)
        i += 1


def _report_zone_act(obj, disp):
    global _wb, _working_obj_l

    if not _validate_obj_type(_working_obj_l, 'FabricObj'):
        brcdapi_log.log('Invalid object type for "zone"', echo=True)
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
        brcdapi_log.log('Creating ' + sheet_name, echo=True)
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

    if not _has_sheet_name(obj):
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
        brcdapi_log.log('"report" action found before "def_report" action.', echo=True)
        return
    report_disp = None
    disp = obj.get('disp')
    if disp is not None:
        if not isinstance(disp, str):
            buf = 'Invalid "disp" type, ' + str(type(disp)) + ', in "report" action. The value associated with '
            buf += '"disp" must be a string. Using default display tables.'
            brcdapi_log.log(buf, echo=True)
        else:
            report_disp = _report_display.get(disp)
            if report_disp is None:
                buf = '"disp", ' + disp + ', in "report" action not found in "def_report". Using default display '\
                                          'tables.'
                brcdapi_log.log(buf, echo=True)

    if _has_sheet_name(obj):
        obj_type = obj.get('type')
        if obj_type is not None and obj_type in _report_action_d:
            _report_action_d[obj_type](obj, report_disp)
        else:
            brcdapi_log.log('Invalid "type", "' + str(obj.get('type')) + '" in "report" action', echo=True)


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
    :rtype: dict, list, None
    """
    obj = None
    try:
        obj = brcddb_project.read_from(file)
    except FileNotFoundError:
        brcdapi_log.log(file + ', not found', echo=True)
    if obj is None:
        brcdapi_log.log('Unknown error opening ' + file, echo=True)

    return obj


def psuedo_main(action_l):
    """Basically the main().

    :param action_l: Dictionaries describing actions
    :type action_l: list
    :return ec: Status code.
    :rtype ec: int
"""
    global _proj_obj, _wb, _report_name, _working_obj_l

    brcddb_project.build_xref(_proj_obj)
    brcddb_project.add_custom_search_terms(_proj_obj)
    _working_obj_l.append(_proj_obj)

    for action_d in action_l:
        for k, v in action_d.items():
            if k in _action_d:
                _action_d[k](v)
            else:
                brcdapi_log.log('Invalid action item, ' + str(k))

    if _wb is not None and isinstance(_report_name, str):
        brcdapi_log.log('Saving ' + _report_name, echo=True)
        excel_util.save_report(_wb, _report_name)

    return brcddb_common.EXIT_STATUS_OK


def _get_input():
    """Parses the module load command line

    :return ec: Status code.
    :rtype ec: int
    """
    global __version__, _input_d, _proj_obj, _version_d

    filter_obj, ml, ec = None, list(), brcddb_common.EXIT_STATUS_OK

    # Get command line input
    buf = 'Searches a project file for terms defined with the -f parameter.'
    try:
        args_d = gen_util.get_input(buf, _input_d)
    except TypeError:
        return brcddb_common.EXIT_STATUS_INPUT_ERROR  # gen_util.get_input() already posted the error message.

    # Set up logging
    brcdapi_log.open_log(folder=args_d['log'], suppress=args_d['sup'], no_log=args_d['nl'], version_d=_version_d)

    if args_d['eh']:
        for d in _eh:
            ml.extend(gen_util.wrap_text(d['b'], _MAX_LINE_LEN, d.get('p')))
    else:
        if not isinstance(args_d['i'], str):
            ml.append('Missing project file, -i')
        if not isinstance(args_d['f'], str):
            ml.append('Missing filter file, -f')
    if len(ml) > 0:
        brcdapi_log.log(ml, echo=True)
        return brcddb_common.EXIT_STATUS_INPUT_ERROR
    x, args_f_help, args_i_help = len('.json'), '', ''

    # Read in the filter file
    filter_file = args_d['f']
    if len(filter_file) <= x or filter_file[len(filter_file)-x:].lower() != '.json':
        filter_file = brcdapi_file.full_file_name(filter_file, '.txt')
    try:
        filter_obj = json.loads(''.join(brcdapi_file.read_file(filter_file, remove_blank=True, rc=True)))
    except FileNotFoundError:
        args_f_help = ' not found.'
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    except FileExistsError:
        args_f_help = ' folder does not exist.'
    except ValueError:
        args_f_help = ' not a valid JSON file.'
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Read in the project file
    proj_file = brcdapi_file.full_file_name(args_d['i'], '.json')
    try:
        _proj_obj = brcddb_project.read_from(proj_file)
    except FileNotFoundError:
        args_i_help = ' not found'
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    except FileExistsError:
        args_i_help = ' folder does not exist.'
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Command line feedback
    ml = [os.path.basename(__file__) + ', ' + __version__,
          'Project, -i:     ' + proj_file + args_i_help,
          'filter file, -f: ' + filter_file + args_f_help,
          'Log, -log:       ' + str(args_d['log']),
          'No log, -nl:     ' + str(args_d['nl']),
          'Suppress, -sup:  ' + str(args_d['sup']),
          '',]
    brcdapi_log.log(ml, echo=True)

    if ec != brcddb_common.EXIT_STATUS_OK:
        return ec

    return psuedo_main(gen_util.convert_to_list(filter_obj))


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
