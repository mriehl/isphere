#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

"""
Provides caching VMWare vSphere connection abstractions.
The `isphere.connection.AutoEstablishingConnection` is a connection that is
automatically established when used.

The `isphere.connection.CachingVSphere` encapsulates a
`isphere.connection.AutoEstablishingConnection` and provides caching capabilities
on top.
The cache is filled with names and UUIDs when possible, so it is a very lightweight
operation. Once the items that need to be actually retrieved have been determined,
the `retrieve_vm` and similar methods will allow retrieval of the item based on
its name.


Usage:

```
>>> from isphere.connection import CachingVSphere
>>> vsphere_cache = CachingVSphere()
>>> vsphere_cache.fill()
>>> all_vms = vsphere_cache.list_cached_vms()
>>> all_vms[0]
'some-vm-name'
>>> actual_vm = vsphere_cache.retrieve_vm(all_vms[0])
```

"""

from functools import wraps

from isphere.interactive_wrapper import VVC
from isphere.input import killable_input
import thirdparty.tasks as thirdparty_tasks

try:
    import requests
    requests.packages.urllib3.disable_warnings()
except ImportError:
    pass
except AttributeError:
    pass

__all__ = ["memoized", "CachingVSphere", "AutoEstablishingConnection"]


def memoized(function):
    """
    Memoizes a function.
    Calls will be cached based on the args/kwargs. The cache is public
    (`func.cached_calls`) so it can be cleared or used from the outside.
    """
    cached_calls = function.cached_calls = {}

    @wraps(function)
    def function_with_memoized_calls(*args, **kwargs):
        cache_id_for_this_call = str(args) + str(kwargs)
        if cache_id_for_this_call not in cached_calls:
            call_result = function(*args, **kwargs)
            cached_calls[cache_id_for_this_call] = call_result
        return cached_calls[cache_id_for_this_call]
    return function_with_memoized_calls


class CachingVSphere(object):

    """
    Encapsulates a `isphere.connection.AutoEstablishingConnection` and provides
    a caching layer on top.
    """

    def __init__(self, hostname=None, username=None, password=None):
        """
        Create a new caching vSphere connection.

        - hostname (type `str`) is the vCenter host name. Can be `None` and will
          result in a prompt.
        - username (type `str`) is the vCenter user name. Can be `None` and will
          result in a prompt.
        - password (type `str`) is the vCenter password. Can be `None` and will
          result in a prompt.
        """
        self._connection = AutoEstablishingConnection(hostname, username, password)
        self.vm_name_to_uuid_mapping = {}
        self.esx_name_to_uuid_mapping = {}
        self.dvs_mapping = {}

    @property
    def vvc(self):
        """
        The encapsulated vCenter connection.
        """
        return self._connection.ensure_established()

    @memoized
    def find_by_dns_name(self, dns_name, search_for_vms=False):
        """
        Returns an item by searching for its DNS name.
        Raises an exception if the item cannot be found.

        - dns_name (type `str`): The dns name of the desired item.
        - search_for_vms (type `bool`): Whether to search for virtual machines or not.
        """
        return self.vvc.find_by_dns_name(dns_name, search_for_vms)

    @memoized
    def get_custom_attributes_mapping(self):
        """
        Returns a dictionary with the mapping from custom attribute keys to
        custom attribute names (not values!).
        """
        return self.vvc.get_custom_attributes_mapping()

    def set_custom_attribute(self, item, attribute_name, attribute_value):
        self.vvc.set_custom_attribute(item, attribute_name, attribute_value)

    def fill(self):
        """
        Fill the item cache. Makes listing item names available and retrieving
        items available.
        """
        self.find_by_dns_name.__func__.cached_calls = {}
        self.get_custom_attributes_mapping.__func__.cached_calls = {}
        self.retrieve_vm.__func__.cached_calls = {}

        for vm in self.vvc.get_restricted_view_on_vms(["name", "config.uuid"]):
            self.vm_name_to_uuid_mapping[vm.name] = vm.config.uuid

        for esx in self.vvc.get_restricted_view_on_host_systems(["name", "hardware.systemInfo.uuid"]):
            self.esx_name_to_uuid_mapping[esx.name] = esx.hardware.systemInfo.uuid

        for dvs in self.vvc.get_all_dvs():
            self.dvs_mapping[dvs.name] = dvs

    def list_cached_vms(self):
        """
        List the names of the virtual machines.
        This requires `fill()` to have been called since it operates on the cache.
        """
        return self.vm_name_to_uuid_mapping.keys()

    def list_cached_esxis(self):
        """
        List the names of the ESXi host systems.
        This requires `fill()` to have been called since it operates on the cache.
        """
        return self.esx_name_to_uuid_mapping.keys()

    def list_cached_dvses(self):
        """
        List the names of the distributed virtual switches.
        This requires `fill()` to have been called since it operates on the cache.
        """
        return self.dvs_mapping.keys()

    @memoized
    def retrieve_vm(self, vm_name):
        """
        Retrieve a virtual machine by its name. The name must be in the cache.

        - vm_name (type `str`): The virtual machine name from the cache.
        """
        return self.vvc.get_vm_by_uuid(self.vm_name_to_uuid_mapping[vm_name])

    @memoized
    def retrieve_esx(self, esx_name):
        """
        Retrieve an ESXi host system by its name. The name must be in the cache.

        - esx_name (type `str`): The ESX name from the cache.
        """
        return self.vvc.get_host_system_by_uuid(self.esx_name_to_uuid_mapping[esx_name])

    def retrieve_dvs(self, dvs_name):
        """
        Retrieve a DVS by its name. The name must be in the cache.

        - dvs_name (type `str`): The DVS name from the cache.
        """
        return self.dvs_mapping[dvs_name]

    @property
    def number_of_vms(self):
        """
        The number of virtual machines available in the cache.
        """
        return len(self.vm_name_to_uuid_mapping)

    @property
    def number_of_esxis(self):
        """
        The number of ESXi available in the cache.
        """
        return len(self.esx_name_to_uuid_mapping)

    @property
    def number_of_dvses(self):
        """
        The number of DVS available in the cache.
        """
        return len(self.dvs_mapping)

    def wait_for_tasks(self, tasks):
        """
        Wait until a collection of tasks completes.

        - tasks (type `vim.Task[]`): The tasks which should complete.
        """
        return thirdparty_tasks.wait_for_tasks(self.vvc.service_instance, tasks)


class AutoEstablishingConnection(object):

    """
    A vCenter connection that establishes when used.
    """

    def __init__(self, hostname, username, password):
        """
        Create a new connection.

        - hostname (type `str`) is the vCenter host name. Can be `None` and will
          result in a prompt.
        - username (type `str`) is the vCenter user name. Can be `None` and will
          result in a prompt.
        - password (type `str`) is the vCenter password. Can be `None` and will
          result in a prompt.
        """
        self.vvc = None
        self.username = username
        self.hostname = hostname
        self.password = password

    def ensure_established(self):
        """
        Returns the connection encapsulated by this class. Establishes the connection
        if necessary and might prompt for missing information.
        """
        return self.vvc or self._connect()

    def _connect(self):
        self.hostname = self.hostname or killable_input("Remote vsphere hostname: ")
        self.username = self.username or killable_input("User name for {0}: ".format(self.hostname))
        self.vvc = VVC(self.hostname)
        self.vvc.connect(self.username)

        return self.vvc
