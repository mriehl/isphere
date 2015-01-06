#  Copyright (c) 2014 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

from __future__ import print_function

from pyVmomi import vim

from cmd import Cmd
import re

from isphere.connection import CachingVSphere
from isphere.interactive_wrapper import NotFound


try:
    _input = raw_input
except NameError:
    _input = input


class VSphereREPL(Cmd):
    prompt = "isphere > "

    def __init__(self):
        self.cache = CachingVSphere()
        Cmd.__init__(self)

    def preloop(self):
        self.cache.fill()
        print("{0} VMs available.".format(self.cache.length()))

    def do_reload(self, line):
        """Usage: reload
        Reload VM cache from the vSphere server.

        Sample usage: `reload`
        """
        self.preloop()

    def do_reset(self, patterns):
        """Usage: reset [pattern1 [pattern2]...]
        Reset vms matching the given ORed name patterns.

        Sample usage: `reset MY_VM_NAME OTHERNAME`
        """
        reset_tasks = []
        for vm_name in self.compile_and_yield_patterns(patterns):
            print("Launching reset task for {0}".format(vm_name))
            reset_task = self.cache.retrieve(vm_name).ResetVM_Task()
            reset_tasks.append(reset_task)

        print("Waiting for {0} reset tasks to complete".format(len(reset_tasks)))
        self.cache.wait_for_tasks(reset_tasks)

    def do_eval(self, line):
        """Usage: eval [pattern1 [pattern2]...] ! <statement>
        Evaluate a statement of python code. You can access the
        virtual machine object by using the variable `vm`.

        Sample usage:
        * `eval MY_VM_NAME ! dir(vm)`
        * `eval MY_VM_NAME ! vm.name`
        * `eval MY_VM_NAME ! vm.RebootGuest()`
        """
        try:
            patterns_and_statement = line.split("!", 1)
            patterns = patterns_and_statement[0]
            statement = patterns_and_statement[1]
        except IndexError:
            print("Looks like your input was malformed. Try `help eval`.")
            return

        for vm_name in self.compile_and_yield_patterns(patterns):
            _globals, _locals = {}, {}
            vm = self.retrieve(vm_name)
            _locals["vm"] = vm
            try:
                separator = "-" * 25
                max_width_of_vm_name = 10
                print("{0} {1:^{2}} {0}".format(separator, vm_name[:max_width_of_vm_name], max_width_of_vm_name))
                print(eval(statement, _globals, _locals))
            except Exception as e:
                print("Eval failed for {0}: {1}".format(vm_name, e))

    def do_reboot(self, patterns):
        """Usage: reboot [pattern1 [pattern2]...]
        Soft reboot vms matching the given ORed name patterns.

        Sample usage: `reboot MY_VM_NAME`
        """
        for vm_name in self.compile_and_yield_patterns(patterns):
            print("Asking {0} to reboot".format(vm_name))
            self.cache.retrieve(vm_name).RebootGuest()

    def do_migrate(self, line):
        """Usage: migrate [pattern1 [pattern2]...] ! TARGET_ESX_NAME
        Migrate one or several VMs to another ESX host by name.

        Sample usage: `migrate MYVNNAME ! ESX_FQDN`
        """
        try:
            patterns_and_esx_name = line.split("!", 1)
            patterns = patterns_and_esx_name[0]
            esx_name = patterns_and_esx_name[1].strip()
        except IndexError:
            print("Looks like your input was malformed. Try `help migrate`.")
            return

        if not esx_name:
            print("No target esx name given. Try `help migrate`.")
            return

        try:
            esx_host = self.cache.find_by_dns_name(esx_name)
        except NotFound:
            print("Target esx host '{0}' not found, maybe try with FQDN?".format(esx_name))
            return

        for vm_name in self.compile_and_yield_patterns(patterns):
            relocate_spec = vim.vm.RelocateSpec(host=esx_host)
            print("Relocating {0} to {1}".format(vm_name, esx_name))
            try:
                self.cache.retrieve(vm_name).Relocate(relocate_spec)
            except Exception as e:
                print("Relocation failed: {0}".format(e))

    def do_alarms(self, patterns):
        """Usage: alarms [pattern1 [pattern2]...]
        Show alarm information for vms matching the given ORed name patterns.

        Sample usage: `alarms MY_VM_NAME`
        """
        for vm_name in self.compile_and_yield_patterns(patterns):
            print("-" * 70)
            print("Alarms for {0}".format(vm_name))
            alarms = self.cache.retrieve(vm_name).triggeredAlarmState
            for alarm in alarms:
                print("\talarm_moref: {0}".format(alarm.key.split('.')[0]))
                print("\talarm status: {0}".format(alarm.overallStatus))

    def do_list(self, patterns):
        """Usage: list [pattern1 [pattern2]...]
        List the vm names matching the given ORed name patterns.

        Sample usage:
        * `list dev.* ...ybc01`
        * `list`
        * `list .*`
        """
        for vm_name in self.compile_and_yield_patterns(patterns, risky=False):
            print(vm_name)

    def do_info(self, patterns):
        """Usage: info [pattern1 [pattern2]...]
        Show quick info about vms matching the given ORed name patterns.

        Sample usage: `info MY_VM_NAME`
        """
        for vm_name in self.compile_and_yield_patterns(patterns):
            vm = self.cache.retrieve(vm_name)
            print("-" * 70)
            print("Name: {0}".format(vm.name))
            print("ESXi Host: {0}".format(vm.get_esx_host().name))
            print("Path to VM: {0}".format(vm.summary.config.vmPathName))
            print("BIOS UUID: {0}".format(vm.config.uuid))
            print("CPUs: {0}".format(vm.config.hardware.numCPU))
            print("MemoryMB: {0}".format(vm.config.hardware.memoryMB))
            print("Guest PowerState: {0}".format(vm.guest.guestState))
            print("Guest Full Name: {0}".format(vm.config.guestFullName))
            print("Guest Container Type: {0}".format(vm.config.guestId))
            print("Container Version: {0}".format(vm.config.version))
            print()

    def do_config(self, patterns):
        """Usage: config [pattern1 [pattern2]...]
        Show the full config of vms matching the given ORed name patterns.
        Careful, there's lots of output!

        Sample usage: `config MY_VM_NAME`
        """
        for vm_name in self.compile_and_yield_patterns(patterns):
            print("-" * 70)
            print("Config for {0}:".format(vm_name))
            print(self.cache.retrieve(vm_name).config)
            print()

    def compile_and_yield_patterns(self, patterns, risky=True):
        if not patterns and risky:
            message = "No pattern specified - you're doing this to all {0} VMs. Proceed? (y/N) ".format(self.cache.length())
            if not _input(message).lower() == "y":
                return []
        actual_patterns = patterns.strip().split(" ")
        try:
            compiled_patterns = [re.compile(pattern) for pattern in actual_patterns]
        except Exception as e:
            print("Invalid regular expression patterns: {0}".format(e))
            return []

        return self.yield_patterns(compiled_patterns)

    def yield_patterns(self, compiled_patterns):
        for vm_name in self.cache.list_cached_vms():
            if any([pattern.match(vm_name) for pattern in compiled_patterns]):
                yield(vm_name)

    def retrieve(self, vm_name):
        return self.cache.retrieve(vm_name)

    def do_EOF(self, line):
        return True
