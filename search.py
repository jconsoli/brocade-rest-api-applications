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
:mod:`search` - Contains several examples of how to perform searches of the brcddb objects

This module illustrates how to use the searching and built in reporting features of the brcddb libraries. Some of the
examples are practical but the primary intent is to illustrate how to use the tools. It is set up to make it easy to
pick examples of interest either to simply look at the output or to set break points to examine the code and data.
Unless edited for a specific function, as a stand-alone utility this module serves no useful purpose.

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 1.x.x     | 03 Jul 2019   | Experimental                                                                      |
    | 2.x.x     |               |                                                                                   |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.0     | 19 Jul 2020   | Initial Launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.1     | 09 Jan 2021   | Open log file.                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.2     | 13 Feb 2021   | Added # -*- coding: utf-8 -*- and some PEP8 cleanup                               |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.3     | 14 Nov 2021   | Perform search from a JSON                                                        |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2019, 2020, 2021 Jack Consoli'
__date__ = '14 Nov 2021'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '3.0.3'

import argparse
import json
import brcddb.brcddb_project as brcddb_project
import brcdapi.log as brcdapi_log
import brcddb.brcddb_common as brcddb_common
import brcddb.util.file as brcddb_file
import brcddb.util.search as brcddb_search
import brcddb.util.obj_convert as brcddb_conv
import brcddb.report.utils as report_utils
import brcddb.report.chassis as report_chassis
import brcddb.report.fabric as report_fabric
import brcddb.report.login as report_login
import brcddb.report.port as report_port
import brcddb.report.switch as report_switch
import brcddb.report.zone as report_zone

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = False  # When True, use the values below instead of reading from the command line
_DEBUG_i = 'test/test_capture'
_DEBUG_f = 's/slow_logins'
_DEBUG_eh = False
_DEBUG_log = '_logs'
_DEBUG_nl = False

_inf = 'vz_sac/vz_sac_capture.json'
_outf = 'vz_sac/vz_slow_login.xlsx'      # This where the results will be written
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
    'def_report  dict  Defines the output report as follows',
    '',
    '    name  str   Name of the Excel workbook. ".xlsx" is automatically',
    '                appended.',
    '',
    '    xxxx  list  Where "xxxx" is a user defined report display format. The',
    '                value is a list of object keys to display. This list is passed',
    '                directly to the report page methods in brcddb.report',
    '',
    'object      str   The search.py utility maintains a list of brcddb objects to',
    '                  operate on. It is preloaded with the project object defined',
    '                  with the -i parameter. Objects are extracted/converted with',
    '                  this option by specifying one of the simple object types in',
    '                  brcddb.classes.util.simple_class_type',
    '',
    'report      dict  Instructs search.py to insert a worksheet into the workbook',
    '                  as follows:',
    '',
    '    disp    str   Optional. Must be one of the predefined display options,',
    '                  see "xxxx" in "def_report". If omitted, the default display',
    '                  for the object type is used.',
    '',
    '    index   int   Optional. Sheet index where the worksheet is to be inserted.',
    '                  If omitted, the default is 0.',
    '',
    '    name    str   Required. Name of the worksheet',
    '',
    '    title   str   Optional. Title to be inserted at the top of the worksheet',
    '',
    '    type  str   The type of report (worksheet) to generate as follows:',
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

_port_disp_tbl = (
    # '_PORT_COMMENTS',
    '_SWITCH_NAME',
    '_PORT_NUMBER',
    'fibrechannel/fcid-hex',
    'fibrechannel/operational-status',
    '_BEST_DESC',
    '_search/speed',
    '_search/remote_sfp_max_speed',
    '_search/sfp_max_speed',
)


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
        brcdapi_log.log('Creating ' + buf + ': ' + sheet_name, True)
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
def _report_alias_act(obj, disp):
    # brcddb.report.zone.alias_page()
    print("_report_act_alias")


def _report_chassis_act(obj, disp):
    report_chassis.chassis_page()
    print("_report_chassis_act")


def _report_fabric_act(obj, disp):
    report_fabric.fabric_page()
    print("_report_fabric_act")


def _report_login_act(obj, disp):
    report_login.login_page()
    print('_report_login_act')


def _report_ntarget_act(obj, disp):
    report_zone.non_target_zone_page()
    print('_report_ntarget_act')


def _report_port_act(obj, disp):
    global _wb, _working_obj_l, _report_display
    report_port.port_page(_wb, None, obj.get('name'), obj.get('index'), obj.get('title'), _working_obj_l, disp)


def _report_switch_act(obj, disp):
    report_switch.switch_page()
    print('_report_switch_act')


def _report_target_act(obj, disp):
    report_zone.zone.target_zone_page()
    print('_report_target_act')


def _report_zone_act(obj, disp):
    report_zone.zone_page()
    print('_report_zone_act')


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
        return  # Appropriate error message is returned in _has_sheet_name
    _wb = report_utils.new_report()
    for k, v in obj.items():
        if k == 'name':
            _report_name = v + '.xlsx' if len(v) < len('.xlsx') or v[len(v)-len('.xlsx'):].lower() != '.xlsx' else v
        else:
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
        try:
            _report_action_d[obj.get('type')](obj, report_disp)
        except (TypeError) as e:
            brcdapi_log.log('Invalid "type",' + str(obj.get('type')) + ' in "report" action', True)



def _test_act(obj):
    global _working_obj_l

    _working_obj_l = brcddb_search.match_test(_working_obj_l, obj)
    return


_action_d = dict(
    def_report=_def_report_act,
    object=_object_act,
    report=_report_act,
    test=_test_act,
)


def _read_file(file):
    """Reads in a JSON formated file

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
    global _DEBUG, _DEBUG_i, _DEBUG_f, _DEBUG_eh, _DEBUG_log, _DEBUG_nl

    proj_obj, filter_obj, ml, ec = None, None, list(), brcddb_common.EXIT_STATUS_OK

    if _DEBUG:
        proj_file, filter_file, eh, log_file, log_nl = _DEBUG_i, _DEBUG_f, _DEBUG_eh, _DEBUG_log, _DEBUG_nl
        ml.append('WARNING!!! Debug is enabled')
    else:
        parser = argparse.ArgumentParser(description='Convert supportshow output to equivalent capture output.')
        parser.add_argument('-i', help='Required. Name of project file. ".json" is automatically appended',
                            required=False)
        buf = 'Required. Name of filter file. ".txt" is automatically appended. Invoke with the -eh option for '\
              'additional help'
        parser.add_argument('-f', help=buf, required=False)
        buf = 'Optional. No parameters. When specified, extended help for the filter file, -f, is displayed and '\
              'processing is terminated.'
        parser.add_argument('-eh', help=buf, action='store_true', required=False)
        buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The ' \
              'log file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
        parser.add_argument('-log', help=buf, required=False,)
        buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
        parser.add_argument('-nl', help=buf, action='store_true', required=False)
        args = parser.parse_args()

        proj_file, filter_file, eh, log_file, log_nl = args.i, args.f, args.eh, args.log, args.nl

    if not log_nl:
        brcdapi_log.open_log(log_file)
    if eh:
        ml.extend(_eh)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    else:
        if not isinstance(proj_file, str):
            ml.append('Missing project file, -i')
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
        if not isinstance(filter_file, str):
            ml.append('Missing filter file, -f')
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    if ec == brcddb_common.EXIT_STATUS_OK:
        # Add extension to the file names
        buf = proj_file.lower()
        x = len(buf)
        proj_file = proj_file if x > len('.json') and buf[x-len('.json'):] == '.json' else proj_file + '.json'
        buf = filter_file.lower()
        x = len(buf)
        filter_file = filter_file if x > len('.txt') and buf[x-len('.txt'):] == '.txt' else filter_file + '.txt'
        ml.append('Project, -i:     ' + str(proj_file))
        ml.append('filter file, -f: ' + str(filter_file))

        # Read in the project file
        try:
            proj_obj = brcddb_project.read_from(proj_file)
        except FileNotFoundError:
            ml.append('Project file, ' + proj_file + ', not found')
            ec = brcddb_common.EXIT_STATUS_ERROR
        if proj_obj is None:
            ec = brcddb_common.EXIT_STATUS_ERROR
        else:
            brcddb_project.build_xref(proj_obj)
            brcddb_project.add_custom_search_terms(proj_obj)

        # Read in the filter file
        try:
            filter_obj = json.loads(''.join(brcddb_file.read_file(filter_file, remove_blank=True, rc=True)))
        except FileNotFoundError:
            ml.append('Filter file, ' + filter_file + ', not found')
            ec = brcddb_common.EXIT_STATUS_ERROR
        except ValueError:
            ml.append('Improperly formatted JSON in ' + filter_file)
            ec = brcddb_common.EXIT_STATUS_ERROR

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
        report_utils.save_report(_wb, _report_name)

    return brcddb_common.EXIT_STATUS_OK

##################################################################
#
#                    Main Entry Point
#
###################################################################


_ec = brcddb_common.EXIT_STATUS_OK
if _DOC_STRING:
    brcdapi_log.close_log('_DOC_STRING is True. No processing', True)
else:
    _ec = psuedo_main()
    brcdapi_log.close_log(str(_ec), True)
exit(_ec)
