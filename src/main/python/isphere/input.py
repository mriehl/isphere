#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

try:
    _input = raw_input
except NameError:
    _input = input


def killable_input(text):
    try:
        return _input(text)
    except KeyboardInterrupt as keyboard_interrupt:
        raise RuntimeError(str(keyboard_interrupt))
