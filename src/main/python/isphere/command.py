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


class NoOutput(Exception):
    pass


class VSphereREPL(Cmd):
    prompt = "isphere > "

    def __init__(self):
        self.cache = CachingVSphere()
        Cmd.__init__(self)

    def preloop(self):
        self.cache.fill()
        print("{0} VMs on {1} ESXis available.".format(self.cache.number_of_vms,
                                                       self.cache.number_of_esxis))

    def do_reload(self, line):
        """Usage: reload
        Reload VM cache from the vSphere server.

        Sample usage: `reload`
        """
        self.preloop()

    def do_reset_vm(self, patterns):
        """Usage: reset_vm [pattern1 [pattern2]...]
        Reset vms matching the given ORed name patterns.

        Sample usage: `reset MY_VM_NAME OTHERNAME`
        """
        reset_tasks = []
        for vm_name in self.compile_and_yield_vm_patterns(patterns):
            print("Launching reset task for {0}".format(vm_name))
            reset_task = self.retrieve_vm(vm_name).ResetVM_Task()
            reset_tasks.append(reset_task)

        print("Waiting for {0} reset tasks to complete".format(len(reset_tasks)))
        self.cache.wait_for_tasks(reset_tasks)

    def eval(self, line, item_name_generator, item_retriever, local_name):
        try:
            patterns_and_statement = line.split("!", 1)
            patterns = patterns_and_statement[0]
            statement = patterns_and_statement[1]
        except IndexError:
            print("Looks like your input was malformed. Try `help eval_*`.")
            return

        for item_name in item_name_generator(patterns):
            def guard():
                raise NoOutput()
            _globals, _locals = {}, {}
            item = item_retriever(item_name)
            _locals[local_name] = item
            _locals["no_output"] = guard
            _globals[local_name] = item
            _globals["no_output"] = guard
            try:
                separator = "-" * 25
                max_width_of_item_name = 10
                result = eval(statement, _globals, _locals)
                print("{0} {1:^{2}} {0}".format(separator, item_name[:max_width_of_item_name], max_width_of_item_name))
                print(result)
            except NoOutput:
                pass
            except Exception as e:
                print("Eval failed for {0}: {1}".format(item_name, e))

    def do_eval_vm(self, line):
        """Usage: eval_vm [pattern1 [pattern2]...] ! <statement>
        Evaluate a statement of python code. You can access the
        virtual machine object by using the variable `vm`.
        Calling the function `no_output` will not produce any output (use this
                                                                      to filter).

        Sample usage:
        * `eval MY_VM_NAME ! filter(lambda field_name: callable(getattr(vm, field_name)) and not field_name.startswith("_"), dir(vm))`
          ^ shows 'public' methods we can call on the vm object
        * `eval MY_VM_NAME ! vm.name`
        * `eval MY_VM_NAME ! vm.RebootGuest()`
        """
        self.eval(line, self.compile_and_yield_vm_patterns, self.retrieve_vm, "vm")

    def do_eval_esx(self, line):
        """Usage: eval_esx [pattern1 [pattern2]...] ! <statement>
        Evaluate a statement of python code. You can access the
        esx object by using the variable `esx`.

        Calling the function `no_output` will not produce any output (use this
                                                                      to filter).

        Sample usage:
        * `eval MY_ESX_NAME ! filter(lambda field_name: callable(getattr(esx, field_name)) and not field_name.startswith("_"), dir(esx))`
          ^ shows 'public' methods we can call on the esx object
        * `eval MY_ESX_NAME ! esx.name`
        * `eval_esx ! esx.overallStatus if esx.overallStatus != "green" else no_output()`
          ^ shows overall status of esx hosts unless they have the "green" status
        """
        self.eval(line, self.compile_and_yield_esx_patterns, self.retrieve_esx, "esx")

    def do_reboot_vm(self, patterns):
        """Usage: reboot_vm [pattern1 [pattern2]...]
        Soft reboot vms matching the given ORed name patterns.

        Sample usage: `reboot MY_VM_NAME`
        """
        for vm_name in self.compile_and_yield_vm_patterns(patterns):
            print("Asking {0} to reboot".format(vm_name))
            self.retrieve_vm(vm_name).RebootGuest()

    def do_migrate_vm(self, line):
        """Usage: migrate_vm [pattern1 [pattern2]...] ! TARGET_ESX_NAME
        Migrate one or several VMs to another ESX host by name.

        Sample usage: `migrate MYVNNAME ! ESX_FQDN`
        """
        try:
            patterns_and_esx_name = line.split("!", 1)
            patterns = patterns_and_esx_name[0]
            esx_name = patterns_and_esx_name[1].strip()
        except IndexError:
            print("Looks like your input was malformed. Try `help migrate_vm`.")
            return

        if not esx_name:
            print("No target esx name given. Try `help migrate_vm`.")
            return

        try:
            # TODO use esx from cache, allows for better error messages (eg no fqdn)
            esx_host = self.cache.find_by_dns_name(esx_name)
        except NotFound:
            print("Target esx host '{0}' not found, maybe try with FQDN?".format(esx_name))
            return

        for vm_name in self.compile_and_yield_vm_patterns(patterns):
            relocate_spec = vim.vm.RelocateSpec(host=esx_host)
            print("Relocating {0} to {1}".format(vm_name, esx_name))
            try:
                self.retrieve_vm(vm_name).Relocate(relocate_spec)
            except Exception as e:
                print("Relocation failed: {0}".format(e))

    def do_alarms_vm(self, patterns):
        """Usage: alarms_vm [pattern1 [pattern2]...]
        Show alarm information for vms matching the given ORed name patterns.

        Sample usage: `alarms MY_VM_NAME`
        """
        for vm_name in self.compile_and_yield_vm_patterns(patterns):
            print("-" * 70)
            print("Alarms for {0}".format(vm_name))
            alarms = self.retrieve_vm(vm_name).triggeredAlarmState
            for alarm in alarms:
                print("\talarm_moref: {0}".format(alarm.key.split('.')[0]))
                print("\talarm status: {0}".format(alarm.overallStatus))

    def do_list_vm(self, patterns):
        """Usage: list [pattern1 [pattern2]...]
        List the vm names matching the given ORed name patterns.

        Sample usage:
        * `list dev.* ...ybc01`
        * `list`
        * `list .*`
        """
        for vm_name in self.compile_and_yield_vm_patterns(patterns, risky=False):
            print(vm_name)

    def do_list_esx(self, patterns):
        """Usage: list [pattern1 [pattern2]...]
        List the esx names matching the given ORed name patterns.

        Sample usage:
        * `list dev.* ...ybc01`
        * `list`
        * `list .*`
        """
        for esx_name in self.compile_and_yield_esx_patterns(patterns, risky=False):
            print(esx_name)

    def do_info_vm(self, patterns):
        """Usage: info_vm [pattern1 [pattern2]...]
        Show quick info about vms matching the given ORed name patterns.

        Sample usage: `info MY_VM_NAME`
        """
        custom_attributes_mapping = self.cache.get_custom_attributes_mapping()

        for vm_name in self.compile_and_yield_vm_patterns(patterns):
            vm = self.retrieve_vm(vm_name)
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
            for custom_field in vm.customValue:
                print("{0}: {1}".format(custom_attributes_mapping[custom_field.key], custom_field.value))

            print()

    def do_config_vm(self, patterns):
        """Usage: config_vm [pattern1 [pattern2]...]
        Show the full config of vms matching the given ORed name patterns.
        Careful, there's lots of output!

        Sample usage: `config MY_VM_NAME`
        """
        for vm_name in self.compile_and_yield_vm_patterns(patterns):
            print("-" * 70)
            print("Config for {0}:".format(vm_name))
            print(self.retrieve_vm(vm_name).config)
            print()

    def compile_and_yield_generic_patterns(self, patterns, item_type, risky=True):
        if not patterns and risky:
            message = "No pattern specified - you're doing this to all {count} {type}. Proceed? (y/N) ".format(count=self.cache.number_of_esxis,
                                                                                                               type=item_type)
            if not _input(message).lower() == "y":
                return []

        actual_patterns = patterns.strip().split(" ")
        try:
            compiled_patterns = [re.compile(pattern) for pattern in actual_patterns]
        except Exception as e:
            print("Invalid regular expression patterns: {0}".format(e))
            return []

        if item_type == ItemType.HOST_SYSTEM:
            return self.yield_esx_patterns(compiled_patterns)
        if item_type == ItemType.VIRTUAL_MACHINE:
            return self.yield_vm_patterns(compiled_patterns)

    def compile_and_yield_esx_patterns(self, patterns, risky=True):
        return self.compile_and_yield_generic_patterns(patterns, ItemType.HOST_SYSTEM, risky)

    def compile_and_yield_vm_patterns(self, patterns, risky=True):
        return self.compile_and_yield_generic_patterns(patterns, ItemType.VIRTUAL_MACHINE, risky)

    def yield_esx_patterns(self, compiled_patterns):
        for esx_name in self.cache.list_cached_esxis():
            if any([pattern.match(esx_name) for pattern in compiled_patterns]):
                yield(esx_name)

    def yield_vm_patterns(self, compiled_patterns):
        for vm_name in self.cache.list_cached_vms():
            if any([pattern.match(vm_name) for pattern in compiled_patterns]):
                yield(vm_name)

    def retrieve_vm(self, vm_name):
        return self.cache.retrieve_vm(vm_name)

    def retrieve_esx(self, esx_name):
        return self.cache.retrieve_esx(esx_name)

    def do_EOF(self, line):
        return True


class ItemType(object):
    VIRTUAL_MACHINE = "vm"
    HOST_SYSTEM = "esx"
