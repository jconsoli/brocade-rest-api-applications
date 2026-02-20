# brocade-rest-api-applications

Jack Consoli
jack_consoli@yahoo.com

**Applications**

Contains Python scripts used primarily for SAN automations tasks with Brocade FOS Rest API:

* Data capture scripts
* Report generation scripts with extensive zone validation and analysis
* Comparison reports.
* Port statistical gathering scripts
* Customer search and report scripts.
* Zone from a workbook.
* Automated zone cleanup workbooks.
* Configure switches from a workbook. Since CLI commands are optionally supported, all configuration tasks are possible even when configuration tasks are not supported via the API.
* Mainframe storage groups are automatically determined based on the RNID sequence number.
* Supports import of IOCPs for end to end mainframe path reporting.
* Define device groups using ReGex and wild card matching on aliases.

For any applications, use -h for help. Some applications have extended help, -eh.

The script should be placed in a folder used where you run Python scripts from.

**shebang Line & Encoding**

The first line should be the shebang line. The shebang line tells the Python interpreter what environment to work in. If you don’t understand this comment, the typical shebang line explained below likely is what you need. If your organization has a system administrator, check with your system administrator.

The second line should be the encoding line. By default, the encoding scheme is utf-8 (formerly known as ASCII). Windows (DOS actually) and Unix/Linux variant operating system use utf-8. Since those are the two most popular operating systems to execute Python scripts, the encoding line is typically omitted. Mainframes, run under z/OS, which uses EBCDIC. Since these scripts are supported in mainframe environments, the encoding line is explicit. I don’t know if Python is supported under TPF, but if it is, I would expect the encoding to be EBCDIC.

# *Windows (default)*

#!/usr/bin/python
# -*- coding: utf-8 -*-

# *Unix/Linux*

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# *z/OS*

#!/usr/bin/env python
# -*- coding: ebcdic -*-

**Applications**

With the exception of lib_check.py, all of the applications require the brcddb and brcdapi libraries. The primary intent of the applications are useful examples on how to use the brcddb library. Most of the applications are a two-step process:

1) Collect data
2) Process the data

The brcddb library is a hierarchical relational database with several commonly used features built into it. This includes a utility to easily generate Excel Workbooks. It is used for applications that require the ability to correlate information returned from multiple KPIs and/or multiple switches. For example, the login KPI only returns information specific to the login. The brcrddb login object in the library determines where the login is physically connected and determines all the zones it is used in so with a single line of code, the physical port or list of all zones the login is used in can be returned.

The collected data is stored in class objects in the brcddb library and converted to standard Python data structures and converted to a JSON format when saving the data to a file. When read back in to a module, it is converted back to the brcddb class objects.

*Common Options For All Modules*

Help

-h Prints a brief description of what the module does and a list of module options.

Debug

-d Prints all data structures, pprint, sent to and received from the switch API interface to the console and log.

Logging

Rather than use print statements, all of the modules in api_examples use the logging utility in brcdapi.log. The log utility has a feature that optionally echoes, print, to the console. Creating a log file is optional as well. All modules have the following options:

-log Use to specify the folder where the log file is to be placed.

-nl Use this to disable logging (do not create a log file).

-sup This option is available in the applications modules and some of the api_examples. When set, print to console is disabled. This is useful for batch processing.

# *capture*

The capture.py module is essential to all modules in the applications folder. As the name implies, it captures data from a chassis. It is capable of determining all logical switches in a chassis and capturing the data for all logical switches. It is capable of automatically determining all KPIs supported by the chassis and collecting all the data. Alternatively, a default list of KPIs can be captured or a file with a list of KPIs can be passed to the module. Data is automatically parsed and added to the brcddb library.

Example: Collect all data required for the report.py module. Note that the default KPIs are all that are needed for the report.py module.

py capture.py –ip xxx.xxx.xxx.xxx –id admin –pw password –s self –f chassis_data.json

# *cli_zone*

Prior to the API, automation was done using the CLI via an SSH connection. As a result, there were several lists of zoning scripts using the CLI so for testing purposes, it was convenient to build this module. This module was made available as a programming example for those new to the API but familiar with the CLI. Since many organizations no longer allow SSH, it provides a means to use existing zoning scripts that rely on the CLI but doing so should be a bridge to fully API scripting.

py cli_zone.py –ip xxx.xxx.xxx.xxx –id admin –pw password –s self –cli zone_commands.txt

# *combine*

Merges the output from execution of capture.py on multiple chassis. This is how the fabric wide database is built for fabrics of more than one switch.

py combine.py –i data_folder –o combined.json

# *compare_report*

Compares two databases and generates an Excel Workbook with all the differences. There is some intelligence in that there is a table that controls the comparisons. For example, Tx and Rx byte counters are ignored since these counters are always increasing so a report filled with Tx and Rx byte count changes would just be noise so these are skipped. Similarly, a 0.1 dBm change in output power level of an SFP is uninteresting so there is a tolerance range for statistical counters.

To edit the control table, search for _control_tables.

py compare_report.py –b old_project.json –c new_project.json –r comparison_report

# *lib_check*

Used to validate proper installation of Python and the Python libraries required by these modules.

py lib_check.py

# *multi_capture*

Reads a list of login credentials from a file and does the following:

1) Launches capture.py for each switch in the input file
2) After all captures complete, launches combine.py
3) Optionally generates a report

py multi_capture.py –i switches.csv

# *report*

Generates an Excel report that includes:

* A dashboard with all best practice violations and faults
* A worksheet with basic chassis information for each chassis
* A worksheet with basic fabric information for each fabric
* A detailed zone analysis for each fabric
* Worksheets for port statistics
* And more

py report.py –i combined.json –o report –sfp sfp_rules_r9

# *scan*

Reads a data collection as output from capture.py or combined.py
and displays basic chassis, fabric, and switch information.

py scan.py -i combined.json

# *scc_policy*

Used primarily in mainframe environments to set the SCC_POLICY
in one or more logical switches.

py scc_policy.py -i switches_to_include.xlsx

# *search*

Primarily intended as a programmer’s example on how to use the
search features of the brcddb libraries.

# *stats_c*

Collects port statistics to be fed to stats_g.py. Typically, the Kafka streams from SANnav are used for gathering port statistics. This module is useful when Kafka recipients have not been configured.

py stats_c.py –ip xxx.xxx.xxx.xxx –id admin –pw password –s self –fid 128 –o stats.json

# *stats_g*

Reads the output of stats_c and formats into an Excel Workbook. Since all statistical counters are cumulative, the counter from the previous poll is subtracted so that incremental statistics are reported. There is an option to create graphs.

py stats_g.py –i stats.json –r stats_report

# *zone_merge*

Merges the zone databases from multiple fabrics. A test mode allows you to validate if the zone database could be merged without actually merging the zone database. Input is taken from an Excel file.

py zone_merge.py –i zone_merge_sample

# *zone_restore*

Sets the zone database to that of a previously captured zone database. Typically used for restoring a zone database.

**Revision History**

# *20 Feb 2026*
* Updated copyright notice
* Added ability to collect, stats_c.py, and graph, stats_g.py, from multiple switches
* Miscellaneous bug fixes

# *19 Oct 2025*
* Added scc_policy.py - Distributes SCC_POLICY. Primarily for mainframe environments
* Added scan.py - Interogates data collections for basic fabric, chassis, and switch information.
* Added summary RNID to report.py output
* Bug fix with create_swconfig.py

# *25 August 2025*
* Added library version to the log file
* Added scc_policy.py
* Added scan.py

# *12 April 2025*
* Added support for additional leaves in FOS 9.2
* Added ability to execute multiple CLI commands from configuration workbook
* Improved switch configuration workbook instructions
  
# *01 Mar 2025*
* Added zone cleanup worksheets
* Misc bug fixes

# *3 Feb 2025*
* Added "full purge" option for zone_config.py.

# *28 Dec 2024 & 4 Jan 2025*
* Added fixed port switches and 4 slot directors to create_swconfig.py
* Add mainframe zoning, mf_zone.py
* Added column "CLI" column to switch configuration workbooks

# *Update 6 Dec 2024*
* Automatically grouped mainframe devices in group section of report.py
* Added Tx and Rx to several report pages
* Miscellaneous bug fixes

# *Update 29 Oct 2024*

* Fixed graphing capabilities in stats_g.py
* Improved error messages in several modules.

# *Update 20 Oct 2024*
* Primary changes were to support the new chassis and report pages.

# *Updates 16 Jun 2024*

* Fixed numerous spelling and grammar mistakes

# *Updates 15 May 2024*

* Added ability to purge zones and aliases to zone_config.py
* Added search by zone to nodefind.py
* Miscellanious bug fixes

# *Updates 6 March 2024*

* Added restore.py
* Improved error messaging
* Updated comments

# *Updates 4 Aug 2023*

*  Initial launch under Consoli Solutions, LLC

