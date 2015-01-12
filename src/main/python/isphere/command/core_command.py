#  Copyright (c) 2014 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

from __future__ import print_function

from cmd import Cmd
import re

from isphere.connection import CachingVSphere


try:
    _input = raw_input
except NameError:
    _input = input


class NoOutput(Exception):
    pass


class CoreCommand(Cmd):
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
                print("{0} {1:^{2}} {0}".format(separator, item_name[:max_width_of_item_name], max_width_of_item_name))
                result = eval(statement, _globals, _locals)
                if result != guard:
                    print(result)
            except NoOutput:
                pass
            except Exception as e:
                print("Eval failed for {0}: {1}".format(item_name, e))

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

    def do_EOF(self, line):
        return True


class ItemType(object):
    VIRTUAL_MACHINE = "vm"
    HOST_SYSTEM = "esx"
