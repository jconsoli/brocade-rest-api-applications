#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2021 Jack Consoli.  All rights reserved.
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
:mod:`zone_merge` - Merges the zones from multiple fabrics

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 1.0.0     | 17 Apr 2021   | Initial launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.1     | 14 May 2021   | Use Excel credentials file rather than a CSV file for input                       |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2021 Jack Consoli'
__date__ = '14 May 2021'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '1.0.1'

import argparse
from os import listdir
from os.path import isfile
import subprocess
import collections
import brcddb.brcddb_project as brcddb_project
import brcdapi.log as brcdapi_log
import brcddb.brcddb_common as brcddb_common
import brcddb.brcddb_fabric as brcddb_fabric
import brcddb.util.compare as brcddb_compare
import brcddb.util.file as brcddb_file
import brcddb.api.interface as api_int
import brcdapi.brcdapi_rest as brcdapi_rest
import brcddb.api.zone as api_zone
import brcdapi.pyfos_auth as pyfos_auth
import brcddb.report.utils as report_utils

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = True   # When True, use _DEBUG_xxx below instead of parameters passed from the command line.
_DEBUG_i = 'zone_merge_test'
_DEBUG_p = None  # '_capture_2021_02_27/combined'
_DEBUG_t = False
_DEBUG_sup = False
_DEBUG_d = True
_DEBUG_log = '_logs'
_DEBUG_nl = False

_ZONE_KPI_FILE = '_zone_merge_kpis.txt'

_control_tables = {
    'FabricObj': {
        '/_(obj_key|project_obj|alerts|base_logins|port_map|eff_zone_objs|switch_keys|login_objs)': dict(skip=True),
        '/_(fdmi_node_objs|fdmi_port_objs|flags|port_map|flags|reserved_keys)': dict(skip=True),
        '/brocade-zone/(.*)': dict(skip=True),  # Everything in brocade-zone is already in the object
    },
    'ZoneCfgObj': {
        '/_(obj_key|project_obj|alerts|flags|fabric_key|reserved_keys)': dict(skip=True),
    },
    'ZoneObj': {
        '/_(obj_key|project_obj|alerts|flags|fabric_key|reserved_keys)': dict(skip=True),
    },
    'AliasObj': {
        '/_(obj_key|project_obj|alerts|flags|fabric_key|reserved_keys)': dict(skip=True),
    },
}

_check_d = dict(user_id='id', pw='pw', ip_addr='ip', security='sec', fabric_name='fab_name', fid='fid',
                fab_wwn='fab_wwn', cfg='cfg')  # Used in _condition_input()



def _patch_zone_db(fab_d):
    """Replaces the zoning in a fabric.

    :param fab_d: Dictionary as defined in _get_input()
    :type fab_d: dict
    :return: List of error messages. Empty list if no errors found
    :rtype: list()
    """
    rl = list()  # List of error messages to return
    base_fab_obj = fab_d['base']['fab_obj']

    for d in [obj for obj in [fab_d['base']] + fab_d['fabrics'] if obj['update']]:
        # Login
        session = api_int.login(d['id'], d['pw'], d['ip'], d['sec'], fab_d['proj_obj'])
        if pyfos_auth.is_error(session):
            rl.append(pyfos_auth.formatted_error_msg(session))
            return rl

        # Send the changes to the switch
        try:
            obj = api_zone.replace_zoning(session, base_fab_obj, d['fid'])
            if pyfos_auth.is_error(obj):
                rl.append(pyfos_auth.formatted_error_msg(obj))
        except:
            rl.append('Software fault in api_zone.replace_zoning()')

        # Logout
        obj = brcdapi_rest.logout(session)
        if pyfos_auth.is_error(obj):
            rl.append(pyfos_auth.formatted_error_msg(obj))

    return rl


def _get_project(cf, pf, d_flag, s_flag, log, nl):
    """Reads or captures project data

    :param cf: Login credentials files
    :type cf: str
    :param pf: Name of project file to read. None if not reading a project file
    :type pf: str, None
    :param d_flag: Debug flag. If True, enable debug logging
    :type d_flag: bool
    :param s_flag: Suppress printing flag. Only used if cf is not None.
    :type s_flag: bool, None
    :param log: Name of log file. Only used if cf is not None.
    :type log: str, None
    :param nl: No log flag. Only used if cf is not None.
    :type nl: bool, None
    :return: Project object. None if there was an error obtaining the project object
    :rtype: brcddb.classes.project.ProjObj
    """
    global _ZONE_KPI_FILE

    if pf is not None:  # Read the project in
        return brcddb_project.read_from(pf)

    # Capture data from live switches
    # Get a unique folder name for multi_capture.py
    folder_l = [f for f in listdir('.') if not isfile(f)]
    base_folder = '_zone_merge_work_folder'
    work_folder = base_folder
    i = 0
    while work_folder in folder_l:
        i += 1
        work_folder = base_folder + str(i)

    # Capture the data
    param = ['python.exe', 'multi_capture.py', '-i', cf, '-f', work_folder, '-c', _ZONE_KPI_FILE]
    if d_flag:
        param.append('-d')
    if s_flag:
        param.append('-sup')
    if isinstance(log, str):
        param.extend(['-log', log])
    if nl:
        param.append('-nl')
    brcdapi_log.log('Capturing switch data. This may take several seconds', True)
    ec = subprocess.Popen(param).wait()
    if ec != brcddb_common.EXIT_STATUS_OK:
        brcdapi_log.log('Data capture completed with errors.', True)
        return ec

    # Read the data back in as a project object
    brcdapi_log.log('Data capture complete. Now reading in the combined data.', True)
    return brcddb_project.read_from(work_folder+'/combined.json')


def _merge_aliases(change_d, base_fab_obj, add_fab_obj):
    """Merges the aliases from two fabrics

    :param change_d: Dictionary of alias changes as returned from brcddb.util.compare.compare()
    :type change_d: dict
    :param base_fab_obj: brcddb fabric object for the fabric we are adding the aliases from add_fab_obj to
    :type base_fab_obj: brcddb.classes.fabric.FabricObj
    :param add_fab_obj: brcddb fabric object with the aliases to be added to base_fab_obj
    :type add_fab_obj: brcddb.classes.fabric.FabricObj
    :return: Error message list. If empty, no errors encountered
    :rtype: list
    """
    # Basic prep
    rl = list()
    if change_d is None:
        return rl
    base_fab_name = brcddb_fabric.best_fab_name(base_fab_obj, True)
    add_fab_name = brcddb_fabric.best_fab_name(add_fab_obj, True)

    # Add what needs to be added or report differences
    for alias, change_obj in change_d.items():
        change_type = change_obj.get('r')
        if change_type is None or change_type == 'Changed':  # This is a simple pass/fail. No need to look further
            rl.append('Alias ' + alias + ' in ' + base_fab_name + ' does not match the same alias in ' + add_fab_name)
        elif change_type == 'Added':
            add_obj = add_fab_obj.r_alias_obj(change_obj['c'])
            base_fab_obj.s_add_alias(alias, add_obj.r_members())

    return rl


def _merge_zones(change_d, base_fab_obj, add_fab_obj):
    """Merges the zones from two fabrics

    :param change_d: Dictionary of alias changes as returned from brcddb.util.compare.compare()
    :type change_d: dict
    :param base_fab_obj: brcddb fabric object for the fabric we are adding the zones from add_fab_obj to
    :type base_fab_obj: brcddb.classes.fabric.FabricObj
    :param add_fab_obj: brcddb fabric object with the zones to be added to base_fab_obj
    :type add_fab_obj: brcddb.classes.fabric.FabricObj
    :return: Error message list. If empty, no errors encountered
    :rtype: list
    """
    # Basic prep
    rl = list()
    if change_d is None:
        return rl
    base_fab_name = brcddb_fabric.best_fab_name(base_fab_obj, True)
    add_fab_name = brcddb_fabric.best_fab_name(add_fab_obj, True)

    # Add what needs to be added or report differences
    for zone, change_obj in change_d.items():
        change_type = change_obj.get('r')
        if change_type is None or change_type == 'Changed':  # This is a simple pass/fail. No need to look further
            rl.append('Zone ' + zone + ' in ' + base_fab_name + ' does not match the same zone in ' + add_fab_name)
        elif change_type == 'Added':
            add_obj = add_fab_obj.r_zone_obj(zone)
            base_fab_obj.s_add_zone(zone, add_obj.r_type(), add_obj.r_members(), add_obj.r_pmembers())

    return rl


def _merge_zone_cfgs(change_d, base_fab_obj, add_fab_obj):
    """Merges the zone configurations from two fabrics

    Note: Theoretically, I could add zones to the base that exist in the same zone configuration but I've never seen a
    scenario where a customer wanted to merge zone configurations with the same name in two different fabrics so I just
    check to see if the members are the same.

    :param change_d: Dictionary of alias changes as returned from brcddb.util.compare.compare()
    :type change_d: dict
    :param base_fab_obj: brcddb fabric object for the fabric we are adding the zones from add_fab_obj to
    :type base_fab_obj: brcddb.classes.fabric.FabricObj
    :param add_fab_obj: brcddb fabric object with the zones to be added to base_fab_obj
    :type add_fab_obj: brcddb.classes.fabric.FabricObj
    :return: Error message list. If empty, no errors encountered
    :rtype: list
    """
    # Basic prep
    rl = list()
    if change_d is None:
        return rl
    base_fab_name = brcddb_fabric.best_fab_name(base_fab_obj, True)
    add_fab_name = brcddb_fabric.best_fab_name(add_fab_obj, True)

    # Add what needs to be added or report differences
    for zonecfg, change_obj in change_d.items():
        if zonecfg == '_effective_zone_cfg':
            continue
        change_type = change_obj.get('r')
        if change_type is None or change_type == 'Changed':  # This is a simple pass/fail. No need to look further
            rl.append('Zone configuration ' + zonecfg + ' in ' + base_fab_name +
                      ' does not match the same zone configuration in ' + add_fab_name)
        elif change_type == 'Added':
            add_obj = add_fab_obj.r_zonecfg_obj(zonecfg)
            base_fab_obj.s_add_zonecfg(zonecfg, add_obj.r_members())

    return rl


_merge_case = collections.OrderedDict()  # Used essentially as case statement actions in _merge_zone_db()
_merge_case['_alias_objs'] = _merge_aliases
_merge_case['_zone_objs']=_merge_zones
_merge_case['_zonecfg_objs']=_merge_zone_cfgs


def _merge_zone_db(fab_d):
    """Merges the zones for the fabrics specified in fab_csv

    :param fab_d: Ordered dictionary whose keys are the WWNs or user friendly names for the fabrics to merge. The value\
                  is the name of the zone configuration that should be merged. Value is None is nothing to merge.
    :type fab_d: dict
    :return rl: Error message list. If empty, no errors encountered
    :rtype rl: list
    """
    rl = list()
    proj_obj = fab_d['proj_obj']

    # Get a list of fabric objects for the fabrics to merge
    fab_l = [fab_d['base']] + fab_d['fabrics']
    for fabric_d in fab_l:
        switch_obj = proj_obj.r_switch_obj(fabric_d['fab_wwn'])
        fab_obj = brcddb_fabric.fab_obj_for_name(proj_obj, fabric_d['fab_name']) if switch_obj is None else \
            switch_obj.r_fabric_obj()
        if fab_obj is None:
            rl.append('Could not find fabric ' + fabric_d['fab_name'] + '(' + fabric_d['fab_wwn'] + ')')
        else:
            fabric_d.update(dict(fab_obj=fab_obj))
            fid_l = brcddb_fabric.fab_fids(fab_d['base']['fab_obj'])
            if len(fid_l) == 0:
                rl.append('Fabric ID (FID) not found for ' + fab_d['base']['fab_obj'].r_obj_key())
            elif len(fid_l) > 1:
                rl.append('Cannot merge fabrics in the same chassis with FID check disabled')
            else:
                fabric_d.update(dict(fid=fid_l[0]))

    # Make sure we didn't encounter any errors and at least 2 fabrics were selected
    if len(fab_l) < 2:
        rl.append('Must have at least two fabrics to merge.')
    base_fab_obj = fab_d['base']['fab_obj']
    base_zonecfg_obj = None if fab_d['base']['cfg'] is None else base_fab_obj.r_zonecfg_obj(fab_d['base']['cfg'])
    if base_zonecfg_obj is None and fab_d['base']['cfg'] is not None:
        rl.append('Could not find zone configuration ' + str(fab_d['base']['cfg']) + ' in ' +
                  brcddb_fabric.best_fab_name(base_fab_obj, True))
    if len(rl) > 0:  # Make sure we didn't encounter any errors
        return rl

    # Merge the zone databases
    for fabric_d in fab_d['fabrics']:
        fab_obj = fabric_d['fab_obj']

        # Merge the individual zone items
        change_count, change_d = brcddb_compare.compare(base_fab_obj, fab_obj, brcddb_control_tbl=_control_tables)
        for local_key, action in _merge_case.items():
            rl.extend(action(change_d.get(local_key), base_fab_obj, fab_obj))

        # Add the zones from the base fabric zone configuration to the merge fabric zone configuration and vice versa
        add_zonecfg_obj = None if fabric_d['cfg'] is None else fab_obj.r_zonecfg_obj(fabric_d['cfg'])
        if add_zonecfg_obj is None or base_zonecfg_obj is None:
            continue
        base_zonecfg_obj.s_add_member(add_zonecfg_obj.r_members())
        add_zonecfg_obj.s_add_member(base_zonecfg_obj.r_members())

    return rl


def parse_args():
    """Parses the module load command line
    
    :return: file
    :rtype: str
    """
    global _DEBUG_i, _DEBUG_p, _DEBUG_t, _DEBUG_d, _DEBUG_sup, _DEBUG_log, _DEBUG_nl

    if _DEBUG:
        return _DEBUG_i, _DEBUG_p, _DEBUG_t, _DEBUG_d, _DEBUG_sup, _DEBUG_log, _DEBUG_nl
    parser = argparse.ArgumentParser(description='Merges the zones from multiple fabrics')
    buf = 'Required. Zone merge data file. See zone_merge_sample.xlsx for details. ".xlsx" is automatically appended.'
    parser.add_argument('-i', help=buf, required=True)
    buf = 'Optional. Project file name from the output of combine.py, capture.py, or multi_capture.py Use this '\
          'instead of polling switches for zoning infromation. The extension ".json" is automatically appended.'
    parser.add_argument('-p', help=buf, required=False)
    buf = 'Optional. No parameters. Perform the merge test only. No fabric changes are made.'
    parser.add_argument('-t', help=buf, action='store_true', required=False)
    buf = 'Optional. Suppress all output to STD_IO except the exit code and argument parsing errors. Useful with '\
          'batch processing where only the exit status code is desired. Messages are still printed to the log file'\
          '. No operands.'
    parser.add_argument('-sup', help=buf, action='store_true', required=False)
    buf = '(Optional) No parameters. When set, a pprint of all content sent and received to/from the API, except ' \
          'login information, is printed to the log.'
    parser.add_argument('-d', help=buf, action='store_true', required=False)
    buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The log ' \
          'file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
    parser.add_argument('-log', help=buf, required=False, )
    buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
    parser.add_argument('-nl', help=buf, action='store_true', required=False)
    args = parser.parse_args()
    return args.i, args.p, args.t, args.sup, args.d, args.log, args.nl


def _condition_input(in_d):
    rd = dict(
        update=True if in_d.get('update') is not None and in_d['update'].lower() == 'yes' else False,
        sec='none' if in_d.get('security') is None else 'none' if in_d['security'] == '' else in_d['security']
    )
    for k, v in _check_d.items():
        rd.update({v: None if in_d.get(k) is not None and in_d.get(k) == '' else in_d.get(k)})
    return rd


def _get_input():
    """Retrieves the command line input, validates the input, and parses input into a machine usable dictionary

    Return dictionary:
    +-----------+-----------------------------------------------------------------------------------+
    | Key       | Value                                                                             |
    +===========+===================================================================================+
    | proj_obj  | Project object, brcddb.classes.project.ProjectObj                                 |
    +-----------+-----------------------------------------------------------------------------------+
    | base      | Dictionary for the base fabric as noted below.                                    |
    +-----------+-----------------------------------------------------------------------------------+
    | fabrics   | List of dictionaries as noted below for all other fabrics that are to be merged.  |
    +-----------+-----------------------------------------------------------------------------------+

    Sub-dictionary:
    +-----------+-----------------------------------------------------------------------------------+
    | Key       | Value
    +===========+===================================================================================+
    | id        | User login ID.                                                                    |
    +-----------+-----------------------------------------------------------------------------------+
    | pw        | User password                                                                     |
    +-----------+-----------------------------------------------------------------------------------+
    | ip        | IP address                                                                        |
    +-----------+-----------------------------------------------------------------------------------+
    | sec       | Security type or certificate                                                      |
    +-----------+-----------------------------------------------------------------------------------+
    | fab_name  | Fabric name                                                                       |
    +-----------+-----------------------------------------------------------------------------------+
    | fab_wwn   | Fabric WWN                                                                        |
    +-----------+-----------------------------------------------------------------------------------+
    | cfg       | Zone configuration                                                                |
    +-----------+-----------------------------------------------------------------------------------+
    | update    | bool. If True, send zoning updates to this switch.                                |
    +-----------+-----------------------------------------------------------------------------------+
    | fid       | Fabric ID                                                                         |
    +-----------+-----------------------------------------------------------------------------------+
    | fab_obj   | Fabric object, brcddb.classes.fabric.FabricObj                                    |
    +-----------+-----------------------------------------------------------------------------------+

    :return ec: Error code from brcddb.brcddb_common
    :rtype ec: int
    :return ml: Message list to print to the log
    :rtype ml: list
    :return fab_d: Dictionary as described above
    :rtype fab_d: dict
    """
    global _DEBUG, __version__

    # Initialize the return variables
    ec = brcddb_common.EXIT_STATUS_OK
    rl = ['WARNING!!! Debug is enabled'] if _DEBUG else list()
    fab_d = dict(fabrics=list())

    # Get the user input
    c_file, p_file, t_flag, s_flag, d_flag, log, nl = parse_args()
    rl.append('zone_merge.py version ' + __version__)
    rl.append('Login credential file: ' + str(c_file))
    rl.append('Project file:          ' + str(p_file))
    rl.append('Test:                  ' + str(t_flag))
    if len(c_file) < len('.xlsx') or c_file[len(c_file)-len('.xlsx'):] != '.xlsx':
        c_file += '.xlsx'  # Add the .xlsx extension to the Workbook if it wasn't specified on the command line

    # Parse the parameters file
    switch_l = report_utils.parse_parameters(sheet_name='parameters', hdr_row=1, wb_name=c_file)['content']
    if len(switch_l) > 0:
        fab_d.update(base=_condition_input(switch_l.pop(0)))
    for sub_d in switch_l:
        fab_d['fabrics'].append(_condition_input(sub_d))
    if len(fab_d['fabrics']) == 0:
        rl.append('At least two fabrics must be defined in the input file, -i.')
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Get the data
    else:
        if p_file is not None:
            if len(p_file) < len('.json') or p_file[len(p_file)-len('.json'):] != '.json':
                p_file += '.json'  # Add the .json extension if it wasn't specified on the command line
        proj_obj = _get_project(c_file, p_file, d_flag, s_flag, log, nl)
        fab_d.update(proj_obj=proj_obj)
        if proj_obj is None:
            rl.append('Error reading project file.')
            ec = brcddb_common.EXIT_STATUS_ERROR

    return ec, rl, t_flag, fab_d



def psuedo_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code. See exit codes in brcddb.brcddb_common
    :rtype: int
    """
    global _DEBUG, __version__

    ec, ml, t_flag, fab_d = _get_input()
    brcdapi_log.log(ml, True)
    if ec != brcddb_common.EXIT_STATUS_OK:
        return ec

    # Merge the zones logically
    ml = _merge_zone_db(fab_d)

    # Make the zoning changes and wrap up
    if len(ml) > 0:
        ec = brcddb_common.EXIT_STATUS_ERROR
        ml.insert(0, 'Merge test failed:')

    else:  # Make the changes
        ml.append('Zone merge test succeeded')
        if not t_flag:
            tl = _patch_zone_db(fab_d)
            if len(tl) > 0:
                ec = brcddb_common.EXIT_STATUS_ERROR
            ml.extend(tl)

    brcdapi_log.log(ml, True)

    return ec


##################################################################
#
#                    Main Entry Point
#
###################################################################

# Read in the project file from which the report is to be created and convert to a project object
# Create project

_ec = brcddb_common.EXIT_STATUS_OK
if _DOC_STRING:
    brcdapi_log.close_log('_DOC_STRING is True. No processing', True)
else:
    _ec = psuedo_main()
    brcdapi_log.close_log(str(_ec), True)
exit(_ec)
