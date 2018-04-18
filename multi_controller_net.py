#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import Link, Intf, TCLink
from mininet.topo import Topo

import logging
import os

def multiControllerNet(con_num=3, sw_num=9, host_num=18):
    "create a network with controller-3, switch-3/domin, host-2/switch!"

    controller_list = []
    switch_list = []
    host_list = []

    net = Mininet(controller=None, switch=OVSSwitch, link=TCLink)

    for i in xrange(con_num):
        name = "c%d" %i
        c = net.addController(name, controller=RemoteController, port=5501+i)
        controller_list.append(c)
        print "***Create controller %s" %name

    print "***Create switches"
    switch_list = [net.addSwitch('s%d' %n) for n in xrange(sw_num)]

    print "***Create hosts"
    host_list = [net.addHost('h%d' %m) for m in xrange(host_num)]

    print "***Create links of host2switch."
    for i in xrange(sw_num):
        net.addLink(switch_list[i], host_list[i*2])
        net.addLink(switch_list[i], host_list[i*2+1])

    print "***Create interior links of switch2switch."
    for i in xrange(0, sw_num, sw_num/con_num):
        # create loop links of switch2switch.
        """
        for j in xrange(sw_num/con_num):
            for k in xrange(sw_num/con_num):
                if j > k and j != k :
                    net.addLink(switch_list[i+j], switch_list[i+k])
        """
        net.addLink(switch_list[i], switch_list[i+1])
        net.addLink(switch_list[i+1], switch_list[i+2])

    print "Create intra links of switch2switch."
    # 0-2 3-5 6-8
    # domain 0-->others
    net.addLink(switch_list[1], switch_list[3])
    #net.addLink(switch_list[2], switch_list[8])

    # domain 1-->others
    net.addLink(switch_list[4], switch_list[6])

    print "***Starting network."
    net.build()
    for c in controller_list:
        c.start()

    _No = 0
    for i in xrange(0, sw_num, sw_num/con_num):
        for j in xrange(sw_num/con_num):
            switch_list[i+j].start([controller_list[_No]])
        _No +=1

    print "***Starting CLI"
    CLI(net)

    print "***Stopping network"
    net.stop()

if __name__ == "__main__":
    setLogLevel('info')  # for CLI output
    multiControllerNet(con_num=3, sw_num=9, host_num=18)


