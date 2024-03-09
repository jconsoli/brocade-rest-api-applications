#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright 2024 Consoli Solutions, LLC.  All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may also obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.

The license is free for single customer use (internal applications). Use of this module in the production,
redistribution, or service delivery for commerce requires an additional license. Contact jack@consoli-solutions.com for
details.

:mod:`report` - Creates a report in Excel Workbook format from a brcddb project

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 4.0.0     | 09 Mar 2024   | Initial launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2024 Consoli Solutions, LLC'
__date__ = '09 Mar 2024'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack@consoli-solutions.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '4.0.0'

import brcdapi.log as brcdapi_log
import brcdapi.file as brcdapi_file
import brcdapi.gen_util as gen_util
import brcddb.brcddb_project as brcddb_project
import brcddb.brcddb_chassis as brcddb_chassis
import brcddb.brcddb_common as brcddb_common

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
# _STAND_ALONE: True: Executes as a standalone module taking input from the command line. False: Does not automatically
# execute. This is useful when importing this module into another module that calls psuedo_main().
_STAND_ALONE = True  # See note above

# debug input (for copy and paste into Run->Edit Configurations->script parameters):
# -id admin -pw AdminPassw0rd! -i _capture_2024_03_06_09_10_24/combined -o test/restore_all -p * -log _logs

# Input parameter definitions
_input_d = dict(
    id=dict(h='Required. User ID.'),
    pw=dict(h='Required. Password.'),
    i=dict(h='Required. Name of input file generated by capture.py, combine.py, or multi_capture.py. Extension '
             '".json" is automatically added if no extension present.'),
    o=dict(h='Required. Name of output file. ".bat" is automatically appended.'),
    p=dict(h='Required. -p parameters for restore.py.'),
    fm=dict(r=False, d=None, h='Optional. -fm parameters for restore.py.'),
)
_input_d.update(gen_util.parseargs_log_d.copy())


def pseudo_main(proj_obj, user_id, pw, in_file, dash_p, dash_fm, out_file, log_folder, sup, nl):
    """Basically the main(). Did it this way so that it can easily be used as a standalone module or called externally.

    :param proj_obj: Project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :param user_id: Login user ID
    :type user_id: str
    :param pw: Login password
    :type pw: str
    :param in_file: Input file
    :type in_file: str
    :param dash_p: -p parameter
    :type dash_p: str
    :param dash_fm: -fm parameter
    :type dash_fm: str, None
    :param out_file: Output file name, -o
    :type out_file: str
    :param log_folder: -log parameter
    :type log_folder: str, None
    :param sup: -sup parameter
    :type sup: bool
    :param nl: -nl parameter
    :type nl: bool
    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    ec, command_l = brcddb_common.EXIT_STATUS_OK, list()

    # Generate the command file
    ip_key = 'brocade-management-ip-interface/management-ip-interface/static-ip-addresses/ip-address'
    ip = 'xxx.xxx.xxx.xxx'
    for chassis_obj in proj_obj.r_chassis_objects():
        try:
            ip = chassis_obj.r_get(ip_key)[0]
        except IndexError:
            pass
        except KeyError:
            brcdapi_log.log(
                'Could not find IP address in chassis object ' + brcddb_chassis.best_chassis_name(chassis_obj),
                echo=True
            )

            ec = brcddb_common.EXIT_STATUS_ERROR
        buf = 'start py restore.py -ip ' + ip + ' -id ' + user_id + ' -pw ' + pw + ' -i ' + in_file + ' -p ' + dash_p
        buf += ' -wwn ' + chassis_obj.r_obj_key()
        buf += ' -fm ' + dash_fm if isinstance(dash_fm, str) else ''
        buf += ' -log ' + log_folder if isinstance(log_folder, str) else ''
        buf += ' -sup' if sup else ''
        buf += ' -nl ' if nl else ''
        command_l.append(buf)

    # Write the output file
    try:
        with open(out_file, 'w') as f:
            f.write('\n'.join(command_l) + '\n')
        f.close()
    except FileNotFoundError:
        brcdapi_log.log('Input file, ' + out_file + ', not found', echo=True)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    except FileExistsError:
        brcdapi_log.log('Folder in ' + out_file + ' does not exist', echo=True)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    return ec


def _get_input():
    """Parses the module load command line

    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """
    global __version__, _input_d

    # Get command line input
    args_d = gen_util.get_input(
        'Creates a batch text file to launch restore.py for each chassis in a project.',
        _input_d
    )

    # Set up logging
    brcdapi_log.open_log(folder=args_d['log'], supress=args_d['sup'], no_log=args_d['nl'])

    # Command line feedback
    ml = ['restore_all.py:        ' + __version__,
          'ID, -id:               ' + str(args_d['id']),
          'In file, -i:           ' + args_d['i'],
          'Output file, -o:       ' + args_d['o'],
          'Option parameters, -p: ' + str(args_d['p']),
          'Best practice, -fm:    ' + str(args_d['fm']),
          'Log, -log:             ' + str(args_d['log']),
          'No log, -nl:           ' + str(args_d['nl']),
          'Supress, -sup:         ' + str(args_d['sup']),
          '',]
    brcdapi_log.log(ml, echo=True)

    # Get full file names
    in_file = brcdapi_file.full_file_name(args_d['i'], '.json')
    out_file = brcdapi_file.full_file_name(args_d['o'], '.bat')

    # Read the project file, -i
    try:
        proj_obj = brcddb_project.read_from(in_file)
    except FileNotFoundError:
        brcdapi_log.log('Input file, ' + in_file + ', not found', echo=True)
        return brcddb_common.EXIT_STATUS_INPUT_ERROR
    except FileExistsError:
        brcdapi_log.log('Folder in ' + in_file + ' does not exist', echo=True)
        return brcddb_common.EXIT_STATUS_INPUT_ERROR
    if proj_obj is None:  # Error messages are sent to the log in brcddb_project.read_from() if proj_obj is None
        return brcddb_common.EXIT_STATUS_INPUT_ERROR

    return pseudo_main(proj_obj, args_d['id'], args_d['pw'], args_d['i'], args_d['p'], args_d['fm'], out_file,
                       args_d['log'], args_d['nl'], args_d['sup'])


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
