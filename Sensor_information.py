import argparse
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import atexit
import ssl



def validate_options():
    parser = argparse.ArgumentParser(description='Input parameters')
    parser.add_argument('-d', '--dest_host', dest='dhost', required=True,
                        help='The ESXi destination host IP')
    parser.add_argument('-v', '--vc_host', dest='vchost', required=False,
                        help='VC host IP')
    parser.add_argument('-u', '--VC_user', dest='vcuser', required=True,
                        help='VC username')
    parser.add_argument('-p', '--vc_pass', dest='vcpasswd', required=True,
                        help='VC password')

    args = parser.parse_args()
    return args


def getHostId(content, dhost):
    if content.searchIndex.FindByIp(None, dhost, False):
        host = content.searchIndex.FindByIp(None, dhost, False)
    else:
        host = content.searchIndex.FindByDnsName(None, dhost, False)
    return host


def main():
    opts = validate_options()
    s = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    s.verify_mode = ssl.CERT_NONE
    if opts.vchost:
        print 'Connecting to vCenter Server and collecting sensor information for %s'  %opts.dhost
    else:
        print 'Connecting directly to Host and collecting sensor information for %s'  %opts.dhost
        opts.vchost = opts.dhost
    si = SmartConnect(host=opts.vchost, user=opts.vcuser, pwd=opts.vcpasswd, sslContext=s)
    atexit.register(Disconnect, si)
    content = si.RetrieveContent()
    hostid = getHostId(content, opts.dhost)
    sensorinfo = hostid.runtime.healthSystemRuntime.systemHealthInfo.numericSensorInfo
    print  '{}'.format("Sensor").ljust(10)+ '{}'.format("Sensor Detail").ljust(60)+'{}'.format('Status').ljust(10)+\
              '{}'.format('Reading').ljust(6) + '{}'.format('Units').ljust(10)+'{}'.format('Summary').ljust(20)
    print '****************************************************************************************************************************************'
    for i in sensorinfo:
        j  = i.healthState
        a=str(i.currentReading)
        b= i.baseUnits
        c= i.sensorType
        print '{}'.format(c).ljust(10)+ '{}'.format(i.name).ljust(60)+'{}'.format(j.label).ljust(10)+\
              '{}'.format(a).ljust(6) + '{}'.format(b).ljust(10)+'{}'.format(j.summary).ljust(20)

if __name__  == '__main__':
    main()