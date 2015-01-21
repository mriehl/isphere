#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

from __future__ import print_function

from cmd2 import Cmd
import re

from isphere.connection import CachingVSphere
from isphere.interactive_wrapper import NotFound


try:
    _input = raw_input
except NameError:
    _input = input


class NoOutput(Exception):
    pass


class CoreCommand(Cmd):
    prompt = "isphere > "

    def __init__(self):
        self.cache = CachingVSphere(self.hostname, self.username, self.password)
        Cmd.__init__(self)

    def preloop(self):
        self.cache.fill()
        print("{0} VMs on {1} ESXis available.".format(self.cache.number_of_vms,
                                                       self.cache.number_of_esxis))
        print("{0} Distributed Virtual Switches configured.".format(
              self.cache.number_of_dvses))

    def do_reload(self, _):
        """Usage: reload
        Reload VM cache from the vSphere server.

        Sample usage: `reload`
        """
        self.preloop()

    @staticmethod
    def eval(line, item_name_generator, item_retriever, local_name):
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
            try:
                item = item_retriever(item_name)
            except NotFound:
                print("Skipping {item} since it could not be retrieved.".format(item=item_name))
                continue
            _locals[local_name] = item
            _locals["no_output"] = guard
            _globals[local_name] = item
            _globals["no_output"] = guard

            separator = "-"
            item_name_header = " {name} ".format(
                name=item_name[:78]).center(
                80, separator)

            try:
                result = eval(statement, _globals, _locals)
                print(item_name_header)
                print(result)
            except NoOutput:
                pass
            except Exception as e:
                print(item_name_header)
                print("Eval failed for {0}: {1}".format(item_name, e))

    @staticmethod
    def compile_and_yield_generic_patterns(patterns, pattern_generator, item_count, risky=True):
        if not patterns and risky:
            unformatted_message = "No pattern specified - you're doing this to all {count} items. Proceed? (y/N) "
            message = unformatted_message.format(count=item_count)
            if not _input(message).lower() == "y":
                return []

        actual_patterns = patterns.strip().split(" ")
        try:
            compiled_patterns = [re.compile(pattern) for pattern in actual_patterns]
        except Exception as e:
            print("Invalid regular expression patterns: {0}".format(e))
            return []

        return pattern_generator(compiled_patterns)

    @staticmethod
    def do_EOF(_):
        """
        Exit this prompt.

        Usage: `EOF` (Ctrl+D also works).
        """
        return True
