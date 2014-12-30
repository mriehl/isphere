#  Copyright (c) 2014 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

from unittest import TestCase
from mock import patch, call, Mock

from isphere.connection import AutoEstablishingConnection, CachingVSphere


class CachingVSphereTests(TestCase):

    def setUp(self):
        self.cache = CachingVSphere()
        self.cache._connection = Mock()
        self.vvc = self.cache._connection.ensure_established.return_value

    def test_should_fill_cache_with_vms_returned_by_vvc(self):
        vm_1, vm_2 = Mock(), Mock()
        vm_1.name = "vm-1"
        vm_2.name = "vm-2"
        self.vvc.get_all_vms.return_value = [vm_1, vm_2]

        self.cache.fill()

        self.assertEqual(self.cache.vm_mapping, {"vm-1": vm_1, "vm-2": vm_2})

    def test_should_passthrough_find_by_dns_name_calls(self):
        mock_item = Mock()
        self.vvc.find_by_dns_name.return_value = mock_item

        actual_item = self.cache.find_by_dns_name("any.dns.name")

        self.assertEqual(actual_item, mock_item)
        self.vvc.find_by_dns_name.assert_called_with("any.dns.name", False)

    def test_should_passthrough_find_by_dns_name_calls_when_searching_for_vms(self):
        mock_item = Mock()
        self.vvc.find_by_dns_name.return_value = mock_item

        actual_item = self.cache.find_by_dns_name("any.dns.name", search_for_vms=True)

        self.assertEqual(actual_item, mock_item)
        self.vvc.find_by_dns_name.assert_called_with("any.dns.name", True)


class ConnectionTests(TestCase):

    @patch("isphere.connection._input")
    @patch("isphere.connection.VVC")
    def test_should_ask_for_credentials_when_connecting(self, vvc, _input):
        _input.return_value = "any-input"
        connection = AutoEstablishingConnection()

        connection._connect()

        self.assertEqual(_input.call_args_list, [
                         call('Remote vsphere hostname: '),
                         call('User name for any-input: ')])

    @patch("isphere.connection._input")
    @patch("isphere.connection.VVC")
    def test_should_use_supplied_credentials_when_connecting(self, vvc, _input):
        _input.side_effect = ["any-hostname.domain", "any-user-name"]
        connection = AutoEstablishingConnection()

        connection._connect()

        vvc.assert_called_with("any-hostname.domain")
        vvc.return_value.connect.assert_called_with("any-user-name")

    @patch("isphere.connection.AutoEstablishingConnection._connect")
    def test_should_use_existing_connection(self, connect):
        connection = AutoEstablishingConnection()
        fake_vvc = Mock()
        connection.vvc = fake_vvc

        self.assertEqual(connection.ensure_established(), fake_vvc)
        self.assertEqual(False, connect.called)

    @patch("isphere.connection.AutoEstablishingConnection._connect")
    def test_should_connect_when_no_connection_established(self, connect):
        connection = AutoEstablishingConnection()

        connection.ensure_established()
        self.assertEqual(True, connect.called)
