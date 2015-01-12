#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

from __future__ import print_function

from isphere.command.core_command import CoreCommand, ItemType


class EsxCommand(CoreCommand):

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

    def compile_and_yield_esx_patterns(self, patterns, risky=True):
        return self.compile_and_yield_generic_patterns(patterns, ItemType.HOST_SYSTEM, risky)

    def yield_esx_patterns(self, compiled_patterns):
        for esx_name in self.cache.list_cached_esxis():
            if any([pattern.match(esx_name) for pattern in compiled_patterns]):
                yield(esx_name)

    def retrieve_esx(self, esx_name):
        return self.cache.retrieve_esx(esx_name)
