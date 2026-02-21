#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright 2023, 2024, 2025, 2026 Jack Consoli.  All rights reserved.

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

Add statistics to Excel Workbook

Reads in the output of stats_c (which collects port statistics) and creates an Excel Workbook for each port.

**Version Control**

+-----------+---------------+---------------------------------------------------------------------------------------+
| Version   | Last Edit     | Description                                                                           |
+===========+===============+=======================================================================================+
| 4.0.0     | 04 Aug 2023   | Re-Launch                                                                             |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.1     | 06 Mar 2024   | Documentation updates only.                                                           |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.2     | 03 Apr 2024   | Added version numbers of imported libraries.                                          |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.3     | 29 Oct 2024   | Fixed call to cell_match_val().                                                       |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.4     | 06 Dec 2024   | Fixed spelling mistake in message.                                                    |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.5     | 25 Aug 2025   | Use brcddb.util.util.get_import_modules to dynamically determined imported libraries. |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.6     | 19 Oct 2025   | Updated comments only.                                                                |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.7     | 20 Feb 2026   | Added support for graphing from multiple switches.                                    |
+-----------+---------------+---------------------------------------------------------------------------------------+
| 4.0.8     | 21 Feb 2026   | Cleaned up debug code.                                                                |
+-----------+---------------+---------------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2024, 2025, 2026 Jack Consoli'
__date__ = '21 Feb 2026'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack_consoli@yahoo.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '4.0.8'

import sys
import os
import datetime
import time
import collections
import copy
import brcdapi.log as brcdapi_log
import brcdapi.gen_util as gen_util
import brcdapi.util as brcdapi_util
import brcdapi.excel_util as excel_util
import brcdapi.excel_fonts as excel_fonts
import brcdapi.file as brcdapi_file
import brcddb.brcddb_project as brcddb_project
import brcddb.util.util as brcddb_util
import brcddb.brcddb_common as brcddb_common
import brcddb.brcddb_switch as brcddb_switch
import brcddb.report.utils as report_utils
import brcddb.report.zone as report_zone
import brcddb.report.port as report_port
import brcddb.util.copy as brcddb_copy
import brcddb.report.graph as report_graph

# Debug
import random

_DOC_STRING = False  # Should always be False. Prohibits any code execution. Only useful for building documentation
# _STAND_ALONE: True: Executes as a standalone module taking input from the command line. False: Does not automatically
# execute. This is useful when importing this module into another module that calls psuedo_main().
_STAND_ALONE = True  # See note above

_do_not_modify = {  # Used to determine which statistics are a rate or time stamp.
    'in-frame-rate': True,
    'in-peak-rate': True,
    'out-frame-rate': True,
    'out-peak-rate': True,
    'time-generated': True,
}

_unknown_stat_d = dict()  # Used to track unknown statistics

_skip_groups_d = {  # These are the auto-generated groups. Only user defined groups are being graphed.
    report_zone.UNGROUPED_TARGET: True,
    report_zone.UNGROUPED_INITIATOR: True,
    report_zone.MISSING_CPU: True,
}

_std_font = excel_fonts.font_type('std')
_bold_font = excel_fonts.font_type('bold')
_hdr1_font = excel_fonts.font_type('hdr_1')
_link_font = excel_fonts.font_type('link')
_align_wrap = excel_fonts.align_type('wrap')
_align_wrap_c = excel_fonts.align_type('wrap_center')

#################################################
#                                               #
#    Methods to determine -max parameter        #
#                                               #
#################################################


def _all_x(port_obj_l, max_ports, stat):
    """Filters the port list when the -max parameter is all_x

ind_group_d['port_obj_l']

    :param port_obj_l: List of port objects to filter
    :type port_obj_l: list
    :param max_ports: Maximum number of ports, by port object, to return
    :type max_ports: int
    :param stat: The statistic to filter on
    :type stat: str
    :return: List of port objects to plot.
    :rtype: list
    """
    return port_obj_l[0:max_ports]


def _high_x(port_obj_l, max_ports, stat):
    """Filters the port list when the -max parameter is high_x. See _all_x for parameter descriptions."""
    rl = list()

    # Find all the maximum values for the stat
    sort_d = dict()  # Key is the maximum value. Value is a list of port_objects with this value
    for port_obj in port_obj_l:
        stat_val_l = [d[stat] for d in port_obj.r_get('stats_c/samples') if d.get(stat) is not None]
        if len(stat_val_l) > 0:
            max_val = max(stat_val_l)
            max_port_l = sort_d.get(max_val)
            if max_port_l is None:
                max_port_l = list()
                sort_d[max_val] = max_port_l
            max_port_l.append(port_obj)

    # Sort and build the return list
    key_l = sorted([int(i) for i in sort_d.keys()], reverse=True)
    for key in key_l:
        rl.extend(sort_d[key])

    return rl[0:max_ports]


def _low_x(port_obj_l, max_ports, stat):
    """Filters the port list when the -max parameter is low_x. See _all_x for parameter descriptions."""
    rl = list()

    # Find all the minimum values for the stat
    sort_d = dict()  # Key is the maximum value. Value is a list of port_objects with this value
    for port_obj in port_obj_l:
        stat_val_l = [d[stat] for d in port_obj.r_get('stats_c/samples') if d.get(stat) is not None]
        if len(stat_val_l) > 0:
            min_val = min(stat_val_l)
            min_port_l = sort_d.get(min_val)
            if min_port_l is None:
                min_port_l = list()
                sort_d[min_val] = min_port_l
            min_port_l.append(port_obj)

    # Sort and build the return list
    key_l = sorted([int(i) for i in sort_d.keys()])
    for key in key_l:
        rl.extend(sort_d[key])

    return rl[0:max_ports]


def _high_avg_x(port_obj_l, max_ports, stat):
    """Filters the port list when the -max parameter is highavg_x. See _all_x for parameter descriptions."""
    rl = list()

    # Find all the maximum values for the stat
    sort_d = dict()  # Key is the total value. Value is a list of port_objects with this value
    for port_obj in port_obj_l:
        stat_sum = sum([d[stat] for d in port_obj.r_get('stats_c/samples') if d.get(stat) is not None])
        sum_port_l = sort_d.get(stat_sum)
        if sum_port_l is None:
            sum_port_l = list()
            sort_d[stat_sum] = sum_port_l
        sum_port_l.append(port_obj)

    # Sort and build the return list
    key_l = sorted([int(i) for i in sort_d.keys()], reverse=True)
    for key in key_l:
        rl.extend(sort_d[key])

    return rl[0:max_ports]


def _low_avg_x(port_obj_l, max_ports, stat):
    """Filters the port list when the -max parameter is lowavg_x. See _all_x for parameter descriptions."""
    rl = list()

    # Find all the maximum values for the stat
    sort_d = dict()  # Key is the total value. Value is a list of port_objects with this value
    for port_obj in port_obj_l:
        stat_sum = sum([d[stat] for d in port_obj.r_get('stats_c/samples') if d.get(stat) is not None])
        sum_port_l = sort_d.get(stat_sum)
        if sum_port_l is None:
            sum_port_l = list()
            sort_d[stat_sum] = sum_port_l
        sum_port_l.append(port_obj)

    # Sort and build the return list
    key_l = sorted([int(i) for i in sort_d.keys()])
    for key in key_l:
        rl.extend(sort_d[key])

    return rl[0:max_ports]


_max_default = 'all_20'
_max_ports_d = {
    'all_x': _all_x,
    'high_x': _high_x,
    'low_x': _low_x,
    'highavg_x': _high_avg_x,
    'lowavg_x': _low_avg_x,
}

#################################################
#                                               #
#               Input parameters                #
#                                               #
#################################################

_max_buf = 'Optional. The default is ' + _max_default + '. Limits the number of ports to be graphed. Options are: '
_max_buf += ','.join([str(_k) for _k in _max_ports_d.keys()]) + '. "x" is the maximum number of ports to graph. '
_max_buf += '"high_x" limits the number of ports plotted for each group to the number specified by "x" with the '\
            'highest peaks based on the statistic(s), -stat. "highavg_x" is the same as "high_x" except ports are '\
            'sorted by the highest average in the sample period rather than the peak. "low_x" and "lowavg_x" are '\
            'similar but using the lowest rather than the highest. "all_x" just limits the plot to the first "x" '\
            'number of ports found.'
_type_buf = 'Optional. Specifies the graph type. The default is "line". Valid chart types are: '
_type_buf += ', '.join(report_graph.supported_chart_types()) + '. '
_input_d = collections.OrderedDict()
_input_d.update(
    r=dict(h='Required. Report name. ".xlsx" is automatically appended.'),
    i=dict(
        h='Required. Name of data input file. This must be the output file, -o, from stats_c.py. ".json" is '
          'automatically appended'
    ),
    stat=dict(
        r=False,
        h='Required if a group, -group or -isl, is specified. A CSV list of statistics from '
          'brocade-interface/fibrechannel-statistics to plot. For example, to graph the Tx and Rx frames: -stat '
          'in-frames,out-frames'
    ),
    max=dict(r=False, d=_max_default, h=_max_buf,),
    type=dict(r=False, t='str', d='line', v=report_graph.supported_chart_types(), h=_type_buf),
    group=dict(
        r=False,
        h='Optional. Name of Excel file containing group definitions. See group.xlsx for an example. A graph is '
          'created for each group. See -all.'
    ),
    isl=dict(
        r=False,
        d=False,
        t='bool',
        h='Optional. When set, a group for each pair of switches ISLed together is created.'
    ),
    stat_graph=dict(r=False, d=False, t='bool', h='Create a graph for each statistic in -stat.'),
)
_input_d.update(gen_util.parseargs_log_d.copy())

#################################################
#                                               #
#           Internal methods                    #
#                                               #
#################################################


def _graphs(proj_obj, args_d):
    """Determines what to graph.

    :param proj_obj: First switch object with list of ports
    :type proj_obj: brcddb.classes.project.ProjectObj
    :param args_d: Conditioned input arguments.
    :type args_d: dict
    :return: Dictionary of graphs. Key is the group name. Value is a dictionary whose key is the stat and the value is\
             a list of port objects that met the filter criteria for that stat.
    :rtype: dict
    """
    global _max_ports_d

    graph_l, port_obj_l = list(), proj_obj.r_get('stats_c/stats_g_d/port_obj_l')
    temp_l = args_d['max'].split('_')  # Separate the value name and the value
    filter_type, max_ports = temp_l[0] + '_x', int(temp_l[1])
    return_d = dict()

    if not isinstance(args_d['group'], str):
        return graph_l  # There isn't anything to graph.

    # Decipher the group file, -group, and filter out ports that do not have a collection of stats.
    group_d, el = report_utils.groups(proj_obj, args_d['group'])
    if len(el) > 0:
        brcdapi_log.log(el, echo=True)
    for d in group_d.values():
        d['port_obj_l'] = list(set(d['port_obj_l']) & set(port_obj_l))

    # ports_for_stat_d is a sorted and filtered copy of group_d for each stat. The primary key is the group name. The
    # value is a dictionary whose key is the stat. The value is a list of port objects that met the filter criteria,
    # specified by -max, for the stat.
    for group_name, ind_group_d in group_d.items():
        if _skip_groups_d.get(group_name, False):
            continue
        group_d = return_d.get(group_name)
        if group_d is None:
            group_d = dict()
            return_d[group_name] = group_d
        for stat in args_d['stat']:
            temp_l = _max_ports_d[filter_type](ind_group_d['port_obj_l'], max_ports, stat)
            if len(temp_l) > 0:
                group_d[stat] = temp_l

        if len(group_d) > 0:  # IDK how it can ever not be > 0.
            return_d[group_name] = group_d

    return return_d


def _condition_samples(port_obj_l):
    """Modifies the sample value specified by stats that are not rates to be the difference between samples

    :param port_obj_l: List of port objects
    :type port_obj_l: list
    :rtype: None
    """
    global _do_not_modify

    ignored_stats_l = list()
    for port_obj in port_obj_l:
        for stat in [str(k) for k in port_obj.r_get(brcdapi_util.stats_uri) if not _do_not_modify.get(k, False)]:
            last_value = port_obj.r_get(brcdapi_util.stats_uri + '/' + stat)
            if last_value is None:
                ignored_stats_l.append(stat)
                continue
            for d in port_obj.r_get('stats_c/samples'):
                next_last_value = d[stat]
                if isinstance(d[stat], int):  # At the time this was written, only "name" was not an int
                    d[stat] -= last_value
                    last_value = next_last_value

        if len(ignored_stats_l) > 0:
            buf = brcddb_switch.best_switch_name(port_obj.r_switch_obj()) + ', port ' + port_obj.r_key()
            brcdapi_log.log(buf + ' Statistic(s) not found: '.join(ignored_stats_l), echo=True)


# Debug
def _debug_add_data(proj_obj):
    """Adds debug data to port objects

    :param proj_obj: The project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    """
    proj_obj.rs_key('stats_c', dict())
    time_inc = 10

    port_l = ['3/23', '3/22', '3/1', '3/0', '3/47', '3/46', '3/25']
    port_l.extend(['4/23', '4/22', '4/2', '4/1', '4/0', '4/47', '4/25'])
    port_l.extend(['5/23', '5/22', '5/1', '5/0', '5/33', '5/26'])
    port_l.extend(['6/23', '6/22', '6/21', '6/8'])
    port_l.extend(['9/23', '9/22', '9/21', '9/2', '9/25'])
    port_l.extend(['10/21', '10/0', '10/45', '10/43', '10/26', '10/25'])
    port_l.extend(['11/23', '11/22', '11/5', '11/47', '11/28'])
    port_l.extend(['12/8', '12/47', '12/46'])

    switch_poll_d = dict()
    proj_obj.s_new_key('stats_c', switch_poll_d)
    switch_wwn = '10:00:88:94:71:37:dd:28'
    switch_obj = proj_obj.r_switch_obj(switch_wwn)
    if switch_obj is None:
        brcdapi_log.log('**Debug ERROR** Switch ' + switch_wwn + ' not found.', echo=True)

    for port in port_l:
        port_obj = switch_obj.r_port_obj(port)
        if port_obj is None:
            brcdapi_log.log('**Debug ERROR** Port ' + port + ' not found.', echo=True)
            continue
        # Insert fake data
        port_data_l = list()
        port_obj.rs_key('stats_c/samples', port_data_l)
        port_stats_d = port_obj.r_get(brcdapi_util.stats_uri)
        if port_stats_d.get('time-generated') is None:
            port_stats_d['time-generated'] = int(time.time())
        port_stats_d = port_stats_d.copy()
        for i in range(0, 20):
            port_stats_d['in-frames'] += random.randint(0, 1000)
            port_stats_d['out-frames'] += random.randint(0, 5000)
            port_stats_d['time-generated'] += time_inc
            port_data_l.append(port_stats_d)
            port_stats_d = copy.deepcopy(port_stats_d)

    return


def pseudo_main(proj_obj, args_d):
    """Basically the main(). Did it this way, so it can easily be used as a standalone module or called from another.

    :param proj_obj: The project object
    :type proj_obj: brcddb.classes.project.ProjectObj
    :param args_d: Conditioned input arguments.
    :type args_d: dict
    :return: Exit code. See exit codes in brcddb.brcddb_common
    :rtype: int
    """
    global _hdr1_font, _align_wrap_c, _std_font, _bold_font, _link_font, _unknown_stat_d

    ec = brcddb_common.EXIT_STATUS_OK
    stats_map_d, graph_map_d, stats_g_d = dict(), dict(), proj_obj.r_get('stats_c/stats_g_d')
    chart_msg = 'WARNING: The FOS statistics poll cycle, 2 sec, is not synchronized between different switches. Network'
    chart_msg += ' delays that occurred during data capture with stats_c.py may add additional time base discrepancies.'

    # Modify the samples so that they are differences instead of running counts
    _condition_samples(proj_obj.r_get('stats_c/stats_g_d/port_obj_l'))

    # Build the cross-reference tables.
    brcddb_util.build_login_port_map(proj_obj)  # Correlates name server logins with ports
    
    # Create the workbook and add the worksheets with the port statistics
    wb = excel_util.new_report()
    brcdapi_log.log('Creating individual port statistics pages', echo=True)
    unique_sheet_num = 0
    for port_obj in stats_g_d['port_obj_l']:
        time_generated = port_obj.r_get(brcdapi_util.stats_time)
        sname = str(unique_sheet_num) + '_Port_' + port_obj.r_obj_key().replace('/', '_')
        title = brcddb_switch.best_switch_name(port_obj.r_switch_obj(), did=True) + ' Port ' + port_obj.r_obj_key()
        stats_map_d[title] = sname
        title += ' Beginning ' + datetime.datetime.fromtimestamp(time_generated).strftime('%d %b %Y')
        cell_map_d = report_port.port_stats(
            wb,
            '#Contents!A1',
            sname,
            title,
            0,  # Sheet index
            port_obj.r_get('stats_c/samples'),
            time_format='HH:MM:SS;@',
            sub_hdr=brcddb_switch.best_switch_name(port_obj.r_switch_obj())[0:27] + ' ' + port_obj.r_obj_key(),
            time_hdr=port_obj.r_get(brcdapi_util.stats_time)
        )
        port_obj.r_get('stats_c').update(dict(sheet=cell_map_d['sheet'], sheet_name=sname, cell_map_d=cell_map_d))
        unique_sheet_num += 1

    # Add the graph worksheets
    brcdapi_log.log('Adding graphs.', echo=True)
    unique_sheet_num = 0
    for group_name, stats_d in _graphs(proj_obj, args_d).items():
        for stat, port_obj_l in stats_d.items():
            if len(port_obj_l) > 0:
                
                # Add the Y axis data
                y_data_l = list()
                for cell_map_d in [obj.r_get('stats_c')['cell_map_d'] for obj in port_obj_l]:
                    try:
                        stat_col = cell_map_d['col'][stat]
                        y_data_l.append(
                            dict(
                                sheet=cell_map_d['sheet'],
                                start_col=stat_col,
                                end_col=stat_col,
                                start_row=cell_map_d['row']['start'],
                                end_row=cell_map_d['row']['end'],
                            )
                        )
                    except KeyError:
                        _unknown_stat_d[stat] = True

                # Add the basic chart infor, the X axis (time), and the Y axis data from above
                cell_map_d = port_obj_l[0].r_get('stats_c')['cell_map_d']
                data_ref_d = dict(
                    title=group_name + ': ' + str(stat),
                    type=args_d['type'],
                    x_title='Time',
                    x_sheet=cell_map_d['sheet'],
                    x_start_col=cell_map_d['col']['time-generated'],
                    x_start_row=cell_map_d['row']['start'],
                    x_end_row=cell_map_d['row']['end'],
                    y_title=stat,
                    y_data_l=y_data_l,
                )
                
                # Create the graph
                sname = 'graph_' + str(unique_sheet_num)
                unique_sheet_num += 1
                report_graph.graph(wb, '#Contents!A1', sname, 0, data_ref_d, msg=chart_msg, title_in_data=True)
                graph_map_d[data_ref_d['title']] = sname

    # Create a table of contents worksheet
    sheet = wb.create_sheet(index=0, title='Contents')
    sheet.page_setup.paperSize = sheet.PAPERSIZE_LETTER
    sheet.page_setup.orientation = sheet.ORIENTATION_PORTRAIT
    col = 10
    sheet.column_dimensions['A'].width = col
    sheet.column_dimensions['B'].width = 80 - col

    # Add the title to the table of contents
    row, col = 1, 1
    sheet.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col+1)
    excel_util.cell_update(sheet, row, col, 'Port Statistics Project', font=_hdr1_font, align=_align_wrap_c)
    row += 2

    # Add the Summary to the table of contents
    sheet.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col+1)
    excel_util.cell_update(sheet, row, col, 'Summary', font=_bold_font, align=_align_wrap)
    row += 1
    port_obj = stats_g_d['port_obj_l'][0]  # They should all start and end at the same time, so just pick one
    buf = datetime.datetime.fromtimestamp(port_obj.r_get(brcdapi_util.stats_time)).strftime('%d %b %Y %H:%M:%S')
    excel_util.cell_update(sheet, row, col, 'Start', font=_std_font, align=_align_wrap)
    excel_util.cell_update(sheet, row, col+1, buf, font=_std_font, align=_align_wrap)
    row += 1
    samples_l = port_obj.r_get('stats_c/samples')
    buf = datetime.datetime.fromtimestamp(samples_l[len(samples_l)-1]['time-generated']).strftime('%d %b %Y %H:%M:%S')
    excel_util.cell_update(sheet, row, col, 'End', font=_std_font, align=_align_wrap)
    excel_util.cell_update(sheet, row, col+1, buf, font=_std_font, align=_align_wrap)

    # Add the Graphs to the table of contents
    row += 2
    sheet.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col+1)
    excel_util.cell_update(sheet, row, col, 'Graphs', font=_bold_font, align=_align_wrap)
    for buf, sname in graph_map_d.items():
        row += 1
        sheet.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col + 1)
        excel_util.cell_update(sheet, row, col, buf, font=_link_font, align=_align_wrap, link='#' + sname + '!A1')

    # Add the port statistics detail to the table of contents
    row += 2
    sheet.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col+1)
    excel_util.cell_update(sheet, row, col, 'Port Statistics Detail', font=_bold_font, align=_align_wrap)
    for buf, sname in stats_map_d.items():
        row += 1
        sheet.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col + 1)
        excel_util.cell_update(sheet, row, col, buf, font=_link_font, align=_align_wrap, link='#' + sname + '!A1')

    stat_l = ['  ' + str(k) for k in _unknown_stat_d.keys()]
    if len(stat_l) > 0:
        stat_l.insert(0, 'The following statistics are unknown and therefore skipped:')
        brcdapi_log.log(stat_l, echo=True)

    brcdapi_log.log('Writing ' + args_d['r'])
    try:
        excel_util.save_report(wb, args_d['r'])
    except FileExistsError:
        brcdapi_log.log('Folder in ' + args_d['r'] + ' does not exist', echo=True)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    except PermissionError:
        buf = 'Permission error writing ' + args_d['r'] + '. This typically occurs when the file is open in Excel.'
        brcdapi_log.log(buf, echo=True)
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    return ec

def _get_input():
    """Parses the module load command line

    :return: Exit code. See exit codes in brcddb.brcddb_common
    :rtype: int
    """
    global __version__, _input_d, _max_ports_d

    # Get command line input
    buf = 'Create Excel Workbook from statistics gathered with stats_c.py. If a group is defined, using -group or '\
          '-isl, worksheets with graphs for each group are also created.'
    args_d = gen_util.get_input(buf, _input_d)
    ec = brcddb_common.EXIT_STATUS_OK

    # Set up logging
    brcdapi_log.open_log(
        folder=args_d['log'],
        suppress=args_d['sup'],
        no_log=args_d['nl'],
        version_d=brcdapi_util.get_import_modules()
    )

    # Validate the input

    # -i, and get proj_obj
    proj_obj, obj, i_help = None, None, ''
    input_file = brcdapi_file.full_file_name(args_d['i'], '.json')
    try:
        obj = brcdapi_file.read_dump(input_file)
    except FileNotFoundError:
        i_help = ' **ERROR** File not found.'
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    except FileExistsError:
        i_help = ' **ERROR** Folder does not exist.'
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    except PermissionError:
        i_help = ' **ERROR** You do not have permission to read this file.'
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    except BaseException as e:
        i_help = ' **ERROR** ' + str(e)
        ec = brcddb_common.EXIT_STATUS_ERROR
    if ec == brcddb_common.EXIT_STATUS_OK:
        if not isinstance(obj, dict) or len(list(obj.keys())) == 0:
            i_help = ' **ERROR** Unknown error encountered.'
            ec = brcddb_common.EXIT_STATUS_ERROR

    if ec == brcddb_common.EXIT_STATUS_OK:
        proj_obj = brcddb_project.new(obj.get('_obj_key'), obj.get('_date'))
        proj_obj.s_python_version(sys.version)
        proj_obj.s_description(obj.get('_description'))
        brcddb_copy.plain_copy_to_brcddb(obj, proj_obj)

        # Debug
        _debug_add_data(proj_obj)

        port_obj_l = [p for p in proj_obj.r_port_objects() if p.r_get('stats_c') is not None]
        if len(port_obj_l) == 0:
            i_help = ' **ERROR** No data captured'
            ec = brcddb_common.EXIT_STATUS_ERROR
        else:
            # The ports don't need to be sorted. Humans just like to see them added to the report this way.
            proj_obj.rs_key('stats_c/stats_g_d/port_obj_l', brcddb_util.sort_ports(port_obj_l))

    # -stat
    stat_help = str(args_d['stat'])
    if args_d['stat'] is None and (args_d['group'] is not None or args_d['isl']):
        stat_help = ' **ERROR** Required when -group or -isl is specified.'
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # -max
    max_help = ''
    temp_l = args_d['max'].split('_')
    if len(temp_l) != 2:
        max_help = ' **ERROR** Invalid value for -max. Re-run with -h for valid parameters.'
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    elif temp_l[0] + '_x' not in _max_ports_d:
        max_help = ' **ERROR** Invalid value for -max. Re-run with -h for valid parameters.'
        ec = brcddb_common.EXIT_STATUS_INPUT_ERROR
    else:
        try:
            int(temp_l[1])
        except ValueError:
            max_help = ' **ERROR** The value after "_" must be an integer.'
            ec = brcddb_common.EXIT_STATUS_INPUT_ERROR

    # Command line feedback
    ml = [
        os.path.basename(__file__) + ' version: ' + __version__,
        'Report, -r:                ' + args_d['r'],
        'Input file, -i:            ' + args_d['i'] + i_help,
        'Statistics, -stat:         ' + stat_help,
        'Max ports per graph, -max: ' + args_d['max'] + max_help,
        'Graph type, -type:         ' + args_d['type'],
        'Group file, -group:        ' + str(args_d['group']),
        'ISL groups, -isl:          ' + str(args_d['isl']),
        'Log, -log:                 ' + str(args_d['log']),
        'No log, -nl:               ' + str(args_d['nl']),
        'Suppress, -sup:            ' + str(args_d['sup']),
        '',
        ]
    brcdapi_log.log(ml, echo=True)

    # Condition the input
    args_d['r'] = brcdapi_file.full_file_name(args_d['r'], '.xlsx')
    args_d['i'] = input_file
    if isinstance(args_d['group'], str):
        args_d['group'] = brcdapi_file.full_file_name(args_d['group'], '.xlsx')
    args_d['stat'] = args_d['stat'].replace(' ', '').split(',') if isinstance(args_d['stat'], str) else list()

    return pseudo_main(proj_obj, args_d) if ec == brcddb_common.EXIT_STATUS_OK else ec


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
