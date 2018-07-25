from pyVim.connect import SmartConnect, Disconnect
import argparse
import ssl
import atexit
from pyVmomi import vim
import time

'''
Script usage : python vm_reconfig.py -i <vCenter IP>  -u <vCenter Admin username>  -p <vCenter admin password>  -v <VM1 VM2 VM3>
Note: VMnames mentioned after -v option should be seperated using space
'''

def validate_options():
    parser = argparse.ArgumentParser(description='Input parameters')
    parser.add_argument('-i', '--VC_IP', dest='VCIP', required=True,help='VC IP')
    parser.add_argument('-u', '--vc_user', dest='vcuser', required=True,help='VC admin username')
    parser.add_argument('-p', '--vc_pass', dest='vcpasswd', required=True,help='VC admin password')
    parser.add_argument('-v', nargs='+', dest='vmname', required=True,help='VM name with Coma seperated')
    args = parser.parse_args()
    return args

def task_status(task, operation):
    while task.info.state == ('running' or 'queued'):
        print '%s   going on , lets wait' % operation
        time.sleep(5)
    if task.info.state.lower() == 'success':
        print '%s  completed' % operation
    else:
        print 'The %s operaiton failed' % operation
        #print task
        error = task.info.error
        print error.msg

def vm_reconfig(vmname,children):
    for vm in children:
        if vm.config.name in vmname:
            child= vm
            vmspec=vim.vm.ConfigSpec(alternateGuestName="Microsoft Windows Server 2008 R2 (64-bit)",guestId="windows7Server64Guest")
            task=child.ReconfigVM_Task(vmspec)
            task_status(task,"Reconfigure VM:  %s" %vm.config.name)
            vmname.remove(vm.config.name)
    print 'Following VMs given in the input were not found in the inventory'
    for vms in vmname:
        print vms

def main():
    opts = validate_options()
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    si = SmartConnect(host=opts.VCIP, user=opts.vcuser, pwd=opts.vcpasswd,sslContext=context)
    print 'Logged into the vCenter'
    atexit.register(Disconnect, si)
    content = si.RetrieveContent()
    container = content.rootFolder
    viewType = [vim.VirtualMachine]
    recursive = True
    containerView = content.viewManager.CreateContainerView(
        container, viewType, recursive)
    children = containerView.view
    if len(children) < 1:
        print 'Could not locate any VM in inventory , exiting'
        exit()
    vm_reconfig(opts.vmname,children)


if __name__ == '__main__':
    main()

