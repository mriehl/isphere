#  Copyright (c) 2014 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

import atexit
from getpass import getpass

from pyVim import connect
from pyVmomi import vim

"""
This module overlays the pyVmomi library to make its use in a
python shell or short program more enjoyable.
Starting point is instantiating a vCenter Host (VVC) in order
to get all VMs.
"""


class NotFound(BaseException):

    """
    To be raised when a requested item was not found.
    """
    pass


class VVC(object):

    """
    A vCenter host.
    """

    def __init__(self, hostname):
        """
        Creates a VVC instance.

        - `hostname` (str) is the name of the vCenter host.
        """
        self.hostname = hostname
        self.service_instance = None
        self.service_instance_content = None

    def connect(self, username, password=None):
        """
        Connects to the vCenter host encapsulated by this VVC instance.

        - `username` (str) is the username to use for authentication.
        - `password` (str) is the password to use for authentication.
          If the password is not specified, a getpass prompt will be used.
        """
        if not password:
            password = getpass("Password for {0}: ".format(self.hostname))
        self.service_instance = connect.SmartConnect(host=self.hostname,
                                                     user=username,
                                                     pwd=password,
                                                     port=443)
        self.service_instance_content = self.service_instance.RetrieveContent()
        atexit.register(connect.Disconnect, self.service_instance)

    def get_first_level_of_vm_folders(self):
        children = self.service_instance_content.rootFolder.childEntity
        for child in children:
            if hasattr(child, "vmFolder"):
                yield child.vmFolder

    def get_service(self, service_name):
        if hasattr(self.service_instance_content, service_name):
            return getattr(self.service_instance_content, service_name)
        raise NotFound("Service {0} not found".format(service_name))

    def get_custom_attributes_mapping(self):
        custom_attributes_mapping = {}
        for field in self.get_service("customFieldsManager").field:
            custom_attributes_mapping[field.key] = field.name

        return custom_attributes_mapping

    def find_by_dns_name(self, dns_name, search_for_vms=False):
        """
        Returns an item by searching for its DNS name.
        An exception will be raised if the item cannot be found.

        - `dns_name` (str) is the DNS name of the desired item.
        - `search_for_vms` (boolean) (default False) indicates if VMs should
          be included in the search.
        """
        search_index = self.service_instance.RetrieveContent().searchIndex
        item = search_index.FindByDnsName(dnsName=dns_name, vmSearch=search_for_vms)
        if not item:
            raise NotFound(
                "Item with dns name {0} not found (search_for_vms: {1})".format(
                    dns_name,
                    search_for_vms))

        return item

    def get_all_vms(self):
        for vm in self.get_all_by_type([vim.VirtualMachine]):
            yield VM(vm)

    # FIXME @mriehl untested
    def get_all_by_type(self, types):
        view = self.get_service("viewManager").CreateContainerView(
            self.service_instance_content.rootFolder,
            types,
            True)
        all_items = view.view
        view.Destroy()
        return all_items

    def get_all_esx(self):
        for esx in self.get_all_by_type([vim.HostSystem]):
            yield ESX(esx)


class ESX(object):

    """
    An ESX instance.
    """

    def __init__(self, raw_esx):
        self.raw_esx = raw_esx
        self.name = raw_esx.name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return int("".join((str(ord(c)) for c in self.name)))

    def __getattr__(self, attribute):
        return getattr(self.raw_esx, attribute)

    def get_number_of_cores(self):
        """
        Returns the number of CPU cores (type long) on this ESX.
        """
        resources_on_esx = self.raw_esx.licensableResource.resource
        for resource in resources_on_esx:
            if resource.key == "numCpuCores":
                return resource.value
        message = "{0} has no resource numCpuCores.\n Available resources: {1}"
        raise RuntimeError(message.format(self.name, resources_on_esx))


class VM(object):

    """
    A virtual machine.
    """

    def __init__(self, raw_vm):
        self.raw_vm = raw_vm
        self.name = raw_vm.name

    def __getattr__(self, attribute):
        return getattr(self.raw_vm, attribute)

    def __dir__(self):
        return dir(self.raw_vm)

    def get_first_network_interface_matching(self, predicate):
        """
        Returns the first network interface of this VM that matches the given
        predicate.

        - `predicate` (callable) is a function that takes a network and returns
          True (return this network) or False (skip this network).
        """
        for network in self.raw_vm.network:
            if predicate(network):
                return network
        return None

    def get_esx_host(self):
        return ESX(self.raw_vm.runtime.host)


def get_all_vms_in_folder(folder):
    vm_or_folders = folder.childEntity
    for vm_or_folder in vm_or_folders:
        if hasattr(vm_or_folder, "childEntity"):
            # it's still a folder, look deeper
            for vm in get_all_vms_in_folder(vm_or_folder):
                yield vm  # it's now a VM
        else:
            yield VM(vm_or_folder)  # it's a VM
