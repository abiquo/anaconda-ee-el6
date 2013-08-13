/*
 * net.h
 *
 * Copyright (C) 2007  Red Hat, Inc.  All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef H_LOADER_NET
#define H_LOADER_NET

#include <newt.h>
#include "../isys/iface.h"
#include "loader.h"

#define DHCP_METHOD_STR   _("Dynamic IP configuration (DHCP)")
#define MANUAL_METHOD_STR _("Manual configuration")
#ifdef ENABLE_IPV6
#define DHCPV6_METHOD_STR _("Automatic, DHCP only")
#define AUTO_METHOD_STR   _("Automatic")
#endif

#define SYSCONFIG_PATH       "/etc/sysconfig"
#define NETWORK_SCRIPTS_PATH "/etc/sysconfig/network-scripts"

#define NM_DHCP_TIMEOUT 45

struct intfconfig_s {
    newtComponent ipv4Entry, cidr4Entry;
    newtComponent gwEntry, nsEntry;
    const char *ipv4, *cidr4;
#ifdef ENABLE_IPV6
    newtComponent ipv6Entry, cidr6Entry;
    const char *ipv6, *cidr6;
    const char *gw6;
#endif
    const char *gw, *ns;
};

struct netconfopts {
    char ipv4Choice;
    int v4Method;
#ifdef ENABLE_IPV6
    char ipv6Choice;
    int v6Method;
#endif
};

typedef int int32;

int readNetConfig(char * device, iface_t * iface,
                  char * dhcpclass, int methodNum);
int configureTCPIP(char * device, iface_t * iface, struct netconfopts * opts,
                   int methodNum);
int manualNetConfig(char * device, iface_t * iface,
                    struct intfconfig_s * ipcomps, struct netconfopts * opts);
void debugNetworkInfo(iface_t * iface);
int writeDisabledNetInfo(void);
int writeDisabledIfcfgFile(char *device);
int removeDhclientConfFile(char *device);
int removeIfcfgFile(char *device);
int writeEnabledNetInfo(iface_t * iface);
int chooseNetworkInterface(struct loaderData_s * loaderData);
void setupIfaceStruct(iface_t * iface, struct loaderData_s * loaderData);
int setupWireless(iface_t * iface);
void setKickstartNetwork(struct loaderData_s * loaderData, int argc, 
                         char ** argv);
int kickstartNetworkUp(struct loaderData_s * loaderData,
                       iface_t * iface);
int activateDevice(struct loaderData_s * loaderData,
                       iface_t * iface);
int disconnectDevice(char *device);
void splitHostname (char *str, char **host, char **port);
int wait_for_iface_activation(char * ifname, int timeout);
int wait_for_iface_disconnection(char *ifname);
int isURLRemote(char *url);
int split_ipv6addr_prefix_length(char *str, char **address, char **prefix);
int enable_NM_BOND_VLAN(void);
int split_bond_option(char *str, char **bondname, char **bondslaves, char **options);
int networkDeviceExists(char *name);
int writeBondSlaveIfcfgFile(char *slave, char *master);
void parseDnsServers(const char *dnss, iface_t *iface);
#endif
