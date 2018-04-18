#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import RemoteController,OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
import time
import os


def topology():
    "Create a network.  switch=OVSKernelSwitch"
    net=Mininet(controller=RemoteController)
        
    print"***Creating nodes"
    h1=net.addHost('h1',mac='00:00:00:00:00:01',ip='10.0.0.1/16')
    h2=net.addHost('h2',mac='00:00:00:00:00:02',ip='10.0.0.2/16')
    server=net.addHost('server',mac='00:00:00:00:00:20',ip='10.0.0.255/16')
    s1=net.addSwitch('s1')
    s2=net.addSwitch('s2')
    s3=net.addSwitch('s3')
    c0=net.addController('c0',controller=RemoteController)
    vm=net.addHost('vm',mac='00:00:00:00:00:10',ip='10.0.0.10/16')
    
    print"***Creating links"
    #switchLinkOpts=dict(bw=10,delay='1ms')
    #hostLinkOpts=dict(bw=100)
        
    net.addLink(h1,s1,0,1)
    net.addLink(h2,s2,0,1)
    net.addLink(server,s3,0,1)
    net.addLink(s1,s3,2,2)
    net.addLink(s2,s3,2,3)
    net.addLink(vm,s1,0,3)
        
#print"***Removing former QoS&Queue"
#os.popen("ovs-vsctl --all destroy qos")
#os.popen("ovs-vsctl --all destroy queue")
    
    print"***Building network"
    net.build()
    s1.start([c0])
    s2.start([c0])
    s3.start([c0])
    
    print"***Starting network"
    c0.start()
        
    print"\n***Stage 1:VM connected to s1"
    print"***Type'exit'to Stage"
    CLI(net)
    print"***Migrating VM"
    s1.detach('s1-eth3')
    time.sleep(2)
    s2.attach('s1-eth3')
    print"\n***Stage 2:VM connected to s2"
    CLI(net)
    
    print"***Stopping network"
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()


