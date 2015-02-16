#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

from unittest import TestCase
from mock import patch, call, Mock

from isphere.connection import (AutoEstablishingConnection,
                                CachingVSphere,
                                memoized)


class CachingVSphereTests(TestCase):

    def setUp(self):
        self.cache = CachingVSphere(None, None, None)
        self.cache._connection = Mock()
        self.vvc = self.cache._connection.ensure_established.return_value

    def test_should_fill_cache_with_vms_and_esxis_returned_by_vvc(self):
        vm_1, vm_2 = Mock(), Mock()
        vm_1.name = "vm-1"
        vm_1.config.uuid = "vm-1-uuid"
        vm_2.name = "vm-2"
        vm_2.config.uuid = "vm-2-uuid"
        esx_1, esx_2 = Mock(), Mock()
        esx_1.name = "esx-1"
        esx_2.name = "esx-2"
        dvs_1, dvs_2 = Mock(), Mock()
        dvs_1.name = "dvs-1"
        dvs_2.name = "dvs-2"
        self.vvc.get_restricted_view_on_vms.return_value = [vm_1, vm_2]
        self.vvc.get_all_esx.return_value = [esx_1, esx_2]
        self.vvc.get_all_dvs.return_value = [dvs_1, dvs_2]

        self.cache.fill()

        self.assertEqual(self.cache.vm_name_to_uuid_mapping, {"vm-1": "vm-1-uuid", "vm-2": "vm-2-uuid"})

    def test_should_passthrough_find_by_dns_name_calls(self):
        mock_item = Mock()
        self.vvc.find_by_dns_name.return_value = mock_item

        actual_item = self.cache.find_by_dns_name("any.dns.name")

        self.assertEqual(actual_item, mock_item)
        self.vvc.find_by_dns_name.assert_called_with("any.dns.name", False)

    def test_should_retrieve_vm_by_uuid(self):
        mock_vm = Mock()
        self.vvc.get_vm_by_uuid.return_value = mock_vm
        self.cache.vm_name_to_uuid_mapping = {"any-vm-name": "any-uuid"}

        actual_vm = self.cache.retrieve_vm("any-vm-name")
        self.assertEqual(mock_vm, actual_vm)
        self.vvc.get_vm_by_uuid.assert_called_with("any-uuid")

    def test_should_passthrough_find_by_dns_name_calls_when_searching_for_vms(self):
        mock_item = Mock()
        self.vvc.find_by_dns_name.return_value = mock_item

        actual_item = self.cache.find_by_dns_name("any.dns.name", search_for_vms=True)

        self.assertEqual(actual_item, mock_item)
        self.vvc.find_by_dns_name.assert_called_with("any.dns.name", True)

    def test_should_passthrough_set_custom_attribute(self):
        self.cache.set_custom_attribute("any-vim-item", "any-name", "any-value")

        self.cache.vvc.set_custom_attribute.assert_called_with('any-vim-item', 'any-name', 'any-value')


class ConnectionTests(TestCase):

    @patch("isphere.connection.killable_input")
    @patch("isphere.connection.VVC")
    def test_should_ask_for_credentials_when_connecting(self, _, killable_input):
        killable_input.return_value = "any-input"
        connection = AutoEstablishingConnection(None, None, None)

        connection._connect()

        self.assertEqual(killable_input.call_args_list, [
                         call('Remote vsphere hostname: '),
                         call('User name for any-input: ')])

    @patch("isphere.connection.killable_input")
    @patch("isphere.connection.VVC")
    def test_should_use_supplied_credentials_when_connecting(self, vvc, killable_input):
        killable_input.side_effect = ["any-hostname.domain", "any-user-name"]
        connection = AutoEstablishingConnection(None, None, None)

        connection._connect()

        vvc.assert_called_with("any-hostname.domain")
        vvc.return_value.connect.assert_called_with("any-user-name")

    @patch("isphere.connection.AutoEstablishingConnection._connect")
    def test_should_use_existing_connection(self, connect):
        connection = AutoEstablishingConnection(None, None, None)
        fake_vvc = Mock()
        connection.vvc = fake_vvc

        self.assertEqual(connection.ensure_established(), fake_vvc)
        self.assertEqual(False, connect.called)

    @patch("isphere.connection.AutoEstablishingConnection._connect")
    def test_should_connect_when_no_connection_established(self, connect):
        connection = AutoEstablishingConnection(None, None, None)

        connection.ensure_established()
        self.assertEqual(True, connect.called)

    @patch("isphere.connection.killable_input")
    @patch("isphere.connection.VVC")
    def test_should_not_ask_for_credentials_when_credentials_supplied(self, _, killable_input):
        killable_input.return_value = "any-input"
        connection = AutoEstablishingConnection("any-hostname", "any-user-name", None)

        connection._connect()

        self.assertFalse(killable_input.called)

    @patch("isphere.connection.killable_input")
    @patch("isphere.connection.VVC")
    def test_should_ask_for_hostname_when_username_given(self, _, killable_input):
        killable_input.return_value = "any-input"
        connection = AutoEstablishingConnection(None, "any-user-name", None)

        connection._connect()

        self.assertEqual(killable_input.call_args_list, [
                         call('Remote vsphere hostname: ')])

    @patch("isphere.connection.killable_input")
    @patch("isphere.connection.VVC")
    def test_should_ask_for_username_when_hostname_given(self, _, killable_input):
        killable_input.return_value = "any-input"
        connection = AutoEstablishingConnection("any-host-name", None, None)

        connection._connect()

        self.assertEqual(killable_input.call_args_list, [
                         call('User name for any-host-name: ')])


class MemoizingTests(TestCase):

    def setUp(self):
        self.mock_function = Mock()
        self.mock_function.return_value = "any-return-value"
        self.mock_function.__name__ = "any-name"
        self.mock_function.__doc__ = "any-doc"
        self.memoized_mock_function = memoized(self.mock_function)

    def test_should_compute_new_value(self):
        self.assertEqual(self.memoized_mock_function(), "any-return-value")
        self.mock_function.assert_called_with()

    def test_should_compute_new_value_with_args(self):
        self.assertEqual(self.memoized_mock_function("arg1", "arg2"), "any-return-value")
        self.mock_function.assert_called_with("arg1", "arg2")

    def test_should_compute_new_value_with_args_and_kwargs(self):
        self.assertEqual(self.memoized_mock_function("arg1", "arg2", any_kwarg="any-kwarg"), "any-return-value")
        self.mock_function.assert_called_with("arg1", "arg2", any_kwarg="any-kwarg")

    def test_should_not_reissue_call_when_it_was_issued_before(self):
        self.assertEqual(self.memoized_mock_function("any-arg", any_kwarg="any-kwarg"), "any-return-value")
        self.assertEqual(self.memoized_mock_function("any-arg", any_kwarg="any-kwarg"), "any-return-value")

        self.assertEqual(self.mock_function.call_args_list,
                         [call("any-arg", any_kwarg="any-kwarg")])

    def test_should_compute_new_value_when_arg_differs_from_previous_calls(self):
        self.assertEqual(self.memoized_mock_function("arg1"), "any-return-value")
        self.assertEqual(self.memoized_mock_function("arg1-new-value"), "any-return-value")

        self.assertEqual(self.mock_function.call_args_list,
                         [call("arg1"), call("arg1-new-value")])

    def test_should_compute_new_value_when_arity_differs_from_previous_calls(self):
        self.assertEqual(self.memoized_mock_function("arg1"), "any-return-value")
        self.assertEqual(self.memoized_mock_function("arg1", "arg2"), "any-return-value")

        self.assertEqual(self.mock_function.call_args_list,
                         [call("arg1"), call("arg1", "arg2")])

    def test_should_compute_new_value_when_kwarg_differs_from_previous_calls(self):
        self.assertEqual(self.memoized_mock_function("arg1", any_kwarg="any-kwarg"), "any-return-value")
        self.assertEqual(self.memoized_mock_function("arg1", any_kwarg="any-kwarg-other-value"), "any-return-value")

        self.assertEqual(self.mock_function.call_args_list,
                         [call('arg1', any_kwarg='any-kwarg'),
                          call('arg1', any_kwarg='any-kwarg-other-value')])

    def test_should_preserve_name_when_decorating_function(self):
        self.assertEqual(self.memoized_mock_function.__name__, "any-name")

    def test_should_preserve_docstring_when_decorating_function(self):
        self.assertEqual(self.memoized_mock_function.__doc__, "any-doc")
