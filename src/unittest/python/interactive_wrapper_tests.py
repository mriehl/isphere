#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>
#  This work is free. You can redistribute it and/or modify it under the
#  terms of the Do What The Fuck You Want To Public License, Version 2,
#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.
#

from unittest import TestCase
from mock import Mock

from isphere.interactive_wrapper import (
    VM,
    VVC,
    ESX,
    get_all_vms_in_folder,
    NotFound
)


class VMTests(TestCase):

    def setUp(self):
        self.raw_vm = Mock()
        self.wrapped_vm = VM(self.raw_vm)

    def test_should_passthrough_unwrapped_attributes(self):
        self.assertEqual(self.wrapped_vm.anything, self.raw_vm.anything)

    def test_should_return_interface_when_one_matches(self):
        foo_mock = lambda: None
        foo_mock.name = "foo"
        bar_mock = lambda: None
        bar_mock.name = "bar"
        self.raw_vm.network = [foo_mock, bar_mock]

        bar = lambda n: n.name == "bar"
        actual = self.wrapped_vm.get_first_network_interface_matching(bar)

        self.assertEqual(actual, bar_mock)

    def test_should_return_first_interface_when_several_match(self):
        aha_mock = lambda: None
        aha_mock.name = "aha"
        foo_mock_1 = lambda: None
        foo_mock_1.name = "foo"
        bar_mock = lambda: None
        bar_mock.name = "bar"
        foo_mock_2 = lambda: None
        foo_mock_2.name = "foo"
        self.raw_vm.network = [aha_mock, foo_mock_1, bar_mock, foo_mock_2]

        foo = lambda n: n.name == "foo"
        actual = self.wrapped_vm.get_first_network_interface_matching(foo)

        self.assertEqual(actual, foo_mock_1)


class ESXTests(TestCase):

    def setUp(self):
        self.raw_esx = Mock()
        self.raw_esx.name = "esx-name"
        self.wrapped_esx = ESX(self.raw_esx)

    def test_should_passthrough_unwrapped_attributes(self):
        self.assertEqual(self.wrapped_esx.anything, self.raw_esx.anything)

    def test_should_equal_to_esx_with_same_name(self):
        other_raw_esx = Mock()
        other_raw_esx.name = "esx-name"
        other_esx = ESX(other_raw_esx)

        self.assertTrue(self.wrapped_esx == other_esx)

    def test_should_not_equal_to_esx_with_other_name(self):
        other_raw_esx = Mock()
        other_raw_esx.name = "other-esx-name"
        other_esx = ESX(other_raw_esx)

        self.assertFalse(self.wrapped_esx == other_esx)

    def test_should_raise_when_number_of_cores_not_in_resources(self):
        resources = []
        self.raw_esx.licensableResource.resource = resources

        self.assertRaises(RuntimeError, self.wrapped_esx.get_number_of_cores)

    def test_should_return_number_of_cores_when_in_resources(self):
        resource_1 = Mock()
        resource_1.key = "weLoveCamelCase"
        resource_2 = Mock()
        resource_2.key = "numCpuCores"
        resource_2.value = 42
        resource_3 = Mock()
        resource_3.key = "someOtherKey"

        resources = [resource_1, resource_2, resource_3]
        self.raw_esx.licensableResource.resource = resources

        self.assertEquals(self.wrapped_esx.get_number_of_cores(), 42)


class GetAllVMInFolderTests(TestCase):

    def test_should_resolve_deep_nesting(self):
        vm_1 = lambda: None
        vm_1.name = "vm-1"
        vm_2 = lambda: None
        vm_2.name = "vm-2"
        level_2_nesting = [vm_2]
        child_folder = Mock()
        child_folder.childEntity = level_2_nesting
        level_1_nesting = [vm_1, child_folder]
        root_folder = Mock()
        root_folder.childEntity = level_1_nesting

        actual_vms = [vm for vm in get_all_vms_in_folder(root_folder)]

        self.assertEqual(len(actual_vms), 2)
        self.assertEqual(actual_vms[0].raw_vm, vm_1)
        self.assertEqual(actual_vms[1].raw_vm, vm_2)


class VVCTests(TestCase):

    def setUp(self):
        self.vvc_mock = Mock(VVC, service_instance=Mock())
        self.mock_search = self.vvc_mock.service_instance.RetrieveContent.return_value.searchIndex.FindByDnsName

    def test_should_return_item_when_found_by_searching(self):
        mock_item = Mock()
        self.mock_search.return_value = mock_item

        actual_item = VVC.find_by_dns_name(self.vvc_mock, "any.dns.name")

        self.assertEqual(actual_item, mock_item)

    def test_should_raise_not_found_when_searching_fails(self):
        self.mock_search.return_value = None

        self.assertRaises(NotFound,
                          VVC.find_by_dns_name, self.vvc_mock, "any.dns.name")

    def test_should_passthrough_search_call_with_disabled_vm_search_by_default(self):
        VVC.find_by_dns_name(self.vvc_mock, "any.dns.name")

        self.mock_search.assert_called_with(vmSearch=False, dnsName='any.dns.name')

    def test_should_passthrough_search_call_with_enabled_vm_search_when_specified(self):
        VVC.find_by_dns_name(self.vvc_mock, "any.dns.name", search_for_vms=True)

        self.mock_search.assert_called_with(vmSearch=True, dnsName='any.dns.name')

    def test_should_proxy_service_when_it_exists(self):
        self.vvc_mock.service_instance_content = Mock()
        self.vvc_mock.service_instance_content.any_service_name = Mock()

        self.assertEqual(VVC.get_service(self.vvc_mock, "any_service_name"),
                         self.vvc_mock.service_instance_content.any_service_name)

    def test_should_raise_when_service_does_not_exist(self):
        self.vvc_mock.service_instance_content = object()

        self.assertRaises(NotFound,
                          VVC.get_service, self.vvc_mock, "any_other_service_name")

    def test_should_get_custom_attributes_mapping(self):
        fields = [Mock(key="any-key"),
                  Mock(key="any-other-key")]
        fields[0].name = "any-name"
        fields[1].name = "any-other-name"
        self.vvc_mock.get_service.return_value = Mock(field=fields)

        actual_mapping = VVC.get_custom_attributes_mapping(self.vvc_mock)

        self.assertEqual(actual_mapping,
                         {"any-key": "any-name",
                          "any-other-key": "any-other-name"})
