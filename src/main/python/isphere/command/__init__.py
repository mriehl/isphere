#  Copyright (c) 2014 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

from isphere.command.esx_command import EsxCommand
from isphere.command.virtual_machine_command import VirtualMachineCommand


class VSphereREPL(EsxCommand, VirtualMachineCommand):
    pass
