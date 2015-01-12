#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

from unittest import TestCase

from mock import patch

from isphere.cli import main


class CliLoopTest(TestCase):

    @patch("isphere.cli.VSphereREPL")
    def test_should_create_REPL_and_start_it(self, repl_loop):
        main()

        repl_loop.assert_called_with()
        repl_loop.return_value.cmdloop.assert_called_with()
