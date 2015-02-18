#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

"""
# isphere

isphere (read: *interactive vSphere*) is a platform independent (mac, windows, linux)
[**REPL**](https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop)
thanks to the [pyVmomi](https://pypi.python.org/pypi/pyvmomi)
library, usable from your favourite terminal.
It also features an easy to use **API** for programmatic access.


- `isphere.command`: a subpackage defining REPL commands.
- `isphere.cli`: a module for command line entrypoints.
- `isphere.interactive_wrapper`: A `pyVmomi` API wrapper to make most things
  dead simple.
- `isphere.connection`: A connection and caching abstraction over
  `isphere.interactive_wrapper`.
- `isphere.input`: a module for user input capabilities.


# API capabilities

## Full retrieval API quickstart

The full retrieval API makes it easy to get all items of a certain type.
It will fully populate the items, which may take some time.
See `isphere.interactive_wrapper.VVC` for all the possibilities.

    from isphere.interactive_wrapper import VVC
    vvc = VVC(hostname)
    vvc.connect(username, password)

    for vm in vvc.get_all_vms():
        print("{vm_name} on {host_system}".format(vm_name=vm.name, host_system=vm.runtime.host.name))

## Selective retrieval API (faster)

The selective retrieval API is very fast but requires you to know ahead of time
which attribute you want to access on the API items.
See `isphere.interactive_wrapper.VVC` for all the possibilities.

    from isphere.interactive_wrapper import VVC
    vvc = VVC(hostname)
    vvc.connect(username, password)

    for vm in vvc.get_restricted_view_on_vms(["name", "runtime.host.name"]):
        print("{vm_name} on {host_system}".format(vm_name=vm.name, host_system=vm.runtime.host.name))

## Caching API

The caching API allows to access all available item names with an optional
retrieval of the full item. It caches everything very aggressively and is
especially useful if you need all the item names to decide which ones you want
to use (for example regex matching).

    >>> from isphere.connection import CachingVSphere
    >>> vsphere_cache = CachingVSphere()
    >>> vsphere_cache.fill() # rerun if you need to update the cache later
    >>> all_vms = vsphere_cache.list_cached_vms()
    >>> all_vms[0]
    'some-vm-name'
    >>> actual_vm = vsphere_cache.retrieve_vm(all_vms[0])
"""
