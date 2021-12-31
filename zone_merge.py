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
    | 1.0.2     | 17 Jul 2021   | Fixed error when specified project file does not exist.                           |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.3     | 07 Aug 2021   | Misc. fixes & removed fabric by name.                                             |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.4     | 14 Aug 2021   | Fixed new zone configuration not getting activated.                               |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.5     | 21 Aug 2021   | Added ability to generate CLI for zone changes                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.6     | 31 Dec 2021   | Use brcddb.util.file.full_file_name()                                             |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2021 Jack Consoli'
__date__ = '31 Dec 2021'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '1.0.6'

import argparse
import sys
import datetime
import os
from os.path import isfile
import subprocess
import collections
import brcdapi.log as brcdapi_log
import brcdapi.fos_auth as fos_auth
import brcdapi.brcdapi_rest as brcdapi_rest
import brcdapi.util as brcdapi_util
import brcddb.brcddb_project as brcddb_project
import brcddb.brcddb_common as brcddb_common
import brcddb.brcddb_fabric as brcddb_fabric
import brcddb.util.compare as brcddb_compare
import brcddb.api.interface as api_int
import brcddb.api.zone as api_zone
import brcddb.report.utils as report_utils
import brcddb.util.file as brcddb_file
import brcddb.util.copy as brcddb_copy
import brcddb.util.util as brcddb_util

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = False   # When True, use _DEBUG_xxx below instead of parameters passed from the command line.
_DEBUG_i = 'zone_merge_test'
_DEBUG_cfg = None  # 'combined_cfg'
_DEBUG_a = False
_DEBUG_t = False
_DEBUG_scan = False
_DEBUG_cli = False
_DEBUG_sup = False
_DEBUG_d = False
_DEBUG_log = '_logs'
_DEBUG_nl = False

_kpis_for_capture = ('brocade-fibrechannel-switch/fibrechannel-switch',
                     'brocade-interface/fibrechannel',
                     'brocade-zone/defined-configuration',
                     'brocade-zone/effective-configuration',
                     'brocade-fibrechannel-configuration/zone-configuration',
                     'brocade-fibrechannel-configuration/fabric')
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

# Used in _condition_input() to translate column header names in the Workbook to input names used by capture.py
_check_d = dict(user_id='id', pw='pw', ip_addr='ip', security='sec', fid='fid', fab_wwn='fab_wwn', cfg='cfg')

def _zone_cli(proj_obj):
    """Prints the zoning commands to the log

    :param proj_obj: Project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :return: List of CLI commands
    :rtype: list
    """
    rl = ['', '# To avoid input buffer overflow, copy and paste 20 commands at a time']
    zd = proj_obj.r_get('zone_merge')
    if not isinstance(zd, dict):
        return rl  # This is just belt and suspenders. We should never get here.
    base_fab_obj = zd.get('base_fab_obj')
    for fab_obj in proj_obj.r_fabric_objects():
        zd = fab_obj.r_get('zone_merge')
        if zd is not None:
            rl.extend(brcddb_util.zone_cli(base_fab_obj, fab_obj))

    return rl


def _scan_fabrics(proj_obj):
    """Scan the project for each fabric and list the fabric WWN, FID , and zone configurations

    :param proj_obj: Project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :return: List of fabric detail messages
    :rtype: list
    """

    # Prepare the fabric display
    ml = ['', 'Fabric Scan (* indicates the effective zone config)', '']
    for fab_obj in proj_obj.r_fabric_objects():
        eff_zonecfg = fab_obj.r_defined_eff_zonecfg_key()
        ml.append('From: ' + fab_obj.r_get('zone_merge/file'))
        ml.append(brcddb_fabric.best_fab_name(fab_obj, wwn=True))
        ml.append('  FID:         ' + ', '.join([str(fid) for fid in brcddb_fabric.fab_fids(fab_obj)]))
        for buf in fab_obj.r_zonecfg_keys():
            if isinstance(eff_zonecfg, str) and eff_zonecfg == buf:
                ml.append('  Zone Config: ' + '*' + buf)
            elif buf != '_effective_zone_cfg':
                ml.append('  Zone Config: ' + buf)
        ml.append('')

    return ml


def _patch_zone_db(proj_obj, eff_cfg):
    """Replaces the zoning in the fabric(s).

    :param proj_obj: Project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :param eff_cfg: Name of zone configuration to activate. None if no zone configuration to activate.
    :type eff_cfg: str, None
    :return: List of error messages. Empty list if no errors found
    :rtype: list()
    """
    rl = list()  # List of error messages to return
    base_fab_obj = proj_obj.r_get('zone_merge/base_fab_obj')
    if base_fab_obj is None:
        rl.append('base_fab_obj is None')  # There is a code bug if this happens
        return rl

    update_count = 0
    for fab_obj in proj_obj.r_fabric_objects():

        # Get the login credentials
        ip_addr = fab_obj.r_get('zone_merge/ip')
        id = fab_obj.r_get('zone_merge/id')
        pw = fab_obj.r_get('zone_merge/pw')
        sec = fab_obj.r_get('zone_merge/sec')
        fid = fab_obj.r_get('zone_merge/fid')
        update = fab_obj.r_get('zone_merge/update')
        if ip_addr is None or id is None or pw is None or sec is None or fid is None or update is None or not update:
            continue

        # Login
        session = api_int.login(id, pw, ip_addr, sec, proj_obj)
        if fos_auth.is_error(session):
            rl.append(fos_auth.formatted_error_msg(session))
            return rl

        # Send the changes to the switch
        brcdapi_log.log('Sending zone updates to ' + brcddb_fabric.best_fab_name(fab_obj, wwn=True), True)
        try:
            obj = api_zone.replace_zoning(session, base_fab_obj, fid)
            if fos_auth.is_error(obj):
                rl.append(fos_auth.formatted_error_msg(obj))
            else:
                update_count += 1
                if isinstance(eff_cfg, str):
                    obj = api_zone.enable_zonecfg(session, None, fid, eff_cfg)
                    if fos_auth.is_error(obj):
                        rl.append(fos_auth.formatted_error_msg(obj))
        except:
            rl.append('Software fault in api_zone.replace_zoning()')

        # Logout
        obj = brcdapi_rest.logout(session)
        if fos_auth.is_error(obj):
            rl.append(fos_auth.formatted_error_msg(obj))

        brcdapi_log.log(str(update_count) + ' switch(es) updated.', True)

    return rl


def _get_project(sl, pl, addl_parms):
    """Reads or captures project data

    :param sl: List of switches to poll via the API
    :type sl: list
    :param pl: List of project files to combine
    :type pl: list
    :param addl_parms: Additional parameters (debug and logging) to be passed to capture.py.
    :type addl_parms: list
    :return rl: List of error messages
    :rtype: list
    :return proj_obj: Project object. None if there was an error obtaining the project object
    :rtype proj_obj: brcddb.classes.project.ProjObj, None
    """
    global _ZONE_KPI_FILE

    rl = list()  # Error messages

    # Create project
    proj_obj = brcddb_project.new('zone_merge', datetime.datetime.now().strftime('%d %b %Y %H:%M:%S'))
    proj_obj.s_python_version(sys.version)
    proj_obj.s_description('Zone merge')

    # Get a unique folder name for multi_capture.py and combine.py
    folder_l = [f for f in os.listdir('.') if not isfile(f)]
    base_folder = '_zone_merge_work_folder_'
    i = 0
    work_folder = base_folder + str(i)
    while work_folder in folder_l:
        i += 1
        work_folder = base_folder + str(i)
    os.mkdir(work_folder)

    # Add the KPI file for the captures
    zone_kpi_file = work_folder + '/' + _ZONE_KPI_FILE
    f = open(zone_kpi_file, 'w')
    f.write('\n'.join(_kpis_for_capture) + '\n')
    f.close()

    # Start all the data captures for the switches to be polled so that multiple switches can be captured in parallel
    if len(sl) > 0:
        brcdapi_log.log('Collecting zoning data from switches', True)
    captured_d = dict()
    pid_l = list()
    for sub_d in sl:
        ip_addr = sub_d['ip']
        file_name = work_folder + '/switch_' + ip_addr.split('.').pop() + '_' + str(len(pid_l))
        sub_d.update(dict(file=file_name))
        file_name = brcddb_file.full_file_name(file_name, '.json')
        d = captured_d.get(ip_addr)
        if d is None:
            sub_d_l = list()
            captured_d.update({ip_addr: dict(sub_d_l=sub_d_l, file=file_name)})
            params = ['python.exe',
                      'capture.py',
                      '-ip', ip_addr,
                      '-id', sub_d['id'],
                      '-pw', sub_d['pw'],
                      '-s', sub_d['sec'],
                      '-f', file_name,
                      '-c', zone_kpi_file] + addl_parms
            pid_l.append(dict(p=subprocess.Popen(params), file_name=file_name, ip=ip_addr))
        sub_d_l.append(sub_d)

    # Add the data read from this chassis to the project object
    for pid_d in pid_l:  # Wait for all captures to complete before continuing
        pid_d.update(dict(s=pid_d['p'].wait()))
        brcdapi_log.log('Completed capture for ' + pid_d['file_name'] + '. Ending status: ' + str(pid_d['s']), True)
    for pid_d in pid_l:
        obj = brcddb_file.read_dump(pid_d['file_name'])
        if obj is None:
            rl.append('Capture for ' + file_name + '. failed.')
        else:
            brcddb_copy.plain_copy_to_brcddb(obj, proj_obj)
            captured_d[pid_d['ip']].update(dict(fab_keys=obj['_fabric_objs'].keys()))
    if len(rl) > 0:
        return rl, proj_obj

    # Figure out the fabric WWN for all the FIDs for the polled switches
    for d in captured_d.values():
        fab_obj_l = [proj_obj.r_fabric_obj(k) for k in d['fab_keys']]
        for fab_obj in fab_obj_l:
            if fab_obj.r_get('zone_merge') is None:  # I can't think of a reason why it wouldn't be None
                fab_obj.s_new_key('zone_merge', dict(file=d['file']))
        for sub_d in d['sub_d_l']:
            found = False
            fid = sub_d['fid']
            if isinstance(fid, int):  # If the user is just running a scan, there won't be a fid
                for fab_obj in fab_obj_l:
                    if fid in brcddb_fabric.fab_fids(fab_obj):
                        zm_d = fab_obj.r_get('zone_merge')
                        zm_d.update(dict(fab_wwn=fab_obj.r_obj_key(),
                                         update=sub_d['update'],
                                         cfg=sub_d['cfg'],
                                         fid=sub_d['fid'],
                                         ip=sub_d['ip'],
                                         id=sub_d['id'],
                                         pw=sub_d['pw'],
                                         sec=sub_d['sec']))
                        fab_obj.s_new_key('zone_merge', zm_d)
                        found = True
                        break
                if not found:
                    rl.append('Could not find FID ' + str(fid) + ' in ' + brcdapi_util.mask_ip_addr(sub_d['ip']))

    # Add in all the read in project files
    if len(pl) > 0:
        brcdapi_log.log('Reading project files', True)
    for sub_d in pl:
        file_name = brcddb_file.full_file_name(sub_d['project_file'], '.json')
        obj = brcddb_file.read_dump(file_name)
        brcddb_copy.plain_copy_to_brcddb(obj, proj_obj)
        for fab_obj in [proj_obj.r_fabric_obj(k) for k in obj['_fabric_objs'].keys()]:
            if fab_obj.r_get('zone_merge') is None:  # It should be None. This is just future proofing.
                fab_obj.s_new_key('zone_merge', dict(file=file_name))
        fab_obj = proj_obj.r_fabric_obj(sub_d.get('fab_wwn'))
        if fab_obj is None:
            rl.append('Could not find fabric WWN ' + str(sub_d.get('fab_wwn')) + ' in ' + file_name)
        else:
            fab_obj.r_get('zone_merge').update(dict(fab_wwn=fab_obj.r_obj_key(), update=False, cfg=sub_d['cfg']))

    return rl, proj_obj


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

    # Add what needs to be added or report differences
    for zonecfg, change_obj in change_d.items():
        if zonecfg != '_effective_zone_cfg':
            change_type = change_obj.get('r')
            if isinstance(change_type, str) and change_type == 'Added':
                add_obj = add_fab_obj.r_zonecfg_obj(zonecfg)
                base_fab_obj.s_add_zonecfg(zonecfg, add_obj.r_members())

    return rl


_merge_case = collections.OrderedDict()  # Used essentially as case statement actions in _merge_zone_db()
_merge_case['_alias_objs'] = _merge_aliases
_merge_case['_zone_objs'] = _merge_zones
_merge_case['_zonecfg_objs'] = _merge_zone_cfgs


def _merge_zone_db(proj_obj, new_zone_cfg, a_flag):
    """Merges the zones for the fabrics specified in fab_csv

    :param proj_obj: Project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :param new_zone_cfg: Name of zone configuration to add
    :type new_zone_cfg: str, None
    :param a_flag: If True, make new_zone_cfg the effective zone configuration
    :type a_flag: bool
    :return rl: Error message list. If empty, no errors encountered
    :rtype rl: list
    """
    rl = list()

    # Find a fabric to start with, base_fab_obj, and get a list of the remaining fabrics to add to it.
    fab_l = list()
    base_fab_obj = None
    new_zonecfg_obj = None
    for fab_obj in proj_obj.r_fabric_objects():
        zd = fab_obj.r_get('zone_merge')  # zd should never be None. This is just future proofing.
        if zd is None or zd.get('fab_wwn') is None:
            continue
        if base_fab_obj is None:
            base_fab_obj = brcddb_fabric.copy_fab_obj(fab_obj, fab_key=None, full_copy=False)
            if isinstance(new_zone_cfg, str):
                mem_l = list()
                if isinstance(zd['cfg'], str):
                    zonecfg_obj = fab_obj.r_zonecfg_obj(zd['cfg'])
                    if zonecfg_obj is None:
                        rl.append('Could not find ' + zd['cfg'] + ' in ' +
                                  brcddb_fabric.best_fab_name(fab_obj, wwn=True))
                    else:
                        mem_l = zonecfg_obj.r_members()
                if isinstance(new_zone_cfg, str):
                    new_zonecfg_obj = base_fab_obj.s_add_zonecfg(new_zone_cfg, mem_l)
            brcddb_util.add_to_obj(proj_obj, 'zone_merge/base_fab_obj', base_fab_obj)
        else:
            fab_l.append(fab_obj)
    if base_fab_obj is None:
        rl.append('Could not find a fabric containing any of the specified zone configurations.')
    if len(fab_l) < 1:
        rl.append('Could not find any fabrics to merge. Must have at least 2.')
    if len(rl) > 0:
        return rl

    # Merge the individual zone items
    for fab_obj in fab_l:
        change_count, change_d = brcddb_compare.compare(base_fab_obj, fab_obj, brcddb_control_tbl=_control_tables)
        for local_key, action in _merge_case.items():
            rl.extend(action(change_d.get(local_key), base_fab_obj, fab_obj))

        # Add the zones to the merged zone configuration
        zd = fab_obj.r_get('zone_merge')  # zd should never be None. This is just future proofing.
        if new_zonecfg_obj is None or zd is None or zd.get('cfg') is None:
            continue
        add_zonecfg_obj = fab_obj.r_zonecfg_obj(zd.get('cfg'))
        if add_zonecfg_obj is not None:
            new_zonecfg_obj.s_add_member(add_zonecfg_obj.r_members())

    # If the new zone configuration is to be enabled, set it as the effective zone configuration
    if a_flag:
        base_fab_obj.s_del_eff_zonecfg()
        base_fab_obj.s_add_eff_zonecfg(new_zonecfg_obj.r_members())

    return rl


def parse_args():
    """Parses the module load command line
    
    :return: file
    :rtype: str
    """
    global _DEBUG, _DEBUG_i, _DEBUG_cfg, _DEBUG_a, _DEBUG_t, _DEBUG_scan, _DEBUG_cli, _DEBUG_d, _DEBUG_sup, _DEBUG_log
    global _DEBUG_nl

    if _DEBUG:
        return _DEBUG_i, _DEBUG_cfg, _DEBUG_a, _DEBUG_t, _DEBUG_scan, _DEBUG_cli, _DEBUG_d, _DEBUG_sup, _DEBUG_log, \
               _DEBUG_nl
    buf = 'The zone_merge utility merges the zone databases from two or more fabrics by reading the zone database from'\
          ' a project file or a live switch.'
    parser = argparse.ArgumentParser(description=buf)
    buf = 'Required. Zone merge data file. See zone_merge_sample.xlsx for details. ".xlsx" is automatically appended.'
    parser.add_argument('-i', help=buf, required=True)
    buf = 'Optional. Typically, when merging fabrics it’s desired to have one new zone configuration that will be used'\
          'as the final zone configuration. Use this option to specify the name of the new zone configuration to be '\
          'created. Included in this zone configuration are all the zones specified in the "cfg" column in the '\
          'workbook specified with the -i option.'
    parser.add_argument('-cfg', help=buf, required=False)
    buf = 'Optional. No parameters. Activates the zone configuration specified with the -cfg option.'
    parser.add_argument('-a', help=buf, action='store_true', required=False)
    buf = 'Optional. No parameters. Perform the merge test only. No fabric changes are made.'
    parser.add_argument('-t', help=buf, action='store_true', required=False)
    buf = 'Optional. No parameters. Scan switches and files for fabric information.'
    parser.add_argument('-scan', help=buf, action='store_true', required=False)
    buf = 'Optional. No parameters. Prints the zome merge CLI commands to the log and console.'
    parser.add_argument('-cli', help=buf, action='store_true', required=False)
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
    return args.i, args.cfg, args.a, args.t, args.scan, args.d, args.cli, args.sup, args.log, args.nl


def _condition_input(in_d):
    rd = dict(
        update=True if in_d.get('update') is not None and in_d['update'].lower() == 'yes' else False,
        sec='none' if in_d.get('security') is None else 'none' if in_d['security'] == '' else in_d['security']
    )
    for k, v in _check_d.items():
        key_val = in_d.get(k)
        rd.update({v: None if key_val is not None and key_val == '' else key_val})
    return rd


def _get_input():
    """Retrieves the command line input, reads the input Workbook, and validates the input

    :return ec: Error code from brcddb.brcddb_common
    :rtype ec: int
    :return sl: List of switches to poll as read from the input Workbook
    :rtype sl: list
    :return pl: List of project files to combine
    :rtype pl: list
    :return cfg_name: Name of zone configuration file to create
    :rtype cfg_name: str, None
    :return a_cfg: Activation flag. If True, activate the zone configuration specified by cfg_name
    :rtype a_cfg: bool
    :return t_flag: Test flag. If True, test only. Do not make any changes
    :rtype t_flag: bool
    :return scan_flag: Scan flag. If True, scan files and switches for fabric information
    :rtype scan_flag: bool
    :return cli_flag: If True, generate CLI
    :rtype cli_flag: bool
    :return addl_parms: Additional parameters (logging and debug flags) to pass to multi_capture.py
    :rtype addl_parms: list
    """
    global _DEBUG, __version__

    # Initialize the return variables
    ec = brcddb_common.EXIT_STATUS_OK
    sl = list()
    pl = list()
    addl_parms = list()

    # Get the user input
    c_file, cfg_name, a_flag, t_flag, scan_flag, cli_flag, d_flag, s_flag, log, nl = parse_args()
    if s_flag:
        addl_parms.append('-sup')
        brcdapi_log.set_suppress_all()
    if nl:
        addl_parms.append('-nl')
    else:
        brcdapi_log.open_log(log)
    if log is not None:
        addl_parms.extend(['-log', log])
    if d_flag:
        addl_parms.append('-d')
        brcdapi_rest.verbose_debug = True
    ml = ['WARNING!!! Debug is enabled'] if _DEBUG else list()
    ml.append('zone_merge.py version: ' + __version__)
    ml.append('Login credential file: ' + str(c_file))
    ml.append('Common zone cfg name:  ' + str(cfg_name))
    ml.append('Activate zone cfg:     ' + str(a_flag))
    ml.append('Scan flag, -scan:      ' + str(scan_flag))
    ml.append('CLI flag, -cli:        ' + str(cli_flag))
    ml.append('Test:                  ' + str(t_flag))
    brcdapi_log.log(ml, True)
    c_file = brcddb_file.full_file_name(c_file, '.xlsx')

    # Parse the input file
    ml = list()
    switch_l = report_utils.parse_parameters(sheet_name='parameters', hdr_row=0, wb_name=c_file)['content']
    if a_flag and not isinstance(cfg_name, str):
        ml.append('Configuration activate flag, -a, specified without a valid zone configuration name, -cfg')
    if len(ml) == 0:
        for i in range(0, len(switch_l)):
            sub_d = switch_l[i]
            buf = sub_d.get('project_file')
            if buf is None:
                sl.append(_condition_input(sub_d))
            else:
                pl.append(sub_d)
                if not scan_flag and not brcddb_util.is_wwn(sub_d.get('fab_wwn'), full_check=True):
                    ml.append('fab_wwn is not a valid WWN in row ' + str(i+1))
    if len(ml) > 0:
        brcdapi_log.log(ml, True)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    return ec, sl, pl, cfg_name, a_flag, t_flag, scan_flag, cli_flag, addl_parms


def pseudo_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code. See exit codes in brcddb.brcddb_common
    :rtype: int
    """
    global __version__

    ec, sl, pl, cfg_name, a_flag, t_flag, scan_flag, cli_flag, addl_parms = _get_input()
    if ec != brcddb_common.EXIT_STATUS_OK:
        return ec

    # Capture the zoning data
    ml, proj_obj = _get_project(sl, pl, addl_parms)

    if scan_flag and proj_obj is not None:
        brcdapi_log.log(_scan_fabrics(proj_obj), True)
        return brcddb_common.EXIT_STATUS_OK
    if len(ml) > 0:
        brcdapi_log.log(ml, True)
        return brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Merge the zones logically
    ml = _merge_zone_db(proj_obj, cfg_name, a_flag)
    if len(ml) > 0:
        ml.insert(0, 'Merge test failed:')
        brcdapi_log.log(ml, True)
        ec = brcddb_common.EXIT_STATUS_ERROR

    else:
        # Make the changes
        ml.append('Zone merge test succeeded')
        if not t_flag:
            tl = _patch_zone_db(proj_obj, cfg_name if a_flag else None)
            if len(tl) > 0:
                ec = brcddb_common.EXIT_STATUS_ERROR
            else:
                ml.append('Zone merge complete: 0 errors.')
            ml.extend(tl)

    if cli_flag:
        ml.extend(_zone_cli(proj_obj))

    brcdapi_log.log(ml, True)

    return ec


##################################################################
#
#                    Main Entry Point
#
###################################################################
if _DOC_STRING:
    print('_DOC_STRING is True. No processing')
    exit(brcddb_common.EXIT_STATUS_OK)

_ec = pseudo_main()
brcdapi_log.close_log('Processing complete. Exit status: ' + str(_ec))
exit(_ec)
