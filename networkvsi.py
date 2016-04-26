#Script created to capture the number of TX and RX packets sent through each VMNIC in a esxi box in every 10 seconds
#How to run: Copy this script and save it inside esxi. Run the script directly from ESXi



import vmware.vsi as vsi
import time
from collections import defaultdict

def calculate(xyz,nics):
        if xyz[0] == 0 and xyz[1] == 0:
                print "Lets wait for packets to come to %s, sleeping for 10 seconds" %(nics)
        else:
                print "The number of packets received for %s in the last 10 seconds are " %(nics.upper())+ str(xyz[2]-xyz[0])
                print "The number of packets sent from %s in the last 10 seconds are " %(nics.upper())+ str(xyz[3]-xyz[1])


vmnics = defaultdict(list)
no_nics=vsi.list('/net/pNics/')
print "There are total of %d network cards in the machine " %(len(no_nics))
for i in no_nics:
        vmnics[i]=[0,0]
while True:
        for nics in no_nics:
                ReceivePackets=vsi.get('/net/pNics/%s/stats' % nics)['rxpkt']
                vmnics[nics].append(ReceivePackets)
                SendPackets=vsi.get('/net/pNics/%s/stats' % nics)['txpkt']
                vmnics[nics].append(SendPackets)
                calculate(vmnics[nics],nics)
                del vmnics[nics][0:2]
		print "-"*20 +  "Sleeping for 10 seconds" + "-"*20
        time.sleep(10)
