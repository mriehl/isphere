#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

"""
Virtual machine specific REPL commands.
"""

from __future__ import print_function

from pyVmomi import vim

from isphere.interactive_wrapper import NotFound
from isphere.command.core_command import CoreCommand, _input


class VirtualMachineCommand(CoreCommand):

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

    def do_set_custom_attribute_vm(self, patterns):
        """Usage: set_custom_attribute_vm [pattern1 [pattern2]...]
        Set custom attributes by name on VMs matching the given ORed name patterns.

        Sample usage: `set_custom_attribute_vm` foo.* ^other-name$
        """
        attribute_names = self.cache.get_custom_attributes_mapping().values()
        formatted_attribute_names = "".join(
            [
                "\n\t{attribute_name}".format(attribute_name=attribute_name) for attribute_name in attribute_names
            ]
        )
        print("Available custom attribute names: {names}".format(
            names=formatted_attribute_names))
        target_name = _input("Target custom attribute name? ")
        target_value = _input("Target value for {name}? ".format(
            name=target_name))

        for vm_name in self.compile_and_yield_vm_patterns(patterns):
            print("Setting attribute for {vm_name}".format(vm_name=vm_name))
            try:
                self.cache.set_custom_attribute(
                    self.cache.retrieve_vm(vm_name).raw_vm,
                    target_name,
                    target_value)
            except Exception as e:
                print(self.colorize(
                    "Got a problem: {problem}".format(problem=e),
                    "red"))
                print(self.colorize("Not continuing.", "red"))
                break

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

    def do_reboot_vm(self, patterns):
        """Usage: reboot_vm [pattern1 [pattern2]...]
        Soft reboot vms matching the given ORed name patterns.

        Sample usage: `reboot MY_VM_NAME`
        """
        for vm_name in self.compile_and_yield_vm_patterns(patterns):
            print("Asking {0} to reboot".format(vm_name))
            self.retrieve_vm(vm_name).RebootGuest()

    def do_shutdown_vm(self, patterns, ask=True):
        """Usage: shutdown_vm [pattern1 [pattern2]...]
        shutdown vms matching the given ORed name patterns.

        Sample usage: `shutdown_vm MY_VM_NAME`
        """

        for vm_name in self.compile_and_yield_vm_patterns(patterns, True, ask):
            task = ['']
            print("Asking {0} to shutdown".format(vm_name))
            task = self.retrieve_vm(vm_name).PowerOffVM_Task()

        return

    def do_startup_vm(self, patterns):
        """Usage: startup_vm [pattern1 [pattern2]...]
        start vms matching the given ORed name patterns.

        Sample usage: `startup_vm MY_VM_NAME`
        """

        for vm_name in self.compile_and_yield_vm_patterns(patterns):
            print("Asking {0} to start".format(vm_name))
            self.retrieve_vm(vm_name).PowerOn()
        return

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

    def compile_and_yield_vm_patterns(self, patterns, risky=True, ask=False):
        return self.compile_and_yield_generic_patterns(patterns,
                                                       self.yield_vm_patterns,
                                                       self.cache.number_of_vms,
                                                       risky,
                                                       ask)

    def yield_vm_patterns(self, compiled_patterns):
        for vm_name in self.cache.list_cached_vms():
            if any([pattern.match(vm_name) for pattern in compiled_patterns]):
                yield(vm_name)

    def retrieve_vm(self, vm_name):
        return self.cache.retrieve_vm(vm_name)
