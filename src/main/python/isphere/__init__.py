#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

"""
# The isphere package.

- `isphere.command`: a subpackage defining REPL commands.
- `isphere.cli`: a module for command line entrypoints.
- `isphere.interactive_wrapper`: A `pyVmomi` API wrapper to make most things
  dead simple.
- `isphere.connection`: A connection and caching abstraction over
  `isphere.interactive_wrapper`.
- `isphere.input`: a module for user input capabilities.


## Full retrieval API quickstart

    from isphere.interactive_wrapper import VVC
    vvc = VVC(hostname)
    vvc.connect(username, password)

    for vm in vvc.get_all_vms():
        print("{vm_name} on {host_system}".format(vm_name=vm.name, host_system=vm.runtime.host.name))

## Selective retrieval API (faster)

    from isphere.interactive_wrapper import VVC
    vvc = VVC(hostname)
    vvc.connect(username, password)

    for vm in vvc.get_restricted_view_on_vms(["name", "runtime.host.name"]):
        print("{vm_name} on {host_system}".format(vm_name=vm.name, host_system=vm.runtime.host.name))

"""
