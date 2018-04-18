from pox.core import core
from pox.lib.util import dpidToStr
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, EthAddr
import pox.lib.packet as pkt
from pox.openflow.of_json import *
from pox.lib.recoco import Timer
import time
from pox.lib.packet.packet_base import packet_base
from pox.lib.packet.packet_utils import *
import struct
 
log = core.getLogger()
 
#global variables
start_time = 0.0
sent_time1=0.0
sent_time2=0.0
received_time1 = 0.0
received_time2 = 0.0
src_dpid=0
dst_dpid=0
mytimer = 0
OWD1=0.0
OWD2=0.0
 
#probe protocol, only timestamp field
class myproto(packet_base):
  "My Protocol packet struct"
 
  def __init__(self):
     packet_base.__init__(self)
     self.timestamp=0
 
  def hdr(self, payload):
     return struct.pack('!I', self.timestamp)
 
def _handle_ConnectionDown (event):
  global mytimer
  print "ConnectionDown: ", dpidToStr(event.connection.dpid)
  mytimer.cancel()
  
def _handle_ConnectionUp (event):
  global src_dpid, dst_dpid, mytimer
  print "ConnectionUp: ", dpidToStr(event.connection.dpid)
 
  #remember the connection dpid for switch to controller (src_dpid) and switch1 to controller(dst_dpid)
  for m in event.connection.features.ports:
    if m.name == "s0-eth0":
      src_dpid = event.connection.dpid
    elif m.name == "s1-eth0":
      dst_dpid = event.connection.dpid
 
  # when the controller knows both src_dpid and dst_dpid, the probe packet is sent out every 2 seconds
  if src_dpid<>0 and dst_dpid<>0:
    mytimer=Timer(2, _timer_func, recurring=True)
    mytimer.start()
 
def _handle_portstats_received (event):
   global start_time, sent_time1, sent_time2, received_time1, received_time2, src_dpid, dst_dpid,OWD1,OWD2
 
   received_time = time.time() * 1000 - start_time
   #measure T1
   if event.connection.dpid == src_dpid:
     OWD1=0.5*(received_time - sent_time1)
     #print "OWD1: ", OWD1, "ms"
   #measure T3
   elif event.connection.dpid == dst_dpid:
     OWD2=0.5*(received_time - sent_time1)
     #print "OWD2: ", OWD2, "ms"
 
def _handle_PacketIn (event):
  global start_time,OWD1,OWD2
  packet = event.parsed
  #print packet
 
  received_time = time.time() * 1000 - start_time
  if packet.type==0x5577 and event.connection.dpid==dst_dpid:
    c=packet.find('ethernet').payload
    d,=struct.unpack('!I', c)
    #obtain T2
    print "delay:", received_time - d - OWD1-OWD2, "ms"
   
  a=packet.find('ipv4')
  b=packet.find('arp')
  if a:
    #print "IPv4 Packet:", packet
    msg = of.ofp_flow_mod()
    msg.priority =1
    msg.idle_timeout = 0
    msg.match.in_port =1
    msg.match.dl_type=0x0800
    msg.actions.append(of.ofp_action_output(port = 2))
    event.connection.send(msg)
  
    msg = of.ofp_flow_mod()
    msg.priority =1
    msg.idle_timeout = 0
    msg.match.in_port =2
    msg.match.dl_type=0x0800
    msg.actions.append(of.ofp_action_output(port = 1))
    event.connection.send(msg)   
 
  if b and b.opcode==1:
    #print "ARP Request Packet:", packet
    msg = of.ofp_flow_mod()
    msg.priority =1
    msg.idle_timeout = 0
    msg.match.in_port =1
    msg.match.dl_type=0x0806
    msg.actions.append(of.ofp_action_output(port = 2))
    if event.connection.dpid == src_dpid:
      #print "send to switch"
      event.connection.send(msg)
    elif event.connection.dpid == dst_dpid:
      #print "send to switch1"
      event.connection.send(msg)
 
  if b and b.opcode==2:
    #print "ARP Reply Packet:", packet
    msg = of.ofp_flow_mod()
    msg.priority =1
    msg.idle_timeout = 0
    msg.match.in_port =2
    msg.match.dl_type=0x0806
    msg.actions.append(of.ofp_action_output(port = 1))
    if event.connection.dpid == src_dpid:
      #print "send to switch"
      event.connection.send(msg)
    elif event.connection.dpid == dst_dpid:
      #print "send to switch1"
      event.connection.send(msg)
 
def _timer_func ():
  global start_time, sent_time1, sent_time2, src_dpid, dst_dpid
 
  if src_dpid <>0:
    sent_time1=time.time() * 1000 - start_time
    #print "sent_time1:", sent_time1
    #send out port_stats_request packet through src_dpid
    core.openflow.getConnection(src_dpid).send(of.ofp_stats_request(body=of.ofp_port_stats_request()))
   
    f = myproto()
    f.timestamp = int(time.time()*1000 - start_time)
    #print f.timestamp
    e = pkt.ethernet()
    e.src=EthAddr("0:0:0:0:0:2")
    e.dst=EthAddr("0:1:0:0:0:1")
    e.type=0x5577
    e.payload = f
    msg = of.ofp_packet_out()
    msg.data = e.pack()
    msg.actions.append(of.ofp_action_output(port=2))
    core.openflow.getConnection(src_dpid).send(msg)
   
  if dst_dpid <>0:
     sent_time2=time.time() * 1000 - start_time
     #print "sent_time2:", sent_time2
     #send out port_stats_request packet through dst_dpid
     core.openflow.getConnection(dst_dpid).send(of.ofp_stats_request(body=of.ofp_port_stats_request()))
  
def launch ():
  global start_time
  start_time = time.time() * 1000
  print "start_time:", start_time
  core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
  core.openflow.addListenerByName("ConnectionDown", _handle_ConnectionDown)
  core.openflow.addListenerByName("PortStatsReceived",
    _handle_portstats_received)
  core.openflow.addListenerByName("PacketIn",
    _handle_PacketIn) 