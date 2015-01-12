isphere
=======

REPL to work with vmware vsphere


Why does this exist?
--------------------

* The web interface for vSphere is in flash and does some version pinning - this it does not work on my linux computer with firefox.
* Web interfaces are awkward to use for batch operations


How does this solve the problems above?
---------------------------------------
This is a platform independent REPL (mac, windows, linux) thanks to the [pyVmomi](https://pypi.python.org/pypi/pyvmomi) library, usable from your favourite terminal.


Usage
-----

### Help
`help` will provide an overview of available commands.
`help <command>` will provide detailed help for a command.

### Concepts
#### Long lived sessions
Long lived session that fetches all data on startup (and manually with the `reload` command).

#### ORed name patterns
Operations on ORed name patterns, for example "shutdown all VMs starting with foo or ending with bar" is done with:
```
reboot_vm ^foo bar$
Asking foobarvm to reboot
Asking foo to reboot
Asking bar to reboot
Asking vmbar to reboot
```

No pattern means "everything", so
```
list_vm
```
will list all VM names.
There is a protection against mistakes like rebooting your entire datacenter though :-)

#### Python knowledge usable to do custom things.
It's possible to inline python code to act on virtual machines or host systems (ESXis).
The basic idea is that you can write one statement which will be able to use the virtual machine or host system object.

For VM evals, you can use the object `vm` (both in local and global scope, for lambdas for example).
For ESXi evals, you can use the object `esx`.


Calling reboot on all VMs containing the substring "baz":
```
eval_vm baz ! vm.RebootGuest()
```


Finding out the overall status of all ESXi host systems:
```
eval_esx ! esx.overallStatus
------------------------- esx-3 -------------------------
green
------------------------- esx-2 -------------------------
yellow
[...]
```


Note that you can decide to not produce any output from `eval` by calling the function `no_output`. 

The following will yield all VM names where the vm name starts with `prefix`:

```
eval_vm ! vm.name if vm.name.lower().startswith("prefix") else no_output()
No pattern specified - you're doing this to all 42 VMs. Proceed? (y/N) y
prefix-vm1
prefixvm2
Prefixed VM
```
It's obviously braindead since you should do this with a pattern, but for demonstration purposes it will do.

For example we can find out the overall status of our ESXis that are not in good shape:

```
isphere > eval_esx ! esx.overallStatus if esx.overallStatus != "green" else no_output()
No pattern specified - you're doing this to all 8 esx. Proceed? (y/N) y
------------------------- esx-4 -------------------------
yellow
------------------------- esx-5 -------------------------
red
```


License
-------

Licensed under the WTFPL, but for some parts of the code individual licenses apply (check the file header). Those files are all isolated in the package `isphere.thirdparty`.
