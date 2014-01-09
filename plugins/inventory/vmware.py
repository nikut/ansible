#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
VSPHERE external inventory script
=================================

shamelessly copied from existing inventory scripts.

This script and it's ini can be used more than once,

i.e vsphere_colo.py/vsphere_colo.ini vsphere_idf.py/vsphere_idf.ini
(script can be link)

so if you don't have clustered vcenter  but multiple esx machines or
just diff clusters you can have a inventory  per each and automatically
group hosts based on file name or specify a group in the ini.
'''

import os
import sys
import argparse
import ConfigParser
from psphere.client import Client
from psphere.managedobjects import HostSystem
from psphere.managedobjects import VirtualMachine

try:
    import json
except ImportError:
    import simplejson as json


def get_host_info(client, config, hostname):
    ''' Get variables about a specific host '''

    # todo get host and api
    return json_format_dict(instance_vars, True)


def get_inventory(client, config):
    ''' Reads the inventory from vsphere api '''

    inv= { 'all': [], '_meta': { 'hostvars': {} } }
    default_group = os.path.basename(sys.argv[0]).rstrip('.py')
    if config.has_option('vsphere','hw_group'):
        hw_group = config.get('vsphere','hw_group')
    else:
        hw_group = default_group + '_hw'
    inv[hw_group] = []

    if config.has_option('vsphere','vm_group'):
        vm_group = config.get('vsphere','vm_group')
    else:
        vm_group = default_group + '_vm'
    inv[vm_group] = []

    # Loop through physical hosts:
    hosts = HostSystem.all(client)
    for host in hosts:
        inv['all'].append(host.name)
        inv[hw_group].append(host.name)
        if host.tag:
            taggroup = 'vsphere_' + host.tag
            if taggroup in inv:
                inv[taggroup].append(host.name)
            else:
                inv[taggroup] = [ host.name ]

        inv['_meta']['hostvars'][host.name] = { 'vsphere_name': host.name,
                                                'vsphere_hostname': 'N/A',
                                                'vsphere_ip': 'good_question',
                                              }

        for vm in host.vm:
            inv['all'].append(vm.name)
            inv[vm_group].append(vm.name)
            if vm.tag:
                taggroup = 'vsphere_' + vm.tag
                if taggroup in inv:
                    inv[taggroup].append(vm.name)
                else:
                    inv[taggroup] = [ vm.name ]

            inv['_meta']['hostvars'][vm.name] = { 'vsphere_name' : vm.name,
                       #                           'vsphere_hostname': vm.guest.hostName,
                       #                           'vsphere_ip'   : vm.guest.ipAddress,
                       #                           'vsphere_cpus'   : vm.hardware.numCPU,
                       #                           'vsphere_ram'   : vm.hardware.memoryMB,
                                                }
    return json_format_dict(inv)

def json_format_dict(data, pretty=False):
    ''' Converts a dict to a JSON object and dumps it as a formatted string '''
    if pretty:
        return json.dumps(data, sort_keys=True, indent=2)
    else:

        return json.dumps(data)


if __name__ == '__main__':
    inventory = {}

    # Command line argument processing
    parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on vsphere')
    parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
    parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
    args = parser.parse_args()

    # Read config
    config = ConfigParser.SafeConfigParser()
    for configfilename in [os.path.abspath(sys.argv[0]).rstrip('.py') + '.ini', 'vsphere.ini']:
        if os.path.exists(configfilename):
            config.read(configfilename)
            break
    try:
        client =  Client( config.get('vsphere','host'),
                          config.get('vsphere','user'),
                          config.get('vsphere','password'),
                        )
    except Exception, e:
        print "Unable to login: ", str(e)
        exit(1)

    # acitually do the work
    if args.list:
        inventory = get_inventory(client, config)
    elif args.hostname:
        inventory = get_host_info(client, config, args.hostname)

    # return to ansible
    print inventory
