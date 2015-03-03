#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

"""
ESXi host system specific REPL commands.
"""

from __future__ import print_function

from isphere.command.core_command import CoreCommand


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
        return self.compile_and_yield_generic_patterns(patterns,
                                                       self.yield_esx_patterns,
                                                       self.cache.number_of_esxis,
                                                       risky)

    def do_enter_maintenance(self, esx_name):
        """Usage: enter_maintenance <esx.rz.is>
        The given esx enters the maintenance mode.

        Sample usage:
        * `enter_maintenance devesx99.rz.is`
        """
        if not esx_name:
            print("No target esx name given. Try `help enter_maintenance`.")
            return

        myesx = self.retrieve_esx(esx_name)
        if not myesx.runtime.inMaintenanceMode:
            maintain_task = myesx.EnterMaintenanceMode(10)
            self.cache.wait_for_tasks([maintain_task])
        else:
            print("Esx already in maintenance mode")
            return
        return

    def do_exit_maintenance(self, esx_name):
        """Usage: exit_maintenance <esx.rz.is>
        The given esx exits the maintenance mode.

        Sample usage:
        * `exit_maintenance devesx99.rz.is`
        """
        if not esx_name:
            print("No target esx name given. Try `help exit_maintenance`.")
            return

        myesx = self.retrieve_esx(esx_name)
        if myesx.runtime.inMaintenanceMode:
            maintain_task = myesx.ExitMaintenanceMode(10)
            self.cache.wait_for_tasks([maintain_task])
        else:
            print("Esx was not in maintenance mode")
            return
        return

    def do_shutdown_esx(self, esx_name):
        """Usage: shutdown_esx <esx.rz.is>
        Shutdown the given esx

        Sample usage:
        * `shutdown_esx devesx99.rz.is`
        """
        if not esx_name:
            print("No target esx name given. Try `help shutdown_esx`.")
            return

        myesx = self.retrieve_esx(esx_name)
        print(myesx.runtime.powerState)
        print(myesx.capability.shutdownSupported)
        shutdown_task = myesx.ShutdownHost(True)
        self.cache.wait_for_tasks([shutdown_task])
        return

    def yield_esx_patterns(self, compiled_patterns):
        for esx_name in self.cache.list_cached_esxis():
            if any([pattern.match(esx_name) for pattern in compiled_patterns]):
                yield(esx_name)

    def retrieve_esx(self, esx_name):
        return self.cache.retrieve_esx(esx_name)
