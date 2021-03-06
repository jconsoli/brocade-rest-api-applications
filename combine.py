#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019, 2020, 2021, 2022 Jack Consoli.  All rights reserved.
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
:mod:`combine` - Combines the output of multiple capture or combine files into a single project object.

* inputs:
    * -i=<Folder Name>: Directory of captured data files
        Required.
    * -o=<File Name>: Name of file containing the combined capture data
        Required
    * -suppress<bool flag> suppress all output except final status code. Useful for batch processing
        Optional

* Outputs:
    * Writes a json dump to the file specified in -o

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
    | 3.0.2     | 13 Feb 2021   | Added # -*- coding: utf-8 -*-                                                     |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.3     | 13 Mar 2021   | Corrected help text and filtered for JSON files only.                             |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.4     | 14 Mar 2021   | Added ".txt" as acceptable input files as well.                                   |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.5     | 17 Jul 2021   | Minor user interface enhancements.                                                |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.6     | 31 Dec 2021   | Removed unused code.                                                              |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 3.0.7     | 28 Apr 2022   | Improved error messages and used new libraries.                                   |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2019, 2020, 2021, 2022 Jack Consoli'
__date__ = '28 Apr 2022'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '3.0.7'

import argparse
import sys
import datetime

import brcddb.brcddb_project as brcddb_project
import brcdapi.log as brcdapi_log
import brcdapi.file as brcdapi_file
import brcddb.util.copy as brcddb_copy
import brcddb.brcddb_common as brcddb_common

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
_DEBUG = False   # When True, use _DEBUG_xxx below instead of parameters passed from the command line.
_DEBUG_INF = 'test/captures'
_DEBUG_OUTF = 'combined'
_DEBUG_SUP = False
_DEBUG_LOG = '_logs'
_DEBUG_NL = False


def parse_args():
    """Parses the module load command line

    :return: i, o
    :rtype: (str, str)
    """
    global _DEBUG, _DEBUG_INF, _DEBUG_OUTF, _DEBUG_SUP, _DEBUG_LOG, _DEBUG_NL

    if _DEBUG:
        return _DEBUG_INF, _DEBUG_OUTF, _DEBUG_SUP, _DEBUG_LOG, _DEBUG_NL

    buf = 'Combine the output of multiple JSON files from capture.py or this utility.'
    parser = argparse.ArgumentParser(description=buf)
    buf = 'Required. Directory of captured data files. Only files with a ".json" extension are read.'
    parser.add_argument('-i', help=buf, required=True)
    buf = 'Required. Name of combined data capture file. Placed in the folder specified by -i. The extension ".json" '\
          'is automatically appended.'
    parser.add_argument('-o', help=buf, required=True)
    buf = 'Optional. Suppress all output to STD_IO except the exit code and argument parsing errors. Useful with '\
          'batch processing where only the exit status code is desired. Messages are still printed to the log file.'
    parser.add_argument('-sup', help=buf, action='store_true', required=False)
    buf = 'Optional. Directory where log file is to be created. Default is to use the current directory. The log ' \
          'file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
    parser.add_argument('-log', help=buf, required=False, )
    buf = 'Optional. No parameters. When set, a log file is not created. The default is to create a log file.'
    parser.add_argument('-nl', help=buf, action='store_true', required=False)
    args = parser.parse_args()
    return args.i, args.o, args.sup, args.log, args.nl


def combine_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code
    :rtype: int
    """
    global _DEBUG

    # Get and validate user input
    inf, outf, s_flag, log, nl = parse_args()
    if s_flag:
        brcdapi_log.set_suppress_all()
    if not nl:
        brcdapi_log.open_log(log)
    ml = ['WARNING!!! Debug is enabled'] if _DEBUG else list()
    ml.append('Directory, -i:   ' + inf)
    ml.append('Output file, -o: ' + outf)
    brcdapi_log.log(ml, True)

    # Create project
    proj_obj = brcddb_project.new(inf, datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
    proj_obj.s_python_version(sys.version)
    proj_obj.s_description('Captured data from ' + inf)

    # Get a list of files - Filter out directories is just to protect the user. It shouldn't be necessary.
    outf = brcdapi_file.full_file_name(outf, '.json')
    files = brcdapi_file.read_directory(inf)
    if outf in files:
        brcdapi_log.log('Combined output file, ' + outf + ', already exists in: ' + inf + '. Processing halted', True)
        proj_obj.s_error_flag()
    else:
        x = len('.json')
        for file in [f for f in files if len(f) > x and f.lower()[len(f)-x:] == '.json']:
            brcdapi_log.log('Processing file: ' + file, True)
            obj = brcdapi_file.read_dump(inf + '/' + file)
            brcddb_copy.plain_copy_to_brcddb(obj, proj_obj)

        # Now save the combined file
        plain_copy = dict()
        brcddb_copy.brcddb_to_plain_copy(proj_obj, plain_copy)
        try:
            brcdapi_file.write_dump(plain_copy, inf + '/' + outf)
        except FileNotFoundError:
            brcdapi_log.log(['', 'Folder not found: ' + inf, ''], True)

    return brcddb_common.EXIT_STATUS_OK


##################################################################
#
#                    Main Entry Point
#
###################################################################
if _DOC_STRING:
    print('_DOC_STRING is True. No processing')
    exit(brcddb_common.EXIT_STATUS_OK)

_ec = combine_main()
brcdapi_log.close_log('\nProcessing Complete. Exit code: ' + str(_ec))
exit(_ec)
