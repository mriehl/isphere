#  Copyright (c) 2014 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

from functools import wraps

from isphere.interactive_wrapper import VVC
import thirdparty.tasks as thirdparty_tasks

try:
    import requests
    requests.packages.urllib3.disable_warnings()
except ImportError:
    pass
except AttributeError:
    pass

try:
    _input = raw_input
except NameError:
    _input = input


class CachingVSphere(object):

    def __init__(self):
        self._connection = AutoEstablishingConnection()
        self.vm_mapping = {}

    @property
    def vvc(self):
        return self._connection.ensure_established()

    def find_by_dns_name(self, dns_name, search_for_vms=False):
        return self.vvc.find_by_dns_name(dns_name, search_for_vms)

    def fill(self):
        for vm in self.vvc.get_all_vms():
            self.vm_mapping[vm.name] = vm

    def list_cached_vms(self):
        return self.vm_mapping.keys()

    def retrieve(self, vm_name):
        return self.vm_mapping[vm_name]

    def length(self):
        return len(self.vm_mapping)

    def wait_for_tasks(self, tasks):
        return thirdparty_tasks.wait_for_tasks(self.vvc.service_instance, tasks)


class AutoEstablishingConnection(object):

    def __init__(self):
        self.vvc = None
        self.username = None
        self.hostname = None

    def ensure_established(self):
        return self.vvc or self._connect()

    def _connect(self):
        self.hostname = _input("Remote vsphere hostname: ")
        self.username = _input("User name for {0}: ".format(self.hostname))
        self.vvc = VVC(self.hostname)
        self.vvc.connect(self.username)

        return self.vvc


def memoized(function):
    cached_calls = function.cached_calls = {}

    @wraps(function)
    def function_with_memoized_calls(*args, **kwargs):
        cache_id_for_this_call = str(args) + str(kwargs)
        if cache_id_for_this_call not in cached_calls:
            call_result = function(*args, **kwargs)
            cached_calls[cache_id_for_this_call] = call_result
        return cached_calls[cache_id_for_this_call]
    return function_with_memoized_calls
