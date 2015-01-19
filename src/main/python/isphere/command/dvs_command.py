#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

from __future__ import print_function

from isphere.command.core_command import CoreCommand


class DvsCommand(CoreCommand):

    def do_eval_dvs(self, line):
        """Usage: eval_dvs [pattern1 [pattern2]...] ! <statement>
        Evaluate a statement of python code. You can access the
        dvs object by using the variable `dvs`.

        Calling the function `no_output` will not produce any output (use this
                                                                      to filter).

        Sample usage:
        * `eval MY_DVS_NAME ! filter(lambda field_name: callable(getattr(dvs, field_name)) and not field_name.startswith("_"), dir(dvs))`
          ^ shows 'public' methods we can call on the dvs object
        * `eval MY_DVS_NAME ! dvs.name`
        * `eval_dvs ! dvs.overallStatus if dvs.overallStatus != "green" else no_output()`
          ^ shows overall status of dvs hosts unless they have the "green" status
        """
        self.eval(line, self.compile_and_yield_dvs_patterns, self.retrieve_dvs, "dvs")

    def do_list_dvs(self, patterns):
        """Usage: list_dvs [pattern1 [pattern2]...]
        List the dvs names matching the given ORed name patterns.

        Sample usage:
        * `list_dvs`
        * `list_dvs .*`
        """
        for dvs_name in self.compile_and_yield_dvs_patterns(patterns, risky=False):
            print(dvs_name)

    def compile_and_yield_dvs_patterns(self, patterns, risky=True):
        return self.compile_and_yield_generic_patterns(patterns, self.yield_dvs_patterns, self.cache.number_of_dvses, risky)

    def yield_dvs_patterns(self, compiled_patterns):
        for dvs_name in self.cache.list_cached_dvses():
            if any([pattern.match(dvs_name) for pattern in compiled_patterns]):
                yield(dvs_name)

    def retrieve_dvs(self, dvs_name):
        return self.cache.retrieve_dvs(dvs_name)
