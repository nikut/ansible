#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
VMWARE external inventory script
=================================

shamelessly copied from existing inventory scripts.

This script and it's ini can be used more than once,

i.e vmware.py/vmware_colo.ini vmware_idf.py/vmware_idf.ini
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

try:
    import json
except ImportError:
    import simplejson as json


def get_host_info(host):
    ''' Get variables about a specific host '''
    hostinfo = {
                'vmware_name' : host.name,
                'vmware_tag' : host.tag,
                'vmware_parent': host.parent.name,
               }
    for k in host.capability.__dict__.keys():
        if k.startswith('_'):
           continue
        try:
            hostinfo['vmware_' + k] = str(host.capability[k])
        except:
           continue

    return hostinfo


def get_inventory(client, config):
    ''' Reads the inventory from vmware api '''

    inv= { 'all': [], '_meta': { 'hostvars': {} } }
    default_group = os.path.basename(sys.argv[0]).rstrip('.py')

    if config.has_option('defaults', 'guests_only'):
        guests_only = config.get('defaults', 'guests_only')
    else:
        guests_only = True

    if not guests_only:
        if config.has_option('defaults','hw_group'):
            hw_group = config.get('defaults','hw_group')
        else:
            hw_group = default_group + '_hw'
        inv[hw_group] = []

    if config.has_option('defaults','vm_group'):
        vm_group = config.get('defaults','vm_group')
    else:
        vm_group = default_group + '_vm'
    inv[vm_group] = []

    # Loop through physical hosts:
    hosts = HostSystem.all(client)
    for host in hosts:
        if not guests_only:
            inv['all'].append(host.name)
            inv[hw_group].append(host.name)
            if host.tag:
                taggroup = 'vmware_' + host.tag
                if taggroup in inv:
                    inv[taggroup].append(host.name)
                else:
                    inv[taggroup] = [ host.name ]

            inv['_meta']['hostvars'][host.name] = get_host_info(host)

        for vm in host.vm:
            inv['all'].append(vm.name)
            inv[vm_group].append(vm.name)
            if vm.tag:
                for tag in vm.tag:
                    taggroup = 'vmware_' + repr(tag)
                    if taggroup in inv:
                        inv[taggroup].append(vm.name)
                    else:
                        inv[taggroup] = [ vm.name ]

            inv['_meta']['hostvars'][vm.name] = get_host_info(host)
    return json.dumps(inv)


if __name__ == '__main__':
    inventory = {}

    # Command line argument processing
    parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on vmware')
    parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
    parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
    args = parser.parse_args()

    # Read config
    config = ConfigParser.SafeConfigParser()
    for configfilename in [os.path.abspath(sys.argv[0]).rstrip('.py') + '.ini', 'vmware.ini']:
        if os.path.exists(configfilename):
            config.read(configfilename)
            break
    try:
        client =  Client( config.get('auth','host'),
                          config.get('auth','user'),
                          config.get('auth','password'),
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
