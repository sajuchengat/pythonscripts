
# Script to do multiple migrations back and forth. Initially for vmotion only.
# No check for vmotion network validation or shared datastore. These are todo items
#usage:  -v <VC_IP>  -i <iterations> -g <vm_name>  -d <datacenter>  -u <vc_username> -p <vc_password> -s <host1> -f <host2>
author__ = 'saju'


import argparse
import time
import ssl
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim


def validate_options():
    parser = argparse.ArgumentParser(description='Input parameters')
    parser.add_argument('-v', '--vc_host', dest='vchost', required=True,
                        help='VC host IP')
    parser.add_argument('-u', '--VC_user', dest='vcuser', required=True,
                        help='VC username')
    parser.add_argument('-p', '--vc_pass', dest='vcpasswd', required=True,
                        help='VC password')
    parser.add_argument('-d', dest='datacenter', required=True,
                        help='Datacenter On which operation host need to be done')
    parser.add_argument('-c', dest='cluster', required=False,
                        help='Cluster On which operation host need to be done')
    parser.add_argument('-s', dest='shost', required=True,
                        help='source host which migration to be started')
    parser.add_argument('-f', dest='dhost', required=True,
                        help='Destination host to which migration to happen')
    parser.add_argument('-g', dest='guest', required=True,
                        help='Guest OS name')
    parser.add_argument('-i', dest='iterations' , required=True,
                        help='Number of times the migration need to be repeated')
    args = parser.parse_args()
    return args


def getDatacenter(dcName, content):
    rootFolder = content.rootFolder
    childEntities = rootFolder.childEntity
    for datacenter in childEntities:
        if datacenter.name == dcName:
            dc = datacenter
            return dc
    return

def getVM(content,guest):
    container = content.rootFolder
    viewType = [vim.VirtualMachine]
    recursive = True
    containerView = content.viewManager.CreateContainerView(
        container, viewType, recursive)
    children = containerView.view
    child = None
    if len(children) < 1:
        print 'Could not locate any VM in inventory , exiting'
        return
    for vm in children:
        if vm.config.name == guest.strip():
            child = vm
            return child
    if child is None:
        print 'Could not locate the source VM in inventory, exiting'
        return

def getHostId(dcRef, content, dhost):
    if content.searchIndex.FindByIp(dcRef, dhost, False):
        host = content.searchIndex.FindByIp(dcRef, dhost, False)
    else:
        host = content.searchIndex.FindByDnsName(dcRef, dhost, False)
    return host

def task_status(task, operation):
    while task.info.state == ('running' or 'queued'):
        print '%s task  going on , lets wait' % operation
        time.sleep(5)
    if task.info.state.lower() == 'success':
        print '%s operation completed' % operation
    else:
        print 'The %s operaiton failed' % operation
        error = task.info.error
        print error.msg

def main():
    opts = validate_options()
    s = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    s.verify_mode = ssl.CERT_NONE
    si = SmartConnect(host=opts.vchost,user=opts.vcuser,pwd=opts.vcpasswd, sslContext=s)
    content = si.RetrieveContent()
    dcRef = getDatacenter(opts.datacenter, content)
    if dcRef is None:
        print 'The datacenter is not in inventory, exiting '
        exit()
    vmRefs = getVM(content, opts.guest)
    if not vmRefs:
        print "Could not locate the VM in inventory, exiting"
        exit()
    srcHostCr = getHostId(dcRef,content,opts.shost)
    destHostCr = getHostId(dcRef,content,opts.dhost)
    currenthost  = vmRefs.runtime.host
    if srcHostCr == currenthost:
        print ' The VM is in expected host'
    elif currenthost == destHostCr:
        srcHostCr, destHostCr = destHostCr, srcHostCr
    else :
        print 'The input VM is located in a different host, please check, exiting.'
        exit()
    count = 0
    while count < int(opts.iterations):
            task=vmRefs.MigrateVM_Task(host=destHostCr,priority='highPriority')
            task_status(task, 'Migration')
            srcHostCr,destHostCr = destHostCr, srcHostCr
            count += 1
            print "Number of migration completed : %d" %count

if __name__ == '__main__':
    main()

