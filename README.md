isphere
=======

REPL to work with vmware vsphere


Why does this exist?
--------------------

* The web interface for vSphere is in flash and does some version pinning - this it does not work on my linux computer with firefox.
* Web interfaces are awkward to use for batch operations
* Because it's easy, fast, tested and extensible. While the primary targeted use is interactive, everything you do interactively can be automated easily, since isphere also exposes an easy to use [python API](http://max.riehl.io/isphere/) with exactly the same capabilities and usage.


How does this solve the problems above?
---------------------------------------
This is a platform independent REPL (mac, windows, linux) thanks to the [pyVmomi](https://pypi.python.org/pypi/pyvmomi) library, usable from your favourite terminal.


Usage
-----

## How does it work?

Starting the application loads up a REPL (read eval print loop). You can see what's possible by running
```
isphere > help
```

This will list all the available commands. You can then obtain command-specific help with `help COMMAND`, e.G.

```
isphere > help list_vm
Usage: list [pattern1 [pattern2]...]
        List the vm names matching the given ORed name patterns.
        Sample usage:
        * `list dev.* ...ybc01`
        * `list`
        * `list .*`
```

## Command design

The general idea (for most commands!) is:

```
<command> <patterns>
```

The patterns given are regular expressions that will be ORed to obtain the matching items by name.

Let's say you want to know which VMs start with "sdo" OR have a name that consists of exactly three characters: (remember that `.` means any character, `^` means start of line and `$` means end of line)

```
isphere > list_vm ...sdo ^...$
tuvsdo01
devsdo02
opa
```

You can omit the patterns if you want to operate on all available items. For example showing info for all vms:

```
isphere > info_vm
```

Some commands require more than just patterns to work.
In that case, the `!` (bang) character is used to delimit patterns and further arguments.

The `eval` series of commands for example allows to call any native methods you want on the objects from the vmware API.

The usage is
```
isphere > eval_<type> <patterns> ! <statement>
```
where "statement" is exactly one valid python statement. The statement will be able to use the object `<type>` (but not much more).

Finding out the name of all ESXis that start with `foo` is done with:

```
isphere > eval_esx foo ! esx.name
```

Note that the above is functionally equivalent to `list_esx foo`. You can explore the API by using the dir() function on the objects, e.G.

```
isphere > eval_vm devytc97 ! dir(vm)
----------------------------------- devytc97 -----------------------------------
['AcquireMksTicket', 'AcquireTicket', 'Answer', 'AnswerVM', 'Array', 'CheckCustomizationSpec', 'Clone', 'CloneVM_Task', 'ConsolidateDisks', 'ConsolidateVMDisks_Task', 'CreateScreenshot', 'CreateScreenshot_Task', 'CreateSecondary', 'CreateSecondaryVM_Task', 'CreateSnapshot', 'CreateSnapshot_Task', 'Customize', 'CustomizeVM_Task', 'DefragmentAllDisks', 'Destroy', 'Destroy_Task', 'DisableSecondary', 'DisableSecondaryVM_Task', 'EnableSecondary', 'EnableSecondaryVM_Task', 'EstimateStorageForConsolidateSnapshots_Task', 'EstimateStorageRequirementForConsolidate', 'ExportVm', 'ExtractOvfEnvironment', 'MakePrimary', 'MakePrimaryVM_Task', 'MarkAsTemplate', 'MarkAsVirtualMachine', 'Migrate', 'MigrateVM_Task', 'MountToolsInstaller', 'PowerOff', 'PowerOffVM_Task', 'PowerOn', 'PowerOnVM_Task', 'PromoteDisks', 'PromoteDisks_Task', 'QueryChangedDiskAreas', 'QueryFaultToleranceCompatibility', 'QueryUnownedFiles', 'RebootGuest', 'ReconfigVM_Task', 'Reconfigure', 'RefreshStorageInfo', 'Reload', 'ReloadFromPath', 'Relocate', 'RelocateVM_Task', 'RemoveAllSnapshots', 'RemoveAllSnapshots_Task', 'Rename', 'Rename_Task', 'Reset', 'ResetGuestInformation', 'ResetVM_Task', 'RevertToCurrentSnapshot', 'RevertToCurrentSnapshot_Task', 'SetCustomValue', 'SetDisplayTopology', 'SetScreenResolution', 'ShutdownGuest', 'StandbyGuest', 'StartRecording', 'StartRecording_Task', 'StartReplaying', 'StartReplaying_Task', 'StopRecording', 'StopRecording_Task', 'StopReplaying', 'StopReplaying_Task', 'Suspend', 'SuspendVM_Task', 'Terminate', 'TerminateFaultTolerantVM', 'TerminateFaultTolerantVM_Task', 'TerminateVM', 'TurnOffFaultTolerance', 'TurnOffFaultToleranceForVM_Task', 'UnmountToolsInstaller', 'Unregister', 'UnregisterVM', 'UpgradeTools', 'UpgradeTools_Task', 'UpgradeVM_Task', 'UpgradeVirtualHardware', '_GetMethodInfo', '_GetMethodList', '_GetMoId', '_GetPropertyInfo', '_GetPropertyList', '_GetServerGuid', '_GetStub', '_InvokeAccessor', '_InvokeMethod', '__class__', '__delattr__', '__dict__', '__doc__', '__eq__', '__format__', '__getattribute__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_methodInfo', '_moId', '_propInfo', '_propList', '_serverGuid', '_stub', '_version', '_wsdlName', 'alarmActionsEnabled', 'availableField', 'capability', 'config', 'configIssue', 'configStatus', 'customValue', 'datastore', 'declaredAlarmState', 'disabledMethod', 'effectiveRole', 'environmentBrowser', 'guest', 'guestHeartbeatStatus', 'layout', 'layoutEx', 'name', 'network', 'overallStatus', 'parent', 'parentVApp', 'permission', 'recentTask', 'reloadVirtualMachineFromPath_Task', 'resourceConfig', 'resourcePool', 'rootSnapshot', 'runtime', 'setCustomValue', 'snapshot', 'storage', 'summary', 'tag', 'triggeredAlarmState', 'value']
```

which could lead to

```
isphere > eval_vm devytc97 ! vm.PowerOff()
```

if you wanted to power off the machine.
You can then use the pattern feature to turn off all vms that start with old:

```
isphere > eval_vm ^old.*$ ! vm.PowerOff()
```


## Quality of life features (powered by cmd2)
### History search

Works, just like in bash (Ctrl+R)

### Shell commands

```
isphere > shell ls
Desktop  Documents  Downloads  local  media  Music
```

or
```
isphere > ! ls
Desktop  Documents  Downloads  local  media  Music
```

### Output redirection
```
isphere > list_vm ...opa > opa_vms.txt
isphere > ! ls
opa_vms.txt
```

### Pipes
```
isphere > list_vm ...opa
devopa01
tuvopa02
tuvopa01
isphere > list_vm ...opa | wc -l
3
```

### Python shell
```
isphere > py
Python x.x.x (Jan 22 2014)
[GCC x.x.x (Red Hat x.x.x-x)] on xxx
Type "help", "copyright", "credits" or "license" for more information.
(VSphereREPL)
        py <command>: Executes a Python command.
        py: Enters interactive Python mode.
>>> all_vm_names = self.cache.list_cached_vms()
>>> devytc_vm_names = [vm_name for vm_name in self.cache.list_cached_vms() if "devytc" in vm_name]
>>> len(devytc_vm_names) 
5
>>> devytc_vm_names[0] 
'devytc98'
>>> devytc98_vm = self.cache.retrieve_vm("devytc98")
>>> devytc98_vm.ResetVM()
```

Note that the python shell is persistent in an isphere session. So quitting the python shell above with Ctrl+D, I would be able to relaunch a python shell and continue using the variable "devytc98_vm".

### History saving, loading

Save the commands from your session (or the last n) to a file:

```
isphere > save *
Saved to command.txt
isphere > shell cat command.txt
info_vm devytc97
eval_dvs ! dvs.name
save *
```

Run the command file when you want:

```
isphere > ! cat command.txt
list_vm devytc
info_vm devytc97
isphere > load command.txt
devytc98
devytc99
devytc96
devytc97
devytc95
----------------------------------------------------------------------
Name: devytc97
ESXi Host: xxx
Path to VM: [xxx] xxx/xxx.vmx
BIOS UUID: xxx-xxx-xxx
CPUs: 1
MemoryMB: 2048
Guest PowerState: running
Guest Full Name: xxx
Guest Container Type: xxx
Container Version: vmx-xx
Contact User ID: xxx
```

License
-------

Licensed under the WTFPL, but for some parts of the code individual licenses apply (check the file header). Those files are all isolated in the package `isphere.thirdparty`.
