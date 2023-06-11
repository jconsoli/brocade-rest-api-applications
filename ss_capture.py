#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019, 2020, 2021 Broadcom Communications, Inc.  All rights reserved.
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
:mod:`ss_capture` - Simulates multi_capture.py by reading and parsing supportshow files

**Description**

Parses the output of supportshow and equivalent supportshow output from supportDecode.pl. Captured data is limited to:

    * All zoning information
    * Name server information
    * Basic switch configuration information
    * Basic port configuration information
    * Port statistics
    * Local media (SFP) information. No RDP information
    * Port RNID data

The only thing different between this script and parsing data from a SAN Health report, sh_capture.py, is that peer
zoning information is read.

**Required libraries**

    From: https://github.com/jconsoli

    brcdapi
    brcddb

**supportshow and supportsave notes**

    * switch.login.enforce_login does not appear in supportshow output, only the output of supportdecode.pl
    * FabricID:x is always FabricID:128 in supportsave, even when there isn't a FID 128
    * Although switch.login.enforce_login appears for each logical switch, since FabricID is used to determine the
      the logical switch in the configuration area and FabricID is the only thing used in the configuration area to
      determine the logical switch, there is no reasonable way to determine which logical switch the
      switch.login.enforce_login is associated with.

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 3.0.0     | 22 Aug 2020   | Initial Launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.1     | 28 Aug 2020   | Missed checks with supportsave                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.2     | 02 Sep 2020   | PEP 8 cleanup                                                                      |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.3     | 29 Sep 2020   | Added chassis parsing and fixed TX Power                                          |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.4     | 13 Mar 2021   | Used ReGex matching from brcddb.util.util. Removed private methods to manipulate  |
    |           |               | dictionaries and replaced with calls to equivalent methods in brcddb.util.util    |
    |           |               | Added # -*- coding: utf-8 -*-                                                     |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.5     | 31 Oct 2022   | Prepended tag with '0x', look for defzone, add standard zone type                 |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.6     | 01 Jun 2023   | Updated documentation only                                                        |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2019, 2020, 2021 Broadcom Communications, Inc.'
__date__ = '01 Jun 2023'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '3.0.6'

import argparse
import datetime
import sys
import brcdapi.log as brcdapi_log
import brcdapi.gen_util as gen_util
import brcdapi.file as brcdapi_file
import brcddb.brcddb_common as brcddb_common
import brcddb.brcddb_project as brcddb_project
import brcddb.brcddb_chassis as brcddb_chassis
import brcddb.util.copy as brcddb_copy
import brcddb.util.util as brcddb_util
import brcddb.util.parse_cli as parse_cli

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = False  # When True, use _DEBUG_ss and _DEBUG_o instead of passed arguments
_DEBUG_ss = 'dtcc_test/ss'
_DEBUG_o = 'dtcc_test/dtcc_test'
_DEBUG_sd = None
_DEBUG_log = '_logs'
_DEBUG_nl = False

_working_proj_obj = None
_working_chassis_obj = None
_working_fabric_obj = None
_working_switch_obj = None
_parsed_ss = list()
_fid = 0  # Last known FID
_content = list()  # supportshow output in list format
_BF_FS = 'brocade-fabric/fabric-switch/'


class Found(Exception):
    pass

###################################################################
#
#                    Common Methods
#
###################################################################


def _check_fid(buf):
    """Updates the global FID, _fid, and working objects if necessary

    :param buf: Text line from supportshow
    :type buf: str
    :return: True if context changed
    :rtype: bool
    """
    global _fid, _working_chassis_obj, _working_fabric_obj, _working_switch_obj

    if len(buf) >= len('CURRENT CONTEXT') and buf[0: len('CURRENT CONTEXT')] == 'CURRENT CONTEXT':
        if 'FID: ' in buf:
            _fid = int(gen_util.non_decimal.sub('', buf[buf.index('FID: '):].split(' ')[1]))
        else:
            _fid = int(buf.strip().split(' ').pop())
        _working_switch_obj = _working_chassis_obj.r_switch_obj_for_fid(_fid)
        if _working_switch_obj is not None:
            _working_fabric_obj = _working_switch_obj.r_fabric_obj()
        return True

    return False


def _find_in(content, search_term, start_i=0):
    """Returns the index into content where the first occurrence of search_term is found.

    :param content: List of text to parse
    :type content: list
    :param search_term: Term to search for
    :type search_term: str
    :param start_i: Index where to start searching
    :type start_i: int
    :return: Index, relative to content, where the search term was found. None if not found
    :rtype: int, None
    """
    for ri in range(start_i, len(content)):
        buf = content[ri]
        _check_fid(buf)
        if search_term in buf:
            return ri

    return None


def _skip(search_term):
    """Removes everything in _content up to the line that begin with buf

    :param search_term: Text to look for lines beginning with
    :type search_term: str, list
    :return: Next state
    :rtype: int
    """
    global _content, _PARSE_NEXT, _PARSE_ERROR

    i = 0
    for buf in _content:
        i += 1
        sl = gen_util.convert_to_list(search_term)
        for search_text in sl:
            search_text_len = len(search_text)
            if len(buf) >= search_text_len and buf[0: search_text_len] == search_text:
                _content = _content[i:]
                return _PARSE_NEXT

    # If we didn't return out of the loop above, we never found the end
    brcdapi_log.exception('Failed to find the end of:\n' + _content[0] + '\n. End search term: ' + ','.join(sl),
                          echo=True)
    return _PARSE_ERROR


def _next(action):
    """Find the next thing to parse"""
    global _content

    i = 0
    while len(_content) > i:
        buf = _content[i]
        _check_fid(buf)
        for k in _search_tbl.keys():
            if k in buf:  # This is a little more efficient
                if len(buf) >= len(k) and buf[0: len(k)] == k:
                    _content = _content[i:]
                    return _search_tbl[k]
        i += 1
    _content = list()
    return


# Methods for values, 'v', in the _xxx_tbl tables

def _split_colon(buf):
    temp_l = buf.split(':')
    return temp_l[1].strip() if len(temp_l) == 2 else None


###################################################################
#
#                          Data
#
###################################################################
# States
_PARSE_START = 0
_PARSE_NEXT = _PARSE_START + 1
_PARSE_CFGSHOW = _PARSE_NEXT + 1
_PARSE_DEFZONE = _PARSE_CFGSHOW + 1
_PARSE_CFGSIZE = _PARSE_DEFZONE + 1
_PARSE_IMMEDIATE = _PARSE_CFGSIZE + 1
_PARSE_CLIHISTORY = _PARSE_IMMEDIATE + 1
_PARSE_ERRDUMP_A = _PARSE_CLIHISTORY + 1
_PARSE_NSSHOW = _PARSE_ERRDUMP_A + 1
_PARSE_PORT_STATS64_SHOW = _PARSE_NSSHOW + 1
_PARSE_SFP_SHOW = _PARSE_PORT_STATS64_SHOW + 1
_PARSE_FICONSHOW = _PARSE_SFP_SHOW + 1
_PARSE_SLOTSHOW = _PARSE_FICONSHOW + 1
_PARSE_ERROR = _PARSE_SLOTSHOW + 1
_PARSE_PORTCFGNAME = _PARSE_ERROR + 1

_CUSTOM_PARSE = 'custom_parse_ss'
_immediate_key_tbl = {  # Used for states that have an immediate action
    'Fabric OS:': dict(k=_CUSTOM_PARSE+'/firmware-version', v=_split_colon),
}
_immediate_keys = [str(_key) for _key in _immediate_key_tbl.keys()]  # Makes searching through keys more efficient
_cmd_chassisshow = 'chassisshow'
_sdcmd_chassisshow = 'CHASSISCMD /fabos/cliexec/chassisshow'
_cmd_fabricshow = 'fabricshow'
_sdcmd_fabricshow = 'SWITCHCMD /fabos/cliexec/fabricshow'
_cmd_switchshow = 'switchshow'
_sdcmd_switchshow = 'SWITCHCMD /fabos/bin/switchshow'
_search_tbl = {
    'portCfgName.': _PARSE_PORTCFGNAME,
    'cfgshow': _PARSE_CFGSHOW,
    '/fabos/cliexec/cfgshow': _PARSE_CFGSHOW,
    'defzone': _PARSE_DEFZONE,
    '/fabos/cliexec/defzone': _PARSE_DEFZONE,
    'clihistory': _PARSE_CLIHISTORY,
    '/fabos/sbin/clihistory': _PARSE_CLIHISTORY,
    'errdump -a': _PARSE_ERRDUMP_A,
    '/fabos/cliexec/errdump -a': _PARSE_ERRDUMP_A,
    'nsshow': _PARSE_NSSHOW,
    '/fabos/cliexec/nsshow': _PARSE_NSSHOW,
    'portstats64show': _PARSE_PORT_STATS64_SHOW,
    'sfpshow -all': _PARSE_SFP_SHOW,
    '/fabos/cliexec/sfpshow -all': _PARSE_SFP_SHOW,
    'ficonshow rnid table': _PARSE_FICONSHOW,
    '/fabos/cliexec/ficonshow rnid table': _PARSE_FICONSHOW,
    'slotshow -d576': _PARSE_SLOTSHOW,
    '/fabos/cliexec/slotshow -d576': _PARSE_SLOTSHOW,
}
for _k in _immediate_key_tbl.keys():
    _search_tbl.update({_k: _PARSE_IMMEDIATE})

_debug_states_1 = {
    _PARSE_START: '_PARSE_START',
    _PARSE_NEXT: '_PARSE_NEXT',
    _PARSE_CFGSHOW: '_PARSE_CFGSHOW',
    _PARSE_DEFZONE: '_PARSE_DEFZONE',
    _PARSE_CFGSIZE: '_PARSE_CFGSIZE',
    _PARSE_IMMEDIATE: '_PARSE_IMMEDIATE',
    _PARSE_CLIHISTORY: '_PARSE_CLIHISTORY',
    _PARSE_ERRDUMP_A: '_PARSE_ERRDUMP_A',
    _PARSE_NSSHOW: '_PARSE_NSSHOW',
    _PARSE_PORT_STATS64_SHOW: '_PARSE_PORT_STATS64_SHOW',
    _PARSE_SFP_SHOW: '_PARSE_SFP_SHOW',
    _PARSE_FICONSHOW: '_PARSE_FICONSHOW',
    _PARSE_SLOTSHOW: '_PARSE_SLOTSHOW',
    _PARSE_ERROR: '_PARSE_ERROR',
    _PARSE_PORTCFGNAME: '_PARSE_PORTCFGNAME',
}


def _immediate_action(action):
    """Action when what we are looking for is on a single line. Example: something: some value."""
    global _content, _PARSE_NEXT, _immediate_key_tbl, _working_chassis_obj

    buf = _content.pop(0)
    for k in _immediate_keys:
        if len(buf) >= len(k) and buf[0: len(k)] == k:
            v = _immediate_key_tbl[k]['v']
            v0 = v(buf) if callable(v) else v
            if isinstance(v0, dict):
                brcddb_util.get_from_obj(_working_chassis_obj, _immediate_key_tbl[k]['k']).update(v0)
            else:
                brcddb_util.add_to_obj(_working_chassis_obj, _immediate_key_tbl[k]['k'], v0)
            break
    return _PARSE_NEXT


def _clihistory(action):
    """Skips past everything in clihistory"""
    return _skip(('dbgshow', '/fabos/cliexec/dbgshow', '** SS CMD END **', 'CHASSISCMD /fabos/cliexec/dbgshow'))


def _errdump_a(action):
    """Skips past everything in errdump -a"""
    return _skip(('pdshow', '** SS CMD END **', 'CHASSISCMD /fabos/sbin/pdshow', '/fabos/sbin/pdshow'))


def _vf_or_nonvf(action):
    """Looks for VF or non-VF is supportshow output"""
    global _content, _PARSE_NEXT, _fid, _working_chassis_obj

    i = 0
    for buf in _content:
        i += 1
        if buf[0:len('Non-VF')] == 'Non-VF':
            brcddb_util.add_to_obj(_working_chassis_obj, 'brocade-chassis/chassis/vf-enabled', False)
            _fid = 0
            break
        elif buf[0: len('VF')] == 'VF':
            brcddb_util.add_to_obj(_working_chassis_obj, 'brocade-chassis/chassis/vf-enabled', True)
            brcddb_util.add_to_obj(_working_chassis_obj, 'brocade-chassis/chassis/vf-supported', True)
            break

    _content = _content[i:]
    return _PARSE_NEXT


def _standard_parse(action):
    """Parse cfgshow output"""
    global _content, _PARSE_NEXT, _working_switch_obj

    # Look ahead to see if the FID is changing
    _check_fid(_content[1])

    _content = _content[action(_working_switch_obj, _content):]

    return _PARSE_NEXT


def _portcfgname(action):
    global _content, _PARSE_NEXT, _working_chassis_obj, _CUSTOM_PARSE

    colon_l = _content[0].split(':')
    if len(colon_l) >= 2:
        dot_l = colon_l[0].split('.')
        if len(dot_l) >= 2:
            d = _working_chassis_obj.r_get(_CUSTOM_PARSE + '/portcfgname')
            if d is None:
                d = dict()
                brcddb_util.add_to_obj(_working_chassis_obj, _CUSTOM_PARSE + '/portcfgname', d)
            d.update({int(dot_l[1]): colon_l[1]})
            _content = _content[1:]
            return None

    return _PARSE_NEXT


def _final_mash_up():
    """Based on the order of data in the supportshow, it's not always obvious where it goes so this puts it all together
    """
    global _working_proj_obj

    ml = list()

    for chassis_obj in _working_proj_obj.r_chassis_objects():
        switch_obj_l = chassis_obj.r_switch_objects()
        d = chassis_obj.r_get(_CUSTOM_PARSE)
        if isinstance(d, dict):
            for k, v in d.items():

                if k == 'firmware-version':
                    for switch_obj in switch_obj_l:
                        brcddb_util.add_to_obj(switch_obj, 'brocade-fabric/fabric-switch/firmware-version', v)

                elif k == 'portcfgname':
                    for k0, v0 in v.items():
                        port_obj = chassis_obj.r_port_object_for_index(k0)
                        if port_obj is None:
                            ml.append('Could not find port matching ' + str(k0) + ' in ' +
                                      brcddb_chassis.best_chassis_name(chassis_obj, wwn=True))
                        else:
                            brcddb_util.add_to_obj(port_obj, 'fibrechannel/user-friendly-name', v0)

                else:
                    ml.append('Unknown key in: ' + str(k) + ' in ' +
                              brcddb_chassis.best_chassis_name(chassis_obj, wwn=True))

    if len(ml) > 0:
        brcdapi_log.exception(ml, echo=True)

    return


def _add_switch_objects(content):
    """Parses content for switchshow output and adds a switch to the chassis and project objects for each switch found

    :param content: List of text, line by line, from the supportshow file
    :type content: list
    """
    global _fid, _working_proj_obj, _working_chassis_obj, _working_switch_obj

    i = 0
    while len(content) > i:
        buf = content[i]
        i += 1
        _check_fid(buf)
        for t_buf in (_cmd_switchshow, _sdcmd_switchshow):
            if len(buf) > len(t_buf) and buf[0: len(t_buf)] == t_buf:
                if t_buf == _sdcmd_switchshow:  # Skip the preamble from supportDecode.pl
                    i = _find_in(content[i:], _cmd_switchshow, 0) + i
                _working_switch_obj, x = parse_cli.switchshow(_working_proj_obj, content[i:])
                i += x
                _working_chassis_obj.s_add_switch(_working_switch_obj.r_obj_key())
                brcddb_util.add_to_obj(_working_switch_obj,
                                       'brocade-fibrechannel-logical-switch/fibrechannel-logical-switch/fabric-id',
                                       _fid)
                break


def _add_fabric_objects(content):
    """Parses content for fabricshow output and adds a fabric to the project object for each fabric found

    :param content: List of text, line by line, from the supportshow file
    :type content: list
    """
    global _working_proj_obj

    i = 0
    while len(content) > i:
        buf = content[i]
        i += 1
        # Find where the list of fabricshow begins
        for t_buf in (_cmd_fabricshow, _sdcmd_fabricshow):
            if len(buf) > len(t_buf) and buf[0: len(t_buf)] == t_buf:
                if t_buf == _sdcmd_fabricshow:  # Skip the preamble from supportDecode.pl
                    i = _find_in(content[i:], _cmd_fabricshow, 0) + i
                fabric_obj, x = parse_cli.fabricshow(_working_proj_obj, content[i:])
                i += x
                break


def _get_input():
    """Parses the module load command line

    :return ss_folder: Name of folder containing supportshow output
    :rtype ss_folder: str
    :return out_file: Name of output file
    :rtype out_file: str
    :return sd_folder: Name of folder containing supportDecode output
    :rtype sd_folder: str
    """
    global _DEBUG_ss, _DEBUG_o, _DEBUG_sd, _DEBUG_log, _DEBUG_nl

    if _DEBUG:
        args_ss, args_o, args_sd, args_log, args_nl = _DEBUG_ss, _DEBUG_o, _DEBUG_sd, _DEBUG_log, _DEBUG_nl
    else:
        parser = argparse.ArgumentParser(description='Convert supportshow output to equivalent capture output.')
        parser.add_argument('-ss', help='Optional. Name of folder containing supportshow output files.', required=False)
        parser.add_argument('-o', help='Required. Output file for converted data.', required=True)
        buf = 'Optional. Folder containing output of supportDecode.pl utility output. Although only the supportshow '\
              'files are used, entire folders of multiple outputs can be in here. The script parses through the '\
              'directory structure and picks out the necessary files.'
        parser.add_argument('-sd', help=buf, required=False)
        buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The log '\
              'file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
        parser.add_argument('-log', help=buf, required=False,)
        buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
        parser.add_argument('-nl', help=buf, action='store_true', required=False)
        args = parser.parse_args()
        args_ss, args_o, args_sd, args_log, args_nl = args.ss, args.o, args.sd, args.log, args.nl

    # Setup the log file
    if not args_nl:
        brcdapi_log.open_log(args_log)

    ml = ['WARNING!!! Debug is enabled'] if _DEBUG else list()
    ml.append('SS folder:    ' + str(args_ss))
    ml.append('Output file:  ' + args_o)
    ml.append('SD folder:    ' + str(args_sd))
    brcdapi_log.log(ml, echo=True)
    
    return args_ss, brcdapi_file.full_file_name(args_o, '.json'), args_sd


# In _parse_actions, la is the local method (within this module to call) and ra is the method in parse_cli to call
_parse_actions = {
    _PARSE_START: dict(la=_vf_or_nonvf),
    _PARSE_NEXT: dict(la=_next),
    _PARSE_CFGSHOW: dict(la=_standard_parse, ra=parse_cli.cfgshow),
    _PARSE_DEFZONE: dict(la=_standard_parse, ra=parse_cli.defzone),
    _PARSE_IMMEDIATE: dict(la=_immediate_action),
    _PARSE_CLIHISTORY: dict(la=_clihistory),
    _PARSE_ERRDUMP_A: dict(la=_errdump_a),
    _PARSE_NSSHOW: dict(la=_standard_parse, ra=parse_cli.nsshow),
    _PARSE_PORT_STATS64_SHOW: dict(la=_standard_parse, ra=parse_cli.portstats64show),
    _PARSE_SFP_SHOW: dict(la=_standard_parse, ra=parse_cli.sfpshow),
    _PARSE_FICONSHOW: dict(la=_standard_parse, ra=parse_cli.ficonshow),
    _PARSE_SLOTSHOW: dict(la=_standard_parse, ra=parse_cli.slotshow_d576),
    _PARSE_PORTCFGNAME: dict(la=_portcfgname),
}


def pseudo_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    global _content, _parse_actions, _working_proj_obj, _working_chassis_obj

    # Get command line input
    ss_folder, out_file, sd_folder = _get_input()

    # Create a project object
    _working_proj_obj = brcddb_project.new("Captured_data", datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
    _working_proj_obj.s_python_version(sys.version)
    _working_proj_obj.s_description('' if ss_folder is None else ss_folder + '' if sd_folder is None else sd_folder)

    # Get the files to parse from ss_folder
    file_l = list() if ss_folder is None else [ss_folder + '/' + f for f in brcdapi_file.read_directory(ss_folder)]

    # Add the files from sd_folder. Bladed directors have two supportshow files, one for the active CP and one for the
    # standby CP. We only want the active CP. The active CP is larger. temp_d is used to determine the larger file.
    if sd_folder is not None:

        # Get all the supportshow file names
        temp_d = dict()  # key is full folder. Value is a list of supportshow files.
        for file_d in [d for d in brcdapi_file.read_full_directory(sd_folder) if 'SUPPORTSHOW_ALL' in d['name']]:
            ss_list = temp_d.get(file_d['folder'])
            if ss_list is None:
                ss_list = list()
                temp_d.update({file_d['folder']: ss_list})
            ss_list.append(file_d)

        # Bladed directors have two supportshow files, one for the active CP and one for the standby CP. We only want
        # the active CP. The active CP is larger. The code below is generic in that it just picks the larger file.
        for folder, ss_list in temp_d.items():
            save_file_d = None
            size = 0
            for file_d in ss_list:
                if file_d['st_size'] > size:
                    size = file_d['st_size']
                    save_file_d = file_d
            file_l.append(save_file_d['folder'] + '/' + save_file_d['name'])

    # Process each file in the folder
    i = 0
    for file in file_l:

        # Read the supportshow file
        brcdapi_log.log('Processing: ' + file, echo=True)
        _content = brcdapi_file.read_file(file, False, False)

        # Get the chassis and add all the switch objects to it. This isn't very efficient, but it's good enough. I want
        # the chassis and all switch and fabric objects first because everything else is added to one of those objects.
        x, _working_chassis_obj = 0, None
        try:
            while len(_content) > x:
                buf = _content[x]
                for t_buf in (_cmd_chassisshow, _sdcmd_chassisshow):
                    if len(buf) > len(t_buf) and buf[0: len(t_buf)] == t_buf:
                        raise Found
                x += 1
        except Found:
            _working_chassis_obj, i = parse_cli.chassisshow(_working_proj_obj, _content[x:])

        if _working_chassis_obj is None:
            brcdapi_log.log('Could not find chassis', echo=True)
            exit(-1)
        _add_fabric_objects(_content)
        _add_switch_objects(_content)

        # Now pick out everything else in the file
        state = _PARSE_START
        while len(_content) > 0:
            next_state = _parse_actions[state]['la'](_parse_actions[state].get('ra'))
            if _DEBUG and next_state is not None and state != next_state:
                t_buf = 'Current state: ' + str(_debug_states_1.get(state)) + ' (' + str(state) + '), '\
                        'Next state: ' + str(_debug_states_1.get(next_state)) + ' (' + str(next_state) + ')'
                brcdapi_log.log(t_buf, echo=True)
            state = state if next_state is None else next_state
            if state == _PARSE_ERROR:
                return brcddb_common.EXIT_STATUS_ERROR
        i += 1

    brcdapi_log.log('Number of files processed: ' + str(i), echo=True)
    if i == 0:
        brcdapi_log.log('No files to process. No output generated', echo=True)
        return brcddb_common.EXIT_STATUS_OK
    _final_mash_up()

    brcdapi_log.log('Saving project to: ' + out_file, echo=True)
    plain_copy = dict()
    brcddb_copy.brcddb_to_plain_copy(_working_proj_obj, plain_copy)
    brcdapi_file.write_dump(plain_copy, out_file)
    brcdapi_log.log('Save complete', echo=True)

    return _working_proj_obj.r_exit_code()


###################################################################
#
#                    Main Entry Point
#
###################################################################
if _DOC_STRING:
    print('_DOC_STRING is True. No processing')
    exit(brcddb_common.EXIT_STATUS_OK)

_ec = pseudo_main()
brcdapi_log.close_log(['', 'Processing Complete. Exit code: ' + str(_ec)], echo=True)
exit(_ec)
