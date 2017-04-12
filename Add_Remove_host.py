# This script can add and remove host from a vc into a datacenter. No support to add/remove from cluster
#"The arguments need to be -v <VC_IP> -o <add/remove> -s <host_ips > -d <datacenter> -u <vc_username> -p <vc_password> -e <esx_password>

from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import argparse
import sys
import ssl
import time

def validate_options():
    parser = argparse.ArgumentParser(description='Input parameters')
    parser.add_argument('-v', '--vc_host', dest='vchost', required=True,
                        help='VC host IP')
    parser.add_argument('-u', '--VC_user', dest='vcuser', required=True,
                        help='VC username')
    parser.add_argument('-p', '--vc_pass', dest='vcpasswd', required=True,
                        help='VC password')
    parser.add_argument('-d', dest='datacenter', required=True,
                        help='Datacenter On which operation host need to be added/removed')
    parser.add_argument('-e', dest='esxpass', required=True,
                        help='esx password')
    parser.add_argument('-s', dest='hostIP',nargs='+', required=True,
                        help='esx IP')
    parser.add_argument('-o', dest='operation' , required=True,
                        help='Whether the host need to be added/removed. Expected values are "add" or "remove"')
    args = parser.parse_args()
    return args


def GetDatacenter(dcName, si):
    content = si.RetrieveContent()
    rootFolder = content.rootFolder
    childEntities = rootFolder.childEntity
    for datacenter in childEntities:
        if datacenter.name == dcName:
            dc = datacenter
            return dc
    return


def CreateDatacenter(DCName, si):
    content = si.RetrieveContent()
    rootFolder = content.rootFolder
    return rootFolder.CreateDatacenter(DCName)

def AddHost(hostip,esxpass,dcref,si):
    configspec = vim.host.ConnectSpec()
    configspec.force = True
    configspec.hostName = hostip
    configspec.password = esxpass
    configspec.userName = 'root'
    task = dcref.hostFolder.AddStandaloneHost(spec=configspec, addConnected=True)
    task_status(task, 'Host addition')
    if task.info.state.lower() == 'success':
        print "Operation Complted"
    elif isinstance(task.info.error, vim.fault.SSLVerifyFault) :
        configspec.sslThumbprint = task.info.error.thumbprint
        task = dcref.hostFolder.AddStandaloneHost(spec=configspec, addConnected=True)
        task_status(task, 'Host addition')
    else :
        print 'Host addition failed'
        print task.info.error.msg


def getHostId(content, dhost):
    if content.searchIndex.FindByIp(None, dhost, False):
        host = content.searchIndex.FindByIp(None, dhost, False)
    else:
        host = content.searchIndex.FindByDnsName(None, dhost, False)
    return host

def RemoveHost(hostip,si):
    content = si.RetrieveContent()
    hostId = getHostId(content, hostip)
    task = hostId.DisconnectHost_Task()
    task_status(task, 'Host disconnection')
    task= hostId.parent.Destroy_Task()
    task_status(task, 'Host Removal')


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
    s = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    s.verify_mode = ssl.CERT_NONE
    si = SmartConnect(host=opts.vchost,user=opts.vcuser,pwd=opts.vcpasswd, sslContext=s)
    dcref = GetDatacenter(opts.datacenter, si)

    if not dcref:
        print 'The input datacenter not found in inventory, creating a new datacenter with name %s ' %opts.datacenter
        dcref = CreateDatacenter(opts.datacenter, si)

    for host in opts.hostIP:
        print 'Going to %s host %s from/to VC : %s' % (opts.operation, host, opts.vchost)
        if opts.operation == 'add':
            Add_task = AddHost(host,opts.esxpass,dcref,si)
            exit()
        elif opts.operation == 'remove':
            RemoveHost(host,si)
        else :
            print 'The input operation is incorrect'
            exit()

if __name__ == '__main__':
    main()
