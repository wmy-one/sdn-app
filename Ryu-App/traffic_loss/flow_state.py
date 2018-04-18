#!/usr/bin/python
# Copyright 2012 William Yu
# wyu@ateneo.edu
#
# This file is part of POX.
#
# POX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# POX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with POX. If not, see <http://www.gnu.org/licenses/>.
#
 
"""
This is a demonstration file created to show how to obtain flow
and port statistics from OpenFlow 1.0-enabled switches. The flow
statistics handler contains a summary of web-only traffic.
"""
 
# standard includes
from pox.core import core
from pox.lib.util import dpidToStr
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, EthAddr
 
# include as part of the betta branch
from pox.openflow.of_json import *
from pox.lib.recoco import Timer
import time
 
log = core.getLogger()
 
src_dpid = 0
dst_dpid = 0
input_pkts = 0
output_pkts = 0
 
def getTheTime():  #fuction to create a timestamp
  flock = time.localtime()
  then = "[%s-%s-%s" %(str(flock.tm_year),str(flock.tm_mon),str(flock.tm_mday))
 
  if int(flock.tm_hour)<10:
    hrs = "0%s" % (str(flock.tm_hour))
  else:
    hrs = str(flock.tm_hour)
  if int(flock.tm_min)<10:
    mins = "0%s" % (str(flock.tm_min))
  else:
    mins = str(flock.tm_min)
  if int(flock.tm_sec)<10:
    secs = "0%s" % (str(flock.tm_sec))
  else:
    secs = str(flock.tm_sec)
  then +="]%s.%s.%s" % (hrs,mins,secs)
  return then
 
# handler for timer function that sends the requests to all the
# switches connected to the controller.
def _timer_func ():
  for connection in core.openflow._connections.values():
    connection.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))
    connection.send(of.ofp_stats_request(body=of.ofp_port_stats_request()))
  log.debug("Sent %i flow/port stats request(s)", len(core.openflow._connections))
 
# handler to display flow statistics received in JSON format
# structure of event.stats is defined by ofp_flow_stats()
def _handle_flowstats_received (event):
   #stats = flow_stats_to_list(event.stats)
   #log.debug("FlowStatsReceived from %s: %s", dpidToStr(event.connection.dpid), stats)
   global src_dpid, dst_dpid, input_pkts, output_pkts
   #print "src_dpid=", dpidToStr(src_dpid), "dst_dpid=", dpidToStr(dst_dpid)
   for f in event.stats:
     if f.match.dl_type==0x0800 and f.match.nw_dst==IPAddr("192.168.123.2") and f.match.nw_tos==0x64 and event.connection.dpid==src_dpid:
       #print "input: ", f.byte_count, f.packet_count
       input_pkts = f.packet_count
     if f.match.dl_type==0x0800 and f.match.nw_dst==IPAddr("192.168.123.2") and f.match.nw_tos==0x64 and event.connection.dpid==dst_dpid:
       #print "output: ", f.byte_count, f.packet_count 
       output_pkts = f.packet_count
       if input_pkts !=0:
         print getTheTime(), "Path Loss Rate =", (input_pkts-output_pkts)*1.0/input_pkts*100, "%"
 
# handler to display port statistics received in JSON format
def _handle_portstats_received (event):
   #print "\n<<<STATS-REPLY: Return PORT stats for Switch", event.connection.dpid,"at ",getTheTime()
   #for f in event.stats:
      #if int(f.port_no)<65534:
        #print "   PortNo:", f.port_no, " Fwd's Pkts:", f.tx_packets, " Fwd's Bytes:", f.tx_bytes, " Rc'd Pkts:", f.rx_packets, " Rc's Bytes:", f.rx_bytes
        #print "   PortNo:", f.port_no,  " TxDrop:", f.tx_dropped, " RxDrop:", f.rx_dropped, " TxErr:", f.tx_errors, " RxErr:", f.rx_errors, " CRC:", f.rx_crc_err, " Coll:", f.collisions
  stats = flow_stats_to_list(event.stats)
  log.debug("PortStatsReceived from %s: %s", dpidToStr(event.connection.dpid), stats)
 
def _handle_ConnectionUp (event):
  global src_dpid, dst_dpid
  print "ConnectionUp: ", dpidToStr(event.connection.dpid)
  for m in event.connection.features.ports:
    if m.name == "s0-eth0":
      src_dpid = event.connection.dpid
    elif m.name == "s1-eth0":
      dst_dpid = event.connection.dpid
 
  msg = of.ofp_flow_mod()
  msg.priority =1
  msg.idle_timeout = 0
  msg.match.in_port =1
  msg.actions.append(of.ofp_action_output(port = of.OFPP_ALL))
  event.connection.send(msg)
 
  msg = of.ofp_flow_mod()
  msg.priority =1
  msg.idle_timeout = 0
  msg.match.in_port =2
  msg.actions.append(of.ofp_action_output(port = of.OFPP_ALL))
  event.connection.send(msg)
 
  msg = of.ofp_flow_mod()
  msg.priority =10
  msg.idle_timeout = 0
  msg.hard_timeout = 0
  msg.match.dl_type = 0x0800
  msg.match.nw_tos = 0x64
  msg.match.in_port=1
  msg.match.nw_dst = "192.168.123.2"
  msg.actions.append(of.ofp_action_output(port = 2))
  event.connection.send(msg)
 
  msg = of.ofp_flow_mod()
  msg.priority =10
  msg.idle_timeout = 0
  msg.hard_timeout = 0
  msg.match.dl_type = 0x0800
  msg.match.nw_tos = 0x64
  msg.match.nw_dst = "192.168.123.1"
  msg.actions.append(of.ofp_action_output(port = 1))
  event.connection.send(msg)
   
# main functiont to launch the module
def launch ():
  # attach handsers to listners
  core.openflow.addListenerByName("FlowStatsReceived",
    _handle_flowstats_received)
  core.openflow.addListenerByName("PortStatsReceived",
    _handle_portstats_received)
  core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
 
  # timer set to execute every five seconds
  Timer(1, _timer_func, recurring=True)
