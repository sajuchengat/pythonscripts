author__ = 'saju'
import argparse
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import atexit
import time
import threading


def validate_options():
    parser = argparse.ArgumentParser(description='Input parameters')
    parser.add_argument('-d', '--dest_host', dest='dhost', required=True,
                        help='The ESXi destination host IP')
    parser.add_argument('-v', '--vc_host', dest='vchost', required=True,
                        help='VC host IP')
    parser.add_argument('-u', '--VC_user', dest='vcuser', required=True,
                        help='VC username')
    parser.add_argument('-p', '--vc_pass', dest='vcpasswd', required=True,
                        help='VC password')
    parser.add_argument('--vm_name', dest='vmname', required=True,
                        help='Source VM to be cloned')
    parser.add_argument('--datastore', dest='datastore', required=True,
                        help='Destination datastore for cloned VM')
    parser.add_argument('--num_vms', dest='numvm', type=int, required=True,
                        help='Number of VMs to be created')
    args = parser.parse_args()
    return args


def getHostId(content, dhost):
    if content.searchIndex.FindByIp(None, dhost, False):
        host = content.searchIndex.FindByIp(None, dhost, False)
    else:
        host = content.searchIndex.FindByDnsName(None, dhost, False)
    return host


def getdatastore(content):
    container = content.rootFolder  # starting point to look into
    viewType = [vim.Datastore]  # object types to look for
    recursive = True
    containerView = content.viewManager.CreateContainerView(
        container, viewType, recursive)
    children = containerView.view
    return children


def getdc(objec):
    if isinstance(objec.parent, vim.Datacenter):
        return objec.parent.vmFolder
    else:
        objec = objec.parent
        return getdc(objec)


def linkedvm(child, vmfolder, i, clone_spec):
    vmname = 'clone_%s_vm' % i
    task = child.CloneVM_Task(vmfolder, vmname, clone_spec)
    task_status(task, "clone")


def vmcreateTaskTracker():
    while threading.active_count() > 1:
        print "Waiting for clone to complete"
        print "The number of  on-going clone operations are %d" % (threading.active_count() - 1)
        time.sleep(5)


def task_status(task, operation):
    while task.info.state == ('running' or 'queued'):
        print '%s task  going on , lets wait' % operation
        time.sleep(5)
    if task.info.state.lower() == 'success':
        print '%s creation completed' % operation
    else:
        print 'The %s operaiton failed' % operation
        error = task.info.error
        print error.msg


def main():
    opts = validate_options()
    si = SmartConnect(host=opts.vchost, user=opts.vcuser, pwd=opts.vcpasswd)
    atexit.register(Disconnect, si)
    content = si.RetrieveContent()
    hostid = getHostId(content, opts.dhost)
    print 'Checking the input parameters and validating the host compatibility for linked clone'
    if hostid is None:
        print 'Could not get the host details, verify if the host IP/DNS is correct'
        exit()
    container = content.rootFolder
    viewType = [vim.VirtualMachine]
    recursive = True
    containerView = content.viewManager.CreateContainerView(
        container, viewType, recursive)
    children = containerView.view
    child = None
    if len(children) < 1:
        print 'Could not locate any VM in inventory , exiting'
        exit()
    for vm in children:
        if vm.config.name == opts.vmname.strip():
            child = vm
            break
    if child is None:
        print 'Could not locate the source VM in inventory, exiting'
        exit()
    vmhost = child.runtime.host

    if child.capability.snapshotOperationsSupported is False:
        print 'The VM do not support snapshot, exiting'
        exit()

    vmfolder = getdc(hostid)
    ds = getdatastore(content)
    cspec = vim.vm.RelocateSpec()
    cspec.folder = vmfolder
    cspec.host = hostid
    cspec.diskMoveType = "createNewChildDiskBacking"
    datastore = None
    for idx, ds1 in enumerate(ds):
        if opts.datastore and ds1.info.name == opts.datastore:
            datastore = ds1
            break
    if datastore is None:
        print 'Could not locate the input datastore in the inventory, exiting'
        exit()

    # Validate the clone datastore is accisble to both source and destination
    # host.

    # Thanks to stackoverflow
    if all(x in datastore.host for x in [opts.dhost, vmhost]):  #Thanks to stack overflow
        print 'Both source host and destination host has access to datastore'

    for hosts in datastore.host:
        if hosts.key == hostid and not hosts.mountInfo.accessMode == 'readWrite':
            print 'The destination host has NO write permission in the datastore, exiting'
            exit()
    cspec.datastore = datastore

    print 'Taking snapshot of the source VM, The snapshot is without memory '
    task = child.CreateSnapshot_Task(
        name='snap1', description="This is a snapshot", memory=False, quiesce=True)
    task_status(task, 'snapshot')

    print 'Lets start cloning'
    clone_spec = vim.vm.CloneSpec(location=cspec, powerOn=False, template=False, snapshot=child.snapshot.currentSnapshot,
                                  memory=False)
    count = 0
    for vms in range(0, opts.numvm):
        t = threading.Thread(target=linkedvm, args=(
            child, vmfolder, vms, clone_spec))
        t.start()
        if count > 23:
            vmcreateTaskTracker()
            count = 0
        else:
            count = count + 1
    vmcreateTaskTracker()


if __name__ == '__main__':
    main()
