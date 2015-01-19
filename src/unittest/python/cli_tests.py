#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

from unittest import TestCase

from mock import patch

from isphere.cli import main


class CliLoopTest(TestCase):

    @patch("isphere.cli.docopt")
    @patch("isphere.cli.VSphereREPL")
    def test_should_create_REPL_and_start_it(self, repl_loop, arguments):
        arguments.return_value = {"--username": "any-user-name",
                                  "--password": "any-password",
                                  "--hostname": "any-hostname"}
        main()

        repl_loop.assert_called_with('any-hostname',
                                     'any-user-name',
                                     'any-password')
        repl_loop.return_value.cmdloop.assert_called_with()
