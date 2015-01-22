#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

"""
Provides user input capabilities.
"""

try:
    _input = raw_input
except NameError:
    _input = input

__all__ = ["killable_input"]


def killable_input(text):
    """
    Displays `text`, requiring and returning user input.
    In case the user sends a `KeyboardInterrupt`, raise a `RuntimeError`.

    - text (type `str`): The text that should be displayed before asking for input.
    """
    try:
        return _input(text)
    except KeyboardInterrupt as keyboard_interrupt:
        raise RuntimeError(str(keyboard_interrupt))
