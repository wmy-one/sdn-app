#!/usr/bin/env python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel
import time
import os

class SimpleTopo(Topo):
    "simple switch topo"
    def build(self):
        print"***Creating nodes"

        s1=self.addSwitch('s1')
        s2=self.addSwitch('s2')
        s3=self.addSwitch('s3')

        h1=self.addHost('h1',mac='00:00:00:00:00:01',ip='10.0.0.1/16')
        h2=self.addHost('h2',mac='00:00:00:00:00:02',ip='10.0.0.2/16')
        vm=self.addHost('vm',mac='00:00:00:00:00:10',ip='10.0.0.10/16')
        server=self.addHost('server',mac='00:00:00:00:00:ff',ip='10.0.0.255/16')

        print"***Creating links"
        #switchLinkOpts=dict(bw=10,delay='1ms')
        #hostLinkOpts=dict(bw=100)

        self.addLink(h1,s1,0,1)
        self.addLink(h2,s2,0,1)
        self.addLink(server,s3,0,1)
        self.addLink(s1,s3,2,2)
        self.addLink(s2,s3,2,3)
        self.addLink(vm,s1,0,3)              

def topology():
    "Create a network. "
    topo = SimpleTopo()
    net=Mininet(topo=topo,controller=RemoteController)
    
    print"***Building network"
    net.start()
    CLI(net)
    
    print"***Stopping network"
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()
