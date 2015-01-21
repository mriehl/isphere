#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

import cmd2 as cmd

from isphere.command.core_command import CoreCommand
from isphere.command.esx_command import EsxCommand
from isphere.command.virtual_machine_command import VirtualMachineCommand
from isphere.command.dvs_command import DvsCommand


class VSphereREPL(EsxCommand, VirtualMachineCommand, DvsCommand):

    def __init__(self, hostname=None, username=None, password=None):
        self.hostname = hostname
        self.username = username
        self.password = password
        CoreCommand.__init__(self)

    def cmdloop(self, **kwargs):
        try:
            cmd.Cmd.cmdloop(self, **kwargs)
        except KeyboardInterrupt:
            print("Quit with Ctrl+D or `EOF`.")
            self.cmdloop(**kwargs)
