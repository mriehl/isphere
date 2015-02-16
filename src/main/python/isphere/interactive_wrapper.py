#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

"""
This module overlays the pyVmomi library to make its use in a
python shell or short program more enjoyable.
Starting point is instantiating a vCenter Host (VVC) in order
to get all VMs.
"""

import atexit
from getpass import getpass

from pyVim import connect
from pyVmomi import vim, vmodl

__all__ = ["NotFound", "VVC", "ESX", "VM", "DVS"]


class NotFound(Exception):

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
            password = getpass("Password for {0}@{1}: ".format(username, self.hostname))
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
        """
        Returns a dictionary that maps custom field keys to custom field names.
        """
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

    def get_vm_by_uuid(self, uuid):
        """
        Returns a VM by searching for its UUID.
        An exception will be raised if the VM cannot be found.

        - `uuid` (str) is the UUID of the desired VM.
        """
        vm = self.get_service("searchIndex").FindByUuid(uuid=uuid, vmSearch=True)
        if not vm:
            raise NotFound("VM with uuid {0} not found".format(uuid))
        return VM(vm)

    def get_all_vms(self):
        """
        Returns a generator for all virtual machines on this vCenter.
        """
        for vm in self.get_all_by_type([vim.VirtualMachine]):
            yield VM(vm)

    def get_all_by_type(self, types):
        """
        Returns a list of all matching item types.

        - `types` (type[]) is a list of desired types. The types should be
          attributes of the `pyVmomi.vim` module, for example `pyVmomi.vim.VirtualMachine`
        """
        view = self.view_for(types)
        all_items = view.view
        view.Destroy()
        return all_items

    def get_all_esx(self):
        """
        Returns a generator for all ESXi host systems on this vCenter.
        """
        for esx in self.get_all_by_type([vim.HostSystem]):
            yield ESX(esx)

    def get_all_dvs(self):
        """
        Returns a generator for all distributed virtual switches on this vCenter.
        """
        for dvs in self.get_all_by_type([vim.VmwareDistributedVirtualSwitch]):
            yield DVS(dvs)

    def view_for(self, types):
        return self.get_service("viewManager").CreateContainerView(
            self.service_instance_content.rootFolder,
            types,
            True)

    def get_restricted_view_on_vms(self, properties):
        """
        Returns a list of all virtual machines.
        The VMs will only have the specified properties but retrieval will be
        insanely fast. The properties must exist on the `pyVmomi.vim.VirtualMachine`
        object, of course.

        - `properties` (str[]) is a list of desired properties.
          For example using `properties=["name", "runtime.host"]` will return
          objects that have only the attributes `name` and `runtime.host`.
        """
        return self.get_restricted_view_on_items(properties, [vim.VirtualMachine])

    def get_restricted_view_on_host_systems(self, properties):
        """
        Returns a list of all ESXi host systems.
        The ESXis will only have the specified properties but retrieval will be
        insanely fast. The properties must exist on the `pyVmomi.vim.HostSystem`
        object, of course.

        - `properties` (str[]) is a list of desired properties.
          For example using `properties=["name", "hardware.memorySize"]` will return
          objects that have only the attributes `name` and `hardware.memorySize`.
        """
        return self.get_restricted_view_on_items(properties, [vim.HostSystem])

    def get_restricted_view_on_items(self, properties, types):
        """
        Returns a restricted view on a specific item type collection.
        The items are restricted in the sense that only properties which were
        specified upon retrieval can be accessed.

        The return value will be a list of items that have the desired properties
        as attributes.
        Note that recursing properties (e.G. summary.config) will be stored under
        their full name (item.summary.config).

        - `properties` (str[]) is a list of properties that should be fetched.
          Recursing properties can be separated by dots, e.G. "summary.config".
        - `types` (type[]) is a list of types to restrict the items that are given
          back. The types must be attributes of the `pyVmomi.vim` module.
        """
        unrestricted_view = self.view_for(types)
        collector_spec = build_property_collector_specs(unrestricted_view, properties)

        retrieved_contents = self.get_service("propertyCollector").RetrieveContents(collector_spec)
        items = []
        for item in retrieved_contents:
            item_instance = ItemContainer()
            for item_property in item.propSet:
                if item_property.name in properties:
                    item_instance.set_path_value(item_property.name, item_property.val)
            items.append(item_instance)
        return items


class ItemContainer(object):

    def set_path_value(self, path, value):
        part_names = path.split(".")
        self._inner_set_path_value(part_names, value)

    def _inner_set_path_value(self, part_names, value, current_item=None):
        if not part_names:
            return
        current_item = self if not current_item else current_item
        current_part = part_names.pop(0)
        need_to_set_value = not part_names  # if part_names is empty we're done with the path and can set the value
        if need_to_set_value:
            setattr(current_item, current_part, value)
            return
        else:
            if not hasattr(current_item, current_part):
                part_container = ItemContainer()
                setattr(current_item, current_part, part_container)
            else:
                part_container = getattr(current_item, current_part)
            part_container._inner_set_path_value(part_names, value, part_container)


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

    def __dir__(self):
        return dir(self.raw_esx)

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


class DVS(object):

    """
    A DistributedVirtualSwitch
    """

    def __init__(self, raw_dvs):
        self.raw_dvs = raw_dvs
        self.name = raw_dvs.name

    def __eq__(self, other):
        return self.name == other.name

    def __dir__(self):
        return dir(self.raw_dvs)

    def __getattr__(self, attribute):
        return getattr(self.raw_dvs, attribute)


def get_all_vms_in_folder(folder):
    vm_or_folders = folder.childEntity
    for vm_or_folder in vm_or_folders:
        if hasattr(vm_or_folder, "childEntity"):
            # it's still a folder, look deeper
            for vm in get_all_vms_in_folder(vm_or_folder):
                yield vm  # it's now a VM
        else:
            yield VM(vm_or_folder)  # it's a VM


def build_property_collector_specs(view, item_properties):
    obj_spec = vmodl.query.PropertyCollector.ObjectSpec()
    obj_spec.obj = view
    obj_spec.skip = True

    traversal_spec = vmodl.query.PropertyCollector.TraversalSpec()
    traversal_spec.name = 'traverseEntities'
    traversal_spec.path = 'view'
    traversal_spec.skip = False
    traversal_spec.type = view.__class__
    obj_spec.selectSet = [traversal_spec]

    property_spec = vmodl.query.PropertyCollector.PropertySpec()
    property_spec.type = getattr(vim, view.type[0])
    property_spec.pathSet = item_properties

    filter_spec = vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = [obj_spec]
    filter_spec.propSet = [property_spec]
    return [filter_spec]
