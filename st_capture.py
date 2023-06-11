#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2022 Broadcom Communications, Inc.  All rights reserved.
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
:mod:`st_capture` - Simulates multi_capture.py by reading and parsing show-tech files

**Description**

    Reads and parses a subset of the data read by multi_capture.py. Instead of capturing data from the API, data is
    parsed from a supportshow output or the output of the supportDecode.pl utility. Captured data is limited to:

    * All zoning information
    * Name server information
    * Basic switch configuration information
    * Basic port configuration information
    * Port statistics
    * Local media (SFP) information. No RDP information
    * Port RNID data

**Warning**

    This was a quick and dirty script intended for parsing supportshow or supportsave for the aforementioned information
    only. The primary intent was for zoning evaluation. Information such as port statistics was captured only because it
    is often relevant when evaluating zones.

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
    | 1.0.0     | xx xxx 2022   | Initial launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2019, 2020, 2021 Broadcom Communications, Inc.'
__date__ = 'xx xxx 2022'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Development'
__version__ = '1.0.0'

import argparse
import datetime
import sys
import brcdapi.log as brcdapi_log
import brcddb.brcddb_common as brcddb_common
import brcddb.brcddb_project as brcddb_project
import brcddb.brcddb_chassis as brcddb_chassis
import brcddb.util.copy as brcddb_copy
import brcddb.util.file as brcddb_file
import brcddb.util.util as brcddb_util
import brcddb.util.parse_cli as parse_cli

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = True  # When True, use _DEBUG_st and _DEBUG_o instead of passed arguments
_DEBUG_st = 'show_tech/st'
_DEBUG_o = 'test/test'
_DEBUG_log = '_logs'
_DEBUG_nl = False

_working_proj_obj = None
_working_chassis_obj = None
_working_fabric_obj = None
_working_switch_obj = None

_start_of_mod = 'Start of output for module'
_start_of_mod_len = len(_start_of_mod)

###################################################################
#
#                    Common Methods
#
###################################################################


###################################################################
#
#                          Data
#
###################################################################


###################################################################
#
#            Parse action methods for _parse_actions
#
###################################################################
def _null_act(proj_obj, content):
    """Does nothing

    :param proj_obj:
    :type proj_obj:
    :param content: show-tech output for this command
    :type content: list
    """


# In _parse_actions, la is the local method (within this module to call) and ra is the method in parse_cli to call
_parse_actions = {
    'test': _null_act,
}


def _add_cmd(rd, cmd_in_prog, mod_num, content, p_cmd_d):
    """Adds content to the return dictionary for _parse_show_tech()

    :param rd: Return dictionary
    :type rd: dict
    :param cmd_in_prog: Command to be added
    :type cmd_in_prog: str, None
    :param mod_num: Module number
    :type mod_num: int, None
    :param content: Content associated with this command
    :type content:list
    :param p_cmd_d: Previous command dictionary
    :type p_cmd_d: dict, None
    :return cmd_d: The command dict added to rd for cmd_in_prog if cmd_in_prog is not None, else None
    :rtype cmd_d: dict, None
    """
    if cmd_in_prog is None:
        return p_cmd_d

    cmd_l = rd.get(cmd_in_prog)
    if cmd_l is None:
        cmd_l = list()
        rd.update({cmd_in_prog: cmd_l})
    cmd_d = dict(p_cmd_d=p_cmd_d, cmd=cmd_in_prog, content=content, mod_num=mod_num)
    cmd_l.append(cmd_d)

    return cmd_d


def _parse_show_tech(content):
    """Parses each command in show-tech output into individual buckets

    Return is a dict. The keys are the commands found and the value a list of dictionaries as follows:

    +-----------+-------+-------------------------------------------------------------------------------------------+
    | key       | type  | Value                                                                                     |
    +===========+=======+===========================================================================================+
    | p_cmd_d   | dict  | Previous command dictionary. This dict becomes the p_cmd_d of the next command            |
    +-----------+-------+-------------------------------------------------------------------------------------------+
    | cmd       | str   | Command                                                                                   |
    +-----------+-------+-------------------------------------------------------------------------------------------+
    | content   | list  | The content associated with this command. This becomes the p_content for the next command |
    +-----------+-------+-------------------------------------------------------------------------------------------+
    | mod_num   | int   | Module number from previous "Start of output for module x"                                |
    +-----------+-------+-------------------------------------------------------------------------------------------+

    :param content: File contents in list format
    :type content: list
    :return: Dictionary of commands. See method description for detail.
    :rtype: dict
    """
    global _start_of_mod, _start_of_mod_len

    i, start_i, cmd_in_prog, mod_num, p_cmd_d, rd = 0, 0, None, None, None, dict()

    for buf in content:

        x = buf.find(_start_of_mod)
        if x >= 0:
            mod_num = int(buf[x+_start_of_mod_len:].lstrip().split(' ')[0])

        elif len(buf) > 1 and (buf[0] == '`' or buf[1] == '`'):
            # Under the modules in the show tech output, the command is preceded with a space. I initially just did an
            # lstrip() but ran into a rather bizarre problem. With large files the lstrip had no effect yet when I took
            # the same file and deleted a bunch of unrelated stuff for test it worked. Rather than make a career out of
            # trying to determine the cause of this oddity, I just checked both scenarios. If Cisco ever adds more than
            # one space the if statement above won't work but so far so good.
            p_cmd_d = _add_cmd(rd, cmd_in_prog, mod_num, content[start_i:i], p_cmd_d)
            cmd_in_prog = buf[buf.index('`')+1: buf[2:].index('`')+2]
            start_i = i

        elif 'End of output' in buf:
            cmd_in_prog = None
            mod_num = None

        i += 1

    return rd


def _get_input():
    """Parses the module load command line

    :return st_folder: Name of folder containing show-tech output files
    :rtype st_folder: str
    :return st_files: List of show-tech files with relative path
    :rtype st_files: list
    :return out_file: Name of output file
    :rtype out_file: str
    """
    global _DEBUG_st, _DEBUG_o, _DEBUG_sd, _DEBUG_log, _DEBUG_nl

    if _DEBUG:
        args_st, args_o, args_log, args_nl = _DEBUG_st, _DEBUG_o, _DEBUG_log, _DEBUG_nl
    else:
        parser = argparse.ArgumentParser(description='Convert supportshow output to equivalent capture output.')
        parser.add_argument('-st', help='Optional. Name of folder containing show-tech output files.', required=True)
        parser.add_argument('-o', help='Required. Output file for converted data.', required=True)
        buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The log ' \
              'file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
        parser.add_argument('-log', help=buf, required=False,)
        buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
        parser.add_argument('-nl', help=buf, action='store_true', required=False)
        args = parser.parse_args()
        args_st, args_o, args_log, args_nl = args.st, args.o, args.log, args.nl

    # Setup the log file
    if not args_nl:
        brcdapi_log.open_log(args_log)

    ml = ['WARNING!!! Debug is enabled'] if _DEBUG else list()
    ml.append('show-tech folder, -st: ' + str(args_st))
    ml.append('Output file, -o:       ' + args_o)
    brcdapi_log.log(ml, echo=True)

    st_folders = [args_st + '/' + f for f in brcddb_file.read_directory(args_st)]
    return args_st, st_folders, brcddb_file.full_file_name(args_o, '.json'),


def pseudo_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    global _parse_actions

    # Get command line input
    st_folder, st_files, out_file = _get_input()

    # Create a project object
    proj_obj = brcddb_project.new("Captured_data", datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
    proj_obj.s_python_version(sys.version)
    proj_obj.s_description('Parsed show-tech output from: ' + st_folder)

    # Process each file in the folder
    i = 0
    for file in st_files:

        # Read the show-tech file
        brcdapi_log.log('Processing: ' + file, echo=True)
        show_tech_d = _parse_show_tech(brcddb_file.read_file(file, False, False))
        print(len(show_tech_d))

        i += 1

    brcdapi_log.log('Number of files processed: ' + str(i), echo=True)
    if i == 0:
        brcdapi_log.log('No files to process. No output generated', echo=True)
        return brcddb_common.EXIT_STATUS_OK

    # brcdapi_log.log('Saving project to: ' + out_file, echo=True)
    # plain_copy = dict()
    # brcddb_copy.brcddb_to_plain_copy(_working_proj_obj, plain_copy)
    # brcddb_file.write_dump(plain_copy, out_file)
    # brcdapi_log.log('Save complete', echo=True)

    return proj_obj.r_exit_code()


###################################################################
#
#                    Main Entry Point
#
###################################################################
if _DOC_STRING:
    print('_DOC_STRING is True. No processing')
    exit(brcddb_common.EXIT_STATUS_OK)

_ec = pseudo_main()
brcdapi_log.close_log('\nProcessing Complete. Exit code: ' + str(_ec))
exit(_ec)
