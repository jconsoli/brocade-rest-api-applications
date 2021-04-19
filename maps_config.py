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
:mod:`maps_config.py` - Creates MAPS SFP rules from an Excel Workbook. Useful as is or an example on how to:

    * Determine the active policy
    * Clone a policy
    * Create new rules
    * Modify the cloned policy
    * Activate a MAPS policy

Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 1.0.0     | 26 Jan 2021   | Initial Launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.1     | 27 Jan 2021   | Fix bug where SFP rules were not cloned if an SFP Workbook was not included.      |
    +-----------+---------------+-----------------------------------------------------------------------------------+
    | 1.0.2     | 13 Feb 2021   | Added # -*- coding: utf-8 -*-                                                     |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""
__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2021 Jack Consoli'
__date__ = '13 Feb 2021'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack.consoli@broadcom.com'
__maintainer__ = 'Jack Consoli'
__status__ = 'Released'
__version__ = '1.0.2'

import argparse
import brcdapi.pyfos_auth as pyfos_auth
import brcdapi.log as brcdapi_log
import brcdapi.brcdapi_rest as brcdapi_rest
import brcddb.report.utils as report_utils
import brcddb.api.interface as api_int
import brcddb.brcddb_common as brcddb_common

_DOC_STRING = False  # Should always be False. Prohibits any actual I/O. Only useful for building documentation
_MAX_RULE_BATCH = 20  # Maximum number of MAPS rules to create in one API call. This is far more conservative than req.
_DEBUG = False   # When True, use _DEBUG_xxx below instead of parameters passed from the command line.
_DEBUG_IP = '10.8.105.10'
_DEBUG_ID = 'admin'
_DEBUG_PW = 'password'
_DEBUG_SEC = 'self'  # 'none'
_DEBUG_FID = 2
_DEBUG_NP = 'Test_Policy_2'
_DEBUG_MP = 'dflt_aggressive_policy'
_DEBUG_F = 'sfp_rules_r9.xlsx'
_DEBUG_A = False
_DEBUG_SUPPRESS = False
_DEBUG_VERBOSE = False
_DEBUG_LOG = '_logs'
_DEBUG_NL = False

_sfp_groups = list()  # List of SFP groups read from the switch
_sfp_monitoring_system = list()  # I shoe horned this in after the fact to be able to clone a policy without new rules

def _get_groups(session, fid):
    """Get the defined groups

    :param session: Session object returned from brcdapi.pyfos_auth.login()
    :type session: dict
    :param fid: Fabric ID of the logical switch whose MAPS policy we want to modify. None if not VF enabled
    :type fid: None, int
    :return: List of defined group names
    :rtype: list
    """
    group_obj = api_int.get_rest(session, 'brocade-maps/group', None, fid)
    if pyfos_auth.is_error(group_obj):
        brcdapi_log.log('Failed to get MAPS groups.', True)  # api_int.get_rest() logs detailed error message
        return None
    # obj.get('name') should never be None. This is just extra caution
    return [obj.get('name') for obj in group_obj.get('group') if obj.get('name') is not None]


def _get_policy(session, fid, policy=None):
    """Get the specified MAPS policy. If None, return the active MAPS policy

    :param session: Session object returned from brcdapi.pyfos_auth.login()
    :type session: dict
    :param fid: Fabric ID of the logical switch whose MAPS policy we want to modify. None if not VF enabled
    :type fid: None, int
    :param policy: Name of policy to look for. If None, returns the active policy
    :type policy: str, None
    :return: Active MAPS policy. None if no active MAPS policy
    :rtype: int
    """
    # Get the policies
    obj = api_int.get_rest(session, 'brocade-maps/maps-policy', None, fid)
    if pyfos_auth.is_error(obj):
        brcdapi_log.log('Failed to get MAPS policies.', True)  # api_int.get_rest() logs detailed error message
        return brcddb_common.EXIT_STATUS_API_ERROR, None

    # Find the policy to return
    for maps_policy in obj.get('maps-policy'):
        if policy is None:
            if maps_policy.get('is-active-policy'):
                return brcddb_common.EXIT_STATUS_OK, maps_policy
        elif maps_policy.get('name') == policy:
            return brcddb_common.EXIT_STATUS_OK, maps_policy
    return brcddb_common.EXIT_STATUS_INPUT_ERROR, None  # If we got this far, we didn't find the policy


def _create_new_rules(session, fid, new_sfp_rules):
    """Create all new SFP rules

    :param session: Session object returned from brcdapi.pyfos_auth.login()
    :type session: dict
    :param fid: Fabric ID of the logical switch whose MAPS policy we want to modify. None if not VF enabled
    :type fid: None, str
    :param new_sfp_rules: List of dictionaries of rules returned from report_utils.parse_sfp_file_for_rules()
    :type new_sfp_rules: list
    :return: List of new rules created.
    """
    # Build the new rules content for the API POST request
    sum_new_rules = list()
    num_rules = len(new_sfp_rules)
    # After writing the code, I was getting HTTP connection timeouts so I had to batch the number of rules to add.
    i = 0
    while i < num_rules:
        x = i + _MAX_RULE_BATCH if i + _MAX_RULE_BATCH <= num_rules else num_rules
        new_rules = new_sfp_rules[i:x]
        obj = brcdapi_rest.send_request(session, 'brocade-maps/rule', 'POST', dict(rule=new_rules), fid)
        if pyfos_auth.is_error(obj):
            # If the rule already exists, you cannot use POST or PATCH to write over it and PUT is not supported. I'm
            # assuming you could DELETE then POST and I could also check to see if the rule is changing but this simple
            # example on how to modify a MAPS policy is already getting to complicated so I just post warnings.
            er_l = list()
            er_obj = dict(errors=dict(error=er_l))
            if 'errors' in obj and isinstance(obj['errors'].get('error'), list):
                for d in obj['errors']['error']:
                    buf = d.get('error-message')
                    if buf is not None and buf == 'Rule name is present.' and isinstance(d.get('error-path'), str):
                        brcdapi_log.log('Rule ' + d['error-path'].replace('/rule/name/', '').replace('/', '')
                                        + ' already exists. Not changed.', True)
                    else:
                        er_l.append(d)
            if len(er_l) > 0:
                brcdapi_log.log('Failed to create rules. API response:' + pyfos_auth.formatted_error_msg(er_obj), True)
                return sum_new_rules  # If we get here, something is really wrong so just bail out
        # rule.get('name') should never be None in the line below. I'm just extra cautious
        sum_new_rules.extend([rule.get('name') for rule in new_rules if rule.get('name') is not None])
        i = x
    return sum_new_rules


def _rules_to_keep(session, fid, maps_policy):
    """Get the current MAPS rules 'brocade-maps/rule' from specified policy and remove all the SFP rules.

    :param session: Session object returned from brcdapi.pyfos_auth.login()
    :type session: dict
    :param fid: Fabric ID of the logical switch whose MAPS policy we want to modify. None if not VF enabled
    :type fid: None, str
    :param maps_policy: MAPS policy from 'brocade-maps/maps-policy' to keep
    :type maps_policy: dict
    :return: List of rule names to keep. None if error encountered
    :rtype: list
    """
    global _sfp_groups

    # Get all the MAPS rules
    obj = api_int.get_rest(session, 'brocade-maps/rule', None, fid)
    if pyfos_auth.is_error(obj):
        brcdapi_log.log('Failed to get MAPS rules.', True)  # api_int.get_rest() logs detailed error message
        return None

    # Remove all old SFP rules and add the new rules
    rule_list = maps_policy.get('rule-list').get('rule')
    # return [rule.get('name') for rule in obj.get('rule') if rule.get('monitoring-system') not in _sfp_monitoring_system
    #         and rule.get('group-name') not in _sfp_groups and rule.get('name') in rule_list]
    return [rule.get('name') for rule in obj.get('rule') if rule.get('monitoring-system') not in _sfp_monitoring_system
            and rule.get('name') in rule_list]


def _create_new_policy(session, fid, policy, rule_list, enable_flag=False):
    """Create a new MAPS policy.

    :param session: Session object returned from brcdapi.pyfos_auth.login()
    :type session: dict
    :param fid: Fabric ID of the logical switch whose MAPS policy we want to modify. None if not VF enabled
    :type fid: None, str
    :param policy: Name of the MAPS policy to create
    :type policy: str
    :param rule_list: List of rule names for the MAPS policy
    :type rule_list: list
    :param enable_flag: If True, enables the policy
    :type enable_flag: bool
    :return: List of new rules
    :rtype: list
    """
    new_content = {
        'name': policy,
        'rule-list': {'rule': rule_list},
        'is-active-policy': enable_flag
    }

    # Now send the new MAPS policy to the switch
    obj = brcdapi_rest.send_request(session, 'brocade-maps/maps-policy', 'POST', {'maps-policy': new_content}, fid)
    if pyfos_auth.is_error(obj):
        brcdapi_log.log('Failed to set MAPS policy. API response:\n' + pyfos_auth.formatted_error_msg(obj), True)
        brcdapi_log.log('This typically occurs when the policy already exists.', True)
        return brcddb_common.EXIT_STATUS_API_ERROR
    return brcddb_common.EXIT_STATUS_OK


def _modify_maps(session, fid, new_sfp_rules, new_policy, old_policy, enable_flag=False):
    """Calls the methods to create new rules, new policy, and activate the new policy.

    :param session: Session object returned from brcdapi.pyfos_auth.login()
    :type session: dict
    :param fid: Fabric ID of the logical switch whose MAPS policy we want to modify. None if not VF enabled
    :type fid: None, str
    :param new_sfp_rules: List of dictionaries of rules returned from report_utils.parse_sfp_file_for_rules()
    :type new_sfp_rules: list
    :param new_policy: Name of new policy to create
    :type new_policy: str
    :param old_policy: Name of MAPS policy to use as a basis for the new policy. If None, the active policy is used
    :type old_policy: str, None
    :param enable_flag: If True, enables the newly created MAPS policy
    :type enable_flag: bool
    :return: Exit code
    :rtype: int
    """
    # Get the MAPS policy
    ec, policy_obj = _get_policy(session, fid, old_policy)
    if policy_obj is None:
        brcdapi_log.log('Could not find MAPS policy: ' + 'Active Policy' if old_policy is None else old_policy, True)
        return ec

    # Create the new rules and new policy
    return _create_new_policy(session,
                              fid,
                              new_policy,
                              _create_new_rules(session, fid, new_sfp_rules) + _rules_to_keep(session, fid, policy_obj),
                              enable_flag)


def parse_args():
    """Parses the module load command line

    :return ip: IP address
    :rtype ip: str
    :return id: User ID
    :rtype id: str
    :return pw: Password
    :rtype pw: str
    :return s: Type of HTTP security. None if not specified
    :rtype s: str, None
    :return fid: Fabric ID
    :rtype fid: int
    :return n: Name of policy. None if not specified
    :rtype n: str, None
    :return f: Name of Excel file with new SFP rules
    :rtype f: str
    :return q: Quiet time
    :rtype q: int
    :return m: Optional. Name of MAPS policy to clone.
    :rtype m: str, None
    :return a: True - Policy should be activated. False - policy should not be activated.
    :rtype a: bool
    """
    global _DEBUG_IP, _DEBUG_ID, _DEBUG_PW, _DEBUG_SEC, _DEBUG_FID, _DEBUG_NP, _DEBUG_F, _DEBUG_MP,\
        _DEBUG_A, _DEBUG_SUPPRESS, _DEBUG_VERBOSE, _DEBUG_LOG, _DEBUG_NL

    if _DEBUG:
        return _DEBUG_IP, _DEBUG_ID, _DEBUG_PW, _DEBUG_SEC, _DEBUG_FID, _DEBUG_NP, _DEBUG_F, _DEBUG_MP,\
               _DEBUG_A, _DEBUG_SUPPRESS, _DEBUG_VERBOSE, _DEBUG_LOG, _DEBUG_NL
    buf = 'Clones a MAPS policy. Optionally replaces the SFPs rules with those read from a Workbook.'
    parser = argparse.ArgumentParser(description=buf)
    parser.add_argument('-ip', help='Required. IP address', required=True)
    parser.add_argument('-id', help='Required. User ID', required=True)
    parser.add_argument('-pw', help='Required. Password', required=True)
    parser.add_argument('-s', help='Optional. \'CA\' or \'self\' for HTTPS mode.', required=False,)
    parser.add_argument('-fid', help='Required. FID number', required=True,)
    parser.add_argument('-n', help='Required. Name of new MAPS policy to create.', required=True,)
    buf = 'Optional. Name of Excel Workbook with new SFP rules. When specified, all SFP rules are removed from the '\
          'policy and only those rules defined in the Workbook are added. The Excel file must be in the format of '\
          'sfp_rules_rx.xlsx which can be found on github/jconsoli/applications. If omitted, the policy specified '\
          'with the -n option is cloned without modifying any rules.'
    parser.add_argument('-sfp', help=buf, required=False,)
    buf = 'Optional. Name of MAPS policy to clone. If omitted, the active policy is cloned.'
    parser.add_argument('-m', help=buf, required=False,)
    buf = 'Optional. No arguments. When specified, activates the new MAPS policy'
    parser.add_argument('-a', help=buf, default=False, action='store_true', required=False,)
    buf = 'Optional. Suppress all library generated output to STD_IO except the exit code. Useful with batch ' \
          'processing'
    parser.add_argument('-sup', help=buf, action='store_true', required=False)
    parser.add_argument('-d', help='Enable debug logging', action='store_true', required=False)
    buf = '(Optional) Directory where log file is to be created. Default is to use the current directory. The log ' \
          'file name will always be "Log_xxxx" where xxxx is a time and date stamp.'
    parser.add_argument('-log', help=buf, required=False, )
    buf = '(Optional) No parameters. When set, a log file is not created. The default is to create a log file.'
    parser.add_argument('-nl', help=buf, action='store_true', required=False)
    args = parser.parse_args()
    return args.ip, args.id, args.pw, args.s, args.fid, args.n, args.sfp, args.m, args.a, args.sup, args.d, args.log,\
           args.nl


def pseudo_main():
    """Basically the main().

    :return: Exit code
    :rtype: int
    """
    global _DEBUG, _sfp_monitoring_system

    # Get and validate the command line input
    ml = ['WARNING!!! Debug is enabled'] if _DEBUG else list()
    ip, user_id, pw, sec, fid, new_policy, file, mp, enable_flag, s_flag, vd, log, nl = parse_args()
    if vd:
        brcdapi_rest.verbose_debug = True
    if not nl:
        brcdapi_log.open_log(log)
    if s_flag:
        brcdapi_log.set_suppress_all()
    fid = int(fid)
    if sec is None:
        sec = 'none'
    ml.extend([
        'FID:                 ' + str(fid),
        'New policy:          ' + new_policy,
        'SFP rules file:      ' + str(file),
        'Policy to clone:     ' + 'Active' if mp is None else mp,
        'Activate new policy: ' + 'Yes' if enable_flag else 'No',
        'The \'User Warning: Data Validation ...\' can be ignored.',
        ])
    brcdapi_log.log(ml, True)

    # Login
    session = api_int.login(user_id, pw, ip, sec)
    if pyfos_auth.is_error(session):  # api_int.login() logs detailed error message
        return brcddb_common.EXIT_STATUS_API_ERROR

    # try/except used during development to ensure logout due to programming errors.
    ec = brcddb_common.EXIT_STATUS_ERROR  # Return code normally gets overwritten
    try:
        if file is None:
            sfp_rules = list()
        else:
            brcdapi_log.log('Adding rules can take up to a minute. Please be patient.', True)
            _sfp_monitoring_system = ['CURRENT', 'RXP', 'SFP_TEMP', 'TXP', 'VOLTAGE']
            sfp_rules = report_utils.parse_sfp_file_for_rules(file, _get_groups(session, fid))
        if sfp_rules is None:
            brcdapi_log.log('Error opening or reading ' + file, True)
        else:
            ec = _modify_maps(session, fid, sfp_rules, new_policy, mp, enable_flag)
    except:
        brcdapi_log.log('Programming error encountered', True)

    obj = brcdapi_rest.logout(session)
    if pyfos_auth.is_error(obj):
        brcdapi_log.log('Logout failed. API response:\n' + pyfos_auth.formatted_error_msg(obj), True)
        ec = brcddb_common.EXIT_STATUS_API_ERROR

    return ec


###################################################################
#
#                    Main Entry Point
#
###################################################################
_ec = brcddb_common.EXIT_STATUS_OK
if _DOC_STRING:
    print('_DOC_STRING is True. No processing')
else:
    _ec = pseudo_main()
    brcdapi_log.close_log('Processing Complete. Exit code: ' + str(_ec), False)
exit(_ec)
