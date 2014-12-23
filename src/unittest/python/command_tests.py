from unittest import TestCase
import re

from mock import patch

from isphere.command import VSphereREPL


class PatternTests(TestCase):

    def setUp(self):
        self.repl = VSphereREPL()

    @patch("isphere.command.CachingVSphere.list_cached_vms")
    def test_should_yield_one_vm_when_pattern_matches(self, list_cached_vms):
        list_cached_vms.return_value = ["vm-1", "vm-2"]

        actual_matches = [match for match in self.repl.yield_patterns([re.compile("vm-1")])]

        self.assertEqual(actual_matches, ["vm-1"])

    @patch("isphere.command.CachingVSphere.list_cached_vms")
    def test_should_yield_empty_list_when_pattern_does_not_match(self, list_cached_vms):
        list_cached_vms.return_value = ["vm-1", "vm-2"]

        actual_matches = [match for match in self.repl.yield_patterns([re.compile("^does-not-match$")])]

        self.assertEqual(actual_matches, [])

    def test_should_yield_empty_list_when_no_vms_cached(self):
        actual_matches = [match for match in self.repl.yield_patterns([re.compile("any-pattern")])]

        self.assertEqual(actual_matches, [])

    @patch("isphere.command._input")
    @patch("isphere.command.CachingVSphere.list_cached_vms")
    def test_should_yield_all_vms_when_no_when_patterns_given_and_user_confirms(self, list_cached_vms, _input):
        list_cached_vms.return_value = ["vm-1", "vm-2", "other-vm"]
        _input.return_value = "y"

        actual_matches = [match for match in self.repl.compile_and_yield_patterns("")]

        self.assertEqual(actual_matches, ["vm-1", "vm-2", "other-vm"])

    @patch("isphere.command._input")
    @patch("isphere.command.CachingVSphere.list_cached_vms")
    def test_should_return_empty_list_when_no_when_patterns_given_and_user_refuses(self, list_cached_vms, _input):
        list_cached_vms.return_value = ["vm-1", "vm-2", "other-vm"]
        _input.return_value = "N"

        actual_matches = [match for match in self.repl.compile_and_yield_patterns("")]

        self.assertEqual(actual_matches, [])

    @patch("isphere.command._input")
    @patch("isphere.command.CachingVSphere.list_cached_vms")
    def test_should_return_empty_list_when_no_when_patterns_given_and_user_defaults(self, list_cached_vms, _input):
        list_cached_vms.return_value = ["vm-1", "vm-2", "other-vm"]
        _input.return_value = ""

        actual_matches = [match for match in self.repl.compile_and_yield_patterns("")]

        self.assertEqual(actual_matches, [])

    @patch("isphere.command._input")
    @patch("isphere.command.CachingVSphere.list_cached_vms")
    def test_should_return_empty_list_when_no_when_patterns_given_and_user_writes_something_else(self, list_cached_vms, _input):
        list_cached_vms.return_value = ["vm-1", "vm-2", "other-vm"]
        _input.return_value = "?"

        actual_matches = [match for match in self.repl.compile_and_yield_patterns("")]

        self.assertEqual(actual_matches, [])

    @patch("isphere.command._input")
    @patch("isphere.command.CachingVSphere.list_cached_vms")
    def test_should_yield_one_vm_when_pattern_given(self, list_cached_vms, _):
        list_cached_vms.return_value = ["vm-1", "vm-2", "other-vm"]

        actual_matches = [match for match in self.repl.compile_and_yield_patterns("other.*")]

        self.assertEqual(actual_matches, ["other-vm"])

    @patch("isphere.command._input")
    @patch("isphere.command.CachingVSphere.list_cached_vms")
    def test_should_yield_several_vms_when_ored_patterns_given(self, list_cached_vms, _):
        list_cached_vms.return_value = ["vm-1", "vm-2", "other-vm", "my-vm-name"]

        actual_matches = [match for match in self.repl.compile_and_yield_patterns("other.* ..-2 my-vm")]

        self.assertEqual(actual_matches, ["vm-2", "other-vm", "my-vm-name"])


class VSphereREPLTests(TestCase):

    def setUp(self):
        self.repl = VSphereREPL()

    @patch("isphere.command.CachingVSphere.retrieve")
    def test_should_retrieve_vm_from_cache(self, cache_retrieve):
        self.assertEqual(self.repl.retrieve("any-vm-name"), cache_retrieve.return_value)
