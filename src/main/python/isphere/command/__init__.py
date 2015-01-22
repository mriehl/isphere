#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

"""
The isphere command classes.
"""

import cmd

import cmd2

from isphere.command.core_command import CoreCommand
from isphere.command.esx_command import EsxCommand
from isphere.command.virtual_machine_command import VirtualMachineCommand
from isphere.command.dvs_command import DvsCommand

__pdoc__ = {}


class VSphereREPL(EsxCommand, VirtualMachineCommand, DvsCommand):

    """
    The isphere REPL command class.
    """

    for field in cmd.Cmd.__dict__.keys():
        __pdoc__['VSphereREPL.%s' % field] = None
    for field in cmd2.Cmd.__dict__.keys():
        __pdoc__['VSphereREPL.%s' % field] = None

    def __init__(self, hostname=None, username=None, password=None):
        """
        Create a new REPL that connects to a vmware vCenter.

        - hostname (type `str`) is the vCenter host name. Can be `None` and will
          result in a prompt.
        - username (type `str`) is the vCenter user name. Can be `None` and will
          result in a prompt.
        - password (type `str`) is the vCenter password. Can be `None` and will
          result in a prompt.
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        CoreCommand.__init__(self)

    def cmdloop(self, **kwargs):
        """
        Launches a REPL and swallows `KeyboardInterrupt`s.
        """
        try:
            cmd2.Cmd.cmdloop(self, **kwargs)
        except KeyboardInterrupt:
            print("Quit with Ctrl+D or `EOF`.")
            self.cmdloop(**kwargs)
