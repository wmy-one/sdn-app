#!/usr/bin/python
 
from mininet.net import Mininet
from mininet.node import Node
from mininet.link import TCLink
from mininet.log import  setLogLevel, info
from threading import Timer
from mininet.util import quietRun
from time import sleep
from mininet.cli import CLI
 
def myNet(cname='controller', cargs='-v ptcp:'):
    "Create network from scratch using Open vSwitch."
    info( "*** Creating nodes\n" )
    controller = Node( 'c0', inNamespace=False )
    s0 = Node( 's0', inNamespace=False )
    s1 = Node( 's1', inNamespace=False )
    h0 = Node( 'h0' )
    h1 = Node( 'h1' )
    h2 = Node( 'h2' )
 
    info( "*** Creating links\n" )
    linkopts0=dict(bw=10, delay='1ms', loss=0)
    TCLink( h0, s0, **linkopts0)
    TCLink( h1, s0, **linkopts0)
    TCLink( s0, s1, **linkopts0)
    TCLink( s1, h2, **linkopts0)
 
 
    info( "*** Configuring hosts\n" )
    h0.setIP( '192.168.123.1/24' )
    h1.setIP( '192.168.123.2/24' )
    h2.setIP( '192.168.123.3/24' )
               
    info( "*** Starting network using Open vSwitch\n" )
    s0.cmd( 'ovs-vsctl del-br dp0' )
    s0.cmd( 'ovs-vsctl add-br dp0' )
    s1.cmd( 'ovs-vsctl del-br dp1' )
    s1.cmd( 'ovs-vsctl add-br dp1' )
 
    controller.cmd( cname + ' ' + cargs + '&' )          
    for intf in s0.intfs.values():
        print intf
        print s0.cmd( 'ovs-vsctl add-port dp0 %s' % intf )
   
    for intf in s1.intfs.values():
        print intf
        print s1.cmd( 'ovs-vsctl add-port dp1 %s' % intf )
  
    # Note: controller and switch are in root namespace, and we
    # can connect via loopback interface
    s0.cmd( 'ovs-vsctl set-controller dp0 tcp:127.0.0.1:6633' )
    s1.cmd( 'ovs-vsctl set-controller dp0 tcp:127.0.0.1:6633' )
   
    info( '*** Waiting for switch to connect to controller' )
    while 'is_connected' not in quietRun( 'ovs-vsctl show' ):
        sleep( 1 )
        info( '.' )
    info( '\n' )
 
    #print s0.cmd('ovs-ofctl show dp0')
 
    #info( "*** Running test\n" )
    h0.cmdPrint( 'ping -c 3 ' + h2.IP() )
    h1.cmdPrint( 'ping -c 3 ' + h2.IP() )
    h2.cmd('iperf -s &')
    print "iperf: h0--s0--s1--h2"
    h0.cmdPrint('iperf -c 192.168.123.3 -t 10')
    print "iperf: h1--s0--s1--h2"
    h1.cmdPrint('iperf -c 192.168.123.3 -t 10')
    print "limit the bandwidth for flow h0-h2"
    s0.cmdPrint('ethtool -K s0-eth2 gro off')
    s0.cmdPrint('tc qdisc del dev s0-eth2 root')
    s0.cmdPrint('tc qdisc add dev s0-eth2 root handle 1: cbq avpkt 1000 bandwidth 10Mbit')
    s0.cmdPrint('tc class add dev s0-eth2 parent 1: classid 1:1 cbq rate 512kbit allot 1500 prio 5 bounded isolated')
    s0.cmdPrint('tc filter add dev s0-eth2 parent 1: protocol ip prio 16 u32 match ip src 192.168.123.1 flowid 1:1')
    s0.cmdPrint('tc qdisc add dev s0-eth2 parent 1:1 sfq perturb 10')
    h0.cmdPrint('iperf -c 192.168.123.3 -t 10')
    print "iperf: h1--s0--s1--h2" 
    h1.cmdPrint('iperf -c 192.168.123.3 -t 10')
 
    info( "*** Stopping network\n" )
    controller.cmd( 'kill %' + cname )
    s0.cmd( 'ovs-vsctl del-br dp0' )
    s0.deleteIntfs()
    s1.cmd( 'ovs-vsctl del-br dp1' )
    s1.deleteIntfs()
    info( '\n' )
 
if __name__ == '__main__':
    global net
    setLogLevel( 'info' )
    info( '*** Scratch network demo (kernel datapath)\n' )
    print ''' we will creat a topology example as below deacribe !
              h0------
                     |
                     |
                     s0----s1----h2
                     |
                     |
              h1------
    h0 and h1 are running iperf client, h2 is running iperf server !'''
    Mininet.init()
    myNet()
