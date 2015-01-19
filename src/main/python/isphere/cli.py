#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#
"""Isphere

Usage:
    isphere [options]
    isphere -h | --help
    isphere --version

Options:
    -u --username <username>    Use specified username.
    --hostname <hostname>       Use specified hostname.
    --password -p <password>    Use specified password.
    -h --help                   Show this screen.
    --version                   Show version.
"""

from docopt import docopt
from isphere.command import VSphereREPL


def main(*args):
    arguments = docopt(__doc__, version='isphere ${version}')
    repl = VSphereREPL(arguments['--hostname'], arguments['--username'], arguments['--password'])
    repl.cmdloop()
