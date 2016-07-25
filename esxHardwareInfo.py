from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import argparse
import atexit

def validate_options():
    parser = argparse.ArgumentParser(description='Input parameters')
    parser.add_argument('-s', '--source_host',dest='shost',
                         help='The ESXi source host IP')
    parser.add_argument('-u', '--username',dest='username',
                         help='The ESXi username')
    parser.add_argument('-p', '--password',dest='password',
                         help='The ESXi host password')
    args=parser.parse_args()
    return args

def main():
    opts=validate_options()
    si = SmartConnect(host=opts.shost,user=opts.username,pwd=opts.password )
    atexit.register(Disconnect, si)
    content=si.RetrieveContent()
    hostid=si.content.rootFolder.childEntity[0].hostFolder.childEntity[0].host[0]  #There are easier way to get this info, but this shows the hierarchy 
    hardware=hostid.hardware
    cpuobj=hardware.cpuPkg[0]
    print 'The CPU vendor is %s and the model is %s'  %(cpuobj.vendor,cpuobj.description)
    systemInfo=hardware.systemInfo
    print 'The server hardware is %s %s' %(systemInfo.vendor,systemInfo.model)
    memoryInfo=hardware.memorySize
    print 'The memory size is %d GB' %((memoryInfo)/(1024*1024*1024))



if __name__ == '__main__':
    main()
