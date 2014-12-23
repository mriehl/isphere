from __future__ import print_function

from cmd import Cmd
import re

from isphere.connection import CachingVSphere


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
        self.preloop()

    def do_reset(self, patterns):
        reset_tasks = []
        for vm_name in self.compile_and_yield_patterns(patterns):
            print("Launching reset task for {0}".format(vm_name))
            reset_tasks.append(self.cache.retrieve(vm_name).ResetVM_Task())

        print("Waiting for {0} reset tasks to complete".format(len(reset_tasks)))
        self.cache.wait_for_tasks(reset_tasks)

    def do_reboot(self, patterns):
        for vm_name in self.compile_and_yield_patterns(patterns):
            print("Asking {0} to reboot".format(vm_name))
            self.cache.retrieve(vm_name).RebootGuest()

    def do_alarms(self, patterns):
        for vm_name in self.compile_and_yield_patterns(patterns):
            print("-" * 70)
            print("Alarms for {0}".format(vm_name))
            alarms = self.cache.retrieve(vm_name).triggeredAlarmState
            for alarm in alarms:
                print("\talarm_moref: {0}".format(alarm.key.split('.')[0]))
                print("\talarm status: {0}".format(alarm.overallStatus))

    def do_list(self, patterns):
        for vm_name in self.compile_and_yield_patterns(patterns, risky=False):
            print(vm_name)

    def do_info(self, patterns):
        for vm_name in self.compile_and_yield_patterns(patterns):
            vm = self.cache.retrieve(vm_name)
            print("-" * 70)
            print("Name: {0}".format(vm.name))
            print("BIOS UUID: {0}".format(vm.config.uuid))
            print("CPUs: {0}".format(vm.config.hardware.numCPU))
            print("MemoryMB: {0}".format(vm.config.hardware.memoryMB))
            print("Guest PowerState: {0}".format(vm.guest.guestState))
            print("Guest Full Name: {0}".format(vm.config.guestFullName))
            print("Guest Container Type: {0}".format(vm.config.guestId))
            print("Container Version: {0}".format(vm.config.version))
            print()

    def do_config(self, patterns):
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
        actual_patterns = patterns.split(" ")
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
