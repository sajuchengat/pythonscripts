'''
script to provide vsan health information for storage controller and controller driver
Python <scriptname> -i <VC-IP>  -c <vsan_cluster_name> -u <VC_username> -p <VC_Password>

To run this script, you need to download the python vsan API's and put them under the python path.
The API's are available for download at https://code.vmware.com/web/sdk/6.6.1/vsan-python

'''

from pyVim.connect import SmartConnect, Disconnect
import argparse
import ssl
import atexit
import vsanapiutils
from pyVmomi import vim, SoapStubAdapter

def validate_options():
    parser = argparse.ArgumentParser(description='Input parameters')
    parser.add_argument('-i', '--VC_IP', dest='VCIP', required=True,
                        help='VC IP')
    parser.add_argument('-c', '--cluster_name', dest='clusterName', required=True,
                        help='Cluster Name')
    parser.add_argument('-u', '--username', dest='username', required=True,
                        help='vCenter username')
    parser.add_argument('-p', '--password', dest='password', required=True,
                        help='vCenter admin password')
    args = parser.parse_args()
    return args

def getClusterInstance(clusterName, serviceInstance):
   content = serviceInstance.RetrieveContent()
   searchIndex = content.searchIndex
   datacenters = content.rootFolder.childEntity
   for datacenter in datacenters:
      cluster = searchIndex.FindChild(datacenter.hostFolder, clusterName)
      if cluster is not None:
         return cluster
   return None


def main():
    opts = validate_options()
    host=opts.VCIP
    user=opts.username
    pwd=opts.password
    cluster=opts.clusterName
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    si = SmartConnect(host=host, user=user, pwd=pwd,sslContext=context)
    atexit.register(Disconnect, si)
    aboutInfo = si.content.about
    apiVersion = vsanapiutils.GetLatestVmodlVersion(host)
    cluster_obj = getClusterInstance(cluster,si)
    if not cluster_obj:
        print 'The required cluster not found in inventory, validate input. Aborting test'
        exit()
    vcMos = vsanapiutils.GetVsanVcMos(si._stub, context=context, version=apiVersion)
    vhs = vcMos['vsan-cluster-health-system']
    healthSummary = vhs.QueryClusterHealthSummary(cluster=cluster_obj, includeObjUuids=True)
    print 'The overall health for the cluster is :'.format().ljust(100) + ':'+ '{}'.format((healthSummary.overallHealth).upper().ljust(10))
    clusterStatus = healthSummary.clusterStatus
    for hosts in healthSummary.hclInfo.hostResults:
        print 'The controller and driver information for host %s is ' %hosts.hostname
        print '-' * 60
        print 'The ESXi version in host {}'.format(hosts.hostname).ljust(100) + ':'+  '{}'.format(hosts.releaseName)
        controllers = hosts.controllers
        for controller in controllers:
            print 'The controller name is'.ljust(100) +':' + '{} '.format(controller.deviceDisplayName)
            print 'The device name used by ESXi is'.ljust(100) +':' +'{}'.format(controller.deviceName)
            print 'The device PCI information is'.ljust(100) + ':' + '{} / {} / {}'.format(controller.vendorId, controller.subVendorId,controller.subDeviceId)
            usedByVsan= controller.usedByVsan
            if usedByVsan:
                print 'The diskgroups connected to this controller is'.ljust(100) +':'+ '{}'.format(controller.diskMode)
                print 'Is this controller listed in HCL'.ljust(100) +':'+ '{}'.format(controller.deviceOnHcl)
                print 'The firmware version on the controller is'.ljust(100) +':'+ '{}'.format(controller.fwVersion)
                supported=controller.deviceOnHcl
                if not supported:
                    print 'The controller device is not suported as per HCL!!!!'.upper()
                else :
                    fwVersionSupported=controller.fwVersionSupported
                    if not fwVersionSupported:
                        print 'The firmware version on the controller is not supported !!!'.upper()
                    else:
                        print 'The firmware version is supported..'.upper()

                print 'The driver which is loaded for this controller is'.ljust(100) +':'+ '{}'.format(controller.driverName)
                print 'The driver version loaded currently is'.ljust(100) + ':' + '{}'.format(controller.driverVersion)
                current_driver=controller.driverVersion
                if len(controller.driversOnHcl) > 0:
                    driver_firmware = {}
                    drivers = controller.driversOnHcl
                    for driver in drivers:
                        if current_driver == driver:
                            print 'The installed driver is supported as per HCL'
                            break
                        driver_firmware[driver.driverVersion] = driver.fwVersion
                    if len(driver_firmware.keys()) == len(drivers):
                        print 'The installed driver version not supported as per HCL !!!'.upper()
                        print 'For this controller following drivers and corrosponding firmwares are supported..'
                        for k,v in driver_firmware.iteritems():
                            print 'Driver: {}'.format(k).ljust(100) +':'+ 'Firmware: {}'.format(v)
                else:
                    print 'The loaded driver is not supported by VSAN..!!'.upper()
            else:
                print 'This controller is not used by vSAN in this host'

    print '\n'
    for hosts in healthSummary.clusterVersions.hostResults:
        print 'The vsan health version on  host {}'.format(hosts.hostname).ljust(100)+ ':' + '{}'.format( hosts.version)
    for hosts in clusterStatus.trackedHostsStatus:
        print 'The vSAN Health service installation status for host {}'.format(hosts.hostname).ljust(100) + ':' + '{}'.format((hosts.status).upper())
    print 'The health service installation status for the cluster {} is '.format(cluster).ljust(
        100) + ':' + '{}'.format((clusterStatus.status).upper()).ljust(10)


if __name__ == '__main__':
    main()
