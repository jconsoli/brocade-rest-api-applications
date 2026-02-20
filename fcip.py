#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2025 Jack Consoli.  All rights reserved.
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
:mod:`cli_test` - Test switchshow parsing with SX6 blade

Notes::

portshow fciptunnel all --circuit --ip-address
# The 't' option is not supported in older versions of FOS
# If an error is returned, just use portshow fciptunnel all -cpsq
portshow fciptunnel all -ctpsq
# The s option above says return just the summary. For full details:
portshow fciptunnel all -ctpq
portcfgshow fciptunnel all
portshow fcipcircuit all
portcfgshow fcipcircuit all
portshow fciptunnel ge0
# View the interface
portcfgshow ipif

# Clear (set to 0) all circuit statistics
portshow fcipcircuit all --reset
# Clear (set to 0) all tunnel statistics
portshow fciptunnel all --reset

# Disable autonegotiation
portCfgGe 9/ge2 --disable -autoneg
# Set port speed
portCfgGe 9/ge2 --set -speed 10G

# IPSEC policy pre-shared key (16-64 characters)
ipsec-policy morgan_ipsec1 create -k "presharedkey"

# Configure interface
portcfg ipif 9/ge2.dp0 create 10.2.8.34/29 mtu auto vlan 500e 10.2.8.34/29 mtu auto vlan 500 10.2.8.34/29 mtu auto \
    vlan 500 10.2.8.34/29 mtu auto vlan 500 10.2.8.34/29 mtu auto vlan 500 10.2.8.34/29 mtu auto vlan 500 10.2.8.34/29 \
    mtu auto vlan 500m 10.2.8.34/29 mtu auto vlan 500o 10.2.8.34/29 mtu auto vlan 500d 10.2.8.34/29 mtu auto vlan 500i \
    10.2.8.34/29 mtu auto vlan 500f 10.2.8.34/29 mtu auto vlan 500y 10.2.8.34/29 mtu auto vlan 500




From MS::

=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.03.31 09:06:06 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> timeout
Shell Idle Timeout is 60 minutes
Session Idle Timeout is disabled.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> extncfg --app-mode fcip
extncfg: slot option is required.

Usage: extncfg <action> [options]

action:
  --ve-mode 10VE|20VE [-slot <#>]      - Set VE-Mode to 10VE or 20VE mode.
  --ge-mode copper|optical [-slot <#>] - Set GE-Mode to copper or optical.
  --app-mode fcip|hybrid [-slot <#>]   - Set APP-Mode to FCIP or HYBRID
                                         (FCIP with IPEXT).
  --show [-slot <#>|-all]              - Display APP/VE/GE mode details.
  --config -default [-slot <#>|-all]   - Default the Extension configuration.
  --config -clear -slot <#>            - clear the Extension configuration.
  --config -manager                    - Run the extension configuration
                                         management utility.
  --fwdl-prep [-version #.#.#] [-abort] - Prepare the switch for firmware
                                         download to the target version.
  -h,--help                            - Print this usage statement.

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> extncfg --app-mode fcip -slot 9
App mode is already set to FCIP.
Nothing to modify.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> extncfg --app-mode fcip -slot 9 10
App mode is already set to FCIP.
Nothing to modify.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portCfgGe 9/ge2 --disable -autoneg
Nothing to modify.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portCfgGe 9/ge10 --disable -autoneg
Nothing to modify.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portCfgGe 10/ge2 --disable -autoneg
Nothing to modify.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portCfgGe 10/ge2 --disable -autoneg /ge2 --disable -autoneg 1 --disable -autoneg 0 --disable -autoneg
Nothing to modify.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> timed out waiting for input: auto-logout
Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.03.31 11:31:04 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portCfgGe 9/ge2 --set -speed 10G
Nothing to modify.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portCfgGe 9/ge10 --set -speed 10G
Nothing to modify.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portCfgGe 10/ge2 --set -speed 10G
Nothing to modify.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portCfgGe 10/ge10 --set -speed 10G
Nothing to modify.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg ipsec-policy morgan_ipsec1 create -k "eraw
drahfmsm"
IPSec-Policy pre-shared key invalid.
IPSec Policy pre-shared key too short. Key length must be between 16-64 characters.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg ipsec-policy morgan_ipsec1 create -k "eraw
drahfmyelnatsnagrom"
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> Configure ipif              portcfg ipif 9/ge2.dp0 create 10.2.8.34/29 mtu aut
o vlan 500
IP Address already configured.
IP Address 10.2.8.34 already configured on port 9/ge2.dp0.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow ipif

 Port         IP Address                     / Pfx  MTU   VLAN  Flags
--------------------------------------------------------------------------------
 9/ge2.dp0    10.2.8.34                      / 29   9214  500
 9/ge2.dp1    10.2.8.35                      / 29   9214  500
 9/ge10.dp0   10.2.8.42                      / 29   9214  600
 9/ge10.dp1   10.2.8.43                      / 29   9214  600
 10/ge2.dp0   10.2.8.50                      / 29   9214  501
 10/ge2.dp1   10.2.8.51                      / 29   9214  501
 10/ge10.dp0  10.2.8.58                      / 29   9214  601
 10/ge10.dp1  10.2.8.59                      / 29   9214  601
--------------------------------------------------------------------------------
Flags: I=InUse X=Crossport

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg ipif 9/ge2.dp0 create 10.2.8.34/29 mtu auto vlan 500e 10.2.8.34/29 mtu auto vlan 500 10.2.8.34/29 mtu auto vlan 500 10.2.8.34/29 mtu auto vlan 500 10.2.8.34/29 mtu auto vlan 500 10.2.8.34/29 mtu auto vlan 500 10.2.8.34/29 mtu auto vlan 500m 10.2.8.34/29 mtu auto vlan 500o 10.2.8.34/29 mtu auto vlan 500d 10.2.8.34/29 mtu auto vlan 500i 10.2.8.34/29 mtu auto vlan 500f 10.2.8.34/29 mtu auto vlan 500y 10.2.8.34/29 mtu auto vlan 500

!!!! WARNING !!!!
Modify operation can disrupt the traffic on any tunnel using this IP address. This operation may bring the existing tunnel down (if tunnel is up) before applying new configuration.

Note: This operation can take a long time depending on the size or complexity of the configuration. It may take up to 3 minutes in some cases.

Continue with Modification (Y,y,N,n): [ n]y
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow ipifCfgGe 10/ge10 --set -speed 10G2 --set -speed 10G9/ge10 --set -speed 10G2 --set -speed 10G                                portcfgshow ipif

 Port         IP Address                     / Pfx  MTU   VLAN  Flags
--------------------------------------------------------------------------------
 9/ge2.dp0    10.2.8.34                      / 29   AUTO  500
 9/ge2.dp1    10.2.8.35                      / 29   9214  500
 9/ge10.dp0   10.2.8.42                      / 29   9214  600
 9/ge10.dp1   10.2.8.43                      / 29   9214  600
 10/ge2.dp0   10.2.8.50                      / 29   9214  501
 10/ge2.dp1   10.2.8.51                      / 29   9214  501
 10/ge10.dp0  10.2.8.58                      / 29   9214  601
 10/ge10.dp1  10.2.8.59                      / 29   9214  601
--------------------------------------------------------------------------------
Flags: I=InUse X=Crossport

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg ipif 9/ge10.dp0 modify 10.2.8.42/29 mtu auto vlan 600

!!!! WARNING !!!!
Modify operation can disrupt the traffic on any tunnel using this IP address. This operation may bring the existing tunnel down (if tunnel is up) before applying new configuration.

Note: This operation can take a long time depending on the size or complexity of the configuration. It may take up to 3 minutes in some cases.

Continue with Modification (Y,y,N,n): [ n]y
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg ipif 10/ge2.dp0 modify 10.2.8.50/29 mtu auto vlan 501

!!!! WARNING !!!!
Modify operation can disrupt the traffic on any tunnel using this IP address. This operation may bring the existing tunnel down (if tunnel is up) before applying new configuration.

Note: This operation can take a long time depending on the size or complexity of the configuration. It may take up to 3 minutes in some cases.

Continue with Modification (Y,y,N,n): [ n]y
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg ipif 10/ge10.dp0 modify 10.2.8.58/29 mtu auto vlan 601

!!!! WARNING !!!!
Modify operation can disrupt the traffic on any tunnel using this IP address. This operation may bring the existing tunnel down (if tunnel is up) before applying new configuration.

Note: This operation can take a long time depending on the size or complexity of the configuration. It may take up to 3 minutes in some cases.

Continue with Modification (Y,y,N,n): [ n]y
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg ipif 9/ge2.dp1 modify 10.2.8.35/29 mtu auto vlan 500

!!!! WARNING !!!!
Modify operation can disrupt the traffic on any tunnel using this IP address. This operation may bring the existing tunnel down (if tunnel is up) before applying new configuration.

Note: This operation can take a long time depending on the size or complexity of the configuration. It may take up to 3 minutes in some cases.

Continue with Modification (Y,y,N,n): [ n]y
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg ipif 9/ge10.dp1 modify 10.2.8.43/29 mtu auto vlan 600

!!!! WARNING !!!!
Modify operation can disrupt the traffic on any tunnel using this IP address. This operation may bring the existing tunnel down (if tunnel is up) before applying new configuration.

Note: This operation can take a long time depending on the size or complexity of the configuration. It may take up to 3 minutes in some cases.

Continue with Modification (Y,y,N,n): [ n]y
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg ipif 10/ge2.dp1 modify 10.2.8.51/29 mtu auto vlan 501

!!!! WARNING !!!!
Modify operation can disrupt the traffic on any tunnel using this IP address. This operation may bring the existing tunnel down (if tunnel is up) before applying new configuration.

Note: This operation can take a long time depending on the size or complexity of the configuration. It may take up to 3 minutes in some cases.

Continue with Modification (Y,y,N,n): [ n]y
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg ipif 10/ge10.dp1 modify 10.2.8.59/29 mtu auto vlan 601

!!!! WARNING !!!!
Modify operation can disrupt the traffic on any tunnel using this IP address. This operation may bring the existing tunnel down (if tunnel is up) before applying new configuration.

Note: This operation can take a long time depending on the size or complexity of the configuration. It may take up to 3 minutes in some cases.

Continue with Modification (Y,y,N,n): [ n]y
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --ping 9/ge2.dp0 -s 10.2.8.34 -d 10.2.18.34

PING 10.2.18.34 (10.2.8.34) with 64 bytes of data.

IProute does not exist.
Destination IP address 10.2.18.34 has no configured route.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow ipif

 Port         IP Address                     / Pfx  MTU   VLAN  Flags
--------------------------------------------------------------------------------
 9/ge2.dp0    10.2.8.34                      / 29   AUTO  500
 9/ge2.dp1    10.2.8.35                      / 29   AUTO  500
 9/ge10.dp0   10.2.8.42                      / 29   AUTO  600
 9/ge10.dp1   10.2.8.43                      / 29   AUTO  600
 10/ge2.dp0   10.2.8.50                      / 29   AUTO  501
 10/ge2.dp1   10.2.8.51                      / 29   AUTO  501
 10/ge10.dp0  10.2.8.58                      / 29   AUTO  601
 10/ge10.dp1  10.2.8.59                      / 29   AUTO  601
--------------------------------------------------------------------------------
Flags: I=InUse X=Crossport

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> timed out waiting for input: auto-logout
Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.03.31 16:02:41 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg iproute 9/ge2.dp0  create 10.2.18.32/29 10
.2.8.33
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg iproute 9/ge2.dp1  create 10.2.18.32/29 10.2.8.33
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg iproute 9/ge10.dp0  create 10.2.18.40/29 10.2.8.49
Route gateway unreachable.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg iproute 9/ge10.dp1  create 10.2.48.40/29 10.2.8.49
Route gateway unreachable.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg iproute 10/ge2.dp0  create 10.2.18.48/29 10.2.8.49
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg iproute 10/ge2.dp1  create 10.2.18.48/29 10.2.8.49
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg iproute 10/ge10.dp0  create 10.2.18.56/29 10.2.8.57
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg iproute 10/ge10.dp1  create 10.2.18.56/29 10.2.8.57
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --ping 9/ge2.dp0 -s 10.2.8.34 -d 10.2.18.34

PING 10.2.18.34 (10.2.8.34) with 64 bytes of data.
From 10.2.18.34: icmp_seq=1 Destination host unreachable
From 10.2.18.34: icmp_seq=2 Request timed out
From 10.2.18.34: icmp_seq=3 Destination host unreachable
From 10.2.18.34: icmp_seq=4 Request timed out

--- 10.2.18.34 ping statistics ---
4 packets transmitted, 0 received, 100% packet loss, time 6116 ms

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> switchshow
switchName:REPISG1A_DEF
switchType:180.0
switchState:Online
switchMode:Native
switchRole:Principal
switchDomain:26
switchId:fffc1a
switchWwn:10:00:d8:1f:cc:71:62:00
zoning:OFF
switchBeacon:OFF
FC Router:OFF
Fabric Name:REPISG1A/EA_FAB
HIF Mode:OFF
Allow XISL Use:OFF
LS Attributes:[FID: 128, Base Switch: No, Default Switch: Yes, Ficon Switch: No, Address Mode 0]
Index Slot Port Address Media  Speed        State    Proto
============================================================
   0    3    0   1a0000   id    N32  No_Light    FC
   1    3    1   1a0100   id    N32  No_Light    FC
   2    3    2   1a0200   id    N32  No_Light    FC
   3    3    3   1a0300   id    N32  No_Light    FC
   4    3    4   1a0400   id    N32  No_Light    FC
   5    3    5   1a0500   id    N32  No_Light    FC
   6    3    6   1a0600   id    N32  No_Light    FC
   7    3    7   1a0700   id    N32  No_Light    FC
   8    3    8   1a0800   id    N32  No_Light    FC
   9    3    9   1a0900   id    N32  No_Light    FC
  10    3   10   1a0a00   id    N32  No_Light    FC
  11    3   11   1a0b00   id    N32  No_Light    FC
  12    3   12   1a0c00   id    N32  No_Light    FC
  13    3   13   1a0d00   id    N32  No_Light    FC
  14    3   14   1a0e00   id    N32  No_Light    FC
  15    3   15   1a0f00   id    N32  No_Light    FC
  16    3   16   1a1000   id    N32  No_Light    FC
  17    3   17   1a1100   id    N32  No_Light    FC
  18    3   18   1a1200   id    N32  No_Light    FC
  19    3   19   1a1300   id    N32  No_Light    FC
  20    3   20   1a1400   id    N32  No_Light    FC
  21    3   21   1a1500   id    N32  No_Light    FC
  22    3   22   1a1600   id    N32  No_Light    FC
  23    3   23   1a1700   id    N32  No_Light    FC
  24    3   24   1a1800   id    N32  No_Light    FC
  25    3   25   1a1900   id    N32  No_Light    FC
  26    3   26   1a1a00   id    N32  No_Light    FC
  27    3   27   1a1b00   id    N32  No_Light    FC
  28    3   28   1a1c00   id    N32  No_Light    FC
  29    3   29   1a1d00   id    N32  No_Light    FC
  30    3   30   1a1e00   id    N32  No_Light    FC
  31    3   31   1a1f00   id    N32  No_Light    FC
  32    3   32   1a2000   id    N32  No_Light    FC
  33    3   33   1a2100   id    N32  No_Light    FC
  34    3   34   1a2200   id    N32  No_Light    FC
  35    3   35   1a2300   id    N32  No_Light    FC
  36    3   36   1a2400   id    N32  No_Light    FC
  37    3   37   1a2500   id    N32  No_Light    FC
  38    3   38   1a2600   id    N32  No_Light    FC
  39    3   39   1a2700   id    N32  No_Light    FC
  40    3   40   1a2800   id    N32  No_Light    FC
  41    3   41   1a2900   id    N32  No_Light    FC
  42    3   42   1a2a00   id    N32  No_Light    FC
  43    3   43   1a2b00   id    N32  No_Light    FC
  44    3   44   1a2c00   id    N32  No_Light    FC
  45    3   45   1a2d00   id    N32  No_Light    FC
  46    3   46   1a2e00   id    N32  No_Light    FC
  47    3   47   1a2f00   id    N32  No_Light    FC
  96    4    0   1a6000   id    N32  No_Light    FC
  97    4    1   1a6100   id    N32  No_Light    FC
  98    4    2   1a6200   id    N32  No_Light    FC
  99    4    3   1a6300   id    N32  No_Light    FC
 100    4    4   1a6400   id    N32  No_Light    FC
 101    4    5   1a6500   id    N32  No_Light    FC
 102    4    6   1a6600   id    N32  No_Light    FC
 103    4    7   1a6700   id    N32  No_Light    FC
 104    4    8   1a6800   id    N32  No_Light    FC
 105    4    9   1a6900   id    N32  No_Light    FC
 106    4   10   1a6a00   id    N32  No_Light    FC
 107    4   11   1a6b00   id    N32  No_Light    FC
 108    4   12   1a6c00   id    N32  No_Light    FC
 109    4   13   1a6d00   id    N32  No_Light    FC
 110    4   14   1a6e00   id    N32  No_Light    FC
 111    4   15   1a6f00   id    N32  No_Light    FC
 112    4   16   1a7000   id    N32  No_Light    FC
 113    4   17   1a7100   id    N32  No_Light    FC
 114    4   18   1a7200   id    N32  No_Light    FC
 115    4   19   1a7300   id    N32  No_Light    FC
 116    4   20   1a7400   id    N32  No_Light    FC
 117    4   21   1a7500   id    N32  No_Light    FC
 118    4   22   1a7600   id    N32  No_Light    FC
 119    4   23   1a7700   id    N32  No_Light    FC
 120    4   24   1a7800   id    N32  No_Light    FC
 121    4   25   1a7900   id    N32  No_Light    FC
 122    4   26   1a7a00   id    N32  No_Light    FC
 123    4   27   1a7b00   id    N32  No_Light    FC
 124    4   28   1a7c00   id    N32  No_Light    FC
 125    4   29   1a7d00   id    N32  No_Light    FC
 126    4   30   1a7e00   id    N32  No_Light    FC
 127    4   31   1a7f00   id    N32  No_Light    FC
 128    4   32   1a8000   id    N32  No_Light    FC
 129    4   33   1a8100   id    N32  No_Light    FC
 130    4   34   1a8200   id    N32  No_Light    FC
 131    4   35   1a8300   id    N32  No_Light    FC
 132    4   36   1a8400   id    N32  No_Light    FC
 133    4   37   1a8500   id    N32  No_Light    FC
 134    4   38   1a8600   id    N32  No_Light    FC
 135    4   39   1a8700   id    N32  No_Light    FC
 136    4   40   1a8800   id    N32  No_Light    FC
 137    4   41   1a8900   id    N32  No_Light    FC
 138    4   42   1a8a00   id    N32  No_Light    FC
 139    4   43   1a8b00   id    N32  No_Light    FC
 140    4   44   1a8c00   id    N32  No_Light    FC
 141    4   45   1a8d00   id    N32  No_Light    FC
 142    4   46   1a8e00   id    N32  No_Light    FC
 143    4   47   1a8f00   id    N32  No_Light    FC
 768    7    0   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 769    7    1   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 770    7    2   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 771    7    3   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 772    7    4   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 773    7    5   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 774    7    6   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 775    7    7   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 776    7    8   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 777    7    9   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 778    7   10   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 779    7   11   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 780    7   12   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 781    7   13   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 782    7   14   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 783    7   15   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 784    7   16   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 785    7   17   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 786    7   18   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 787    7   19   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 788    7   20   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 789    7   21   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 790    7   22   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 791    7   23   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 792    7   24   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 793    7   25   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 794    7   26   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 795    7   27   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 796    7   28   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 797    7   29   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 798    7   30   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 799    7   31   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 800    7   32   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 801    7   33   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 802    7   34   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 803    7   35   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 804    7   36   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 805    7   37   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 806    7   38   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 807    7   39   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 808    7   40   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 809    7   41   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 810    7   42   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 811    7   43   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 812    7   44   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 813    7   45   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 814    7   46   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 815    7   47   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 816    7   48   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 817    7   49   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 818    7   50   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 819    7   51   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 820    7   52   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 821    7   53   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 822    7   54   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 823    7   55   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 824    7   56   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 825    7   57   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 826    7   58   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 827    7   59   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 828    7   60   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 829    7   61   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 830    7   62   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 831    7   63   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 832    8    0   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 833    8    1   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 834    8    2   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 835    8    3   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 836    8    4   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 837    8    5   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 838    8    6   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 839    8    7   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 840    8    8   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 841    8    9   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 842    8   10   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 843    8   11   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 844    8   12   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 845    8   13   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 846    8   14   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 847    8   15   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 848    8   16   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 849    8   17   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 850    8   18   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 851    8   19   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 852    8   20   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 853    8   21   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 854    8   22   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 855    8   23   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 856    8   24   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 857    8   25   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 858    8   26   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 859    8   27   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 860    8   28   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 861    8   29   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 862    8   30   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 863    8   31   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 864    8   32   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 865    8   33   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 866    8   34   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 867    8   35   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 868    8   36   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 869    8   37   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 870    8   38   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 871    8   39   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 872    8   40   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 873    8   41   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 874    8   42   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 875    8   43   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 876    8   44   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 877    8   45   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 878    8   46   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 879    8   47   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 880    8   48   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 881    8   49   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 882    8   50   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 883    8   51   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 884    8   52   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 885    8   53   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 886    8   54   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 887    8   55   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 888    8   56   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 889    8   57   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 890    8   58   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 891    8   59   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 892    8   60   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 893    8   61   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 894    8   62   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 895    8   63   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 384    9    0   1a8040   id    N32  No_Light    FC
 385    9    1   1a8140   id    N32  No_Light    FC
 386    9    2   1a8240   id    N32  No_Light    FC
 387    9    3   1a8340   id    N32  No_Light    FC
 388    9    4   1a8440   id    N32  No_Light    FC
 389    9    5   1a8540   id    N32  No_Light    FC
 390    9    6   1a8640   id    N32  No_Light    FC
 391    9    7   1a8740   id    N32  No_Light    FC
 392    9    8   1a8840   id    N32  No_Light    FC
 393    9    9   1a8940   id    N32  No_Light    FC
 394    9   10   1a8a40   id    N32  No_Light    FC
 395    9   11   1a8b40   id    N32  No_Light    FC
 396    9   12   1a8c40   id    N32  No_Light    FC
 397    9   13   1a8d40   id    N32  No_Light    FC
 398    9   14   1a8e40   id    N32  No_Light    FC
 399    9   15   1a8f40   id    N32  No_Light    FC
 400    9   16   1a9040   --    --   Offline     VE
 401    9   17   1a9140   --    --   Offline     VE
 402    9   18   1a9240   --    --   Offline     VE
 403    9   19   1a9340   --    --   Offline     VE
 404    9   20   1a9440   --    --   Offline     VE
 405    9   21   1a9540   --    --   Offline     VE  Disabled (10VE Mode)
 406    9   22   1a9640   --    --   Offline     VE  Disabled (10VE Mode)
 407    9   23   1a9740   --    --   Offline     VE  Disabled (10VE Mode)
 408    9   24   1a9840   --    --   Offline     VE  Disabled (10VE Mode)
 409    9   25   1a9940   --    --   Offline     VE  Disabled (10VE Mode)
 410    9   26   1a9a40   --    --   Offline     VE
 411    9   27   1a9b40   --    --   Offline     VE
 412    9   28   1a9c40   --    --   Offline     VE
 413    9   29   1a9d40   --    --   Offline     VE
 414    9   30   1a9e40   --    --   Offline     VE
 415    9   31   1a9f40   --    --   Offline     VE  Disabled (10VE Mode)
 416    9   32   1aa040   --    --   Offline     VE  Disabled (10VE Mode)
 417    9   33   1aa140   --    --   Offline     VE  Disabled (10VE Mode)
 418    9   34   1aa240   --    --   Offline     VE  Disabled (10VE Mode)
 419    9   35   1aa340   --    --   Offline     VE  Disabled (10VE Mode)
        9  ge0            --    40G    No_Module   FCIP
        9  ge1            --    40G    No_Module   FCIP
        9  ge2            id    10G    Online      FCIP
        9  ge3            --    10G    No_Module   FCIP
        9  ge4            --    10G    No_Module   FCIP
        9  ge5            --    10G    No_Module   FCIP
        9  ge6            --    10G    No_Module   FCIP
        9  ge7            --    10G    No_Module   FCIP
        9  ge8            --    10G    No_Module   FCIP
        9  ge9            --    10G    No_Module   FCIP
        9  ge10           id    10G    Online      FCIP
        9  ge11           --    10G    No_Module   FCIP
        9  ge12           --    10G    No_Module   FCIP
        9  ge13           --    10G    No_Module   FCIP
        9  ge14           --    10G    No_Module   FCIP
        9  ge15           --    10G    No_Module   FCIP
        9  ge16           --    10G    No_Module   FCIP
        9  ge17           --    10G    No_Module   FCIP
 480   10    0   1ae040   id    N32  No_Light    FC
 481   10    1   1ae140   id    N32  No_Light    FC
 482   10    2   1ae240   id    N32  No_Light    FC
 483   10    3   1ae340   id    N32  No_Light    FC
 484   10    4   1ae440   id    N32  No_Light    FC
 485   10    5   1ae540   id    N32  No_Light    FC
 486   10    6   1ae640   id    N32  No_Light    FC
 487   10    7   1ae740   id    N32  No_Light    FC
 488   10    8   1ae840   id    N32  No_Light    FC
 489   10    9   1ae940   id    N32  No_Light    FC
 490   10   10   1aea40   id    N32  No_Light    FC
 491   10   11   1aeb40   id    N32  No_Light    FC
 492   10   12   1aec40   id    N32  No_Light    FC
 493   10   13   1aed40   id    N32  No_Light    FC
 494   10   14   1aee40   id    N32  No_Light    FC
 495   10   15   1aef40   id    N32  No_Light    FC
 496   10   16   1af040   --    --   Offline     VE
 497   10   17   1af140   --    --   Offline     VE
 498   10   18   1af240   --    --   Offline     VE
 499   10   19   1af340   --    --   Offline     VE
 500   10   20   1af440   --    --   Offline     VE
 501   10   21   1af540   --    --   Offline     VE  Disabled (10VE Mode)
 502   10   22   1af640   --    --   Offline     VE  Disabled (10VE Mode)
 503   10   23   1af740   --    --   Offline     VE  Disabled (10VE Mode)
 504   10   24   1af840   --    --   Offline     VE  Disabled (10VE Mode)
 505   10   25   1af940   --    --   Offline     VE  Disabled (10VE Mode)
 506   10   26   1afa40   --    --   Offline     VE
 507   10   27   1afb40   --    --   Offline     VE
 508   10   28   1afc40   --    --   Offline     VE
 509   10   29   1afd40   --    --   Offline     VE
 510   10   30   1afe40   --    --   Offline     VE
 511   10   31   1aff40   --    --   Offline     VE  Disabled (10VE Mode)
 512   10   32   1a0080   --    --   Offline     VE  Disabled (10VE Mode)
 513   10   33   1a0180   --    --   Offline     VE  Disabled (10VE Mode)
 514   10   34   1a0280   --    --   Offline     VE  Disabled (10VE Mode)
 515   10   35   1a0380   --    --   Offline     VE  Disabled (10VE Mode)
       10  ge0            --    40G    No_Module   FCIP
       10  ge1            --    40G    No_Module   FCIP
       10  ge2            id    10G    Online      FCIP
       10  ge3            --    10G    No_Module   FCIP
       10  ge4            --    10G    No_Module   FCIP
       10  ge5            --    10G    No_Module   FCIP
       10  ge6            --    10G    No_Module   FCIP
       10  ge7            --    10G    No_Module   FCIP
       10  ge8            --    10G    No_Module   FCIP
       10  ge9            --    10G    No_Module   FCIP
       10  ge10           id    10G    Online      FCIP
       10  ge11           --    10G    No_Module   FCIP
       10  ge12           --    10G    No_Module   FCIP
       10  ge13           --    10G    No_Module   FCIP
       10  ge14           --    10G    No_Module   FCIP
       10  ge15           --    10G    No_Module   FCIP
       10  ge16           --    10G    No_Module   FCIP
       10  ge17           --    10G    No_Module   FCIP
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow 9/ge2
Eth Mac Address: d8.1f.cc.bf.0b.d2
Port State: 1Online
Port Phys:  6In_Sync
Port Flags: 0x4003 PRESENT ACTIVE LED
Port Speed: 10G
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow 9/ge2 10
Eth Mac Address: d8.1f.cc.bf.0b.da
Port State: 1Online
Port Phys:  6In_Sync
Port Flags: 0x4003 PRESENT ACTIVE LED
Port Speed: 10G
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow 9/ge10/ge101/ge100/ge10
Eth Mac Address: d8.1f.cc.44.01.da
Port State: 1Online
Port Phys:  6In_Sync
Port Flags: 0x4003 PRESENT ACTIVE LED
Port Speed: 10G
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow 10/ge100  2
Eth Mac Address: d8.1f.cc.44.01.d2
Port State: 1Online
Port Phys:  6In_Sync
Port Flags: 0x3 PRESENT ACTIVE
Port Speed: 10G
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --ping 9/ge2.dp0 -s 10.2.8.34 -d 10.2.18.34

PING 10.2.18.34 (10.2.8.34) with 64 bytes of data.
64 bytes from 10.2.18.34: icmp_seq=1 ttl=18 time=6 ms
64 bytes from 10.2.18.34: icmp_seq=2 ttl=18 time=5 ms
64 bytes from 10.2.18.34: icmp_seq=3 ttl=18 time=5 ms
64 bytes from 10.2.18.34: icmp_seq=4 ttl=18 time=5 ms

--- 10.2.18.34 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 125 ms
rtt min/avg/max = 5/5/6 ms

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --ping 9/ge2.dp1 -s 10.2.8.35 -d 10.2.18.35

PING 10.2.18.35 (10.2.8.35) with 64 bytes of data.
64 bytes from 10.2.18.35: icmp_seq=1 ttl=18 time=6 ms
64 bytes from 10.2.18.35: icmp_seq=2 ttl=18 time=6 ms
64 bytes from 10.2.18.35: icmp_seq=3 ttl=18 time=6 ms
64 bytes from 10.2.18.35: icmp_seq=4 ttl=18 time=6 ms

--- 10.2.18.35 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 141 ms
rtt min/avg/max = 6/6/6 ms

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --ping 9/ge10.dp0 -s 10.2.8.42 -d 10.2.18.42

PING 10.2.18.42 (10.2.8.42) with 64 bytes of data.

IProute does not exist.
Destination IP address 10.2.18.42 has no configured route.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --ping 9/ge10.dp1 -s 10.2.8.43 -d 10.2.18.43

PING 10.2.18.43 (10.2.8.43) with 64 bytes of data.

IProute does not exist.
Destination IP address 10.2.18.43 has no configured route.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --ping 10/ge2.dp0 -s 10.2.8.50 -d 10.2.18.50

PING 10.2.18.50 (10.2.8.50) with 64 bytes of data.
64 bytes from 10.2.18.50: icmp_seq=1 ttl=18 time=20 ms
64 bytes from 10.2.18.50: icmp_seq=2 ttl=18 time=7 ms
64 bytes from 10.2.18.50: icmp_seq=3 ttl=18 time=7 ms
64 bytes from 10.2.18.50: icmp_seq=4 ttl=18 time=7 ms

--- 10.2.18.50 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 177 ms
rtt min/avg/max = 7/10/20 ms

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --ping 10/ge2.dp1 -s 10.2.8.51 -d 10.2.18.51

PING 10.2.18.51 (10.2.8.51) with 64 bytes of data.
64 bytes from 10.2.18.51: icmp_seq=1 ttl=18 time=6 ms
64 bytes from 10.2.18.51: icmp_seq=2 ttl=18 time=5 ms
64 bytes from 10.2.18.51: icmp_seq=3 ttl=18 time=5 ms
64 bytes from 10.2.18.51: icmp_seq=4 ttl=18 time=5 ms

--- 10.2.18.51 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 136 ms
rtt min/avg/max = 5/5/6 ms

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --ping 10/ge10.dp0 -s 10.2.8.58 -d 10.2.18.58

PING 10.2.18.58 (10.2.8.58) with 64 bytes of data.
64 bytes from 10.2.18.58: icmp_seq=1 ttl=18 time=6 ms
64 bytes from 10.2.18.58: icmp_seq=2 ttl=18 time=5 ms
64 bytes from 10.2.18.58: icmp_seq=3 ttl=18 time=5 ms
64 bytes from 10.2.18.58: icmp_seq=4 ttl=18 time=5 ms

--- 10.2.18.58 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 140 ms
rtt min/avg/max = 5/5/6 ms

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --ping 10/ge10.dp1 -s 10.2.8.59 -d 10.2.18.59

PING 10.2.18.59 (10.2.8.59) with 64 bytes of data.
64 bytes from 10.2.18.59: icmp_seq=1 ttl=18 time=6 ms
64 bytes from 10.2.18.59: icmp_seq=2 ttl=18 time=5 ms
64 bytes from 10.2.18.59: icmp_seq=3 ttl=18 time=5 ms
64 bytes from 10.2.18.59: icmp_seq=4 ttl=18 time=5 ms

--- 10.2.18.59 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 131 ms
rtt min/avg/max = 5/5/6 ms

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fciptunnel 10/16 create
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --ping 10/ge10.dp1 -s 10.2.8.59 -d 10.2.18.59                                                     portcfg fciptunnel 10/16 create/16 create/16 create9/16 create
fciptunnel operation failed.
Object exists.
Tunnel ID 9/16 already exists.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg  show fciptunnel

 Tunnel Circuit   AdminSt Flags
--------------------------------------------------------------------------------
 9/16  -         Enabled --i------
 10/16 -         Enabled ---------
--------------------------------------------------------------------------------
 Flags (tunnel): l=Legacy QOS Mode
                 i=IPSec f=Fastwrite T=TapePipelining F=FICON r=ReservedBW
                 a=FastDeflate d=Deflate D=AggrDeflate P=Protocol
                 I=IP-Ext

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fcipcircuit 10/16 create 0 --local-ip 10.2.8.34 --remote-ip 10.2.18.34 --local-ha-ip 10.2.
8.35 --remote-ha-ip 10.2.18.35  -b 2000000 -B 5000000 -k 3000
Object does not exist.
Local IP address 10.2.8.34 is configured on slot 9 whereas target VE is from slot 10.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fcipcircuit 10/16 create 0  --local-ip 10.2.8.50 --remote-ip 10.2.18.50 --local-ha-ip 10.2
.8.51 --remote-ha-ip 10.2.18.51 -b 2000000 -B 5000000 -k 3000
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fcipcircuit 10/16 create 1 --local-ip 10.2.8.58 --remote-ip 10.2.18.58 --local-ha-ip 10.2.
8.59 --remote-ha-ip 10.2.18.59  -b 2000000 -B 5000000 -k 3000
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fciptunnel 9/16 modify -i morgan_ipsec1

!!!! WARNING !!!!
Modify operation can disrupt the traffic on the fciptunnel specified for a brief period of time. This operation will bring the existing tunnel down (if tunnel is up) before applying new configuration.

Continue with Modification (Y,y,N,n): [ n]y
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fciptunnel 10/16 modify -i morgan_ipsec1

!!!! WARNING !!!!
Modify operation can disrupt the traffic on the fciptunnel specified for a brief period of time. This operation will bring the existing tunnel down (if tunnel is up) before applying new configuration.

Continue with Modification (Y,y,N,n): [ n]y
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fciptunnel 9/16 modify --fc-compression fast-deflate

!!!! WARNING !!!!
Modify operation can disrupt the traffic on the fciptunnel specified for a brief period of time. This operation will bring the existing tunnel down (if tunnel is up) before applying new configuration.

Continue with Modification (Y,y,N,n): [ n]y
Tunnel modify failed: Modification of FC/IP compression option not allowed on non-hybrid tunnel.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fciptunnel 9/16 modify -c fast-deflate

!!!! WARNING !!!!
Modify operation can disrupt the traffic on the fciptunnel specified for a brief period of time. This operation will bring the existing tunnel down (if tunnel is up) before applying new configuration.

Continue with Modification (Y,y,N,n): [ n]y
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fciptunnel 10/16 modify -c fast-deflate

!!!! WARNING !!!!
Modify operation can disrupt the traffic on the fciptunnel specified for a brief period of time. This operation will bring the existing tunnel down (if tunnel is up) before applying new configuration.

Continue with Modification (Y,y,N,n): [ n]y
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow fciptunnel 9/16

 Tunnel: VE-Port:9/16 (idx:0, DP0)
 ====================================================
  Oper State           : Enabled
  TID                  : 0
  Flags                : 0x00000000
  IP-Extension         : Disabled
  Compression          : Fast Deflate
  QoS BW Ratio         : 50% / 30% / 20%
  Fastwrite            : Disabled
  Tape Pipelining      : Disabled
  IPSec                : Enabled
  IPSec-Policy         : morgan_ipsec1
  Legacy QOS Mode      : Disabled
  Load-Level           : Failover
  Local WWN            : 10:00:d8:1f:cc:71:62:00
  cfgmask              : 0x0000001f 0x4000020c
  Uncomp/Comp Bytes    : 0 / 0 / 1.00 : 1
  Uncomp/Comp Byte(30s): 0 / 0 / 1.00 : 1

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow fciptunnel 9/16    10/16

 Tunnel: VE-Port:10/16 (idx:0, DP0)
 ====================================================
  Oper State           : Enabled
  TID                  : 0
  Flags                : 0x00000000
  IP-Extension         : Disabled
  Compression          : Fast Deflate
  QoS BW Ratio         : 50% / 30% / 20%
  Fastwrite            : Disabled
  Tape Pipelining      : Disabled
  IPSec                : Enabled
  IPSec-Policy         : morgan_ipsec1
  Legacy QOS Mode      : Disabled
  Load-Level           : Failover
  Local WWN            : 10:00:d8:1f:cc:71:62:00
  cfgmask              : 0x0000001f 0x4000020c
  Uncomp/Comp Bytes    : 0 / 0 / 1.00 : 1
  Uncomp/Comp Byte(30s): 0 / 0 / 1.00 : 1

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg iproute 9/ge10.dp1 modify 10.2.18.40/29 10.2.8.49
IProute does not exist.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow fciptunnel 10/166666666666666666666666666666 portcfg iproute 9/ge10.dp1 modify 10.2.18.40/29 10.2.8.49fy 10.2.18.40/29 10.2.8.49 10.2.18.40/29 10.2.8.49 10.2.18.40/29 10.2.8.49 10.2.18.40/29 10.2.8.49 10.2.18.40/29 10.2.8.49 10.2.18.40/29 10.2.8.49c 10.2.18.40/29 10.2.8.49r 10.2.18.40/29 10.2.8.49e 10.2.18.40/29 10.2.8.49a 10.2.18.40/29 10.2.8.49t 10.2.18.40/29 10.2.8.49e 10.2.18.40/29 10.2.8.49
Route gateway unreachable.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --wtool 9/0 create -d 10.2.18.34 -s 10.2.8.34 -r 2500000
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --wtool 9/1 create -d 10.2.18.35 -s 10.2.8.35 -r 2500000
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --wtool 9/2 create -d 10.2.18.20 -s 10.2.8.42 -r 2500000
Address/device unreachable.
No IP route from 10.2.8.42 -> 10.2.18.20 on 9/ge10.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --wtool 9/3 create -d 10.2.18.21 -s 10.2.8.43 -r 2500000
Address/device unreachable.
No IP route from 10.2.8.43 -> 10.2.18.21 on 9/ge10.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --wtool 10/0 create -d 10.2.18.34 -s 10.2.8.50 -r 2500000
Address/device unreachable.
No IP route from 10.2.8.50 -> 10.2.18.34 on 10/ge2.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --wtool 10/1 create -d 10.2.18.35 -s 10.2.8.51 -r 2500000
Address/device unreachable.
No IP route from 10.2.8.51 -> 10.2.18.35 on 10/ge2.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --wtool 10/2 create -d 10.2.18.36 -s 10.2.8.58 -r 2500000
Address/device unreachable.
No IP route from 10.2.8.58 -> 10.2.18.36 on 10/ge10.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --wtool 10/3 create -d 10.2.18.37 -s 10.2.8.59 -r 2500000
Address/device unreachable.
No IP route from 10.2.8.59 -> 10.2.18.37 on 10/ge10.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fciptunnel modify -a 0

fciptunnel: Invalid port parameter 'modify' (rc:-1).


Usage:   portCfg fciptunnel [<slot>/]<port> <option> [<args>]

Option:    create - Create the specified tunnel/circuit
           modify - Modify the specified tunnel/circuit
           delete - Delete the specified tunnel/circuit

Optional Arguments:
  -f,--fastwrite               -  Enable / Disable the fastwrite option.
  -t,--tape-pipelining         -  Set the FCP tape-pipelining mode.
  -c,--compression <mode>      -  Set the compression mode. Allowable modes are
                                  [none] [deflate] [aggr-deflate] [fast-deflate
                                  {7840 / SX6Only}]. [7810 / 7840 / SX6 only]
     --fc-compression <mode>   -  Set the compression mode. Allowable modes are
                                  [none] [deflate] [aggr-deflate] [fast-deflate]
                                  [default]. [7810 / 7840 / SX6 only]
     --ip-compression <mode>   -  Set the compression mode. Allowable modes are
                                  [none] [deflate] [aggr-deflate] [default].
                                  [7810 / 7840 / SX6 only]
  -n,--remote-wwn <wwn>        -  Set the remote-wwn for this tunnel.
  -d,--description <string>    -  Set a description for this tunnel.
  -i,--ipsec <policy>|none     -  Set the IPSec policy for this tunnel, or
                                  disable IPSec with 'none' option. [7810 / 7840
                                  / SX6 only]
  -p,--distribution [<mode>,]<percentage ratio,...> -
                               -  Set tunnel bandwidth distribution mode and
                                  ratio percentages for the specified mode.
                                  mode:protocol ratio:<fc>,<ip>
  -Q,--fc-qos-ratio <high>,<med>,<low> -
                               -  Set the bandwidth ratio for FC priorities.
                                  [distribution:protocol only].
  -I,--ip-qos-ratio <high>,<med>,<low> -
                               -  Set the bandwidth ratio for IP priorities.
                                  [distribution:protocol only].
  -q,--qos-bw-ratio <ratio>|default -
                               -  Set the QoS bandwidth percentages for FC
                                  and/or IP or restore the defaults with
                                  'default' option. Ratio syntax: FCIP-Only
                                  Tunnels: <fcHigh>,<fcMed>,<fcLow> Hybrid
                                  Tunnels:
                                  <fcHigh>,<fcMed>,<fcLow>,<ipHigh>,<ipMed>,<ipLow>
  -F,--ficon                   -  Set FICON operating mode for this tunnel.
     --ficon-xrc               -  Set FICON XRC emulation mode.
     --ficon-tape              -  Set FICON tape read/write emulation mode.
     --ficon-tape-write        -  Set FICON tape write emulation mode.
     --ficon-tape-read         -  Set FICON tape read emulation mode.
     --ficon-tin-tir           -  Set FICON Tin Tir emulation mode.
     --ficon-dvcack            -  Set FICON Device-Acking emulation mode.
     --ficon-read-blk          -  Set FICON Read BLK-ID emulation mode.
     --ficon-tera-read         -  Set FICON Teradata read emulation mode.
     --ficon-tera-write        -  Set FICON Teradata write emulation mode.
     --ficon-print             -  Set FICON Printer emulation mode.
     --max-read-pipe <max>     -  Set the FICON max read pipelining value.
     --max-write-pipe <max>    -  Set the FICON max write pipelining value.
     --max-read-devs <max>     -  Set the FICON max read devices value.
     --max-write-devs <max>    -  Set the FICON max write devices value.
     --write-timer <ms>        -  Set the FICON write timer in ms.
     --write-chain <max>       -  Set the FICON max write chain size.
     --oxid-base <oxid>        -  Set the FICON base oxid value.
     --ficon-debug <hex>       -  Set the FICON debug flags.
  -a,--admin-status <enable|disable> -
                               -  Set the admin-status of the circuit.
  -S,--local-ip <ipaddr>|none  -  Set local IP address.
  -D,--remote-ip <ipaddr>|none -  Set remote IP address.
     --local-ha-ip <ipaddr>|none -
                               -  Set local HA IP address. This allows for HCL
                                  operations on local switch. [7840 / SX6 only]
     --remote-ha-ip <ipaddr>|none -
                               -  Set remote HA IP address. This allows for HCL
                                  operations on remote switch. [7810 / 7840 /
                                  SX6 only]
  -x,--metric <0|1>            -  Set the metric. 0=Primary 1=Failover.
  -g,--failover-group <0-9>    -  Set the failover group ID.
  -L,--load-leveling <default|failover|spillover> -
                               -  Set load leveling algorithm. [7810 / 7840 /
                                  SX6 only]
  -b,--min-comm-rate <kbps>    -  Set the minimum guaranteed rate.
  -B,--max-comm-rate <kbps>    -  Set the maximum rate.
     --arl-algorithm <mode>    -  Set the ARL algorithm. Allowable modes are
                                  [auto] [reset] [step-down] [timed-step-down].
                                  [7810 / 7840 / SX6 only]
  -C,--connection-type <type>  -  Set the connection type. Allowable types are
                                  [default] [listener] [initiator].
  -k,--keepalive-timeout <ms>  -  Set keepalive timeout in ms.
     --dscp-f-class <dscp>     -  Set DSCP marking for Control traffic.
     --dscp-high <dscp>        -  Set DSCP marking for FC-High priority traffic.
     --dscp-medium <dscp>      -  Set DSCP marking for FC-Medium priority
                                  traffic.
     --dscp-low <dscp>         -  Set DSCP marking for FC-Low priority traffic.
     --dscp-ip-high <dscp>     -  Set DSCP marking for IP-High priority traffic.
                                  [7810 / 7840 / SX6 only]
     --dscp-ip-medium <dscp>   -  Set DSCP marking for IP-Medium priority
                                  traffic. [7810 / 7840 / SX6 only]
     --dscp-ip-low <dscp>      -  Set DSCP marking for IP-Low priority traffic.
                                  [7810 / 7840 / SX6 only]
     --l2cos-f-class <l2cos>   -  Set L2CoS value for Control priority traffic.
     --l2cos-high <l2cos>      -  Set L2CoS value for FC-High priority traffic.
     --l2cos-medium <l2cos>    -  Set L2CoS value for FC-Medium priority
                                  traffic.
     --l2cos-low <l2cos>       -  Set L2CoS value for FC-Low priority traffic.
     --l2cos-ip-high <l2cos>   -  Set L2CoS value for IP-High priority traffic.
     --l2cos-ip-medium <l2cos> -  Set L2CoS value for IP-Medium priority
                                  traffic.
     --l2cos-ip-low <l2cos>    -  Set L2CoS value for IP-Low priority traffic.
     --ipext <enable|disable>  -  Enable / Disable IP Extension on this tunnel.
                                  [7810 / 7840 / SX6 only]
     --sla <sla-name>|none     -  Set the SLA name for this circuit. [7810 /
                                  7840 / SX6 only]
     --help                    -  Print this usage statement.

Example:
  portcfg fciptunnel 24 create --compression none

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
logout:Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.01 14:10:12 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> switchs show
switchName:REPISG1A_DEF
switchType:180.0
switchState:Online
switchMode:Native
switchRole:Principal
switchDomain:26
switchId:fffc1a
switchWwn:10:00:d8:1f:cc:71:62:00
zoning:OFF
switchBeacon:OFF
FC Router:OFF
Fabric Name:REPISG1A/EA_FAB
HIF Mode:OFF
Allow XISL Use:OFF
LS Attributes:[FID: 128, Base Switch: No, Default Switch: Yes, Ficon Switch: No, Address Mode 0]
Index Slot Port Address Media  Speed        State    Proto
============================================================
   0    3    0   1a0000   id    N32  No_Light    FC
   1    3    1   1a0100   id    N32  No_Light    FC
   2    3    2   1a0200   id    N32  No_Light    FC
   3    3    3   1a0300   id    N32  No_Light    FC
   4    3    4   1a0400   id    N32  No_Light    FC
   5    3    5   1a0500   id    N32  No_Light    FC
   6    3    6   1a0600   id    N32  No_Light    FC
   7    3    7   1a0700   id    N32  No_Light    FC
   8    3    8   1a0800   id    N32  No_Light    FC
   9    3    9   1a0900   id    N32  No_Light    FC
  10    3   10   1a0a00   id    N32  No_Light    FC
  11    3   11   1a0b00   id    N32  No_Light    FC
  12    3   12   1a0c00   id    N32  No_Light    FC
  13    3   13   1a0d00   id    N32  No_Light    FC
  14    3   14   1a0e00   id    N32  No_Light    FC
  15    3   15   1a0f00   id    N32  No_Light    FC
  16    3   16   1a1000   id    N32  No_Light    FC
  17    3   17   1a1100   id    N32  No_Light    FC
  18    3   18   1a1200   id    N32  No_Light    FC
  19    3   19   1a1300   id    N32  No_Light    FC
  20    3   20   1a1400   id    N32  No_Light    FC
  21    3   21   1a1500   id    N32  No_Light    FC
  22    3   22   1a1600   id    N32  No_Light    FC
  23    3   23   1a1700   id    N32  No_Light    FC
  24    3   24   1a1800   id    N32  No_Light    FC
  25    3   25   1a1900   id    N32  No_Light    FC
  26    3   26   1a1a00   id    N32  No_Light    FC
  27    3   27   1a1b00   id    N32  No_Light    FC
  28    3   28   1a1c00   id    N32  No_Light    FC
  29    3   29   1a1d00   id    N32  No_Light    FC
  30    3   30   1a1e00   id    N32  No_Light    FC
  31    3   31   1a1f00   id    N32  No_Light    FC
  32    3   32   1a2000   id    N32  No_Light    FC
  33    3   33   1a2100   id    N32  No_Light    FC
  34    3   34   1a2200   id    N32  No_Light    FC
  35    3   35   1a2300   id    N32  No_Light    FC
  36    3   36   1a2400   id    N32  No_Light    FC
  37    3   37   1a2500   id    N32  No_Light    FC
  38    3   38   1a2600   id    N32  No_Light    FC
  39    3   39   1a2700   id    N32  No_Light    FC
  40    3   40   1a2800   id    N32  No_Light    FC
  41    3   41   1a2900   id    N32  No_Light    FC
  42    3   42   1a2a00   id    N32  No_Light    FC
  43    3   43   1a2b00   id    N32  No_Light    FC
  44    3   44   1a2c00   id    N32  No_Light    FC
  45    3   45   1a2d00   id    N32  No_Light    FC
  46    3   46   1a2e00   id    N32  No_Light    FC
  47    3   47   1a2f00   id    N32  No_Light    FC
  96    4    0   1a6000   id    N32  No_Light    FC
  97    4    1   1a6100   id    N32  No_Light    FC
  98    4    2   1a6200   id    N32  No_Light    FC
  99    4    3   1a6300   id    N32  No_Light    FC
 100    4    4   1a6400   id    N32  No_Light    FC
 101    4    5   1a6500   id    N32  No_Light    FC
 102    4    6   1a6600   id    N32  No_Light    FC
 103    4    7   1a6700   id    N32  No_Light    FC
 104    4    8   1a6800   id    N32  No_Light    FC
 105    4    9   1a6900   id    N32  No_Light    FC
 106    4   10   1a6a00   id    N32  No_Light    FC
 107    4   11   1a6b00   id    N32  No_Light    FC
 108    4   12   1a6c00   id    N32  No_Light    FC
 109    4   13   1a6d00   id    N32  No_Light    FC
 110    4   14   1a6e00   id    N32  No_Light    FC
 111    4   15   1a6f00   id    N32  No_Light    FC
 112    4   16   1a7000   id    N32  No_Light    FC
 113    4   17   1a7100   id    N32  No_Light    FC
 114    4   18   1a7200   id    N32  No_Light    FC
 115    4   19   1a7300   id    N32  No_Light    FC
 116    4   20   1a7400   id    N32  No_Light    FC
 117    4   21   1a7500   id    N32  No_Light    FC
 118    4   22   1a7600   id    N32  No_Light    FC
 119    4   23   1a7700   id    N32  No_Light    FC
 120    4   24   1a7800   id    N32  No_Light    FC
 121    4   25   1a7900   id    N32  No_Light    FC
 122    4   26   1a7a00   id    N32  No_Light    FC
 123    4   27   1a7b00   id    N32  No_Light    FC
 124    4   28   1a7c00   id    N32  No_Light    FC
 125    4   29   1a7d00   id    N32  No_Light    FC
 126    4   30   1a7e00   id    N32  No_Light    FC
 127    4   31   1a7f00   id    N32  No_Light    FC
 128    4   32   1a8000   id    N32  No_Light    FC
 129    4   33   1a8100   id    N32  No_Light    FC
 130    4   34   1a8200   id    N32  No_Light    FC
 131    4   35   1a8300   id    N32  No_Light    FC
 132    4   36   1a8400   id    N32  No_Light    FC
 133    4   37   1a8500   id    N32  No_Light    FC
 134    4   38   1a8600   id    N32  No_Light    FC
 135    4   39   1a8700   id    N32  No_Light    FC
 136    4   40   1a8800   id    N32  No_Light    FC
 137    4   41   1a8900   id    N32  No_Light    FC
 138    4   42   1a8a00   id    N32  No_Light    FC
 139    4   43   1a8b00   id    N32  No_Light    FC
 140    4   44   1a8c00   id    N32  No_Light    FC
 141    4   45   1a8d00   id    N32  No_Light    FC
 142    4   46   1a8e00   id    N32  No_Light    FC
 143    4   47   1a8f00   id    N32  No_Light    FC
 768    7    0   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 769    7    1   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 770    7    2   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 771    7    3   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 772    7    4   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 773    7    5   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 774    7    6   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 775    7    7   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 776    7    8   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 777    7    9   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 778    7   10   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 779    7   11   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 780    7   12   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 781    7   13   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 782    7   14   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 783    7   15   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 784    7   16   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 785    7   17   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 786    7   18   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 787    7   19   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 788    7   20   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 789    7   21   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 790    7   22   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 791    7   23   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 792    7   24   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 793    7   25   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 794    7   26   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 795    7   27   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 796    7   28   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 797    7   29   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 798    7   30   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 799    7   31   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 800    7   32   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 801    7   33   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 802    7   34   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 803    7   35   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 804    7   36   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 805    7   37   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 806    7   38   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 807    7   39   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 808    7   40   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 809    7   41   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 810    7   42   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 811    7   43   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 812    7   44   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 813    7   45   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 814    7   46   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 815    7   47   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 816    7   48   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 817    7   49   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 818    7   50   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 819    7   51   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 820    7   52   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 821    7   53   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 822    7   54   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 823    7   55   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 824    7   56   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 825    7   57   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 826    7   58   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 827    7   59   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 828    7   60   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 829    7   61   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 830    7   62   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 831    7   63   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 832    8    0   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 833    8    1   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 834    8    2   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 835    8    3   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 836    8    4   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 837    8    5   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 838    8    6   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 839    8    7   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 840    8    8   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 841    8    9   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 842    8   10   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 843    8   11   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 844    8   12   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 845    8   13   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 846    8   14   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 847    8   15   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 848    8   16   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 849    8   17   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 850    8   18   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 851    8   19   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 852    8   20   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 853    8   21   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 854    8   22   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 855    8   23   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 856    8   24   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 857    8   25   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 858    8   26   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 859    8   27   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 860    8   28   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 861    8   29   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 862    8   30   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 863    8   31   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 864    8   32   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 865    8   33   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 866    8   34   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 867    8   35   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 868    8   36   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 869    8   37   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 870    8   38   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 871    8   39   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 872    8   40   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 873    8   41   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 874    8   42   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 875    8   43   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 876    8   44   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 877    8   45   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 878    8   46   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 879    8   47   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 880    8   48   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 881    8   49   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 882    8   50   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 883    8   51   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 884    8   52   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 885    8   53   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 886    8   54   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 887    8   55   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 888    8   56   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 889    8   57   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 890    8   58   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 891    8   59   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 892    8   60   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 893    8   61   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 894    8   62   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 895    8   63   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 384    9    0   1a8040   id    N32  No_Light    FC
 385    9    1   1a8140   id    N32  No_Light    FC
 386    9    2   1a8240   id    N32  No_Light    FC
 387    9    3   1a8340   id    N32  No_Light    FC
 388    9    4   1a8440   id    N32  No_Light    FC
 389    9    5   1a8540   id    N32  No_Light    FC
 390    9    6   1a8640   id    N32  No_Light    FC
 391    9    7   1a8740   id    N32  No_Light    FC
 392    9    8   1a8840   id    N32  No_Light    FC
 393    9    9   1a8940   id    N32  No_Light    FC
 394    9   10   1a8a40   id    N32  No_Light    FC
 395    9   11   1a8b40   id    N32  No_Light    FC
 396    9   12   1a8c40   id    N32  No_Light    FC
 397    9   13   1a8d40   id    N32  No_Light    FC
 398    9   14   1a8e40   id    N32  No_Light    FC
 399    9   15   1a8f40   id    N32  No_Light    FC
 400    9   16   1a9040   --    --   Offline     VE
 401    9   17   1a9140   --    --   Offline     VE
 402    9   18   1a9240   --    --   Offline     VE
 403    9   19   1a9340   --    --   Offline     VE
 404    9   20   1a9440   --    --   Offline     VE
 405    9   21   1a9540   --    --   Offline     VE  Disabled (10VE Mode)
 406    9   22   1a9640   --    --   Offline     VE  Disabled (10VE Mode)
 407    9   23   1a9740   --    --   Offline     VE  Disabled (10VE Mode)
 408    9   24   1a9840   --    --   Offline     VE  Disabled (10VE Mode)
 409    9   25   1a9940   --    --   Offline     VE  Disabled (10VE Mode)
 410    9   26   1a9a40   --    --   Offline     VE
 411    9   27   1a9b40   --    --   Offline     VE
 412    9   28   1a9c40   --    --   Offline     VE
 413    9   29   1a9d40   --    --   Offline     VE
 414    9   30   1a9e40   --    --   Offline     VE
 415    9   31   1a9f40   --    --   Offline     VE  Disabled (10VE Mode)
 416    9   32   1aa040   --    --   Offline     VE  Disabled (10VE Mode)
 417    9   33   1aa140   --    --   Offline     VE  Disabled (10VE Mode)
 418    9   34   1aa240   --    --   Offline     VE  Disabled (10VE Mode)
 419    9   35   1aa340   --    --   Offline     VE  Disabled (10VE Mode)
        9  ge0            --    40G    No_Module   FCIP
        9  ge1            --    40G    No_Module   FCIP
        9  ge2            id    10G    Online      FCIP
        9  ge3            --    10G    No_Module   FCIP
        9  ge4            --    10G    No_Module   FCIP
        9  ge5            --    10G    No_Module   FCIP
        9  ge6            --    10G    No_Module   FCIP
        9  ge7            --    10G    No_Module   FCIP
        9  ge8            --    10G    No_Module   FCIP
        9  ge9            --    10G    No_Module   FCIP
        9  ge10           id    10G    Online      FCIP
        9  ge11           --    10G    No_Module   FCIP
        9  ge12           --    10G    No_Module   FCIP
        9  ge13           --    10G    No_Module   FCIP
        9  ge14           --    10G    No_Module   FCIP
        9  ge15           --    10G    No_Module   FCIP
        9  ge16           --    10G    No_Module   FCIP
        9  ge17           --    10G    No_Module   FCIP
 480   10    0   1ae040   id    N32  No_Light    FC
 481   10    1   1ae140   id    N32  No_Light    FC
 482   10    2   1ae240   id    N32  No_Light    FC
 483   10    3   1ae340   id    N32  No_Light    FC
 484   10    4   1ae440   id    N32  No_Light    FC
 485   10    5   1ae540   id    N32  No_Light    FC
 486   10    6   1ae640   id    N32  No_Light    FC
 487   10    7   1ae740   id    N32  No_Light    FC
 488   10    8   1ae840   id    N32  No_Light    FC
 489   10    9   1ae940   id    N32  No_Light    FC
 490   10   10   1aea40   id    N32  No_Light    FC
 491   10   11   1aeb40   id    N32  No_Light    FC
 492   10   12   1aec40   id    N32  No_Light    FC
 493   10   13   1aed40   id    N32  No_Light    FC
 494   10   14   1aee40   id    N32  No_Light    FC
 495   10   15   1aef40   id    N32  No_Light    FC
 496   10   16   1af040   --    --   Offline     VE
 497   10   17   1af140   --    --   Offline     VE
 498   10   18   1af240   --    --   Offline     VE
 499   10   19   1af340   --    --   Offline     VE
 500   10   20   1af440   --    --   Offline     VE
 501   10   21   1af540   --    --   Offline     VE  Disabled (10VE Mode)
 502   10   22   1af640   --    --   Offline     VE  Disabled (10VE Mode)
 503   10   23   1af740   --    --   Offline     VE  Disabled (10VE Mode)
 504   10   24   1af840   --    --   Offline     VE  Disabled (10VE Mode)
 505   10   25   1af940   --    --   Offline     VE  Disabled (10VE Mode)
 506   10   26   1afa40   --    --   Offline     VE
 507   10   27   1afb40   --    --   Offline     VE
 508   10   28   1afc40   --    --   Offline     VE
 509   10   29   1afd40   --    --   Offline     VE
 510   10   30   1afe40   --    --   Offline     VE
 511   10   31   1aff40   --    --   Offline     VE  Disabled (10VE Mode)
 512   10   32   1a0080   --    --   Offline     VE  Disabled (10VE Mode)
 513   10   33   1a0180   --    --   Offline     VE  Disabled (10VE Mode)
 514   10   34   1a0280   --    --   Offline     VE  Disabled (10VE Mode)
 515   10   35   1a0380   --    --   Offline     VE  Disabled (10VE Mode)
       10  ge0            --    40G    No_Module   FCIP
       10  ge1            --    40G    No_Module   FCIP
       10  ge2            id    10G    Online      FCIP
       10  ge3            --    10G    No_Module   FCIP
       10  ge4            --    10G    No_Module   FCIP
       10  ge5            --    10G    No_Module   FCIP
       10  ge6            --    10G    No_Module   FCIP
       10  ge7            --    10G    No_Module   FCIP
       10  ge8            --    10G    No_Module   FCIP
       10  ge9            --    10G    No_Module   FCIP
       10  ge10           id    10G    Online      FCIP
       10  ge11           --    10G    No_Module   FCIP
       10  ge12           --    10G    No_Module   FCIP
       10  ge13           --    10G    No_Module   FCIP
       10  ge14           --    10G    No_Module   FCIP
       10  ge15           --    10G    No_Module   FCIP
       10  ge16           --    10G    No_Module   FCIP
       10  ge17           --    10G    No_Module   FCIP
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow iproute

 Port         IP Address                / Pfx  Gateway                Flags
--------------------------------------------------------------------------------
 9/ge2.dp0    10.2.18.32                / 29   10.2.8.33
 9/ge2.dp1    10.2.18.32                / 29   10.2.8.33
 10/ge2.dp0   10.2.18.48                / 29   10.2.8.49
 10/ge2.dp1   10.2.18.48                / 29   10.2.8.49
 10/ge10.dp0  10.2.18.56                / 29   10.2.8.57
 10/ge10.dp1  10.2.18.56                / 29   10.2.8.57
--------------------------------------------------------------------------------
 Flags: S=Static X=Crossport

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow iproute       fciptunnel

 Tunnel Circuit   AdminSt Flags
--------------------------------------------------------------------------------
 9/16  -         Enabled --i----a-
 10/16 -         Enabled --i----a-
--------------------------------------------------------------------------------
 Flags (tunnel): l=Legacy QOS Mode
                 i=IPSec f=Fastwrite T=TapePipelining F=FICON r=ReservedBW
                 a=FastDeflate d=Deflate D=AggrDeflate P=Protocol
                 I=IP-Ext

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portenable 9/16
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portenable 9/16/161/160/16
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portenable 10/169/16cfgshow fciptunneliprouteswitchshow
switchName:REPISG1A_DEF
switchType:180.0
switchState:Online
switchMode:Native
switchRole:Principal
switchDomain:26
switchId:fffc1a
switchWwn:10:00:d8:1f:cc:71:62:00
zoning:OFF
switchBeacon:OFF
FC Router:OFF
Fabric Name:REPISG1A/EA_FAB
HIF Mode:OFF
Allow XISL Use:OFF
LS Attributes:[FID: 128, Base Switch: No, Default Switch: Yes, Ficon Switch: No, Address Mode 0]
Index Slot Port Address Media  Speed        State    Proto
============================================================
   0    3    0   1a0000   id    N32  No_Light    FC
   1    3    1   1a0100   id    N32  No_Light    FC
   2    3    2   1a0200   id    N32  No_Light    FC
   3    3    3   1a0300   id    N32  No_Light    FC
   4    3    4   1a0400   id    N32  No_Light    FC
   5    3    5   1a0500   id    N32  No_Light    FC
   6    3    6   1a0600   id    N32  No_Light    FC
   7    3    7   1a0700   id    N32  No_Light    FC
   8    3    8   1a0800   id    N32  No_Light    FC
   9    3    9   1a0900   id    N32  No_Light    FC
  10    3   10   1a0a00   id    N32  No_Light    FC
  11    3   11   1a0b00   id    N32  No_Light    FC
  12    3   12   1a0c00   id    N32  No_Light    FC
  13    3   13   1a0d00   id    N32  No_Light    FC
  14    3   14   1a0e00   id    N32  No_Light    FC
  15    3   15   1a0f00   id    N32  No_Light    FC
  16    3   16   1a1000   id    N32  No_Light    FC
  17    3   17   1a1100   id    N32  No_Light    FC
  18    3   18   1a1200   id    N32  No_Light    FC
  19    3   19   1a1300   id    N32  No_Light    FC
  20    3   20   1a1400   id    N32  No_Light    FC
  21    3   21   1a1500   id    N32  No_Light    FC
  22    3   22   1a1600   id    N32  No_Light    FC
  23    3   23   1a1700   id    N32  No_Light    FC
  24    3   24   1a1800   id    N32  No_Light    FC
  25    3   25   1a1900   id    N32  No_Light    FC
  26    3   26   1a1a00   id    N32  No_Light    FC
  27    3   27   1a1b00   id    N32  No_Light    FC
  28    3   28   1a1c00   id    N32  No_Light    FC
  29    3   29   1a1d00   id    N32  No_Light    FC
  30    3   30   1a1e00   id    N32  No_Light    FC
  31    3   31   1a1f00   id    N32  No_Light    FC
  32    3   32   1a2000   id    N32  No_Light    FC
  33    3   33   1a2100   id    N32  No_Light    FC
  34    3   34   1a2200   id    N32  No_Light    FC
  35    3   35   1a2300   id    N32  No_Light    FC
  36    3   36   1a2400   id    N32  No_Light    FC
  37    3   37   1a2500   id    N32  No_Light    FC
  38    3   38   1a2600   id    N32  No_Light    FC
  39    3   39   1a2700   id    N32  No_Light    FC
  40    3   40   1a2800   id    N32  No_Light    FC
  41    3   41   1a2900   id    N32  No_Light    FC
  42    3   42   1a2a00   id    N32  No_Light    FC
  43    3   43   1a2b00   id    N32  No_Light    FC
  44    3   44   1a2c00   id    N32  No_Light    FC
  45    3   45   1a2d00   id    N32  No_Light    FC
  46    3   46   1a2e00   id    N32  No_Light    FC
  47    3   47   1a2f00   id    N32  No_Light    FC
  96    4    0   1a6000   id    N32  No_Light    FC
  97    4    1   1a6100   id    N32  No_Light    FC
  98    4    2   1a6200   id    N32  No_Light    FC
  99    4    3   1a6300   id    N32  No_Light    FC
 100    4    4   1a6400   id    N32  No_Light    FC
 101    4    5   1a6500   id    N32  No_Light    FC
 102    4    6   1a6600   id    N32  No_Light    FC
 103    4    7   1a6700   id    N32  No_Light    FC
 104    4    8   1a6800   id    N32  No_Light    FC
 105    4    9   1a6900   id    N32  No_Light    FC
 106    4   10   1a6a00   id    N32  No_Light    FC
 107    4   11   1a6b00   id    N32  No_Light    FC
 108    4   12   1a6c00   id    N32  No_Light    FC
 109    4   13   1a6d00   id    N32  No_Light    FC
 110    4   14   1a6e00   id    N32  No_Light    FC
 111    4   15   1a6f00   id    N32  No_Light    FC
 112    4   16   1a7000   id    N32  No_Light    FC
 113    4   17   1a7100   id    N32  No_Light    FC
 114    4   18   1a7200   id    N32  No_Light    FC
 115    4   19   1a7300   id    N32  No_Light    FC
 116    4   20   1a7400   id    N32  No_Light    FC
 117    4   21   1a7500   id    N32  No_Light    FC
 118    4   22   1a7600   id    N32  No_Light    FC
 119    4   23   1a7700   id    N32  No_Light    FC
 120    4   24   1a7800   id    N32  No_Light    FC
 121    4   25   1a7900   id    N32  No_Light    FC
 122    4   26   1a7a00   id    N32  No_Light    FC
 123    4   27   1a7b00   id    N32  No_Light    FC
 124    4   28   1a7c00   id    N32  No_Light    FC
 125    4   29   1a7d00   id    N32  No_Light    FC
 126    4   30   1a7e00   id    N32  No_Light    FC
 127    4   31   1a7f00   id    N32  No_Light    FC
 128    4   32   1a8000   id    N32  No_Light    FC
 129    4   33   1a8100   id    N32  No_Light    FC
 130    4   34   1a8200   id    N32  No_Light    FC
 131    4   35   1a8300   id    N32  No_Light    FC
 132    4   36   1a8400   id    N32  No_Light    FC
 133    4   37   1a8500   id    N32  No_Light    FC
 134    4   38   1a8600   id    N32  No_Light    FC
 135    4   39   1a8700   id    N32  No_Light    FC
 136    4   40   1a8800   id    N32  No_Light    FC
 137    4   41   1a8900   id    N32  No_Light    FC
 138    4   42   1a8a00   id    N32  No_Light    FC
 139    4   43   1a8b00   id    N32  No_Light    FC
 140    4   44   1a8c00   id    N32  No_Light    FC
 141    4   45   1a8d00   id    N32  No_Light    FC
 142    4   46   1a8e00   id    N32  No_Light    FC
 143    4   47   1a8f00   id    N32  No_Light    FC
 768    7    0   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 769    7    1   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 770    7    2   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 771    7    3   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 772    7    4   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 773    7    5   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 774    7    6   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 775    7    7   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 776    7    8   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 777    7    9   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 778    7   10   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 779    7   11   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 780    7   12   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 781    7   13   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 782    7   14   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 783    7   15   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 784    7   16   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 785    7   17   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 786    7   18   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 787    7   19   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 788    7   20   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 789    7   21   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 790    7   22   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 791    7   23   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 792    7   24   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 793    7   25   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 794    7   26   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 795    7   27   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 796    7   28   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 797    7   29   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 798    7   30   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 799    7   31   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 800    7   32   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 801    7   33   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 802    7   34   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 803    7   35   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 804    7   36   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 805    7   37   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 806    7   38   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 807    7   39   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 808    7   40   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 809    7   41   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 810    7   42   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 811    7   43   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 812    7   44   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 813    7   45   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 814    7   46   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 815    7   47   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 816    7   48   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 817    7   49   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 818    7   50   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 819    7   51   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 820    7   52   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 821    7   53   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 822    7   54   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 823    7   55   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 824    7   56   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 825    7   57   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 826    7   58   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 827    7   59   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 828    7   60   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 829    7   61   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 830    7   62   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 831    7   63   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 832    8    0   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 833    8    1   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 834    8    2   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 835    8    3   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 836    8    4   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 837    8    5   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 838    8    6   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 839    8    7   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 840    8    8   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 841    8    9   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 842    8   10   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 843    8   11   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 844    8   12   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 845    8   13   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 846    8   14   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 847    8   15   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 848    8   16   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 849    8   17   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 850    8   18   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 851    8   19   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 852    8   20   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 853    8   21   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 854    8   22   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 855    8   23   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 856    8   24   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 857    8   25   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 858    8   26   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 859    8   27   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 860    8   28   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 861    8   29   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 862    8   30   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 863    8   31   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 864    8   32   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 865    8   33   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 866    8   34   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 867    8   35   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 868    8   36   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 869    8   37   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 870    8   38   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 871    8   39   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 872    8   40   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 873    8   41   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 874    8   42   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 875    8   43   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 876    8   44   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 877    8   45   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 878    8   46   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 879    8   47   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 880    8   48   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 881    8   49   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 882    8   50   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 883    8   51   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 884    8   52   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 885    8   53   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 886    8   54   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 887    8   55   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 888    8   56   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 889    8   57   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 890    8   58   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 891    8   59   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 892    8   60   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 893    8   61   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 894    8   62   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 895    8   63   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 384    9    0   1a8040   id    N32  No_Light    FC
 385    9    1   1a8140   id    N32  No_Light    FC
 386    9    2   1a8240   id    N32  No_Light    FC
 387    9    3   1a8340   id    N32  No_Light    FC
 388    9    4   1a8440   id    N32  No_Light    FC
 389    9    5   1a8540   id    N32  No_Light    FC
 390    9    6   1a8640   id    N32  No_Light    FC
 391    9    7   1a8740   id    N32  No_Light    FC
 392    9    8   1a8840   id    N32  No_Light    FC
 393    9    9   1a8940   id    N32  No_Light    FC
 394    9   10   1a8a40   id    N32  No_Light    FC
 395    9   11   1a8b40   id    N32  No_Light    FC
 396    9   12   1a8c40   id    N32  No_Light    FC
 397    9   13   1a8d40   id    N32  No_Light    FC
 398    9   14   1a8e40   id    N32  No_Light    FC
 399    9   15   1a8f40   id    N32  No_Light    FC
 400    9   16   1a9040   --    --   Offline     VE
 401    9   17   1a9140   --    --   Offline     VE
 402    9   18   1a9240   --    --   Offline     VE
 403    9   19   1a9340   --    --   Offline     VE
 404    9   20   1a9440   --    --   Offline     VE
 405    9   21   1a9540   --    --   Offline     VE  Disabled (10VE Mode)
 406    9   22   1a9640   --    --   Offline     VE  Disabled (10VE Mode)
 407    9   23   1a9740   --    --   Offline     VE  Disabled (10VE Mode)
 408    9   24   1a9840   --    --   Offline     VE  Disabled (10VE Mode)
 409    9   25   1a9940   --    --   Offline     VE  Disabled (10VE Mode)
 410    9   26   1a9a40   --    --   Offline     VE
 411    9   27   1a9b40   --    --   Offline     VE
 412    9   28   1a9c40   --    --   Offline     VE
 413    9   29   1a9d40   --    --   Offline     VE
 414    9   30   1a9e40   --    --   Offline     VE
 415    9   31   1a9f40   --    --   Offline     VE  Disabled (10VE Mode)
 416    9   32   1aa040   --    --   Offline     VE  Disabled (10VE Mode)
 417    9   33   1aa140   --    --   Offline     VE  Disabled (10VE Mode)
 418    9   34   1aa240   --    --   Offline     VE  Disabled (10VE Mode)
 419    9   35   1aa340   --    --   Offline     VE  Disabled (10VE Mode)
        9  ge0            --    40G    No_Module   FCIP
        9  ge1            --    40G    No_Module   FCIP
        9  ge2            id    10G    Online      FCIP
        9  ge3            --    10G    No_Module   FCIP
        9  ge4            --    10G    No_Module   FCIP
        9  ge5            --    10G    No_Module   FCIP
        9  ge6            --    10G    No_Module   FCIP
        9  ge7            --    10G    No_Module   FCIP
        9  ge8            --    10G    No_Module   FCIP
        9  ge9            --    10G    No_Module   FCIP
        9  ge10           id    10G    Online      FCIP
        9  ge11           --    10G    No_Module   FCIP
        9  ge12           --    10G    No_Module   FCIP
        9  ge13           --    10G    No_Module   FCIP
        9  ge14           --    10G    No_Module   FCIP
        9  ge15           --    10G    No_Module   FCIP
        9  ge16           --    10G    No_Module   FCIP
        9  ge17           --    10G    No_Module   FCIP
 480   10    0   1ae040   id    N32  No_Light    FC
 481   10    1   1ae140   id    N32  No_Light    FC
 482   10    2   1ae240   id    N32  No_Light    FC
 483   10    3   1ae340   id    N32  No_Light    FC
 484   10    4   1ae440   id    N32  No_Light    FC
 485   10    5   1ae540   id    N32  No_Light    FC
 486   10    6   1ae640   id    N32  No_Light    FC
 487   10    7   1ae740   id    N32  No_Light    FC
 488   10    8   1ae840   id    N32  No_Light    FC
 489   10    9   1ae940   id    N32  No_Light    FC
 490   10   10   1aea40   id    N32  No_Light    FC
 491   10   11   1aeb40   id    N32  No_Light    FC
 492   10   12   1aec40   id    N32  No_Light    FC
 493   10   13   1aed40   id    N32  No_Light    FC
 494   10   14   1aee40   id    N32  No_Light    FC
 495   10   15   1aef40   id    N32  No_Light    FC
 496   10   16   1af040   --    --   Offline     VE
 497   10   17   1af140   --    --   Offline     VE
 498   10   18   1af240   --    --   Offline     VE
 499   10   19   1af340   --    --   Offline     VE
 500   10   20   1af440   --    --   Offline     VE
 501   10   21   1af540   --    --   Offline     VE  Disabled (10VE Mode)
 502   10   22   1af640   --    --   Offline     VE  Disabled (10VE Mode)
 503   10   23   1af740   --    --   Offline     VE  Disabled (10VE Mode)
 504   10   24   1af840   --    --   Offline     VE  Disabled (10VE Mode)
 505   10   25   1af940   --    --   Offline     VE  Disabled (10VE Mode)
 506   10   26   1afa40   --    --   Offline     VE
 507   10   27   1afb40   --    --   Offline     VE
 508   10   28   1afc40   --    --   Offline     VE
 509   10   29   1afd40   --    --   Offline     VE
 510   10   30   1afe40   --    --   Offline     VE
 511   10   31   1aff40   --    --   Offline     VE  Disabled (10VE Mode)
 512   10   32   1a0080   --    --   Offline     VE  Disabled (10VE Mode)
 513   10   33   1a0180   --    --   Offline     VE  Disabled (10VE Mode)
 514   10   34   1a0280   --    --   Offline     VE  Disabled (10VE Mode)
 515   10   35   1a0380   --    --   Offline     VE  Disabled (10VE Mode)
       10  ge0            --    40G    No_Module   FCIP
       10  ge1            --    40G    No_Module   FCIP
       10  ge2            id    10G    Online      FCIP
       10  ge3            --    10G    No_Module   FCIP
       10  ge4            --    10G    No_Module   FCIP
       10  ge5            --    10G    No_Module   FCIP
       10  ge6            --    10G    No_Module   FCIP
       10  ge7            --    10G    No_Module   FCIP
       10  ge8            --    10G    No_Module   FCIP
       10  ge9            --    10G    No_Module   FCIP
       10  ge10           id    10G    Online      FCIP
       10  ge11           --    10G    No_Module   FCIP
       10  ge12           --    10G    No_Module   FCIP
       10  ge13           --    10G    No_Module   FCIP
       10  ge14           --    10G    No_Module   FCIP
       10  ge15           --    10G    No_Module   FCIP
       10  ge16           --    10G    No_Module   FCIP
       10  ge17           --    10G    No_Module   FCIP
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcf
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow fciptunnel 10/16

 Tunnel: VE-Port:10/16 (idx:0, DP0)
 ====================================================
  Oper State           : Enabled
  TID                  : 0
  Flags                : 0x00000000
  IP-Extension         : Disabled
  Compression          : Fast Deflate
  QoS BW Ratio         : 50% / 30% / 20%
  Fastwrite            : Disabled
  Tape Pipelining      : Disabled
  IPSec                : Enabled
  IPSec-Policy         : morgan_ipsec1
  Legacy QOS Mode      : Disabled
  Load-Level           : Failover
  Local WWN            : 10:00:d8:1f:cc:71:62:00
  cfgmask              : 0x0000001f 0x4000020c
  Uncomp/Comp Bytes    : 0 / 0 / 1.00 : 1
  Uncomp/Comp Byte(30s): 0 / 0 / 1.00 : 1

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> islshow
No ISL found
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgctrate     reate "repl     "REPL_ISG_A"
Error: Invalid number of arguments

Usage: cfgcreate "arg1", "arg2"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgcreate "REPL_ISG_A"
Error: Invalid number of arguments

Usage: cfgcreate "arg1", "arg2"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fciptunnel 9/16 modify -a 0 1

!!!! WARNING !!!!
Modify operation can disrupt the traffic on the fciptunnel specified for a brief period of time. This operation will bring the existing tunnel down (if tunnel is up) before applying new configuration.

Continue with Modification (Y,y,N,n): [ n]Y
Circuit modify failed: Object does not exist.
Unable to locate circuit 9/16.0.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgcreate "REPL_ISG_A""                      portcfg fciptunnel 9/16 modify -a 00 19/16 modify -a 11/16 modify -a 10/16 modify -a 1

!!!! WARNING !!!!
Modify operation can disrupt the traffic on the fciptunnel specified for a brief period of time. This operation will bring the existing tunnel down (if tunnel is up) before applying new configuration.

Continue with Modification (Y,y,N,n): [ n]Y
fciptunnel operation failed.
Nothing to modify.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> P portcfg modify                portcfg fciptunnel 9/16 modify -a 0 enable

!!!! WARNING !!!!
Modify operation can disrupt the traffic on the fciptunnel specified for a brief period of time. This operation will bring the existing tunnel down (if tunnel is up) before applying new configuration.

Continue with Modification (Y,y,N,n): [ n]y
Circuit modify failed: Object does not exist.
Unable to locate circuit 9/16.0.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
logout:Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.01 17:31:04 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> timeout
Shell Idle Timeout is 60 minutes
Session Idle Timeout is disabled.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portsh      portcfgshow fciptunnel 9/1

 Tunnel Circuit   AdminSt Flags
--------------------------------------------------------------------------------
 9/16  -         Enabled --i----a-
 10/16 -         Enabled --i----a-
--------------------------------------------------------------------------------
 Flags (tunnel): l=Legacy QOS Mode
                 i=IPSec f=Fastwrite T=TapePipelining F=FICON r=ReservedBW
                 a=FastDeflate d=Deflate D=AggrDeflate P=Protocol
                 I=IP-Ext

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow fciptunnel 9/16

 Tunnel: VE-Port:9/16 (idx:0, DP0)
 ====================================================
  Oper State           : Enabled
  TID                  : 0
  Flags                : 0x00000000
  IP-Extension         : Disabled
  Compression          : Fast Deflate
  QoS BW Ratio         : 50% / 30% / 20%
  Fastwrite            : Disabled
  Tape Pipelining      : Disabled
  IPSec                : Enabled
  IPSec-Policy         : morgan_ipsec1
  Legacy QOS Mode      : Disabled
  Load-Level           : Failover
  Local WWN            : 10:00:d8:1f:cc:71:62:00
  cfgmask              : 0x0000001f 0x4000020c
  Uncomp/Comp Bytes    : 0 / 0 / 1.00 : 1
  Uncomp/Comp Byte(30s): 0 / 0 / 1.00 : 1

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow fciptunnel 9/16                           portcfgshow fciptunnel l 10/16

 Tunnel: VE-Port:10/16 (idx:0, DP0)
 ====================================================
  Oper State           : Enabled
  TID                  : 0
  Flags                : 0x00000000
  IP-Extension         : Disabled
  Compression          : Fast Deflate
  QoS BW Ratio         : 50% / 30% / 20%
  Fastwrite            : Disabled
  Tape Pipelining      : Disabled
  IPSec                : Enabled
  IPSec-Policy         : morgan_ipsec1
  Legacy QOS Mode      : Disabled
  Load-Level           : Failover
  Local WWN            : 10:00:d8:1f:cc:71:62:00
  cfgmask              : 0x0000001f 0x4000020c
  Uncomp/Comp Bytes    : 0 / 0 / 1.00 : 1
  Uncomp/Comp Byte(30s): 0 / 0 / 1.00 : 1

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> switchshow
switchName:REPISG1A_DEF
switchType:180.0
switchState:Online
switchMode:Native
switchRole:Principal
switchDomain:26
switchId:fffc1a
switchWwn:10:00:d8:1f:cc:71:62:00
zoning:OFF
switchBeacon:OFF
FC Router:OFF
Fabric Name:REPISG1A/EA_FAB
HIF Mode:OFF
Allow XISL Use:OFF
LS Attributes:[FID: 128, Base Switch: No, Default Switch: Yes, Ficon Switch: No, Address Mode 0]
Index Slot Port Address Media  Speed        State    Proto
============================================================
   0    3    0   1a0000   id    N32  No_Light    FC
   1    3    1   1a0100   id    N32  No_Light    FC
   2    3    2   1a0200   id    N32  No_Light    FC
   3    3    3   1a0300   id    N32  No_Light    FC
   4    3    4   1a0400   id    N32  No_Light    FC
   5    3    5   1a0500   id    N32  No_Light    FC
   6    3    6   1a0600   id    N32  No_Light    FC
   7    3    7   1a0700   id    N32  No_Light    FC
   8    3    8   1a0800   id    N32  No_Light    FC
   9    3    9   1a0900   id    N32  No_Light    FC
  10    3   10   1a0a00   id    N32  No_Light    FC
  11    3   11   1a0b00   id    N32  No_Light    FC
  12    3   12   1a0c00   id    N32  No_Light    FC
  13    3   13   1a0d00   id    N32  No_Light    FC
  14    3   14   1a0e00   id    N32  No_Light    FC
  15    3   15   1a0f00   id    N32  No_Light    FC
  16    3   16   1a1000   id    N32  No_Light    FC
  17    3   17   1a1100   id    N32  No_Light    FC
  18    3   18   1a1200   id    N32  No_Light    FC
  19    3   19   1a1300   id    N32  No_Light    FC
  20    3   20   1a1400   id    N32  No_Light    FC
  21    3   21   1a1500   id    N32  No_Light    FC
  22    3   22   1a1600   id    N32  No_Light    FC
  23    3   23   1a1700   id    N32  No_Light    FC
  24    3   24   1a1800   id    N32  No_Light    FC
  25    3   25   1a1900   id    N32  No_Light    FC
  26    3   26   1a1a00   id    N32  No_Light    FC
  27    3   27   1a1b00   id    N32  No_Light    FC
  28    3   28   1a1c00   id    N32  No_Light    FC
  29    3   29   1a1d00   id    N32  No_Light    FC
  30    3   30   1a1e00   id    N32  No_Light    FC
  31    3   31   1a1f00   id    N32  No_Light    FC
  32    3   32   1a2000   id    N32  No_Light    FC
  33    3   33   1a2100   id    N32  No_Light    FC
  34    3   34   1a2200   id    N32  No_Light    FC
  35    3   35   1a2300   id    N32  No_Light    FC
  36    3   36   1a2400   id    N32  No_Light    FC
  37    3   37   1a2500   id    N32  No_Light    FC
  38    3   38   1a2600   id    N32  No_Light    FC
  39    3   39   1a2700   id    N32  No_Light    FC
  40    3   40   1a2800   id    N32  No_Light    FC
  41    3   41   1a2900   id    N32  No_Light    FC
  42    3   42   1a2a00   id    N32  No_Light    FC
  43    3   43   1a2b00   id    N32  No_Light    FC
  44    3   44   1a2c00   id    N32  No_Light    FC
  45    3   45   1a2d00   id    N32  No_Light    FC
  46    3   46   1a2e00   id    N32  No_Light    FC
  47    3   47   1a2f00   id    N32  No_Light    FC
  96    4    0   1a6000   id    N32  No_Light    FC
  97    4    1   1a6100   id    N32  No_Light    FC
  98    4    2   1a6200   id    N32  No_Light    FC
  99    4    3   1a6300   id    N32  No_Light    FC
 100    4    4   1a6400   id    N32  No_Light    FC
 101    4    5   1a6500   id    N32  No_Light    FC
 102    4    6   1a6600   id    N32  No_Light    FC
 103    4    7   1a6700   id    N32  No_Light    FC
 104    4    8   1a6800   id    N32  No_Light    FC
 105    4    9   1a6900   id    N32  No_Light    FC
 106    4   10   1a6a00   id    N32  No_Light    FC
 107    4   11   1a6b00   id    N32  No_Light    FC
 108    4   12   1a6c00   id    N32  No_Light    FC
 109    4   13   1a6d00   id    N32  No_Light    FC
 110    4   14   1a6e00   id    N32  No_Light    FC
 111    4   15   1a6f00   id    N32  No_Light    FC
 112    4   16   1a7000   id    N32  No_Light    FC
 113    4   17   1a7100   id    N32  No_Light    FC
 114    4   18   1a7200   id    N32  No_Light    FC
 115    4   19   1a7300   id    N32  No_Light    FC
 116    4   20   1a7400   id    N32  No_Light    FC
 117    4   21   1a7500   id    N32  No_Light    FC
 118    4   22   1a7600   id    N32  No_Light    FC
 119    4   23   1a7700   id    N32  No_Light    FC
 120    4   24   1a7800   id    N32  No_Light    FC
 121    4   25   1a7900   id    N32  No_Light    FC
 122    4   26   1a7a00   id    N32  No_Light    FC
 123    4   27   1a7b00   id    N32  No_Light    FC
 124    4   28   1a7c00   id    N32  No_Light    FC
 125    4   29   1a7d00   id    N32  No_Light    FC
 126    4   30   1a7e00   id    N32  No_Light    FC
 127    4   31   1a7f00   id    N32  No_Light    FC
 128    4   32   1a8000   id    N32  No_Light    FC
 129    4   33   1a8100   id    N32  No_Light    FC
 130    4   34   1a8200   id    N32  No_Light    FC
 131    4   35   1a8300   id    N32  No_Light    FC
 132    4   36   1a8400   id    N32  No_Light    FC
 133    4   37   1a8500   id    N32  No_Light    FC
 134    4   38   1a8600   id    N32  No_Light    FC
 135    4   39   1a8700   id    N32  No_Light    FC
 136    4   40   1a8800   id    N32  No_Light    FC
 137    4   41   1a8900   id    N32  No_Light    FC
 138    4   42   1a8a00   id    N32  No_Light    FC
 139    4   43   1a8b00   id    N32  No_Light    FC
 140    4   44   1a8c00   id    N32  No_Light    FC
 141    4   45   1a8d00   id    N32  No_Light    FC
 142    4   46   1a8e00   id    N32  No_Light    FC
 143    4   47   1a8f00   id    N32  No_Light    FC
 768    7    0   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 769    7    1   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 770    7    2   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 771    7    3   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 772    7    4   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 773    7    5   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 774    7    6   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 775    7    7   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 776    7    8   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 777    7    9   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 778    7   10   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 779    7   11   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 780    7   12   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 781    7   13   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 782    7   14   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 783    7   15   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 784    7   16   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 785    7   17   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 786    7   18   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 787    7   19   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 788    7   20   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 789    7   21   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 790    7   22   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 791    7   23   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 792    7   24   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 793    7   25   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 794    7   26   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 795    7   27   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 796    7   28   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 797    7   29   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 798    7   30   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 799    7   31   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 800    7   32   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 801    7   33   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 802    7   34   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 803    7   35   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 804    7   36   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 805    7   37   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 806    7   38   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 807    7   39   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 808    7   40   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 809    7   41   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 810    7   42   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 811    7   43   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 812    7   44   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 813    7   45   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 814    7   46   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 815    7   47   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 816    7   48   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 817    7   49   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 818    7   50   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 819    7   51   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 820    7   52   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 821    7   53   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 822    7   54   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 823    7   55   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 824    7   56   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 825    7   57   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 826    7   58   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 827    7   59   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 828    7   60   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 829    7   61   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 830    7   62   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 831    7   63   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 832    8    0   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 833    8    1   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 834    8    2   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 835    8    3   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 836    8    4   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 837    8    5   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 838    8    6   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 839    8    7   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 840    8    8   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 841    8    9   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 842    8   10   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 843    8   11   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 844    8   12   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 845    8   13   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 846    8   14   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 847    8   15   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 848    8   16   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 849    8   17   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 850    8   18   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 851    8   19   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 852    8   20   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 853    8   21   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 854    8   22   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 855    8   23   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 856    8   24   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 857    8   25   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 858    8   26   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 859    8   27   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 860    8   28   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 861    8   29   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 862    8   30   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 863    8   31   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 864    8   32   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 865    8   33   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 866    8   34   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 867    8   35   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 868    8   36   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 869    8   37   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 870    8   38   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 871    8   39   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 872    8   40   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 873    8   41   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 874    8   42   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 875    8   43   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 876    8   44   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 877    8   45   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 878    8   46   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 879    8   47   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 880    8   48   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 881    8   49   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 882    8   50   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 883    8   51   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 884    8   52   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 885    8   53   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 886    8   54   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 887    8   55   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 888    8   56   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 889    8   57   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 890    8   58   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 891    8   59   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 892    8   60   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 893    8   61   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 894    8   62   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 895    8   63   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 384    9    0   1a8040   id    N32  No_Light    FC
 385    9    1   1a8140   id    N32  No_Light    FC
 386    9    2   1a8240   id    N32  No_Light    FC
 387    9    3   1a8340   id    N32  No_Light    FC
 388    9    4   1a8440   id    N32  No_Light    FC
 389    9    5   1a8540   id    N32  No_Light    FC
 390    9    6   1a8640   id    N32  No_Light    FC
 391    9    7   1a8740   id    N32  No_Light    FC
 392    9    8   1a8840   id    N32  No_Light    FC
 393    9    9   1a8940   id    N32  No_Light    FC
 394    9   10   1a8a40   id    N32  No_Light    FC
 395    9   11   1a8b40   id    N32  No_Light    FC
 396    9   12   1a8c40   id    N32  No_Light    FC
 397    9   13   1a8d40   id    N32  No_Light    FC
 398    9   14   1a8e40   id    N32  No_Light    FC
 399    9   15   1a8f40   id    N32  No_Light    FC
 400    9   16   1a9040   --    --   Offline     VE
 401    9   17   1a9140   --    --   Offline     VE
 402    9   18   1a9240   --    --   Offline     VE
 403    9   19   1a9340   --    --   Offline     VE
 404    9   20   1a9440   --    --   Offline     VE
 405    9   21   1a9540   --    --   Offline     VE  Disabled (10VE Mode)
 406    9   22   1a9640   --    --   Offline     VE  Disabled (10VE Mode)
 407    9   23   1a9740   --    --   Offline     VE  Disabled (10VE Mode)
 408    9   24   1a9840   --    --   Offline     VE  Disabled (10VE Mode)
 409    9   25   1a9940   --    --   Offline     VE  Disabled (10VE Mode)
 410    9   26   1a9a40   --    --   Offline     VE
 411    9   27   1a9b40   --    --   Offline     VE
 412    9   28   1a9c40   --    --   Offline     VE
 413    9   29   1a9d40   --    --   Offline     VE
 414    9   30   1a9e40   --    --   Offline     VE
 415    9   31   1a9f40   --    --   Offline     VE  Disabled (10VE Mode)
 416    9   32   1aa040   --    --   Offline     VE  Disabled (10VE Mode)
 417    9   33   1aa140   --    --   Offline     VE  Disabled (10VE Mode)
 418    9   34   1aa240   --    --   Offline     VE  Disabled (10VE Mode)
 419    9   35   1aa340   --    --   Offline     VE  Disabled (10VE Mode)
        9  ge0            --    40G    No_Module   FCIP
        9  ge1            --    40G    No_Module   FCIP
        9  ge2            id    10G    Online      FCIP
        9  ge3            --    10G    No_Module   FCIP
        9  ge4            --    10G    No_Module   FCIP
        9  ge5            --    10G    No_Module   FCIP
        9  ge6            --    10G    No_Module   FCIP
        9  ge7            --    10G    No_Module   FCIP
        9  ge8            --    10G    No_Module   FCIP
        9  ge9            --    10G    No_Module   FCIP
        9  ge10           id    10G    Online      FCIP
        9  ge11           --    10G    No_Module   FCIP
        9  ge12           --    10G    No_Module   FCIP
        9  ge13           --    10G    No_Module   FCIP
        9  ge14           --    10G    No_Module   FCIP
        9  ge15           --    10G    No_Module   FCIP
        9  ge16           --    10G    No_Module   FCIP
        9  ge17           --    10G    No_Module   FCIP
 480   10    0   1ae040   id    N32  No_Light    FC
 481   10    1   1ae140   id    N32  No_Light    FC
 482   10    2   1ae240   id    N32  No_Light    FC
 483   10    3   1ae340   id    N32  No_Light    FC
 484   10    4   1ae440   id    N32  No_Light    FC
 485   10    5   1ae540   id    N32  No_Light    FC
 486   10    6   1ae640   id    N32  No_Light    FC
 487   10    7   1ae740   id    N32  No_Light    FC
 488   10    8   1ae840   id    N32  No_Light    FC
 489   10    9   1ae940   id    N32  No_Light    FC
 490   10   10   1aea40   id    N32  No_Light    FC
 491   10   11   1aeb40   id    N32  No_Light    FC
 492   10   12   1aec40   id    N32  No_Light    FC
 493   10   13   1aed40   id    N32  No_Light    FC
 494   10   14   1aee40   id    N32  No_Light    FC
 495   10   15   1aef40   id    N32  No_Light    FC
 496   10   16   1af040   --    --   Offline     VE
 497   10   17   1af140   --    --   Offline     VE
 498   10   18   1af240   --    --   Offline     VE
 499   10   19   1af340   --    --   Offline     VE
 500   10   20   1af440   --    --   Offline     VE
 501   10   21   1af540   --    --   Offline     VE  Disabled (10VE Mode)
 502   10   22   1af640   --    --   Offline     VE  Disabled (10VE Mode)
 503   10   23   1af740   --    --   Offline     VE  Disabled (10VE Mode)
 504   10   24   1af840   --    --   Offline     VE  Disabled (10VE Mode)
 505   10   25   1af940   --    --   Offline     VE  Disabled (10VE Mode)
 506   10   26   1afa40   --    --   Offline     VE
 507   10   27   1afb40   --    --   Offline     VE
 508   10   28   1afc40   --    --   Offline     VE
 509   10   29   1afd40   --    --   Offline     VE
 510   10   30   1afe40   --    --   Offline     VE
 511   10   31   1aff40   --    --   Offline     VE  Disabled (10VE Mode)
 512   10   32   1a0080   --    --   Offline     VE  Disabled (10VE Mode)
 513   10   33   1a0180   --    --   Offline     VE  Disabled (10VE Mode)
 514   10   34   1a0280   --    --   Offline     VE  Disabled (10VE Mode)
 515   10   35   1a0380   --    --   Offline     VE  Disabled (10VE Mode)
       10  ge0            --    40G    No_Module   FCIP
       10  ge1            --    40G    No_Module   FCIP
       10  ge2            id    10G    Online      FCIP
       10  ge3            --    10G    No_Module   FCIP
       10  ge4            --    10G    No_Module   FCIP
       10  ge5            --    10G    No_Module   FCIP
       10  ge6            --    10G    No_Module   FCIP
       10  ge7            --    10G    No_Module   FCIP
       10  ge8            --    10G    No_Module   FCIP
       10  ge9            --    10G    No_Module   FCIP
       10  ge10           id    10G    Online      FCIP
       10  ge11           --    10G    No_Module   FCIP
       10  ge12           --    10G    No_Module   FCIP
       10  ge13           --    10G    No_Module   FCIP
       10  ge14           --    10G    No_Module   FCIP
       10  ge15           --    10G    No_Module   FCIP
       10  ge16           --    10G    No_Module   FCIP
       10  ge17           --    10G    No_Module   FCIP
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> islshow
No ISL found
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fciptunnel

 Tunnel Circuit  OpStatus  Flags    Uptime  TxMBps  RxMBps ConnCnt CommRt Met/G
--------------------------------------------------------------------------------
 9/16  -         Empty   --i----a-       0s    0.00    0.00   0      -       -
 10/16 -         InProg  --i----a-       0s    0.00    0.00   0      -       -
--------------------------------------------------------------------------------
 Flags (tunnel): l=Legacy QOS Mode
                 i=IPSec f=Fastwrite T=TapePipelining F=FICON r=ReservedBW
                 a=FastDeflate d=Deflate D=AggrDeflate P=Protocol
                 I=IP-Ext

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fciptunnel

 Tunnel Circuit  OpStatus  Flags    Uptime  TxMBps  RxMBps ConnCnt CommRt Met/G
--------------------------------------------------------------------------------
 9/16  -         Empty   --i----a-       0s    0.00    0.00   0      -       -
 10/16 -         InProg  --i----a-       0s    0.00    0.00   0      -       -
--------------------------------------------------------------------------------
 Flags (tunnel): l=Legacy QOS Mode
                 i=IPSec f=Fastwrite T=TapePipelining F=FICON r=ReservedBW
                 a=FastDeflate d=Deflate D=AggrDeflate P=Protocol
                 I=IP-Ext

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fciptunnelislshow
No ISL found
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow ipif

 Port         IP Address                     / Pfx  MTU   VLAN  Flags
--------------------------------------------------------------------------------
 9/ge2.dp0    10.2.8.34                      / 29   AUTO  500
 9/ge2.dp1    10.2.8.35                      / 29   AUTO  500
 9/ge10.dp0   10.2.8.42                      / 29   AUTO  600
 9/ge10.dp1   10.2.8.43                      / 29   AUTO  600
 10/ge2.dp0   10.2.8.50                      / 29   AUTO  501
 10/ge2.dp1   10.2.8.51                      / 29   AUTO  501
 10/ge10.dp0  10.2.8.58                      / 29   AUTO  601
 10/ge10.dp1  10.2.8.59                      / 29   AUTO  601
--------------------------------------------------------------------------------
Flags: I=InUse X=Crossport

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow ipif  route

 Port         IP Address                / Pfx  Gateway                Flags
--------------------------------------------------------------------------------
 9/ge2.dp0    10.2.18.32                / 29   10.2.8.33
 9/ge2.dp1    10.2.18.32                / 29   10.2.8.33
 10/ge2.dp0   10.2.18.48                / 29   10.2.8.49
 10/ge2.dp1   10.2.18.48                / 29   10.2.8.49
 10/ge10.dp0  10.2.18.56                / 29   10.2.8.57
 10/ge10.dp1  10.2.18.56                / 29   10.2.8.57
--------------------------------------------------------------------------------
 Flags: S=Static X=Crossport

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg iproute 9/ge10.dp0  create 10.2.18.40/29 10.2.8.49
Route gateway unreachable.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg iproute 9/ge10.dp1  create 10.2.18.40/29 10.2.8.49
Route gateway unreachable.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfh gshow ipif

 Port         IP Address                     / Pfx  MTU   VLAN  Flags
--------------------------------------------------------------------------------
 9/ge2.dp0    10.2.8.34                      / 29   AUTO  500
 9/ge2.dp1    10.2.8.35                      / 29   AUTO  500
 9/ge10.dp0   10.2.8.42                      / 29   AUTO  600
 9/ge10.dp1   10.2.8.43                      / 29   AUTO  600
 10/ge2.dp0   10.2.8.50                      / 29   AUTO  501
 10/ge2.dp1   10.2.8.51                      / 29   AUTO  501
 10/ge10.dp0  10.2.8.58                      / 29   AUTO  601
 10/ge10.dp1  10.2.8.59                      / 29   AUTO  601
--------------------------------------------------------------------------------
Flags: I=InUse X=Crossport

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow iproute

 Port         IP Address                / Pfx  Gateway                Flags
--------------------------------------------------------------------------------
 9/ge2.dp0    10.2.18.32                / 29   10.2.8.33
 9/ge2.dp1    10.2.18.32                / 29   10.2.8.33
 10/ge2.dp0   10.2.18.48                / 29   10.2.8.49
 10/ge2.dp1   10.2.18.48                / 29   10.2.8.49
 10/ge10.dp0  10.2.18.56                / 29   10.2.8.57
 10/ge10.dp1  10.2.18.56                / 29   10.2.8.57
--------------------------------------------------------------------------------
 Flags: S=Static X=Crossport

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg iproute 9/ge10.dp0  create 10.2.18.40/29 10.2.8.41
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow iproute                   portcfg iproute 9/ge10.dp0  create 10.2.18.40/29 10.2.8.410  create 10.2.18.40/29 10.2.8.411  create 10.2.18.40/29 10.2.8.41
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow iproute

 Port         IP Address                / Pfx  Gateway                Flags
--------------------------------------------------------------------------------
 9/ge2.dp0    10.2.18.32                / 29   10.2.8.33
 9/ge2.dp1    10.2.18.32                / 29   10.2.8.33
 9/ge10.dp0   10.2.18.40                / 29   10.2.8.41
 9/ge10.dp1   10.2.18.40                / 29   10.2.8.41
 10/ge2.dp0   10.2.18.48                / 29   10.2.8.49
 10/ge2.dp1   10.2.18.48                / 29   10.2.8.49
 10/ge10.dp0  10.2.18.56                / 29   10.2.8.57
 10/ge10.dp1  10.2.18.56                / 29   10.2.8.57
--------------------------------------------------------------------------------
 Flags: S=Static X=Crossport

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
logout:Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.02 21:27:28 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley                           =~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.02 21:58:09 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> zonecreate "REPL_B_SRDF_0431_0437","REPL_B_SRDF_04
31_3_9;REPL_B_SRDF_0437_3_9;REPL_B_SRDF_0431_3_10;REPL_B_SRDF_0437_3_10;REPL_B_SRDF_0431_5_8;REPL_B_SRD
F_0437_5_8;REPL_B_SRDF_0431_7_8;REPL_B_SRDF_0437_7_8"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgadd "REPL_B","REPL_B_SRDF_0431_0437"
"REPL_B" not found
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfa gshow
Defined configuration:
 zone:REPL_B_SRDF_0431_0437
REPL_B_SRDF_0431_3_10; REPL_B_SRDF_0431_3_9;
REPL_B_SRDF_0431_5_8; REPL_B_SRDF_0431_7_8;
REPL_B_SRDF_0437_3_10; REPL_B_SRDF_0437_3_9;
REPL_B_SRDF_0437_5_8; REPL_B_SRDF_0437_7_8

Effective configuration:
No Effective configuration: (No Access)


REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> zonedelete
error: Usage: zonedelete Name
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>  REPL_B_SRDF_0431_0437^C
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>  REPL_B_SRDF_0431_0437z REPL_B_SRDF_0431_0437o REPL_B_SRDF_0431_0437n REPL_B_SRDF_0431_0437e REPL_B_SRDF_0431_0437d REPL_B_SRDF_0431_0437e REPL_B_SRDF_0431_0437l REPL_B_SRDF_0431_0437e REPL_B_SRDF_0431_0437t REPL_B_SRDF_0431_0437e REPL_B_SRDF_0431_0437
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgshow
Defined configuration:

Effective configuration:
No Effective configuration: (No Access)


REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
logout:Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.03 15:42:39 =~=~=~=~=~=~=~=~=~=~=~=
login as: MA  marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --ping 9/ge2.dp0 -s 10.2.8.34 -d 10.2.8.33
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcmd --ping 9/ge2.dp0 -s 10.2.8.34 -d 10.2.8.33

PING 10.2.8.33 (10.2.8.34) with 64 bytes of data.
64 bytes from 10.2.8.33: icmp_seq=1 ttl=64 time=1 ms
64 bytes from 10.2.8.33: icmp_seq=2 ttl=64 time=1 ms
64 bytes from 10.2.8.33: icmp_seq=3 ttl=64 time=1 ms
64 bytes from 10.2.8.33: icmp_seq=4 ttl=64 time=1 ms

--- 10.2.8.33 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 95 ms
rtt min/avg/max = 1/1/1 ms

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> ortcmd --ping 9/ge10.dp0 -s 10.2.8.42 -d 10.2.8.41
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> ortcmd --ping 9/ge10.dp0 -s 10.2.8.42 -d 10.2.8.41
-rbash: ortcmd: command not found
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> ortcmd --ping 9/ge10.dp0 -s 10.2.8.42 -d 10.2.8.41
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> ortcmd --ping 9/ge10.dp0 -s 10.2.8.42 -d 10.2.8.4portcmd --ping 9/ge10.dp0 -s 10.2.8.42 -d 10.2.8.41
1EPISG1A_DEF:FID128:marvin.parker@morganstanley.com> p


PING 10.2.8.41 (10.2.8.42) with 64 bytes of data.
64 bytes from 10.2.8.41: icmp_seq=1 ttl=64 time=1 ms
64 bytes from 10.2.8.41: icmp_seq=2 ttl=64 time=1 ms
64 bytes from 10.2.8.41: icmp_seq=3 ttl=64 time=1 ms
64 bytes from 10.2.8.41: icmp_seq=4 ttl=64 time=1 ms

--- 10.2.8.41 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 106 ms
rtt min/avg/max = 1/1/1 ms

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow iproute

 Port         IP Address                / Pfx  Gateway                Flags
--------------------------------------------------------------------------------
 9/ge2.dp0    10.2.8.32                 / 29   *                      U C
 9/ge2.dp0    10.2.8.33                 / 32   *                      U H L
 9/ge2.dp0    10.2.18.32                / 29   10.2.8.33              U G S
 9/ge2.dp1    10.2.8.32                 / 29   *                      U C
 9/ge2.dp1    10.2.8.33                 / 32   *                      U H L
 9/ge2.dp1    10.2.18.32                / 29   10.2.8.33              U G S
 9/ge10.dp0   10.2.8.40                 / 29   *                      U C
 9/ge10.dp0   10.2.8.41                 / 32   *                      U H L
 9/ge10.dp0   10.2.18.40                / 29   10.2.8.41              U G S
 9/ge10.dp1   10.2.8.40                 / 29   *                      U C
 9/ge10.dp1   10.2.8.41                 / 32   *                      U H L
 9/ge10.dp1   10.2.18.40                / 29   10.2.8.41              U G S
 10/ge2.dp0   10.2.8.48                 / 29   *                      U C
 10/ge2.dp0   10.2.8.49                 / 32   *                      U H L
 10/ge2.dp0   10.2.18.48                / 29   10.2.8.49              U G S
 10/ge2.dp1   10.2.8.48                 / 29   *                      U C
 10/ge2.dp1   10.2.8.49                 / 32   *                      U H L
 10/ge2.dp1   10.2.18.48                / 29   10.2.8.49              U G S
 10/ge10.dp0  10.2.8.56                 / 29   *                      U C
 10/ge10.dp0  10.2.8.57                 / 32   *                      U H L
 10/ge10.dp0  10.2.18.56                / 29   10.2.8.57              U G S
 10/ge10.dp1  10.2.8.56                 / 29   *                      U C
 10/ge10.dp1  10.2.8.57                 / 32   *                      U H L
 10/ge10.dp1  10.2.18.56                / 29   10.2.8.57              U G S
--------------------------------------------------------------------------------
 Flags: U=Usable G=Gateway H=Host C=Created(Interface)
        S=Static L=LinkLayer X=Crossport

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow iproute

 Port         IP Address                / Pfx  Gateway                Flags
--------------------------------------------------------------------------------
 9/ge2.dp0    10.2.18.32                / 29   10.2.8.33
 9/ge2.dp1    10.2.18.32                / 29   10.2.8.33
 9/ge10.dp0   10.2.18.40                / 29   10.2.8.41
 9/ge10.dp1   10.2.18.40                / 29   10.2.8.41
 10/ge2.dp0   10.2.18.48                / 29   10.2.8.49
 10/ge2.dp1   10.2.18.48                / 29   10.2.8.49
 10/ge10.dp0  10.2.18.56                / 29   10.2.8.57
 10/ge10.dp1  10.2.18.56                / 29   10.2.8.57
--------------------------------------------------------------------------------
 Flags: S=Static X=Crossport

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
logout:Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.03 16:19:28 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow iproute

 Port         IP Address                / Pfx  Gateway                Flags
--------------------------------------------------------------------------------
 9/ge2.dp0    10.2.18.32                / 29   10.2.8.33
 9/ge2.dp1    10.2.18.32                / 29   10.2.8.33
 9/ge10.dp0   10.2.18.40                / 29   10.2.8.41
 9/ge10.dp1   10.2.18.40                / 29   10.2.8.41
 10/ge2.dp0   10.2.18.48                / 29   10.2.8.49
 10/ge2.dp1   10.2.18.48                / 29   10.2.8.49
 10/ge10.dp0  10.2.18.56                / 29   10.2.8.57
 10/ge10.dp1  10.2.18.56                / 29   10.2.8.57
--------------------------------------------------------------------------------
 Flags: S=Static X=Crossport

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fcipcircuit 10/16 create 1 --local-ip 10.2
.8.58 --remote-ip 10.2.18.58 --local-ha-ip 10.2.8.59 --remote-ha-ip 10.2.18.59  -b 2000000 -B 5000000 -
k 3000
Object exists.
Circuit 10/16.1 already exists.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fcipcircuit 10/16 create 0  --local-ip 10.
2.8.50 --remote-ip 10.2.18.50 --local-ha-ip 10.2.8.51 --remote-ha-ip 10.2.18.51 -b 2000000 -B 5000000 -
k 3000
Object exists.
Circuit 10/16.0 already exists.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fcipcircuit

 Tunnel Circuit  OpStatus  Flags    Uptime  TxMBps  RxMBps ConnCnt CommRt Met/G
--------------------------------------------------------------------------------
 10/16 0 10/ge2  Up      ---vahp-4   27m43s    0.00    0.00   5  2000/5000  0/-
 10/16 1 10/ge10 Up      ---vahp-4   27m40s    0.00    0.00   5  2000/5000  0/-
--------------------------------------------------------------------------------
 Flags (circuit): h=HA-Configured v=VLAN-Tagged p=PMTU i=IPSec 4=IPv4 6=IPv6
                 ARL a=Auto r=Reset s=StepDown t=TimedStepDown  S=SLA

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fcipcircuit 9/16 create 0 --local-ip 10.2.
8.34 --remote-ip 10.2.18.34 --local-ha-ip 10.2.8.35 --remote-ha-ip 10.2.18.35  -b 2000000 -B 5000000 -k
 3000
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fcipcircuit 9/16 create 1  --local-ip 10.2
.8.42 --remote-ip 10.2.18.42 --local-ha-ip 10.2.8.43 --remote-ha-ip 10.2.18.43 -b 2000000 -B 5000000 -k
 3000
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fcipcircuit

 Tunnel Circuit  OpStatus  Flags    Uptime  TxMBps  RxMBps ConnCnt CommRt Met/G
--------------------------------------------------------------------------------
 9/16  0 9/ge2   Up      ---vahpi4      21s    0.00    0.00   1  2000/5000  0/-
 9/16  1 9/ge10  Degrade ---vahpi4       0s    0.00    0.00   1  2000/5000  0/-
 10/16 0 10/ge2  Up      ---vahp-4   28m42s    0.00    0.00   5  2000/5000  0/-
 10/16 1 10/ge10 Up      ---vahp-4   28m39s    0.00    0.00   5  2000/5000  0/-
--------------------------------------------------------------------------------
 Flags (circuit): h=HA-Configured v=VLAN-Tagged p=PMTU i=IPSec 4=IPv4 6=IPv6
                 ARL a=Auto r=Reset s=StepDown t=TimedStepDown  S=SLA

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fcipcircuit

 Tunnel Circuit  OpStatus  Flags    Uptime  TxMBps  RxMBps ConnCnt CommRt Met/G
--------------------------------------------------------------------------------
 9/16  0 9/ge2   Up      ---vahpi4      38s    0.00    0.00   1  2000/5000  0/-
 9/16  1 9/ge10  Degrade ---vahpi4      17s    0.00    0.00   1  2000/5000  0/-
 10/16 0 10/ge2  Up      ---vahp-4   28m59s    0.00    0.00   5  2000/5000  0/-
 10/16 1 10/ge10 Up      ---vahp-4   28m57s    0.00    0.00   5  2000/5000  0/-
--------------------------------------------------------------------------------
 Flags (circuit): h=HA-Configured v=VLAN-Tagged p=PMTU i=IPSec 4=IPv4 6=IPv6
                 ARL a=Auto r=Reset s=StepDown t=TimedStepDown  S=SLA

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fcipcircuit       tunnel

 Tunnel Circuit  OpStatus  Flags    Uptime  TxMBps  RxMBps ConnCnt CommRt Met/G
--------------------------------------------------------------------------------
 9/16  -         Degrade --i----a-     1m0s    0.00    0.00   1      -       -
 10/16 -         Up      -------a-   29m22s    0.00    0.00   5      -       -
--------------------------------------------------------------------------------
 Flags (tunnel): l=Legacy QOS Mode
                 i=IPSec f=Fastwrite T=TapePipelining F=FICON r=ReservedBW
                 a=FastDeflate d=Deflate D=AggrDeflate P=Protocol
                 I=IP-Ext

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fciptunnel

 Tunnel Circuit  OpStatus  Flags    Uptime  TxMBps  RxMBps ConnCnt CommRt Met/G
--------------------------------------------------------------------------------
 9/16  -         UpWarn  --i----a-    2m46s    0.00    0.00   1      -       -
 10/16 -         Up      -------a-    31m7s    0.00    0.00   5      -       -
--------------------------------------------------------------------------------
 Flags (tunnel): l=Legacy QOS Mode
                 i=IPSec f=Fastwrite T=TapePipelining F=FICON r=ReservedBW
                 a=FastDeflate d=Deflate D=AggrDeflate P=Protocol
                 I=IP-Ext

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fciptunnel      ci ircuit

 Tunnel Circuit  OpStatus  Flags    Uptime  TxMBps  RxMBps ConnCnt CommRt Met/G
--------------------------------------------------------------------------------
 9/16  0 9/ge2   Up      ---vahpi4     3m1s    0.00    0.00   1  2000/5000  0/-
 9/16  1 9/ge10  Up      ---vahpi4    2m40s    0.00    0.00   1  2000/5000  0/-
 10/16 0 10/ge2  Up      ---vahp-4   31m23s    0.00    0.00   5  2000/5000  0/-
 10/16 1 10/ge10 Up      ---vahp-4   31m19s    0.00    0.00   5  2000/5000  0/-
--------------------------------------------------------------------------------
 Flags (circuit): h=HA-Configured v=VLAN-Tagged p=PMTU i=IPSec 4=IPv4 6=IPv6
                 ARL a=Auto r=Reset s=StepDown t=TimedStepDown  S=SLA

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> switchshow
switchName:REPISG1A_DEF
switchType:180.0
switchState:Online
switchMode:Native
switchRole:Principal
switchDomain:26
switchId:fffc1a
switchWwn:10:00:d8:1f:cc:71:62:00
zoning:OFF
switchBeacon:OFF
FC Router:OFF
Fabric Name:REPISG1A/EA_FAB
HIF Mode:OFF
Allow XISL Use:OFF
LS Attributes:[FID: 128, Base Switch: No, Default Switch: Yes, Ficon Switch: No, Address Mode 0]
Index Slot Port Address Media  Speed        State    Proto
============================================================
   0    3    0   1a0000   id    N32  No_Light    FC
   1    3    1   1a0100   id    N32  No_Light    FC
   2    3    2   1a0200   id    N32  No_Light    FC
   3    3    3   1a0300   id    N32  No_Light    FC
   4    3    4   1a0400   id    N32  No_Light    FC
   5    3    5   1a0500   id    N32  No_Light    FC
   6    3    6   1a0600   id    N32  No_Light    FC
   7    3    7   1a0700   id    N32  No_Light    FC
   8    3    8   1a0800   id    N32  No_Light    FC
   9    3    9   1a0900   id    N32  No_Light    FC
  10    3   10   1a0a00   id    N32  No_Light    FC
  11    3   11   1a0b00   id    N32  No_Light    FC
  12    3   12   1a0c00   id    N32  No_Light    FC
  13    3   13   1a0d00   id    N32  No_Light    FC
  14    3   14   1a0e00   id    N32  No_Light    FC
  15    3   15   1a0f00   id    N32  No_Light    FC
  16    3   16   1a1000   id    N32  No_Light    FC
  17    3   17   1a1100   id    N32  No_Light    FC
  18    3   18   1a1200   id    N32  No_Light    FC
  19    3   19   1a1300   id    N32  No_Light    FC
  20    3   20   1a1400   id    N32  No_Light    FC
  21    3   21   1a1500   id    N32  No_Light    FC
  22    3   22   1a1600   id    N32  No_Light    FC
  23    3   23   1a1700   id    N32  No_Light    FC
  24    3   24   1a1800   id    N32  No_Light    FC
  25    3   25   1a1900   id    N32  No_Light    FC
  26    3   26   1a1a00   id    N32  No_Light    FC
  27    3   27   1a1b00   id    N32  No_Light    FC
  28    3   28   1a1c00   id    N32  No_Light    FC
  29    3   29   1a1d00   id    N32  No_Light    FC
  30    3   30   1a1e00   id    N32  No_Light    FC
  31    3   31   1a1f00   id    N32  No_Light    FC
  32    3   32   1a2000   id    N32  No_Light    FC
  33    3   33   1a2100   id    N32  No_Light    FC
  34    3   34   1a2200   id    N32  No_Light    FC
  35    3   35   1a2300   id    N32  No_Light    FC
  36    3   36   1a2400   id    N32  No_Light    FC
  37    3   37   1a2500   id    N32  No_Light    FC
  38    3   38   1a2600   id    N32  No_Light    FC
  39    3   39   1a2700   id    N32  No_Light    FC
  40    3   40   1a2800   id    N32  No_Light    FC
  41    3   41   1a2900   id    N32  No_Light    FC
  42    3   42   1a2a00   id    N32  No_Light    FC
  43    3   43   1a2b00   id    N32  No_Light    FC
  44    3   44   1a2c00   id    N32  No_Light    FC
  45    3   45   1a2d00   id    N32  No_Light    FC
  46    3   46   1a2e00   id    N32  No_Light    FC
  47    3   47   1a2f00   id    N32  No_Light    FC
  96    4    0   1a6000   id    N32  No_Light    FC
  97    4    1   1a6100   id    N32  No_Light    FC
  98    4    2   1a6200   id    N32  No_Light    FC
  99    4    3   1a6300   id    N32  No_Light    FC
 100    4    4   1a6400   id    N32  No_Light    FC
 101    4    5   1a6500   id    N32  No_Light    FC
 102    4    6   1a6600   id    N32  No_Light    FC
 103    4    7   1a6700   id    N32  No_Light    FC
 104    4    8   1a6800   id    N32  No_Light    FC
 105    4    9   1a6900   id    N32  No_Light    FC
 106    4   10   1a6a00   id    N32  No_Light    FC
 107    4   11   1a6b00   id    N32  No_Light    FC
 108    4   12   1a6c00   id    N32  No_Light    FC
 109    4   13   1a6d00   id    N32  No_Light    FC
 110    4   14   1a6e00   id    N32  No_Light    FC
 111    4   15   1a6f00   id    N32  No_Light    FC
 112    4   16   1a7000   id    N32  No_Light    FC
 113    4   17   1a7100   id    N32  No_Light    FC
 114    4   18   1a7200   id    N32  No_Light    FC
 115    4   19   1a7300   id    N32  No_Light    FC
 116    4   20   1a7400   id    N32  No_Light    FC
 117    4   21   1a7500   id    N32  No_Light    FC
 118    4   22   1a7600   id    N32  No_Light    FC
 119    4   23   1a7700   id    N32  No_Light    FC
 120    4   24   1a7800   id    N32  No_Light    FC
 121    4   25   1a7900   id    N32  No_Light    FC
 122    4   26   1a7a00   id    N32  No_Light    FC
 123    4   27   1a7b00   id    N32  No_Light    FC
 124    4   28   1a7c00   id    N32  No_Light    FC
 125    4   29   1a7d00   id    N32  No_Light    FC
 126    4   30   1a7e00   id    N32  No_Light    FC
 127    4   31   1a7f00   id    N32  No_Light    FC
 128    4   32   1a8000   id    N32  No_Light    FC
 129    4   33   1a8100   id    N32  No_Light    FC
 130    4   34   1a8200   id    N32  No_Light    FC
 131    4   35   1a8300   id    N32  No_Light    FC
 132    4   36   1a8400   id    N32  No_Light    FC
 133    4   37   1a8500   id    N32  No_Light    FC
 134    4   38   1a8600   id    N32  No_Light    FC
 135    4   39   1a8700   id    N32  No_Light    FC
 136    4   40   1a8800   id    N32  No_Light    FC
 137    4   41   1a8900   id    N32  No_Light    FC
 138    4   42   1a8a00   id    N32  No_Light    FC
 139    4   43   1a8b00   id    N32  No_Light    FC
 140    4   44   1a8c00   id    N32  No_Light    FC
 141    4   45   1a8d00   id    N32  No_Light    FC
 142    4   46   1a8e00   id    N32  No_Light    FC
 143    4   47   1a8f00   id    N32  No_Light    FC
 768    7    0   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 769    7    1   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 770    7    2   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 771    7    3   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 772    7    4   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 773    7    5   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 774    7    6   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 775    7    7   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 776    7    8   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 777    7    9   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 778    7   10   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 779    7   11   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 780    7   12   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 781    7   13   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 782    7   14   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 783    7   15   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 784    7   16   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 785    7   17   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 786    7   18   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 787    7   19   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 788    7   20   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 789    7   21   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 790    7   22   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 791    7   23   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 792    7   24   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 793    7   25   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 794    7   26   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 795    7   27   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 796    7   28   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 797    7   29   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 798    7   30   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 799    7   31   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 800    7   32   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 801    7   33   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 802    7   34   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 803    7   35   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 804    7   36   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 805    7   37   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 806    7   38   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 807    7   39   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 808    7   40   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 809    7   41   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 810    7   42   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 811    7   43   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 812    7   44   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 813    7   45   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 814    7   46   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 815    7   47   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 816    7   48   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 817    7   49   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 818    7   50   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 819    7   51   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 820    7   52   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 821    7   53   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 822    7   54   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 823    7   55   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 824    7   56   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 825    7   57   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 826    7   58   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 827    7   59   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 828    7   60   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 829    7   61   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 830    7   62   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 831    7   63   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 832    8    0   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 833    8    1   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 834    8    2   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 835    8    3   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 836    8    4   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 837    8    5   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 838    8    6   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 839    8    7   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 840    8    8   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 841    8    9   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 842    8   10   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 843    8   11   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 844    8   12   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 845    8   13   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 846    8   14   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 847    8   15   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 848    8   16   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 849    8   17   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 850    8   18   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 851    8   19   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 852    8   20   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 853    8   21   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 854    8   22   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 855    8   23   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 856    8   24   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 857    8   25   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 858    8   26   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 859    8   27   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 860    8   28   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 861    8   29   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 862    8   30   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 863    8   31   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 864    8   32   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 865    8   33   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 866    8   34   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 867    8   35   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 868    8   36   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 869    8   37   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 870    8   38   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 871    8   39   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 872    8   40   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 873    8   41   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 874    8   42   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 875    8   43   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 876    8   44   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 877    8   45   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 878    8   46   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 879    8   47   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 880    8   48   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 881    8   49   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 882    8   50   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 883    8   51   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 884    8   52   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 885    8   53   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 886    8   54   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 887    8   55   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 888    8   56   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 889    8   57   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 890    8   58   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 891    8   59   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 892    8   60   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 893    8   61   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 894    8   62   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 895    8   63   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 384    9    0   1a8040   id    N32  No_Light    FC
 385    9    1   1a8140   id    N32  No_Light    FC
 386    9    2   1a8240   id    N32  No_Light    FC
 387    9    3   1a8340   id    N32  No_Light    FC
 388    9    4   1a8440   id    N32  No_Light    FC
 389    9    5   1a8540   id    N32  No_Light    FC
 390    9    6   1a8640   id    N32  No_Light    FC
 391    9    7   1a8740   id    N32  No_Light    FC
 392    9    8   1a8840   id    N32  No_Light    FC
 393    9    9   1a8940   id    N32  No_Light    FC
 394    9   10   1a8a40   id    N32  No_Light    FC
 395    9   11   1a8b40   id    N32  No_Light    FC
 396    9   12   1a8c40   id    N32  No_Light    FC
 397    9   13   1a8d40   id    N32  No_Light    FC
 398    9   14   1a8e40   id    N32  No_Light    FC
 399    9   15   1a8f40   id    N32  No_Light    FC
 400    9   16   1a9040   --    --   Online      VE  VE-Port  10:00:d8:1f:cc:76:c9:c0 "REPISGEA_DEF"
 401    9   17   1a9140   --    --   Offline     VE
 402    9   18   1a9240   --    --   Offline     VE
 403    9   19   1a9340   --    --   Offline     VE
 404    9   20   1a9440   --    --   Offline     VE
 405    9   21   1a9540   --    --   Offline     VE  Disabled (10VE Mode)
 406    9   22   1a9640   --    --   Offline     VE  Disabled (10VE Mode)
 407    9   23   1a9740   --    --   Offline     VE  Disabled (10VE Mode)
 408    9   24   1a9840   --    --   Offline     VE  Disabled (10VE Mode)
 409    9   25   1a9940   --    --   Offline     VE  Disabled (10VE Mode)
 410    9   26   1a9a40   --    --   Offline     VE
 411    9   27   1a9b40   --    --   Offline     VE
 412    9   28   1a9c40   --    --   Offline     VE
 413    9   29   1a9d40   --    --   Offline     VE
 414    9   30   1a9e40   --    --   Offline     VE
 415    9   31   1a9f40   --    --   Offline     VE  Disabled (10VE Mode)
 416    9   32   1aa040   --    --   Offline     VE  Disabled (10VE Mode)
 417    9   33   1aa140   --    --   Offline     VE  Disabled (10VE Mode)
 418    9   34   1aa240   --    --   Offline     VE  Disabled (10VE Mode)
 419    9   35   1aa340   --    --   Offline     VE  Disabled (10VE Mode)
        9  ge0            --    40G    No_Module   FCIP
        9  ge1            --    40G    No_Module   FCIP
        9  ge2            id    10G    Online      FCIP
        9  ge3            --    10G    No_Module   FCIP
        9  ge4            --    10G    No_Module   FCIP
        9  ge5            --    10G    No_Module   FCIP
        9  ge6            --    10G    No_Module   FCIP
        9  ge7            --    10G    No_Module   FCIP
        9  ge8            --    10G    No_Module   FCIP
        9  ge9            --    10G    No_Module   FCIP
        9  ge10           id    10G    Online      FCIP
        9  ge11           --    10G    No_Module   FCIP
        9  ge12           --    10G    No_Module   FCIP
        9  ge13           --    10G    No_Module   FCIP
        9  ge14           --    10G    No_Module   FCIP
        9  ge15           --    10G    No_Module   FCIP
        9  ge16           --    10G    No_Module   FCIP
        9  ge17           --    10G    No_Module   FCIP
 480   10    0   1ae040   id    N32  No_Light    FC
 481   10    1   1ae140   id    N32  No_Light    FC
 482   10    2   1ae240   id    N32  No_Light    FC
 483   10    3   1ae340   id    N32  No_Light    FC
 484   10    4   1ae440   id    N32  No_Light    FC
 485   10    5   1ae540   id    N32  No_Light    FC
 486   10    6   1ae640   id    N32  No_Light    FC
 487   10    7   1ae740   id    N32  No_Light    FC
 488   10    8   1ae840   id    N32  No_Light    FC
 489   10    9   1ae940   id    N32  No_Light    FC
 490   10   10   1aea40   id    N32  No_Light    FC
 491   10   11   1aeb40   id    N32  No_Light    FC
 492   10   12   1aec40   id    N32  No_Light    FC
 493   10   13   1aed40   id    N32  No_Light    FC
 494   10   14   1aee40   id    N32  No_Light    FC
 495   10   15   1aef40   id    N32  No_Light    FC
 496   10   16   1af040   --    --   Online      VE  VE-Port  10:00:d8:1f:cc:76:c9:c0 "REPISGEA_DEF" (downstream)
 497   10   17   1af140   --    --   Offline     VE
 498   10   18   1af240   --    --   Offline     VE
 499   10   19   1af340   --    --   Offline     VE
 500   10   20   1af440   --    --   Offline     VE
 501   10   21   1af540   --    --   Offline     VE  Disabled (10VE Mode)
 502   10   22   1af640   --    --   Offline     VE  Disabled (10VE Mode)
 503   10   23   1af740   --    --   Offline     VE  Disabled (10VE Mode)
 504   10   24   1af840   --    --   Offline     VE  Disabled (10VE Mode)
 505   10   25   1af940   --    --   Offline     VE  Disabled (10VE Mode)
 506   10   26   1afa40   --    --   Offline     VE
 507   10   27   1afb40   --    --   Offline     VE
 508   10   28   1afc40   --    --   Offline     VE
 509   10   29   1afd40   --    --   Offline     VE
 510   10   30   1afe40   --    --   Offline     VE
 511   10   31   1aff40   --    --   Offline     VE  Disabled (10VE Mode)
 512   10   32   1a0080   --    --   Offline     VE  Disabled (10VE Mode)
 513   10   33   1a0180   --    --   Offline     VE  Disabled (10VE Mode)
 514   10   34   1a0280   --    --   Offline     VE  Disabled (10VE Mode)
 515   10   35   1a0380   --    --   Offline     VE  Disabled (10VE Mode)
       10  ge0            --    40G    No_Module   FCIP
       10  ge1            --    40G    No_Module   FCIP
       10  ge2            id    10G    Online      FCIP
       10  ge3            --    10G    No_Module   FCIP
       10  ge4            --    10G    No_Module   FCIP
       10  ge5            --    10G    No_Module   FCIP
       10  ge6            --    10G    No_Module   FCIP
       10  ge7            --    10G    No_Module   FCIP
       10  ge8            --    10G    No_Module   FCIP
       10  ge9            --    10G    No_Module   FCIP
       10  ge10           id    10G    Online      FCIP
       10  ge11           --    10G    No_Module   FCIP
       10  ge12           --    10G    No_Module   FCIP
       10  ge13           --    10G    No_Module   FCIP
       10  ge14           --    10G    No_Module   FCIP
       10  ge15           --    10G    No_Module   FCIP
       10  ge16           --    10G    No_Module   FCIP
       10  ge17           --    10G    No_Module   FCIP
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> islshow
  1:400->400 10:00:d8:1f:cc:76:c9:c0 234 REPISGEA_DEF                    sp:-------- bw: 10.000G
  2:496->496 10:00:d8:1f:cc:76:c9:c0 234 REPISGEA_DEF                    sp:-------- bw: 10.000G
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
logout:Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.04 13:44:58 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morh ganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fciptunnel 9/16 modify --load-leveling spi
llover
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fciptunnel 9/16 modify --load-leveling spi
llover
fciptunnel operation failed.
Nothing to modify.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg fciptunnel 10/16 modify --load-leveling sp
illover
fciptunnel operation failed.
Nothing to modify.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg ipsec-policy morgan_ipsec1 restart
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fciptunnel

 Tunnel Circuit  OpStatus  Flags    Uptime  TxMBps  RxMBps ConnCnt CommRt Met/G
--------------------------------------------------------------------------------
 9/16  -         Up      --i----a-   21h17m    0.00    0.00   1      -       -
 10/16 -         Up      -------a-   21h45m    0.00    0.00   1      -       -
--------------------------------------------------------------------------------
 Flags (tunnel): l=Legacy QOS Mode
                 i=IPSec f=Fastwrite T=TapePipelining F=FICON r=ReservedBW
                 a=FastDeflate d=Deflate D=AggrDeflate P=Protocol
                 I=IP-Ext

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcg fgshow fciptunnel

 Tunnel Circuit   AdminSt Flags
--------------------------------------------------------------------------------
 9/16  -         Enabled --i----a-
 10/16 -         Enabled -------a-
--------------------------------------------------------------------------------
 Flags (tunnel): l=Legacy QOS Mode
                 i=IPSec f=Fastwrite T=TapePipelining F=FICON r=ReservedBW
                 a=FastDeflate d=Deflate D=AggrDeflate P=Protocol
                 I=IP-Ext

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow fciptunnel 9/16

 Tunnel: VE-Port:9/16 (idx:0, DP0)
 ====================================================
  Oper State           : Enabled
  TID                  : 0
  Flags                : 0x00000000
  IP-Extension         : Disabled
  Compression          : Fast Deflate
  QoS BW Ratio         : 50% / 30% / 20%
  Fastwrite            : Disabled
  Tape Pipelining      : Disabled
  IPSec                : Enabled
  IPSec-Policy         : morgan_ipsec1
  Legacy QOS Mode      : Disabled
  Load-Level           : Spillover
  Local WWN            : 10:00:d8:1f:cc:71:62:00
  cfgmask              : 0x0000001f 0x4000420c
  Uncomp/Comp Bytes    : 0 / 0 / 1.00 : 1
  Uncomp/Comp Byte(30s): 0 / 0 / 1.00 : 1

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow fciptunnel 9/16    10/16

 Tunnel: VE-Port:10/16 (idx:0, DP0)
 ====================================================
  Oper State           : Enabled
  TID                  : 0
  Flags                : 0x00000000
  IP-Extension         : Disabled
  Compression          : Fast Deflate
  QoS BW Ratio         : 50% / 30% / 20%
  Fastwrite            : Disabled
  Tape Pipelining      : Disabled
  IPSec                : Disabled
  Legacy QOS Mode      : Disabled
  Load-Level           : Spillover
  Local WWN            : 10:00:d8:1f:cc:71:62:00
  cfgmask              : 0x0000001f 0x40004208
  Uncomp/Comp Bytes    : 0 / 0 / 1.00 : 1
  Uncomp/Comp Byte(30s): 0 / 0 / 1.00 : 1

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfg ipsec-policy morgan_ipsec1 restart                                          portcfg fciptunnle     e nel 10/16 -i morgan_ipsec1

fciptunnel: Unknown option '-i'.

Usage:   portCfg fciptunnel [<slot>/]<port> <option> [<args>]

Option:    create - Create the specified tunnel/circuit
           modify - Modify the specified tunnel/circuit
           delete - Delete the specified tunnel/circuit

Optional Arguments:
  -f,--fastwrite               -  Enable / Disable the fastwrite option.
  -t,--tape-pipelining         -  Set the FCP tape-pipelining mode.
  -c,--compression <mode>      -  Set the compression mode. Allowable modes are
                                  [none] [deflate] [aggr-deflate] [fast-deflate
                                  {7840 / SX6Only}]. [7810 / 7840 / SX6 only]
     --fc-compression <mode>   -  Set the compression mode. Allowable modes are
                                  [none] [deflate] [aggr-deflate] [fast-deflate]
                                  [default]. [7810 / 7840 / SX6 only]
     --ip-compression <mode>   -  Set the compression mode. Allowable modes are
                                  [none] [deflate] [aggr-deflate] [default].
                                  [7810 / 7840 / SX6 only]
  -n,--remote-wwn <wwn>        -  Set the remote-wwn for this tunnel.
  -d,--description <string>    -  Set a description for this tunnel.
  -i,--ipsec <policy>|none     -  Set the IPSec policy for this tunnel, or
                                  disable IPSec with 'none' option. [7810 / 7840
                                  / SX6 only]
  -p,--distribution [<mode>,]<percentage ratio,...> -
                               -  Set tunnel bandwidth distribution mode and
                                  ratio percentages for the specified mode.
                                  mode:protocol ratio:<fc>,<ip>
  -Q,--fc-qos-ratio <high>,<med>,<low> -
                               -  Set the bandwidth ratio for FC priorities.
                                  [distribution:protocol only].
  -I,--ip-qos-ratio <high>,<med>,<low> -
                               -  Set the bandwidth ratio for IP priorities.
                                  [distribution:protocol only].
  -q,--qos-bw-ratio <ratio>|default -
                               -  Set the QoS bandwidth percentages for FC
                                  and/or IP or restore the defaults with
                                  'default' option. Ratio syntax: FCIP-Only
                                  Tunnels: <fcHigh>,<fcMed>,<fcLow> Hybrid
                                  Tunnels:
                                  <fcHigh>,<fcMed>,<fcLow>,<ipHigh>,<ipMed>,<ipLow>
  -F,--ficon                   -  Set FICON operating mode for this tunnel.
     --ficon-xrc               -  Set FICON XRC emulation mode.
     --ficon-tape              -  Set FICON tape read/write emulation mode.
     --ficon-tape-write        -  Set FICON tape write emulation mode.
     --ficon-tape-read         -  Set FICON tape read emulation mode.
     --ficon-tin-tir           -  Set FICON Tin Tir emulation mode.
     --ficon-dvcack            -  Set FICON Device-Acking emulation mode.
     --ficon-read-blk          -  Set FICON Read BLK-ID emulation mode.
     --ficon-tera-read         -  Set FICON Teradata read emulation mode.
     --ficon-tera-write        -  Set FICON Teradata write emulation mode.
     --ficon-print             -  Set FICON Printer emulation mode.
     --max-read-pipe <max>     -  Set the FICON max read pipelining value.
     --max-write-pipe <max>    -  Set the FICON max write pipelining value.
     --max-read-devs <max>     -  Set the FICON max read devices value.
     --max-write-devs <max>    -  Set the FICON max write devices value.
     --write-timer <ms>        -  Set the FICON write timer in ms.
     --write-chain <max>       -  Set the FICON max write chain size.
     --oxid-base <oxid>        -  Set the FICON base oxid value.
     --ficon-debug <hex>       -  Set the FICON debug flags.
  -a,--admin-status <enable|disable> -
                               -  Set the admin-status of the circuit.
  -S,--local-ip <ipaddr>|none  -  Set local IP address.
  -D,--remote-ip <ipaddr>|none -  Set remote IP address.
     --local-ha-ip <ipaddr>|none -
                               -  Set local HA IP address. This allows for HCL
                                  operations on local switch. [7840 / SX6 only]
     --remote-ha-ip <ipaddr>|none -
                               -  Set remote HA IP address. This allows for HCL
                                  operations on remote switch. [7810 / 7840 /
                                  SX6 only]
  -x,--metric <0|1>            -  Set the metric. 0=Primary 1=Failover.
  -g,--failover-group <0-9>    -  Set the failover group ID.
  -L,--load-leveling <default|failover|spillover> -
                               -  Set load leveling algorithm. [7810 / 7840 /
                                  SX6 only]
  -b,--min-comm-rate <kbps>    -  Set the minimum guaranteed rate.
  -B,--max-comm-rate <kbps>    -  Set the maximum rate.
     --arl-algorithm <mode>    -  Set the ARL algorithm. Allowable modes are
                                  [auto] [reset] [step-down] [timed-step-down].
                                  [7810 / 7840 / SX6 only]
  -C,--connection-type <type>  -  Set the connection type. Allowable types are
                                  [default] [listener] [initiator].
  -k,--keepalive-timeout <ms>  -  Set keepalive timeout in ms.
     --dscp-f-class <dscp>     -  Set DSCP marking for Control traffic.
     --dscp-high <dscp>        -  Set DSCP marking for FC-High priority traffic.
     --dscp-medium <dscp>      -  Set DSCP marking for FC-Medium priority
                                  traffic.
     --dscp-low <dscp>         -  Set DSCP marking for FC-Low priority traffic.
     --dscp-ip-high <dscp>     -  Set DSCP marking for IP-High priority traffic.
                                  [7810 / 7840 / SX6 only]
     --dscp-ip-medium <dscp>   -  Set DSCP marking for IP-Medium priority
                                  traffic. [7810 / 7840 / SX6 only]
     --dscp-ip-low <dscp>      -  Set DSCP marking for IP-Low priority traffic.
                                  [7810 / 7840 / SX6 only]
     --l2cos-f-class <l2cos>   -  Set L2CoS value for Control priority traffic.
     --l2cos-high <l2cos>      -  Set L2CoS value for FC-High priority traffic.
     --l2cos-medium <l2cos>    -  Set L2CoS value for FC-Medium priority
                                  traffic.
     --l2cos-low <l2cos>       -  Set L2CoS value for FC-Low priority traffic.
     --l2cos-ip-high <l2cos>   -  Set L2CoS value for IP-High priority traffic.
     --l2cos-ip-medium <l2cos> -  Set L2CoS value for IP-Medium priority
                                  traffic.
     --l2cos-ip-low <l2cos>    -  Set L2CoS value for IP-Low priority traffic.
     --ipext <enable|disable>  -  Enable / Disable IP Extension on this tunnel.
                                  [7810 / 7840 / SX6 only]
     --sla <sla-name>|none     -  Set the SLA name for this circuit. [7810 /
                                  7840 / SX6 only]
     --help                    -  Print this usage statement.

Example:
  portcfg fciptunnel 24 create --compression none

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow fciptunnel 10/166                            portcfg fciptunnel 10/16 -i morgan_ipsec1m-i morgan_ipsec1o-i morgan_ipsec1d-i morgan_ipsec1i-i morgan_ipsec1f-i morgan_ipsec1y-i morgan_ipsec1 -i morgan_ipsec1

!!!! WARNING !!!!
Modify operation can disrupt the traffic on the fciptunnel specified for a brief period of time. This operation will bring the existing tunnel down (if tunnel is up) before applying new configuration.

Continue with Modification (Y,y,N,n): [ n]y
Operation Succeeded.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgshow fciptunnel 10/169/16                       show fciptunnel

 Tunnel Circuit  OpStatus  Flags    Uptime  TxMBps  RxMBps ConnCnt CommRt Met/G
--------------------------------------------------------------------------------
 9/16  -         Up      --i----a-   21h22m    0.00    0.00   1      -       -
 10/16 -         InProg  --i----a-   21h50m    0.00    0.00   1      -       -
--------------------------------------------------------------------------------
 Flags (tunnel): l=Legacy QOS Mode
                 i=IPSec f=Fastwrite T=TapePipelining F=FICON r=ReservedBW
                 a=FastDeflate d=Deflate D=AggrDeflate P=Protocol
                 I=IP-Ext

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fciptunnel 10/16

 Tunnel: VE-Port:10/16 (idx:0, DP0)
 ====================================================
  Oper State           : In Progress
  TID                  : 496
  Flags                : 0x00000000
  IP-Extension         : Disabled
  Compression          : Fast Deflate
  QoS BW Ratio         : 50% / 30% / 20%
  Fastwrite            : Disabled
  Tape Pipelining      : Disabled
  IPSec                : Enabled
  IPSec-Policy         : morgan_ipsec1
  Legacy QOS Mode      : Disabled
  Load-Level (Cfg/Peer): Failover (Spillover / Failover)
  Local WWN            : 10:00:d8:1f:cc:71:62:00
  Peer WWN             : 00:00:00:00:00:00:00:00
  RemWWN (config)      : 00:00:00:00:00:00:00:00
  Peer Platform        : UNKNOWN
  cfgmask              : 0x0000001f 0x4000420c
  Uncomp/Comp Bytes    : 0 / 0 / 1.00 : 1
  Uncomp/Comp Byte(30s): 0 / 0 / 1.00 : 1
  Flow Status          : 0
  ConCount/Duration    : 1 / 18h35m
  Uptime               : 21h50m
  Stats Duration       : 18h35m
  Receiver Stats       : 4220204 bytes / 17483 pkts /    0.00 Bps Avg
  Sender Stats         : 4397092 bytes / 17483 pkts /    0.00 Bps Avg
  TCP Bytes In/Out     : 1814394548 / 1812133488
  ReTx/OOO/SloSt/DupAck: 26 / 39 / 31 / 0
  RTT (min/avg/max)    : 5 / 5 / 49 ms
  Wan Util             : 0.0%
  TxQ Util             : 0.0%

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fciptunnel 10/160/16/169/16

 Tunnel: VE-Port:9/16 (idx:0, DP0)
 ====================================================
  Oper State           : Online
  TID                  : 400
  Flags                : 0x00000000
  IP-Extension         : Disabled
  Compression          : Fast Deflate
  QoS BW Ratio         : 50% / 30% / 20%
  Fastwrite            : Disabled
  Tape Pipelining      : Disabled
  IPSec                : Enabled
  IPSec-Policy         : morgan_ipsec1
  Legacy QOS Mode      : Disabled
  Load-Level (Cfg/Peer): Spillover (Spillover / Spillover)
  Local WWN            : 10:00:d8:1f:cc:71:62:00
  Peer WWN             : 10:00:d8:1f:cc:76:c9:c0
  RemWWN (config)      : 00:00:00:00:00:00:00:00
  Peer Platform        : SX6
  cfgmask              : 0x0000001f 0x4000420c
  Uncomp/Comp Bytes    : 0 / 0 / 1.00 : 1
  Uncomp/Comp Byte(30s): 0 / 0 / 1.00 : 1
  Flow Status          : 0
  ConCount/Duration    : 1 / 18h35m
  Uptime               : 21h22m
  Stats Duration       : 18h35m
  Receiver Stats       : 854696 bytes / 6847 pkts /   93.00 Bps Avg
  Sender Stats         : 854800 bytes / 6847 pkts /   98.00 Bps Avg
  TCP Bytes In/Out     : 2062695304 / 2546729048
  ReTx/OOO/SloSt/DupAck: 28 / 265 / 32 / 0
  RTT (min/avg/max)    : 5 / 5 / 49 ms
  Wan Util             : 0.0%
  TxQ Util             : 0.0%

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
logout:Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.04 16:13:07 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgshow
Defined configuration:

Effective configuration:
No Effective configuration: (No Access)


REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0434_1_8","50:00:09:73:98:06:C8:08"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0434_3_8","50:00:09:73:98:06:C8:88"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0434_5_8","50:00:09:73:98:06:C8:09"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0434_7_8","50:00:09:73:98:06:C8:88"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0438_1_8","50:00:09:73:98:06:D8:08"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0438_3_8","50:00:09:73:98:06:D8:88"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0438_5_8","50:00:09:73:98:06:D8:09"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0438_7_8","50:00:09:73:98:06:D8:88"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> Zonecreate RZonecreate EZonecreate PZonecreate LZonecreate _Zonecreate AZonecreate _Zonecreate SZonecreate RZonecreate DZonecreate FZonecreate _Zonecreate 0Zonecreate 4Zonecreate 3Zonecreate 4Zonecreate _Zonecreate 0Zonecreate 4Zonecreate 3Zonecreate 8Zonecreate "Zonecreate ,Zonecreate "Zonecreate RZonecreate EZonecreate PZonecreate LZonecreate _Zonecreate AZonecreate _Zonecreate SZonecreate RZonecreate DZonecreate FZonecreate _Zonecreate 0Zonecreate 4Zonecreate 3Zonecreate 4Zonecreate _Zonecreate 1Zonecreate _Zonecreate 8Zonecreate ;Zonecreate RZonecreate EZonecreate PZonecreate LZonecreate _Zonecreate AZonecreate _Zonecreate SZonecreate RZonecreate DZonecreate FZonecreate _Zonecreate 0Zonecreate 4Zonecreate 3Zonecreate 8Zonecreate _Zonecreate 1Zonecreate _Zonecreate 8Zonecreate ;Zonecreate RZonecreate EZonecreate PZonecreate LZonecreate _Zonecreate AZonecreate _Zonecreate SZonecreate RZonecreate DZonecreate FZonecreate _Zonecreate 0Zonecreate 4Zonecreate 3Zonecreate 4Zonecreate _Zonecreate 3Zonecreate _Zonecreate 8Zonecreate ;Zonecreate  EPISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;RZonecreate
 EPISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REZonecreate PISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPZonecreate ISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPLZonecreate SG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_Zonecreate G1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_AZonecreate 1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_Zonecreate A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SZonecreate _DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRZonecreate DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDZonecreate EF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDFZonecreate
_Zonecreate
_0Zonecreate
_04Zonecreate
_043Zonecreate
_0438Zonecreate
_0438_Zonecreate
_0438_3Zonecreate
_0438_3_Zonecreate
_0438_3_8Zonecreate
_0438_3_8;Zonecreate RZonecreate EZonecreate PZonecreate LZonecreate _Zonecreate AZonecreate _Zonecreate SZonecreate RZonecreate DZonecreate FZonecreate _Zonecreate 0Zonecreate 4Zonecreate 3Zonecreate 4Zonecreate _Zonecreate 5Zonecreate _Zonecreate 8Zonecreate ;Zonecreate RZonecreate EZonecreate PZonecreate LZonecreate _Zonecreate AZonecreate _Zonecreate SZonecreate RZonecreate DZonecreate FZonecreate _Zonecreate 0Zonecreate 4Zonecreate 3Zonecreate 8Zonecreate _Zonecreate 5Zonecreate _Zonecreate 8Zonecreate ;Zonecreate RZonecreate EZonecreate PZonecreate LZonecreate _Zonecreate AZonecreate _Zonecreate SZonecreate RZonecreate DZonecreate FZonecreate _Zonecreate 0Zonecreate 4Zonecreate 3Zonecreate 4Zonecreate _Zonecreate 7Zonecreate _Zonecreate 8Zonecreate ;Zonecreate RZonecreate EZonecreate PZonecreate LZonecreate _Zonecreate AZonecreate _Zonecreate SZonecreate RZonecreate DZonecreate FZonecreate _Zonecreate 0Zonecreate 4Zonecreate 3Zonecreate 8Zonecreate _Zonecreate 7Zonecreate _Zonecreate 8Zonecreate "Zonecreate Zonecreate                                                                                                          REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRD

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRD

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> zonecreate  Rzonecreate  Ezonecreate  Pzonecreate  Lzonecreate  _zonecreate  Azonecreate  _zonecreate  Szonecreate  Rzonecreate  Dzonecreate  Fzonecreate  _zonecreate  0zonecreate  4zonecreate  3zonecreate  4zonecreate  _zonecreate  0zonecreate  4zonecreate  3zonecreate  8zonecreate  "zonecreate  ,zonecreate  "zonecreate  Rzonecreate  Ezonecreate  Pzonecreate  Lzonecreate  _zonecreate  Azonecreate  _zonecreate  Szonecreate  Rzonecreate  Dzonecreate  Fzonecreate  _zonecreate  0zonecreate  4zonecreate  3zonecreate  4zonecreate  _zonecreate  1zonecreate  _zonecreate  8zonecreate  ;zonecreate  Rzonecreate  Ezonecreate  Pzonecreate  Lzonecreate  _zonecreate  Azonecreate  _zonecreate  Szonecreate  Rzonecreate  Dzonecreate  Fzonecreate  _zonecreate  0zonecreate  4zonecreate  3zonecreate  8zonecreate  _zonecreate  1zonecreate  _zonecreate  8zonecreate  ;zonecreate  Rzonecreate  Ezonecreate  Pzonecreate  Lzonecreate  _zonecreate  Azonecreate  _zonecreate  Szonecreate  Rzonecreate  Dzonecreate  Fzonecreate  _zonecreate  0zonecreate  4zonecreate  3zonecreate  4zonecreate  _zonecreate  3zonecreate  _zonecreate  8zonecreate   EPISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;zonecreate
 EPISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;Rzonecreate  PISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REzonecreate  ISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPzonecreate  SG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPLzonecreate  G1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_zonecreate  1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_Azonecreate  A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_zonecreate  _DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_Szonecreate  DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRzonecreate  EF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDzonecreate  F:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDFzonecreate
_zonecreate
_0zonecreate
_04zonecreate
_043zonecreate
_0438zonecreate
_0438_zonecreate
_0438_3zonecreate
_0438_3_zonecreate
_0438_3_8zonecreate
_0438_3_8;zonecreate
_0438_3_8;Rzonecreate  Ezonecreate  Pzonecreate  Lzonecreate  _zonecreate  Azonecreate  _zonecreate  Szonecreate  Rzonecreate  Dzonecreate  Fzonecreate  _zonecreate  0zonecreate  4zonecreate  3zonecreate  4zonecreate  _zonecreate  5zonecreate  _zonecreate  8zonecreate  ;zonecreate  Rzonecreate  Ezonecreate  Pzonecreate  Lzonecreate  _zonecreate  Azonecreate  _zonecreate  Szonecreate  Rzonecreate  Dzonecreate  Fzonecreate  _zonecreate  0zonecreate  4zonecreate  3zonecreate  8zonecreate  _zonecreate  5zonecreate  _zonecreate  8zonecreate  ;zonecreate  Rzonecreate  Ezonecreate  Pzonecreate  Lzonecreate  _zonecreate  Azonecreate  _zonecreate  Szonecreate  Rzonecreate  Dzonecreate  Fzonecreate  _zonecreate  0zonecreate  4zonecreate  3zonecreate  4zonecreate  _zonecreate  7zonecreate  _zonecreate  8zonecreate  ;zonecreate  Rzonecreate  Ezonecreate  Pzonecreate  Lzonecreate  _zonecreate  Azonecreate  _zonecreate  Szonecreate  Rzonecreate  Dzonecreate  Fzonecreate  _zonecreate  0zonecreate  4zonecreate  3zonecreate  8zonecreate  _zonecreate  7zonecreate  _zonecreate  8zonecreate  "zonecreate  zonecreate
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDzREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8"  oREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8"  nREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8"  eREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8"  cREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8"  rREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8"  eREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8"  aREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8"  tREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8"  eREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8"   REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8"  "REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8"

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgcreate "REPL_A","REPL_A_SRDF_0434_0438"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgsave
You are about to save the Defined zoning configuration. This
action will only save the changes on Defined configuration.
Do you want to save the Defined zoning configuration only?  (yes, y, no, n): [no] y
Updating flash ...
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgenable "REPL_A"
You are about to enable a new zoning configuration.
This action will replace the old zoning configuration with the
current configuration selected.
Do you want to enable 'REPL_A' configuration  (yes, y, no, n): [no] y
zone config "REPL_A" is in effect
Updating flash ...
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgshow
Defined configuration:
 cfg:REPL_AREPL_A_SRDF_0434_0438
 zone:REPL_A_SRDF_0434_0438
REPL_A_SRDF_0434_1_8; REPL_A_SRDF_0434_3_8;
REPL_A_SRDF_0434_5_8; REPL_A_SRDF_0434_7_8;
REPL_A_SRDF_0438_1_8; REPL_A_SRDF_0438_3_8;
REPL_A_SRDF_0438_5_8; REPL_A_SRDF_0438_7_8
 alias:REPL_A_SRDF_0434_1_8
50:00:09:73:98:06:c8:08
 alias:REPL_A_SRDF_0434_3_8
50:00:09:73:98:06:c8:88
 alias:REPL_A_SRDF_0434_5_8
50:00:09:73:98:06:c8:09
 alias:REPL_A_SRDF_0434_7_8
50:00:09:73:98:06:c8:88
 alias:REPL_A_SRDF_0438_1_8
50:00:09:73:98:06:d8:08
 alias:REPL_A_SRDF_0438_3_8
50:00:09:73:98:06:d8:88
 alias:REPL_A_SRDF_0438_5_8
50:00:09:73:98:06:d8:09
 alias:REPL_A_SRDF_0438_7_8
50:00:09:73:98:06:d8:88

Effective configuration:
 cfg:REPL_A
 zone:REPL_A_SRDF_0434_0438
50:00:09:73:98:06:c8:08
50:00:09:73:98:06:c8:88
50:00:09:73:98:06:c8:09
50:00:09:73:98:06:d8:08
50:00:09:73:98:06:d8:88
50:00:09:73:98:06:d8:09

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> zoneshow
Defined configuration:
 cfg:REPL_AREPL_A_SRDF_0434_0438
 zone:REPL_A_SRDF_0434_0438
REPL_A_SRDF_0434_1_8; REPL_A_SRDF_0434_3_8;
REPL_A_SRDF_0434_5_8; REPL_A_SRDF_0434_7_8;
REPL_A_SRDF_0438_1_8; REPL_A_SRDF_0438_3_8;
REPL_A_SRDF_0438_5_8; REPL_A_SRDF_0438_7_8
 alias:REPL_A_SRDF_0434_1_8
50:00:09:73:98:06:c8:08
 alias:REPL_A_SRDF_0434_3_8
50:00:09:73:98:06:c8:88
 alias:REPL_A_SRDF_0434_5_8
50:00:09:73:98:06:c8:09
 alias:REPL_A_SRDF_0434_7_8
50:00:09:73:98:06:c8:88
 alias:REPL_A_SRDF_0438_1_8
50:00:09:73:98:06:d8:08
 alias:REPL_A_SRDF_0438_3_8
50:00:09:73:98:06:d8:88
 alias:REPL_A_SRDF_0438_5_8
50:00:09:73:98:06:d8:09
 alias:REPL_A_SRDF_0438_7_8
50:00:09:73:98:06:d8:88

Effective configuration:
 cfg:REPL_A
 zone:REPL_A_SRDF_0434_0438
50:00:09:73:98:06:c8:08
50:00:09:73:98:06:c8:88
50:00:09:73:98:06:c8:09
50:00:09:73:98:06:d8:08
50:00:09:73:98:06:d8:88
50:00:09:73:98:06:d8:09

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> zoneshow "REPL_A_SRDF_0434_0438"
 zone:REPL_A_SRDF_0434_0438
REPL_A_SRDF_0434_1_8; REPL_A_SRDF_0434_3_8;
REPL_A_SRDF_0434_5_8; REPL_A_SRDF_0434_7_8;
REPL_A_SRDF_0438_1_8; REPL_A_SRDF_0438_3_8;
REPL_A_SRDF_0438_5_8; REPL_A_SRDF_0438_7_8

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> CFGSHOW       cfgshow
Defined configuration:
 cfg:REPL_AREPL_A_SRDF_0434_0438
 zone:REPL_A_SRDF_0434_0438
REPL_A_SRDF_0434_1_8; REPL_A_SRDF_0434_3_8;
REPL_A_SRDF_0434_5_8; REPL_A_SRDF_0434_7_8;
REPL_A_SRDF_0438_1_8; REPL_A_SRDF_0438_3_8;
REPL_A_SRDF_0438_5_8; REPL_A_SRDF_0438_7_8
 alias:REPL_A_SRDF_0434_1_8
50:00:09:73:98:06:c8:08
 alias:REPL_A_SRDF_0434_3_8
50:00:09:73:98:06:c8:88
 alias:REPL_A_SRDF_0434_5_8
50:00:09:73:98:06:c8:09
 alias:REPL_A_SRDF_0434_7_8
50:00:09:73:98:06:c8:88
 alias:REPL_A_SRDF_0438_1_8
50:00:09:73:98:06:d8:08
 alias:REPL_A_SRDF_0438_3_8
50:00:09:73:98:06:d8:88
 alias:REPL_A_SRDF_0438_5_8
50:00:09:73:98:06:d8:09
 alias:REPL_A_SRDF_0438_7_8
50:00:09:73:98:06:d8:88

Effective configuration:
 cfg:REPL_A
 zone:REPL_A_SRDF_0434_0438
50:00:09:73:98:06:c8:08
50:00:09:73:98:06:c8:88
50:00:09:73:98:06:c8:09
50:00:09:73:98:06:d8:08
50:00:09:73:98:06:d8:88
50:00:09:73:98:06:d8:09

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgdelete      clear
The Clear All action will clear all aliases, zones,
and configurations in the Defined configuration.
Run cfgSave to commit the transaction or cfgTransAbort to
cancel the transaction.
Do you really want to clear all configurations?  (yes, y, no, n): [no] y
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgsave
WARNING!!!
The changes you are attempting to save will render the
Effective configuration and the Defined configuration
inconsistent. The inconsistency will result in different
Effective Zoning configurations for switches in the fabric if
a zone merge or HA failover happens. To avoid inconsistency
it is recommended to commit the configurations using the
'cfgenable' command.

Do you want to proceed with saving the Defined
zoning configuration only?  (yes, y, no, n): [no] y
"REPL_A" not found
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgshow
Defined configuration:

Effective configuration:
 cfg:REPL_A
 zone:REPL_A_SRDF_0434_0438
50:00:09:73:98:06:c8:08
50:00:09:73:98:06:c8:88
50:00:09:73:98:06:c8:09
50:00:09:73:98:06:d8:08
50:00:09:73:98:06:d8:88
50:00:09:73:98:06:d8:09

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> d sfg   cfgdisav ble "REPL_A"
error: Usage: cfgDisable [-force | -f]
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgdisable "REPL_A" -FORCE     force
error: Usage: cfgDisable [-force | -f]
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgdisable "REPL_A" -force     -f -f -f -f -f -f -f -f
You have disabled the zoning configuration using the -force option. This
action has disabled any previously enabled zoning configuration.
Updating flash ...
Effective configuration is empty. "No Access" default zone mode is ON.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgshow
Defined configuration:

Effective configuration:
No Effective configuration: (No Access)


REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgsave
You are about to save the Defined zoning configuration. This
action will only save the changes on Defined configuration.
Do you want to save the Defined zoning configuration only?  (yes, y, no, n): [no] u^[[Dy^?
Input not acceptable, please re-enter
Do you want to save the Defined zoning configuration only?  (yes, y, no, n): [no] y
Nothing changed: nothing to save, returning ...
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgsavehow
Defined configuration:

Effective configuration:
No Effective configuration: (No Access)


REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0434_1_8","50:00:09:73:98:06:C8:08"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0434_3_8","50:00:09:73:98:06:C8:88"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0434_5_8","50:00:09:73:98:06:C9:08"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0434_7_8","50:00:09:73:98:06:C9:88"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0438_1_8","50:00:09:73:98:06:D8:08"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0438_3_8","50:00:09:73:98:06:D8:88"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0438_5_8","50:00:09:73:98:06:D9:08"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> alicreate "REPL_A_SRDF_0438_7_8","50:00:09:73:98:06:D9:88"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> zonecreate Rzonecreate Ezonecreate Pzonecreate Lzonecreate _zonecreate Azonecreate _zonecreate Szonecreate Rzonecreate Dzonecreate Fzonecreate _zonecreate 0zonecreate 4zonecreate 3zonecreate 4zonecreate _zonecreate 0zonecreate 4zonecreate 3zonecreate 8zonecreate "zonecreate ,zonecreate "zonecreate Rzonecreate Ezonecreate Pzonecreate Lzonecreate _zonecreate Azonecreate _zonecreate Szonecreate Rzonecreate Dzonecreate Fzonecreate _zonecreate 0zonecreate 4zonecreate 3zonecreate 4zonecreate _zonecreate 1zonecreate _zonecreate 8zonecreate ;zonecreate Rzonecreate Ezonecreate Pzonecreate Lzonecreate _zonecreate Azonecreate _zonecreate Szonecreate Rzonecreate Dzonecreate Fzonecreate _zonecreate 0zonecreate 4zonecreate 3zonecreate 8zonecreate _zonecreate 1zonecreate _zonecreate 8zonecreate ;zonecreate Rzonecreate Ezonecreate Pzonecreate Lzonecreate _zonecreate Azonecreate _zonecreate Szonecreate Rzonecreate Dzonecreate Fzonecreate _zonecreate 0zonecreate 4zonecreate 3zonecreate 4zonecreate _zonecreate 3zonecreate _zonecreate 8zonecreate ;zonecreate  EPISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;Rzonecreate
 EPISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REzonecreate PISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPzonecreate ISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPLzonecreate SG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_zonecreate G1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_Azonecreate 1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_zonecreate A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_Szonecreate _DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRzonecreate DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDzonecreate EF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDFzonecreate
_zonecreate
_0zonecreate
_04zonecreate
_043zonecreate
_0438zonecreate
_0438_zonecreate
_0438_3zonecreate
_0438_3_zonecreate
_0438_3_8zonecreate
_0438_3_8;zonecreate Rzonecreate Ezonecreate Pzonecreate Lzonecreate _zonecreate Azonecreate _zonecreate Szonecreate Rzonecreate Dzonecreate Fzonecreate _zonecreate 0zonecreate 4zonecreate 3zonecreate 4zonecreate _zonecreate 5zonecreate _zonecreate 8zonecreate ;zonecreate Rzonecreate Ezonecreate Pzonecreate Lzonecreate _zonecreate Azonecreate _zonecreate Szonecreate Rzonecreate Dzonecreate Fzonecreate _zonecreate 0zonecreate 4zonecreate 3zonecreate 8zonecreate _zonecreate 5zonecreate _zonecreate 8zonecreate ;zonecreate Rzonecreate Ezonecreate Pzonecreate Lzonecreate _zonecreate Azonecreate _zonecreate Szonecreate Rzonecreate Dzonecreate Fzonecreate _zonecreate 0zonecreate 4zonecreate 3zonecreate 4zonecreate _zonecreate 7zonecreate _zonecreate 8zonecreate ;zonecreate Rzonecreate Ezonecreate Pzonecreate Lzonecreate _zonecreate Azonecreate _zonecreate Szonecreate Rzonecreate Dzonecreate Fzonecreate _zonecreate 0zonecreate 4zonecreate 3zonecreate 8zonecreate _zonecreate 7zonecreate _zonecreate 8zonecreate "zonecreate onecreate necreate ecreate create reate eate ate te e
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDzREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8" oREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8" nREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8" eREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8" cREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8" rREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8" eREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8" aREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8" tREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8" eREPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8"  REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8" "REPL_A_SRDF_0434_0438","REPL_A_SRDF_0434_1_8;REPL_A_SRDF_0438_1_8;REPL_A_SRDF_0434_3_8;REPL_A_SRDF_0438_3_8;REPL_A_SRDF_0434_5_8;REPL_A_SRDF_0438_5_8;REPL_A_SRDF_0434_7_8;REPL_A_SRDF_0438_7_8"

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgcreate "REPL_A","REPL_A_SRDF_0434_0438"
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgsave
You are about to save the Defined zoning configuration. This
action will only save the changes on Defined configuration.
Do you want to save the Defined zoning configuration only?  (yes, y, no, n): [no] y
Updating flash ...
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgsh how
Defined configuration:
 cfg:REPL_AREPL_A_SRDF_0434_0438
 zone:REPL_A_SRDF_0434_0438
REPL_A_SRDF_0434_1_8; REPL_A_SRDF_0434_3_8;
REPL_A_SRDF_0434_5_8; REPL_A_SRDF_0434_7_8;
REPL_A_SRDF_0438_1_8; REPL_A_SRDF_0438_3_8;
REPL_A_SRDF_0438_5_8; REPL_A_SRDF_0438_7_8
 alias:REPL_A_SRDF_0434_1_8
50:00:09:73:98:06:c8:08
 alias:REPL_A_SRDF_0434_3_8
50:00:09:73:98:06:c8:88
 alias:REPL_A_SRDF_0434_5_8
50:00:09:73:98:06:c9:08
 alias:REPL_A_SRDF_0434_7_8
50:00:09:73:98:06:c9:88
 alias:REPL_A_SRDF_0438_1_8
50:00:09:73:98:06:d8:08
 alias:REPL_A_SRDF_0438_3_8
50:00:09:73:98:06:d8:88
 alias:REPL_A_SRDF_0438_5_8
50:00:09:73:98:06:d9:08
 alias:REPL_A_SRDF_0438_7_8
50:00:09:73:98:06:d9:88

Effective configuration:
No Effective configuration: (No Access)


REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgenable "REPL_A"
You are about to enable a new zoning configuration.
This action will replace the old zoning configuration with the
current configuration selected.
Do you want to enable 'REPL_A' configuration  (yes, y, no, n): [no] y
zone config "REPL_A" is in effect
Updating flash ...
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgshow
Defined configuration:
 cfg:REPL_AREPL_A_SRDF_0434_0438
 zone:REPL_A_SRDF_0434_0438
REPL_A_SRDF_0434_1_8; REPL_A_SRDF_0434_3_8;
REPL_A_SRDF_0434_5_8; REPL_A_SRDF_0434_7_8;
REPL_A_SRDF_0438_1_8; REPL_A_SRDF_0438_3_8;
REPL_A_SRDF_0438_5_8; REPL_A_SRDF_0438_7_8
 alias:REPL_A_SRDF_0434_1_8
50:00:09:73:98:06:c8:08
 alias:REPL_A_SRDF_0434_3_8
50:00:09:73:98:06:c8:88
 alias:REPL_A_SRDF_0434_5_8
50:00:09:73:98:06:c9:08
 alias:REPL_A_SRDF_0434_7_8
50:00:09:73:98:06:c9:88
 alias:REPL_A_SRDF_0438_1_8
50:00:09:73:98:06:d8:08
 alias:REPL_A_SRDF_0438_3_8
50:00:09:73:98:06:d8:88
 alias:REPL_A_SRDF_0438_5_8
50:00:09:73:98:06:d9:08
 alias:REPL_A_SRDF_0438_7_8
50:00:09:73:98:06:d9:88

Effective configuration:
 cfg:REPL_A
 zone:REPL_A_SRDF_0434_0438
50:00:09:73:98:06:c8:08
50:00:09:73:98:06:c8:88
50:00:09:73:98:06:c9:08
50:00:09:73:98:06:c9:88
50:00:09:73:98:06:d8:08
50:00:09:73:98:06:d8:88
50:00:09:73:98:06:d9:08
50:00:09:73:98:06:d9:88

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> timed out waiting for input: auto-logout
Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.04 18:25:43 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
logout:Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.08 21:13:56 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parkee r@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> cfgshow
Defined configuration:
 cfg:REPL_AREPL_A_DLm_1001_1004; REPL_A_SRDF_0431_0437;
REPL_A_SRDF_0434_0438
 zone:REPL_A_DLm_1001_1004
REPL_A_DLm_1001_1_6; REPL_A_DLm_1001_2_6; REPL_A_DLm_1001_3_6;
REPL_A_DLm_1001_4_6; REPL_A_DLm_1004_1_6; REPL_A_DLm_1004_2_6;
REPL_A_DLm_1004_3_6; REPL_A_DLm_1004_4_6
 zone:REPL_A_SRDF_0431_0437
REPL_A_SRDF_0431_1_8; REPL_A_SRDF_0431_1_9;
REPL_A_SRDF_0431_3_8; REPL_A_SRDF_0431_5_10;
REPL_A_SRDF_0431_5_9; REPL_A_SRDF_0431_7_8;
REPL_A_SRDF_0437_1_10; REPL_A_SRDF_0437_3_10;
REPL_A_SRDF_0437_3_9; REPL_A_SRDF_0437_5_8;
REPL_A_SRDF_0437_7_10; REPL_A_SRDF_0437_7_9
 zone:REPL_A_SRDF_0434_0438
REPL_A_SRDF_0434_1_8; REPL_A_SRDF_0434_3_8;
REPL_A_SRDF_0434_5_8; REPL_A_SRDF_0434_7_8;
REPL_A_SRDF_0438_1_8; REPL_A_SRDF_0438_3_8;
REPL_A_SRDF_0438_5_8; REPL_A_SRDF_0438_7_8
 alias:REPL_A_DLm_1001_1_6
50:00:09:73:78:0f:a4:06
 alias:REPL_A_DLm_1001_2_6
50:00:09:73:78:0f:a4:46
 alias:REPL_A_DLm_1001_3_6
50:00:09:73:78:0f:a4:86
 alias:REPL_A_DLm_1001_4_6
50:00:09:73:78:0f:a4:c6
 alias:REPL_A_DLm_1004_1_6
50:00:09:73:78:0f:b0:06
 alias:REPL_A_DLm_1004_2_6
50:00:09:73:78:0f:b0:46
 alias:REPL_A_DLm_1004_3_6
50:00:09:73:78:0f:b0:86
 alias:REPL_A_DLm_1004_4_6
50:00:09:73:78:0f:b0:c6
 alias:REPL_A_SRDF_0431_1_8
50:00:09:73:98:06:bc:08
 alias:REPL_A_SRDF_0431_1_9
50:00:09:73:98:06:bc:09
 alias:REPL_A_SRDF_0431_3_8
50:00:09:73:98:06:bc:88
 alias:REPL_A_SRDF_0431_5_10
50:00:09:73:98:06:bd:0a
 alias:REPL_A_SRDF_0431_5_9
50:00:09:73:98:06:bd:09
 alias:REPL_A_SRDF_0431_7_8
50:00:09:73:98:06:bd:88
 alias:REPL_A_SRDF_0434_1_8
50:00:09:73:98:06:c8:08
 alias:REPL_A_SRDF_0434_3_8
50:00:09:73:98:06:c8:88
 alias:REPL_A_SRDF_0434_5_8
50:00:09:73:98:06:c9:08
 alias:REPL_A_SRDF_0434_7_8
50:00:09:73:98:06:c9:88
 alias:REPL_A_SRDF_0437_1_10
50:00:09:73:98:06:d4:08
 alias:REPL_A_SRDF_0437_3_10
50:00:09:73:98:06:d4:88
 alias:REPL_A_SRDF_0437_3_9
50:00:09:73:98:06:d4:09
 alias:REPL_A_SRDF_0437_5_8
50:00:09:73:98:06:d5:09
 alias:REPL_A_SRDF_0437_7_10
50:00:09:73:98:06:d5:88
 alias:REPL_A_SRDF_0437_7_9
50:00:09:73:98:06:d5:0a
 alias:REPL_A_SRDF_0438_1_8
50:00:09:73:98:06:d8:08
 alias:REPL_A_SRDF_0438_3_8
50:00:09:73:98:06:d8:88
 alias:REPL_A_SRDF_0438_5_8
50:00:09:73:98:06:d9:08
 alias:REPL_A_SRDF_0438_7_8
50:00:09:73:98:06:d9:88

Effective configuration:
 cfg:REPL_A
 zone:REPL_A_DLm_1001_1004
50:00:09:73:78:0f:a4:06
50:00:09:73:78:0f:a4:46
50:00:09:73:78:0f:a4:86
50:00:09:73:78:0f:a4:c6
50:00:09:73:78:0f:b0:06
50:00:09:73:78:0f:b0:46
50:00:09:73:78:0f:b0:86
50:00:09:73:78:0f:b0:c6
 zone:REPL_A_SRDF_0431_0437
50:00:09:73:98:06:bc:08
50:00:09:73:98:06:bc:09
50:00:09:73:98:06:bc:88
50:00:09:73:98:06:bd:0a
50:00:09:73:98:06:bd:09
50:00:09:73:98:06:bd:88
50:00:09:73:98:06:d4:08
50:00:09:73:98:06:d4:88
50:00:09:73:98:06:d4:09
50:00:09:73:98:06:d5:09
50:00:09:73:98:06:d5:88
50:00:09:73:98:06:d5:0a
 zone:REPL_A_SRDF_0434_0438
50:00:09:73:98:06:c8:08
50:00:09:73:98:06:c8:88
50:00:09:73:98:06:c9:08
50:00:09:73:98:06:c9:88
50:00:09:73:98:06:d8:08
50:00:09:73:98:06:d8:88
50:00:09:73:98:06:d9:08
50:00:09:73:98:06:d9:88

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
logout:Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.14 10:24:10 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fciptunnel all -c --lifetime

 Tunnel Circuit  OpStatus  Flags    Uptime  TxMBps  RxMBps ConnCnt CommRt Met/G
--------------------------------------------------------------------------------
 9/16  -         Up      --i----a-   10d17h    0.00    0.00   1      -       -
 9/16  0 9/ge2   Up      ---vahpi4   10d17h    0.00    0.00   1  2000/5000  0/-
 9/16  1 9/ge10  Up      ---vahpi4   10d17h    0.00    0.00   1  2000/5000  0/-
 10/16 -         Up      --i----a- 9d20h31m    0.00    0.00   6      -       -
 10/16 0 10/ge2  Up      ---vahpi4 9d20h31m    0.00    0.00   6  2000/5000  0/-
 10/16 1 10/ge10 Up      ---vahpi4 9d20h31m    0.00    0.00   6  2000/5000  0/-
--------------------------------------------------------------------------------
 Flags (tunnel): l=Legacy QOS Mode
                 i=IPSec f=Fastwrite T=TapePipelining F=FICON r=ReservedBW
                 a=FastDeflate d=Deflate D=AggrDeflate P=Protocol
                 I=IP-Ext
      (circuit): h=HA-Configured v=VLAN-Tagged p=PMTU i=IPSec 4=IPv4 6=IPv6
                 ARL a=Auto r=Reset s=StepDown t=TimedStepDown  S=SLA

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
logout:Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.15 18:34:37 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>  10/16 -         Up      --i----a-    11d4h    0.0
0    0.00   2      -       -
-rbash: restricted: cannot specify symbols in command names
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>  10/16 0 10/ge10 Up      ---vahpi4    11d4h    0.0
0    0.00   2  2000/5000  0/-
-rbash: restricted: cannot specify symbols in command names
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>  10/16 1 10/ge2  Up      ---vahpi4    11d4h    0.0
0    0.00   2  2000/5000  0/-
-rbash: restricted: cannot specify symbols in command names
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> --------------------------------------------------
------------------------------
-rbash: --------------------------------------------------------------------------------: command not found
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fciptunnel all -c --lifetime

 Tunnel Circuit  OpStatus  Flags    Uptime  TxMBps  RxMBps ConnCnt CommRt Met/G
--------------------------------------------------------------------------------
 9/16  -         Up      --i----a-    12d2h    0.00    0.00   1      -       -
 9/16  0 9/ge2   Up      ---vahpi4    12d2h    0.00    0.00   1  2000/5000  0/-
 9/16  1 9/ge10  Up      ---vahpi4    12d2h    0.00    0.00   1  2000/5000  0/-
 10/16 -         Up      --i----a-    11d4h    0.00    0.00   6      -       -
 10/16 0 10/ge2  Up      ---vahpi4    11d4h    0.00    0.00   6  2000/5000  0/-
 10/16 1 10/ge10 Up      ---vahpi4    11d4h    0.00    0.00   6  2000/5000  0/-
--------------------------------------------------------------------------------
 Flags (tunnel): l=Legacy QOS Mode
                 i=IPSec f=Fastwrite T=TapePipelining F=FICON r=ReservedBW
                 a=FastDeflate d=Deflate D=AggrDeflate P=Protocol
                 I=IP-Ext
      (circuit): h=HA-Configured v=VLAN-Tagged p=PMTU i=IPSec 4=IPv4 6=IPv6
                 ARL a=Auto r=Reset s=StepDown t=TimedStepDown  S=SLA

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
logout:Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.15 21:46:42 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.  pare ker  @morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fciptunnel all -c --lifetime

 Tunnel Circuit  OpStatus  Flags    Uptime  TxMBps  RxMBps ConnCnt CommRt Met/G
--------------------------------------------------------------------------------
 9/16  -         Up      --i----a-    12d5h    0.00    0.00   1      -       -
 9/16  0 9/ge2   Up      ---vahpi4    12d5h    0.00    0.00   1  2000/5000  0/-
 9/16  1 9/ge10  Up      ---vahpi4    12d5h    0.00    0.00   1  2000/5000  0/-
 10/16 -         Up      --i----a-    11d7h    0.00    0.00   6      -       -
 10/16 0 10/ge2  Up      ---vahpi4    11d7h    0.00    0.00   6  2000/5000  0/-
 10/16 1 10/ge10 Up      ---vahpi4    11d7h    0.00    0.00   6  2000/5000  0/-
--------------------------------------------------------------------------------
 Flags (tunnel): l=Legacy QOS Mode
                 i=IPSec f=Fastwrite T=TapePipelining F=FICON r=ReservedBW
                 a=FastDeflate d=Deflate D=AggrDeflate P=Protocol
                 I=IP-Ext
      (circuit): h=HA-Configured v=VLAN-Tagged p=PMTU i=IPSec 4=IPv4 6=IPv6
                 ARL a=Auto r=Reset s=StepDown t=TimedStepDown  S=SLA

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
logout:Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.18 17:53:36 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgfec --disable -FEC 3/0-47
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgfec --disable -FEC 3/0-473/0-474/0-47
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
^[[D^[[D^[[D^[[DFEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
^[[DFEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
^?FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
^?^?^?^?^?FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
FEC has been disabled for the port at 10G/16G speeds. FEC is required and will always be active for speeds greater than 16G.
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgfec --disable -FEC 4/0-47/0-475/0-47
Error: Invalid slot 5, port 0

Usage:   portCfgFec [Mode] [Options]     [Slot/]Port[-Range]
         portCfgFec [Mode] [-FEC] [-TTS] [Slot/]Port[-Range]
Mode:    --enable       - Enable  the FEC & FEC via TTS feature on 10G/16G ports
         --disable      - Disable the FEC & FEC via TTS feature on 10G/16G ports
         --show         - Show configuration for FEC port
         --help         - Help command to see portCfgFec Usage
Options:
         -FEC           - Enable / Disable the FEC feature on 10G/16G ports
         -TTS           - Enable / Disable the FEC via TTS feature on 10G/16G ports
         -force(or)-f   - Enable the FEC via TTS feature on 10G/16G ports without confirmation

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgfec show
Invalid usage

Usage:   portCfgFec [Mode] [Options]     [Slot/]Port[-Range]
         portCfgFec [Mode] [-FEC] [-TTS] [Slot/]Port[-Range]
Mode:    --enable       - Enable  the FEC & FEC via TTS feature on 10G/16G ports
         --disable      - Disable the FEC & FEC via TTS feature on 10G/16G ports
         --show         - Show configuration for FEC port
         --help         - Help command to see portCfgFec Usage
Options:
         -FEC           - Enable / Disable the FEC feature on 10G/16G ports
         -TTS           - Enable / Disable the FEC via TTS feature on 10G/16G ports
         -force(or)-f   - Enable the FEC via TTS feature on 10G/16G ports without confirmation

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgfec show-show-show
Incomplete --show; [<slot>/]<port>[-range] is required

Usage:   portCfgFec [Mode] [Options]     [Slot/]Port[-Range]
         portCfgFec [Mode] [-FEC] [-TTS] [Slot/]Port[-Range]
Mode:    --enable       - Enable  the FEC & FEC via TTS feature on 10G/16G ports
         --disable      - Disable the FEC & FEC via TTS feature on 10G/16G ports
         --show         - Show configuration for FEC port
         --help         - Help command to see portCfgFec Usage
Options:
         -FEC           - Enable / Disable the FEC feature on 10G/16G ports
         -TTS           - Enable / Disable the FEC via TTS feature on 10G/16G ports
         -force(or)-f   - Enable the FEC via TTS feature on 10G/16G ports without confirmation

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgfec --show --show                 portcfgfec --show
Incomplete --show; [<slot>/]<port>[-range] is required

Usage:   portCfgFec [Mode] [Options]     [Slot/]Port[-Range]
         portCfgFec [Mode] [-FEC] [-TTS] [Slot/]Port[-Range]
Mode:    --enable       - Enable  the FEC & FEC via TTS feature on 10G/16G ports
         --disable      - Disable the FEC & FEC via TTS feature on 10G/16G ports
         --show         - Show configuration for FEC port
         --help         - Help command to see portCfgFec Usage
Options:
         -FEC           - Enable / Disable the FEC feature on 10G/16G ports
         -TTS           - Enable / Disable the FEC via TTS feature on 10G/16G ports
         -force(or)-f   - Enable the FEC via TTS feature on 10G/16G ports without confirmation

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgfec --show 9/ 3/     3/0-47
Port: 0
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 1
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 2
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 3
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 4
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 5
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 6
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 7
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 8
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 9
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 10
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 11
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 12
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 13
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 14
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 15
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 16
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 17
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 18
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 19
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 20
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 21
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 22
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 23
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 24
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 25
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 26
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 27
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 28
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 29
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 30
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 31
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 32
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 33
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 34
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 35
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 36
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 37
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 38
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 39
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 40
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 41
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 42
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 43
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 44
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 45
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 46
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 47
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgfec --show 3/0-47w 3/0-474/0-47
Port: 96
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 97
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 98
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 99
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 100
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 101
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 102
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 103
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 104
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 105
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 106
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 107
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 108
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 109
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 110
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 111
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 112
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 113
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 114
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 115
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 116
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 117
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 118
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 119
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 120
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 121
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 122
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 123
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 124
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 125
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 126
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 127
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 128
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 129
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 130
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 131
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 132
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 133
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 134
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 135
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 136
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 137
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 138
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 139
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 140
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 141
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 142
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 143
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exu it
logout:Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.18 21:25:32 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fciptunnel all -c --lifetime

 Tunnel Circuit  OpStatus  Flags    Uptime  TxMBps  RxMBps ConnCnt CommRt Met/G
--------------------------------------------------------------------------------
 9/16  -         Up      --i----a-    15d4h    0.00    0.00   1      -       -
 9/16  0 9/ge2   Up      ---vahpi4    15d4h    0.00    0.00   1  2000/5000  0/-
 9/16  1 9/ge10  Up      ---vahpi4    15d4h    0.00    0.00   1  2000/5000  0/-
 10/16 -         Up      --i----a-  1d9h12m    0.00    0.00   7      -       -
 10/16 0 10/ge2  Up      ---vahpi4  1d9h12m    0.00    0.00   7  2000/5000  0/-
 10/16 1 10/ge10 Up      ---vahpi4  1d9h12m    0.00    0.00   7  2000/5000  0/-
--------------------------------------------------------------------------------
 Flags (tunnel): l=Legacy QOS Mode
                 i=IPSec f=Fastwrite T=TapePipelining F=FICON r=ReservedBW
                 a=FastDeflate d=Deflate D=AggrDeflate P=Protocol
                 I=IP-Ext
      (circuit): h=HA-Configured v=VLAN-Tagged p=PMTU i=IPSec 4=IPv4 6=IPv6
                 ARL a=Auto r=Reset s=StepDown t=TimedStepDown  S=SLA

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> EXIT
-rbash: EXIT: command not found
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
logout:Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.20 11:55:45 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> switchshow
switchName:REPISG1A_DEF
switchType:180.0
switchState:Online
switchMode:Native
switchRole:Principal
switchDomain:26
switchId:fffc1a
switchWwn:10:00:d8:1f:cc:71:62:00
zoning:ON (REPL_A)
switchBeacon:OFF
FC Router:OFF
Fabric Name:REPISG1A/EA_FAB
HIF Mode:OFF
Allow XISL Use:OFF
LS Attributes:[FID: 128, Base Switch: No, Default Switch: Yes, Ficon Switch: No, Address Mode 0]
Index Slot Port Address Media  Speed        State    Proto
============================================================
   0    3    0   1a0000   id    N32  No_Light    FC
   1    3    1   1a0100   id    N32  No_Light    FC
   2    3    2   1a0200   id    N32  No_Light    FC
   3    3    3   1a0300   id    N32  No_Light    FC
   4    3    4   1a0400   id    N32  No_Light    FC
   5    3    5   1a0500   id    N32  No_Light    FC
   6    3    6   1a0600   id    N32  No_Light    FC
   7    3    7   1a0700   id    N32  No_Light    FC
   8    3    8   1a0800   id    N32  No_Light    FC
   9    3    9   1a0900   id    N32  No_Light    FC
  10    3   10   1a0a00   id    N32  No_Light    FC
  11    3   11   1a0b00   id    N32  No_Light    FC
  12    3   12   1a0c00   id    N32  No_Light    FC
  13    3   13   1a0d00   id    N32  No_Light    FC
  14    3   14   1a0e00   id    N32  No_Light    FC
  15    3   15   1a0f00   id    N32  No_Light    FC
  16    3   16   1a1000   id    N32  No_Light    FC
  17    3   17   1a1100   id    N32  No_Light    FC
  18    3   18   1a1200   id    N32  No_Light    FC
  19    3   19   1a1300   id    N32  No_Light    FC
  20    3   20   1a1400   id    N32  No_Light    FC
  21    3   21   1a1500   id    N32  No_Light    FC
  22    3   22   1a1600   id    N32  No_Light    FC
  23    3   23   1a1700   id    N32  No_Light    FC
  24    3   24   1a1800   id    N32  No_Light    FC
  25    3   25   1a1900   id    N32  No_Light    FC
  26    3   26   1a1a00   id    N32  No_Light    FC
  27    3   27   1a1b00   id    N32  No_Light    FC
  28    3   28   1a1c00   id    N32  No_Light    FC
  29    3   29   1a1d00   id    N32  No_Light    FC
  30    3   30   1a1e00   id    N32  No_Light    FC
  31    3   31   1a1f00   id    N32  No_Light    FC
  32    3   32   1a2000   id    N32  No_Light    FC
  33    3   33   1a2100   id    N32  No_Light    FC
  34    3   34   1a2200   id    N32  No_Light    FC
  35    3   35   1a2300   id    N32  No_Light    FC
  36    3   36   1a2400   id    N32  No_Light    FC
  37    3   37   1a2500   id    N32  No_Light    FC
  38    3   38   1a2600   id    N32  No_Light    FC
  39    3   39   1a2700   id    N32  No_Light    FC
  40    3   40   1a2800   id    N32  No_Light    FC
  41    3   41   1a2900   id    N32  No_Light    FC
  42    3   42   1a2a00   id    N32  No_Light    FC
  43    3   43   1a2b00   id    N32  No_Light    FC
  44    3   44   1a2c00   id    N32  No_Light    FC
  45    3   45   1a2d00   id    N32  No_Light    FC
  46    3   46   1a2e00   id    N32  No_Light    FC
  47    3   47   1a2f00   id    N32  No_Light    FC
  96    4    0   1a6000   id    N32  No_Light    FC
  97    4    1   1a6100   id    N32  No_Light    FC
  98    4    2   1a6200   id    N32  No_Light    FC
  99    4    3   1a6300   id    N32  No_Light    FC
 100    4    4   1a6400   id    N32  No_Light    FC
 101    4    5   1a6500   id    N32  No_Light    FC
 102    4    6   1a6600   id    N32  No_Light    FC
 103    4    7   1a6700   id    N32  No_Light    FC
 104    4    8   1a6800   id    N32  No_Light    FC
 105    4    9   1a6900   id    N32  No_Light    FC
 106    4   10   1a6a00   id    N32  No_Light    FC
 107    4   11   1a6b00   id    N32  No_Light    FC
 108    4   12   1a6c00   id    N32  No_Light    FC
 109    4   13   1a6d00   id    N32  No_Light    FC
 110    4   14   1a6e00   id    N32  No_Light    FC
 111    4   15   1a6f00   id    N32  No_Light    FC
 112    4   16   1a7000   id    N32  No_Light    FC
 113    4   17   1a7100   id    N32  No_Light    FC
 114    4   18   1a7200   id    N32  No_Light    FC
 115    4   19   1a7300   id    N32  No_Light    FC
 116    4   20   1a7400   id    N32  No_Light    FC
 117    4   21   1a7500   id    N32  No_Light    FC
 118    4   22   1a7600   id    N32  No_Light    FC
 119    4   23   1a7700   id    N32  No_Light    FC
 120    4   24   1a7800   id    N32  No_Light    FC
 121    4   25   1a7900   id    N32  No_Light    FC
 122    4   26   1a7a00   id    N32  No_Light    FC
 123    4   27   1a7b00   id    N32  No_Light    FC
 124    4   28   1a7c00   id    N32  No_Light    FC
 125    4   29   1a7d00   id    N32  No_Light    FC
 126    4   30   1a7e00   id    N32  No_Light    FC
 127    4   31   1a7f00   id    N32  No_Light    FC
 128    4   32   1a8000   id    N32  No_Light    FC
 129    4   33   1a8100   id    N32  No_Light    FC
 130    4   34   1a8200   id    N32  No_Light    FC
 131    4   35   1a8300   id    N32  No_Light    FC
 132    4   36   1a8400   id    N32  No_Light    FC
 133    4   37   1a8500   id    N32  No_Light    FC
 134    4   38   1a8600   id    N32  No_Light    FC
 135    4   39   1a8700   id    N32  No_Light    FC
 136    4   40   1a8800   id    N32  No_Light    FC
 137    4   41   1a8900   id    N32  No_Light    FC
 138    4   42   1a8a00   id    N32  No_Light    FC
 139    4   43   1a8b00   id    N32  No_Light    FC
 140    4   44   1a8c00   id    N32  No_Light    FC
 141    4   45   1a8d00   id    N32  No_Light    FC
 142    4   46   1a8e00   id    N32  No_Light    FC
 143    4   47   1a8f00   id    N32  No_Light    FC
 768    7    0   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 769    7    1   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 770    7    2   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 771    7    3   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 772    7    4   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 773    7    5   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 774    7    6   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 775    7    7   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 776    7    8   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 777    7    9   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 778    7   10   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 779    7   11   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 780    7   12   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 781    7   13   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 782    7   14   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 783    7   15   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 784    7   16   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 785    7   17   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 786    7   18   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 787    7   19   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 788    7   20   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 789    7   21   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 790    7   22   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 791    7   23   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 792    7   24   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 793    7   25   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 794    7   26   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 795    7   27   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 796    7   28   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 797    7   29   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 798    7   30   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 799    7   31   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 800    7   32   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 801    7   33   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 802    7   34   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 803    7   35   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 804    7   36   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 805    7   37   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 806    7   38   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 807    7   39   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 808    7   40   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 809    7   41   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 810    7   42   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 811    7   43   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 812    7   44   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 813    7   45   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 814    7   46   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 815    7   47   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 816    7   48   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 817    7   49   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 818    7   50   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 819    7   51   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 820    7   52   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 821    7   53   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 822    7   54   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 823    7   55   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 824    7   56   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 825    7   57   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 826    7   58   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 827    7   59   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 828    7   60   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 829    7   61   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 830    7   62   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 831    7   63   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 832    8    0   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 833    8    1   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 834    8    2   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 835    8    3   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 836    8    4   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 837    8    5   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 838    8    6   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 839    8    7   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 840    8    8   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 841    8    9   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 842    8   10   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 843    8   11   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 844    8   12   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 845    8   13   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 846    8   14   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 847    8   15   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 848    8   16   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 849    8   17   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 850    8   18   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 851    8   19   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 852    8   20   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 853    8   21   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 854    8   22   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 855    8   23   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 856    8   24   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 857    8   25   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 858    8   26   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 859    8   27   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 860    8   28   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 861    8   29   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 862    8   30   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 863    8   31   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 864    8   32   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 865    8   33   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 866    8   34   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 867    8   35   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 868    8   36   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 869    8   37   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 870    8   38   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 871    8   39   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 872    8   40   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 873    8   41   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 874    8   42   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 875    8   43   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 876    8   44   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 877    8   45   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 878    8   46   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 879    8   47   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 880    8   48   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 881    8   49   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 882    8   50   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 883    8   51   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 884    8   52   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 885    8   53   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 886    8   54   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 887    8   55   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 888    8   56   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 889    8   57   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 890    8   58   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 891    8   59   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 892    8   60   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 893    8   61   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 894    8   62   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 895    8   63   ------   --    53G  No_Module   FC  Disabled (No ICL License)
 384    9    0   1a8040   id    N32  No_Light    FC
 385    9    1   1a8140   id    N32  No_Light    FC
 386    9    2   1a8240   id    N32  No_Light    FC
 387    9    3   1a8340   id    N32  No_Light    FC
 388    9    4   1a8440   id    N32  No_Light    FC
 389    9    5   1a8540   id    N32  No_Light    FC
 390    9    6   1a8640   id    N32  No_Light    FC
 391    9    7   1a8740   id    N32  No_Light    FC
 392    9    8   1a8840   id    N32  No_Light    FC
 393    9    9   1a8940   id    N32  No_Light    FC
 394    9   10   1a8a40   id    N32  No_Light    FC
 395    9   11   1a8b40   id    N32  No_Light    FC
 396    9   12   1a8c40   id    N32  No_Light    FC
 397    9   13   1a8d40   id    N32  No_Light    FC
 398    9   14   1a8e40   id    N32  No_Light    FC
 399    9   15   1a8f40   id    N32  No_Light    FC
 400    9   16   1a9040   --    --   Online      VE  VE-Port  10:00:d8:1f:cc:76:c9:c0 "REPISGEA_DEF" (downstream)
 401    9   17   1a9140   --    --   Offline     VE
 402    9   18   1a9240   --    --   Offline     VE
 403    9   19   1a9340   --    --   Offline     VE
 404    9   20   1a9440   --    --   Offline     VE
 405    9   21   1a9540   --    --   Offline     VE  Disabled (10VE Mode)
 406    9   22   1a9640   --    --   Offline     VE  Disabled (10VE Mode)
 407    9   23   1a9740   --    --   Offline     VE  Disabled (10VE Mode)
 408    9   24   1a9840   --    --   Offline     VE  Disabled (10VE Mode)
 409    9   25   1a9940   --    --   Offline     VE  Disabled (10VE Mode)
 410    9   26   1a9a40   --    --   Offline     VE
 411    9   27   1a9b40   --    --   Offline     VE
 412    9   28   1a9c40   --    --   Offline     VE
 413    9   29   1a9d40   --    --   Offline     VE
 414    9   30   1a9e40   --    --   Offline     VE
 415    9   31   1a9f40   --    --   Offline     VE  Disabled (10VE Mode)
 416    9   32   1aa040   --    --   Offline     VE  Disabled (10VE Mode)
 417    9   33   1aa140   --    --   Offline     VE  Disabled (10VE Mode)
 418    9   34   1aa240   --    --   Offline     VE  Disabled (10VE Mode)
 419    9   35   1aa340   --    --   Offline     VE  Disabled (10VE Mode)
        9  ge0            --    40G    No_Module   FCIP
        9  ge1            --    40G    No_Module   FCIP
        9  ge2            id    10G    Online      FCIP
        9  ge3            --    10G    No_Module   FCIP
        9  ge4            --    10G    No_Module   FCIP
        9  ge5            --    10G    No_Module   FCIP
        9  ge6            --    10G    No_Module   FCIP
        9  ge7            --    10G    No_Module   FCIP
        9  ge8            --    10G    No_Module   FCIP
        9  ge9            --    10G    No_Module   FCIP
        9  ge10           id    10G    Online      FCIP
        9  ge11           --    10G    No_Module   FCIP
        9  ge12           --    10G    No_Module   FCIP
        9  ge13           --    10G    No_Module   FCIP
        9  ge14           --    10G    No_Module   FCIP
        9  ge15           --    10G    No_Module   FCIP
        9  ge16           --    10G    No_Module   FCIP
        9  ge17           --    10G    No_Module   FCIP
 480   10    0   1ae040   id    N32  No_Light    FC
 481   10    1   1ae140   id    N32  No_Light    FC
 482   10    2   1ae240   id    N32  No_Light    FC
 483   10    3   1ae340   id    N32  No_Light    FC
 484   10    4   1ae440   id    N32  No_Light    FC
 485   10    5   1ae540   id    N32  No_Light    FC
 486   10    6   1ae640   id    N32  No_Light    FC
 487   10    7   1ae740   id    N32  No_Light    FC
 488   10    8   1ae840   id    N32  No_Light    FC
 489   10    9   1ae940   id    N32  No_Light    FC
 490   10   10   1aea40   id    N32  No_Light    FC
 491   10   11   1aeb40   id    N32  No_Light    FC
 492   10   12   1aec40   id    N32  No_Light    FC
 493   10   13   1aed40   id    N32  No_Light    FC
 494   10   14   1aee40   id    N32  No_Light    FC
 495   10   15   1aef40   id    N32  No_Light    FC
 496   10   16   1af040   --    --   Online      VE  VE-Port  10:00:d8:1f:cc:76:c9:c0 "REPISGEA_DEF"
 497   10   17   1af140   --    --   Offline     VE
 498   10   18   1af240   --    --   Offline     VE
 499   10   19   1af340   --    --   Offline     VE
 500   10   20   1af440   --    --   Offline     VE
 501   10   21   1af540   --    --   Offline     VE  Disabled (10VE Mode)
 502   10   22   1af640   --    --   Offline     VE  Disabled (10VE Mode)
 503   10   23   1af740   --    --   Offline     VE  Disabled (10VE Mode)
 504   10   24   1af840   --    --   Offline     VE  Disabled (10VE Mode)
 505   10   25   1af940   --    --   Offline     VE  Disabled (10VE Mode)
 506   10   26   1afa40   --    --   Offline     VE
 507   10   27   1afb40   --    --   Offline     VE
 508   10   28   1afc40   --    --   Offline     VE
 509   10   29   1afd40   --    --   Offline     VE
 510   10   30   1afe40   --    --   Offline     VE
 511   10   31   1aff40   --    --   Offline     VE  Disabled (10VE Mode)
 512   10   32   1a0080   --    --   Offline     VE  Disabled (10VE Mode)
 513   10   33   1a0180   --    --   Offline     VE  Disabled (10VE Mode)
 514   10   34   1a0280   --    --   Offline     VE  Disabled (10VE Mode)
 515   10   35   1a0380   --    --   Offline     VE  Disabled (10VE Mode)
       10  ge0            --    40G    No_Module   FCIP
       10  ge1            --    40G    No_Module   FCIP
       10  ge2            id    10G    Online      FCIP
       10  ge3            --    10G    No_Module   FCIP
       10  ge4            --    10G    No_Module   FCIP
       10  ge5            --    10G    No_Module   FCIP
       10  ge6            --    10G    No_Module   FCIP
       10  ge7            --    10G    No_Module   FCIP
       10  ge8            --    10G    No_Module   FCIP
       10  ge9            --    10G    No_Module   FCIP
       10  ge10           id    10G    Online      FCIP
       10  ge11           --    10G    No_Module   FCIP
       10  ge12           --    10G    No_Module   FCIP
       10  ge13           --    10G    No_Module   FCIP
       10  ge14           --    10G    No_Module   FCIP
       10  ge15           --    10G    No_Module   FCIP
       10  ge16           --    10G    No_Module   FCIP
       10  ge17           --    10G    No_Module   FCIP
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> timed out waiting for input: auto-logout
Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.20 13:37:11 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fciptunnel all -c --lifetime

 Tunnel Circuit  OpStatus  Flags    Uptime  TxMBps  RxMBps ConnCnt CommRt Met/G
--------------------------------------------------------------------------------
 9/16  -         Up      --i----a-   16d21h    0.00    0.00   1      -       -
 9/16  0 9/ge2   Up      ---vahpi4   16d21h    0.00    0.00   1  2000/5000  0/-
 9/16  1 9/ge10  Up      ---vahpi4   16d21h    0.00    0.00   1  2000/5000  0/-
 10/16 -         Up      --i----a-  3d1h25m    0.00    0.00   7      -       -
 10/16 0 10/ge2  Up      ---vahpi4  3d1h25m    0.00    0.00   7  2000/5000  0/-
 10/16 1 10/ge10 Up      ---vahpi4  3d1h25m    0.00    0.00   7  2000/5000  0/-
--------------------------------------------------------------------------------
 Flags (tunnel): l=Legacy QOS Mode
                 i=IPSec f=Fastwrite T=TapePipelining F=FICON r=ReservedBW
                 a=FastDeflate d=Deflate D=AggrDeflate P=Protocol
                 I=IP-Ext
      (circuit): h=HA-Configured v=VLAN-Tagged p=PMTU i=IPSec 4=IPv4 6=IPv6
                 ARL a=Auto r=Reset s=StepDown t=TimedStepDown  S=SLA

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fciptunnel 10/16 -d0/16 -d/16 -d9/16 -d

 Tunnel: VE-Port:9/16 (idx:0, DP0)
 ====================================================
  Oper State           : Online
  TID                  : 400
  Flags                : 0x00000000
  IP-Extension         : Disabled
  Compression          : Fast Deflate
  QoS BW Ratio         : 50% / 30% / 20%
  Fastwrite            : Disabled
  Tape Pipelining      : Disabled
  IPSec                : Enabled
  IPSec-Policy         : morgan_ipsec1
  Legacy QOS Mode      : Disabled
  Load-Level (Cfg/Peer): Spillover (Spillover / Spillover)
  Local WWN            : 10:00:d8:1f:cc:71:62:00
  Peer WWN             : 10:00:d8:1f:cc:76:c9:c0
  RemWWN (config)      : 00:00:00:00:00:00:00:00
  Peer Platform        : SX6
  cfgmask              : 0x0000001f 0x4000420c
  Uncomp/Comp Bytes    : 0 / 0 / 1.00 : 1
  Uncomp/Comp Byte(30s): 0 / 0 / 1.00 : 1
  Flow Status          : 0
  ConCount/Duration    : 1 / 15d15h
  Uptime               : 16d21h
  Stats Duration       : 15d15h
  Receiver Stats       : 85587276 bytes / 355579 pkts /  129.00 Bps Avg
  Sender Stats         : 89164240 bytes / 355579 pkts /  125.00 Bps Avg
  TCP Bytes In/Out     : 40863191424 / 50504280372
  ReTx/OOO/SloSt/DupAck: 322 / 2200 / 310 / 0
  RTT (min/avg/max)    : 5 / 6 / 54 ms
  Wan Util             : 0.0%
  TxQ Util             : 0.0%

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portshow fciptunnel 9/16 -d/16 -d1/16 -d0/16 -d

 Tunnel: VE-Port:10/16 (idx:0, DP0)
 ====================================================
  Oper State           : Online
  TID                  : 496
  Flags                : 0x00000000
  IP-Extension         : Disabled
  Compression          : Fast Deflate
  QoS BW Ratio         : 50% / 30% / 20%
  Fastwrite            : Disabled
  Tape Pipelining      : Disabled
  IPSec                : Enabled
  IPSec-Policy         : morgan_ipsec1
  Legacy QOS Mode      : Disabled
  Load-Level (Cfg/Peer): Spillover (Spillover / Spillover)
  Local WWN            : 10:00:d8:1f:cc:71:62:00
  Peer WWN             : 10:00:d8:1f:cc:76:c9:c0
  RemWWN (config)      : 00:00:00:00:00:00:00:00
  Peer Platform        : SX6
  cfgmask              : 0x0000001f 0x4000420c
  Uncomp/Comp Bytes    : 0 / 0 / 1.00 : 1
  Uncomp/Comp Byte(30s): 0 / 0 / 1.00 : 1
  Flow Status          : 0
  ConCount/Duration    : 2 / 15d15h
  Uptime               : 3d1h41m
  Stats Duration       : 3d1h41m
  Receiver Stats       : 3290876 bytes / 26533 pkts /   11.00 Bps Avg
  Sender Stats         : 3291580 bytes / 26534 pkts /   13.00 Bps Avg
  TCP Bytes In/Out     : 8300230828 / 10290663116
  ReTx/OOO/SloSt/DupAck: 185 / 2241 / 213 / 0
  RTT (min/avg/max)    : 5 / 5 / 46 ms
  Wan Util             : 0.0%
  TxQ Util             : 0.0%

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
logout:Closing the current session
=~=~=~=~=~=~=~=~=~=~=~= PuTTY log 2023.04.20 14:43:50 =~=~=~=~=~=~=~=~=~=~=~=
login as: marvin.parker@morganstanley.com
marvin.parker@morganstanley.com@10.203.54.76's password:
--------------------------------------------------------------------------------------------
                                       ATTENTION
  It is recommended that you change the default passwords for all the switch accounts.
 Refer to the product release notes and administrators guide if you need further information.
 --------------------------------------------------------------------------------------------

-----------------------------------------------------------------
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com>
REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgfec --show 3/0-473/0-471/0-47/0-47  31
Error: Invalid slot 1, port 0

Usage:   portCfgFec [Mode] [Options]     [Slot/]Port[-Range]
         portCfgFec [Mode] [-FEC] [-TTS] [Slot/]Port[-Range]
Mode:    --enable       - Enable  the FEC & FEC via TTS feature on 10G/16G ports
         --disable      - Disable the FEC & FEC via TTS feature on 10G/16G ports
         --show         - Show configuration for FEC port
         --help         - Help command to see portCfgFec Usage
Options:
         -FEC           - Enable / Disable the FEC feature on 10G/16G ports
         -TTS           - Enable / Disable the FEC via TTS feature on 10G/16G ports
         -force(or)-f   - Enable the FEC via TTS feature on 10G/16G ports without confirmation

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgfec --show 3/0-47
Port: 0
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 1
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 2
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 3
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 4
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 5
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 6
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 7
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 8
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 9
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 10
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 11
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 12
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 13
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 14
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 15
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 16
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 17
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 18
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 19
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 20
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 21
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 22
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 23
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 24
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 25
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 26
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 27
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 28
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 29
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 30
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 31
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 32
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 33
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 34
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 35
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 36
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 37
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 38
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 39
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 40
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 41
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 42
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 43
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 44
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 45
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 46
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 47
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> portcfgfec --show 3/0-473/0-474/0-47
Port: 96
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 97
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 98
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 99
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 100
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 101
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 102
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 103
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 104
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 105
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 106
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 107
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 108
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 109
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 110
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 111
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 112
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 113
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 114
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 115
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 116
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 117
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 118
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 119
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 120
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 121
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 122
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 123
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 124
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 125
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 126
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 127
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 128
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 129
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 130
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 131
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 132
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 133
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 134
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 135
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 136
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 137
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 138
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 139
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 140
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 141
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 142
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

Port: 143
FEC Capable: YES
10G/16G FEC Configured: OFF
16G FEC via TTS Configured: OFF
FEC State: Inactive

REPISG1A_DEF:FID128:marvin.parker@morganstanley.com> exit
logout:Closing the current session


Version Control::

    +-----------+---------------+-----------------------------------------------------------------------------------+
    | Version   | Last Edit     | Description                                                                       |
    +===========+===============+===================================================================================+
    | 1.0.0     | xx xxx 2022   | Initial Launch                                                                    |
    +-----------+---------------+-----------------------------------------------------------------------------------+
"""

__author__ = 'Jack Consoli'
__copyright__ = 'Copyright 2025 Jack Consoli'
__date__ = 'xx xxx 2022'
__license__ = 'Apache License, Version 2.0'
__email__ = 'jack_consoli@yahoo.com'

__maintainer__ = 'Jack Consoli'
__status__ = 'Development'
__version__ = '1.0.0'

import datetime
import brcdapi.log as brcdapi_log
import brcdapi.file as brcdapi_file
import brcddb.brcddb_project as brcddb_project
import brcddb.util.parse_cli as parse_cli
import brcddb.util.copy as brcddb_copy

def pseudo_main():
    """Basically the main(). Did it this way so it can easily be used as a standalone module or called from another.

    :return: Exit code. See exist codes in brcddb.brcddb_common
    :rtype: int
    """

    outf = 'test/switchshow.json'

    content_l = brcdapi_file.read_file('test/switchshow.txt', remove_blank=False, rc=False)
    proj_obj = brcddb_project.new("Captured_data", datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
    switch_obj, x = parse_cli.switchshow(proj_obj, content_l)

    brcdapi_log.log('Saving project to: ' + outf, echo=True)
    plain_copy = dict()
    brcddb_copy.brcddb_to_plain_copy(proj_obj, plain_copy)
    brcdapi_file.write_dump(plain_copy, outf)
    brcdapi_log.log('Save complete', echo=True)

    copy_proj_obj = brcddb_project.read_from(outf)
    print(str(type(copy_proj_obj)))

    return proj_obj.r_exit_code()


###################################################################
#
#                    Main Entry Point
#
###################################################################
_ec = pseudo_main()
brcdapi_log.close_log('\nProcessing Complete. Exit code: ' + str(_ec), echo=True)
exit(_ec)
