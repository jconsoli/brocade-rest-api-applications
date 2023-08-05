# brocade-rest-api-applications

Consoli Solutions, LLC
jack_consoli@yahoo.com

**Updates 4 Aug 2023**

* Added SX6 & FCxx-64 board types to switch configuration workbooks
* * Re-launched under Consoli Solutions, LLC

**Updates 01 Jan 2023**

* Replaced hard-coded best practice table with ability to read best practices from a Workbook
* Added ability to generate CLI commands in zone_restore.py
* Additional summaries in port_count.py
* Added POD reserve to switch_config.py

**Updates: 17 July 2021**

* Help message improvements

**Updates: 7 Aug 2021**

The primary purpose of these updates was to add functionality to the zone merge utility and add a zone restore utility.

* compare_report.py - Fixed call to best_switch_name
* zone_restore.py - New
* zone_merge.py - Misc. fixes & removed fabric by name
* zon_merge_sample.xlsx - Improved instructions & removed fabric by name.
* lib_check.py - Updated with latest changes

**14 Aug 2021 Updates**

* zone_merge.py, added ability to activate the merged zone configuration.
* report.py, added zone by target page

**Updates: 21 Aug 2021**

Added the ability to generate CLI zone commands in the zone merge utility.

* zone_merge.py - Added -cli flag to generate CLI zoming commands
* lib_check.py - Updated with latest changes

**Updates 14 Nov 2021**

* Deprecated pyfos_auth - previously only used in name only.
* search - Greatly simplified search methods but it is now for programmers only as it accepts JSON as input.
* Imporved several help and feedback messages.

**Updated 31 Dec 2021**

* Several comments and user messaging improved
* Replaced all bare exception clauses with explicit exceptions
* Improved search and added more examples

**Updated 28 Apr 2022**

* Added support for new URIs in FOS 9.1
* Moved some generic libraries from brcddb to brcdapi

**applications**

Contains modules used primarily for SAN automations tasks:

* Data capture scripts
* Report generation scripts with extensive zone validation and analysis
* Comparison reports.
* Port statistical gathering scripts
* Customer search and report scripts.

For any applications, use -h for help

The script shold be placed in a folder used where you run Python scripts from.

**shebang Line & Encoding**

Typically, the first line should be:

#!/usr/bin/env python

Unfortunately, the above shebang line does not always work in Windows environments so all of the sample scripts from github/jconsoli use:

#!/usr/bin/python

The reasoning for doing so was that Unix/Linux users are typically more technically astute and can make the change themselves. There are means to get the standard Linux shebang line to work in Windows but that discussion is outside the scope of this document.

Note that #!/usr/bin/env python is preferred because it ensures your script is running inside a virtual environment while #!/usr/bin/python runs outside the virtual environment

Most Windows and Linux environments do not need the encoding line but some, such as z/OS version of Linux do need it. All of the aforementioned sample scripts have the following:

# -*- coding: utf-8 -*-

To net it out, the first two lines should be:

Windows:

#!/usr/bin/python
# -*- coding: utf-8 -*-

Linux and z/OS:

#!/usr/bin/env python
# -*- coding: utf-8 -*-

**Applications**

With the exception of lib_check.py, all of the applications require the brcddb and brcdapi libraries. The primary intent of the applications are useful examples on how to use the brcddb library. Most of the applications are a two-step process:

1) Collect data
2) Process the data

The brcddb library is a hierarchical relational database with several commonly used features built into it. This includes a utility to easily generate Excel Workbooks. It is used for applications that require the ability to correlate information returned from multiple KPIs and/or multiple switches. For example, the login KPI only returns information specific to the login. The brcrddb login object in the library determines where the login is physically connected and determines all the zones it is used in so with a single line of code, the physical port or list of all zones the login is used in can be returned.

The collected data is stored in class objects in the brcddb library and converted to standard Python data structures and converted to a JSON format when saving the data to a file. When read back in to a module, it is converted back to the brcddb class objects.

**Common Options For All Modules**

Help

-h Prints a brief description of what the module does and a list of module options.

Debug

-d Prints all data structures, pprint, sent to and received from the switch API interface to the console and log.

Logging

Rather than use print statements, all of the modules in api_examples use the logging utility in brcdapi.log. The log utility has a feature that optionally echoes, print, to the console. Creating a log file is optional as well. All modules have the following options:

-log Use to specify the folder where the log file is to be placed.

-nl Use this to disable logging (do not create a log file).

-sup This option is available in the applications modules and some of the api_examples. When set, print to console is disabled. This is useful for batch processing.

For programmers

Each module has a _DEBUG variable. When set True, instead of obtaining module input from the command line, input is taken from _DEBUG_xxx variables where “xxx” is the option. This allows you to execute modules from a development environment such as PyCharm.

**applications Module Specific**

**capture**

The capture.py module is essential to all modules in the applications folder. As the name implies, it captures data from a chassis. It is capable of determining all logical switches in a chassis and capturing the data for all logical switches. It is capable of automatically determining all KPIs supported by the chassis and collecting all the data. Alternatively, a default list of KPIs can be captured or a file with a list of KPIs can be passed to the module. Data is automatically parsed and added to the brcddb library.

Example: Collect all data required for the report.py module. Note that the default KPIs are all that are needed for the report.py module.

py capture.py –ip xxx.xxx.xxx.xxx –id admin –pw password –s self –f chassis_data.json

**cli_zone**

Prior to the API, automation was done using the CLI via an SSH connection. As a result, there were several lists of zoning scripts using the CLI so for testing purposes, it was convenient to build this module. This module was made available as a programming example for those new to the API but familiar with the CLI. Since many organizations no longer allow SSH, it provides a means to use existing zoning scripts that rely on the CLI but doing so should be a bridge to fully API scripting.

py cli_zone.py –ip xxx.xxx.xxx.xxx –id admin –pw password –s self –cli zone_commands.txt

**combine**

Merges the output from execution of capture.py on multiple chassis. This is how the fabric wide database is built for fabrics of more than one switch.

py combine.py –i data_folder –o combined.json

**compare_report**

Compares two databases and generates an Excel Workbook with all the differences. There is some intelligence in that there is a table that controls the comparisons. For example, Tx and Rx byte counters are ignored since these counters are always increasing so a report filled with Tx and Rx byte count changes would just be noise so these are skipped. Similarly, a 0.1 dBm change in output power level of an SFP is uninteresting so there is a tolerance range for statistical counters.

To edit the control table, search for _control_tables.

py compare_report.py –b old_project.json –c new_project.json –r comparison_report

**lib_check**

Used to validate proper installation of Python and the Python libraries required by these modules.

py lib_check.py

**multi_capture**

Reads a list of login credentials from a file and does the following:

1) Launches capture.py for each switch in the input file
2) After all captures complete, launches combine.py
3) Optionally generates a report

py multi_capture.py –i switches.csv

**report**

Generates an Excel report that includes:

* A dashboard with all best practice violations and faults
* A worksheet with basic chassis information for each chassis
* A worksheet with basic fabric information for each fabric
* A detailed zone analysis for each fabric
* Worksheets for port statistics
* And more

py report.py –i combined.json –o report –sfp sfp_rules_r9

**search**

Primarily intended as a programmer’s example on how to use the
search features of the brcddb libraries.

**stats_c**

Collects port statistics to be fed to stats_g.py. Typically, the Kafka streams from SANnav are used for gathering port statistics. This module is useful when Kafka recipients have not been configured.

py stats_c.py –ip xxx.xxx.xxx.xxx –id admin –pw password –s self –fid 128 –o stats.json

**stats_g**

Reads the output of stats_c and formats into an Excel Workbook. Since all statistical counters are cumulative, the counter from the previous poll is subtracted so that incremental statistics are reported. There is an option to create graphs.

py stats_g.py –i stats.json –r stats_report

**zone_merge**

Merges the zone databases from multiple fabrics. A test mode allows you to validate if the zone database could be merged without actually merging the zone database. Input is taken from an Excel file.

py zone_merge.py –i zone_merge_sample

**zone_restore**

Sets the zone database to that of a previously captured zone database. Typically used for restoring a zone database.
