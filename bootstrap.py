#!/usr/bin/env python
#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#
import sys
sys.path.insert(0, "src/main/python")

from isphere.command import VSphereREPL

exec(open("src/main/scripts/isphere").read())
