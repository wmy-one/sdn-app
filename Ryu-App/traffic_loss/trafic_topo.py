#!/usr/bin/python
 
from mininet.net import Mininet
from mininet.node import Node
from mininet.link import TCLink
from mininet.log import  setLogLevel, info
from threading import Timer
from mininet.util import quietRun
from time import sleep
 
def myNet(cname='controller', cargs='-v ptcp:'):
    "Create network from scratch using Open vSwitch."
    info( "*** Creating nodes\n" )
    controller = Node( 'c0', inNamespace=False )
    switch = Node( 's0', inNamespace=False )
    switch1 = Node( 's1', inNamespace=False )
    h0 = Node( 'h0' )
    h1 = Node( 'h1' )
   
    info( "*** Creating links\n" )
    linkopts0=dict(bw=100, delay='1ms', loss=0)
    linkopts1=dict(bw=100, delay='1ms', loss=10)
    link0=TCLink( h0, switch, **linkopts0)
    link1 = TCLink( switch, switch1, **linkopts1)    
    link2 = TCLink( h1, switch1, **linkopts0)
    #print link0.intf1, link0.intf2
    link0.intf2.setMAC("0:0:0:0:0:1")
    link1.intf1.setMAC("0:0:0:0:0:2")
    link1.intf2.setMAC("0:1:0:0:0:1")
    link2.intf2.setMAC("0:1:0:0:0:2")
 
    info( "*** Configuring hosts\n" )
    h0.setIP( '192.168.123.1/24' )
    h1.setIP( '192.168.123.2/24' )
      
    info( "*** Starting network using Open vSwitch\n" )
    switch.cmd( 'ovs-vsctl del-br dp0' )
    switch.cmd( 'ovs-vsctl add-br dp0' )
    switch1.cmd( 'ovs-vsctl del-br dp1' )
    switch1.cmd( 'ovs-vsctl add-br dp1' )
 
    controller.cmd( cname + ' ' + cargs + '&' )    
    for intf in switch.intfs.values():
        print intf
        print switch.cmd( 'ovs-vsctl add-port dp0 %s' % intf )
    for intf in switch1.intfs.values():
        print intf
        print switch1.cmd( 'ovs-vsctl add-port dp1 %s' % intf )
  
    # Note: controller and switch are in root namespace, and we
    # can connect via loopback interface
    switch.cmd( 'ovs-vsctl set-controller dp0 tcp:127.0.0.1:6633' )
    switch1.cmd( 'ovs-vsctl set-controller dp1 tcp:127.0.0.1:6633' )
 
    info( '*** Waiting for switch to connect to controller' )
    while 'is_connected' not in quietRun( 'ovs-vsctl show' ):
        sleep( 1 )
        info( '.' )
    info( '\n' )
 
    #info( "*** Running test\n" )
    h0.cmdPrint( 'ping -Q 0x64 -c 20 ' + h1.IP() )
   
    sleep( 1 )
    info( "*** Stopping network\n" )
    controller.cmd( 'kill %' + cname )
    switch.cmd( 'ovs-vsctl del-br dp0' )
    switch.deleteIntfs()
    switch1.cmd( 'ovs-vsctl del-br dp1' )
    switch1.deleteIntfs()
    info( '\n' )
 
if __name__ == '__main__':
    setLogLevel( 'info' )
    info( '***create a topology example as below show***\n' )
    print '''
               h0------
                      |
                      s0
                      |------c0
                      s1
                      |
               h1------'''           
    Mininet.init()
    myNet()
