from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ofproto_v1_3_parser
from ryu.lib.packet import packet
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import mac
 
import re
import networkx as nx

ETHERNET = ethernet.ethernet.__name__
ETHERNET_MULTICAST = "ff:ff:ff:ff:ff:ff"
ARP = arp.arp.__name__
 
class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
 
    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__()
        self.mac_to_port = {}
        self.arp_table = {}
        self.sw = {}
  
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser      
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)] 
        
        mod = datapath.ofproto_parser.OFPFlowMod(datapath=datapath, priority=priority, 
                        idle_timeout=0, hard_timeout=0, match=match, command=ofproto.OFPFC_ADD, instructions=inst)

        datapath.send_msg(mod)
 
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self , ev):
        print "switch_features_handler is called"
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
  
        # add rule for multipath transmission in s1
        if ev.msg.datapath.id == 1:
            #in_port=1,src=10.0.0.1,dst=10.0.0.3
            match = parser.OFPMatch(in_port=1, eth_type=0x0800, ipv4_src="10.0.0.1", ipv4_dst="10.0.0.3")
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 3, match, actions)
            
            #in_port=3,src=10.0.0.3,dst=10.0.0.1
            match = parser.OFPMatch(in_port=3, eth_type=0x0800, ipv4_src="10.0.0.3", ipv4_dst="10.0.0.1")
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 3, match, actions)
            print 'dpid=%d,01' %ev.msg.datapath.id
           

            #in_port=1,src=10.0.0.1,dst=10.0.0.4
            match = parser.OFPMatch(in_port=1, eth_type=0x0800, ipv4_src="10.0.0.1", ipv4_dst="10.0.0.4")
            actions = [parser.OFPActionOutput(4)]
            self.add_flow(datapath, 3, match, actions)
            
            #in_port=4,src=10.0.0.4,dst=10.0.0.1
            match = parser.OFPMatch(in_port=4, eth_type=0x0800, ipv4_src="10.0.0.4", ipv4_dst="10.0.0.1")
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 3, match, actions)
            print 'dpid=%d,02' %ev.msg.datapath.id
            
           
            #in_port=2,src=10.0.0.2,dst=10.0.0.3
            match = parser.OFPMatch(in_port=2, eth_type=0x0800, ipv4_src="10.0.0.2", ipv4_dst="10.0.0.3")
            actions = [parser.OFPActionOutput(4)]
            self.add_flow(datapath, 3, match, actions)
            
            #in_port=4,src=10.0.0.3,dst=10.0.0.2
            match = parser.OFPMatch(in_port=4, eth_type=0x0800, ipv4_src="10.0.0.3", ipv4_dst="10.0.0.2")
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 3, match, actions)
            print 'dpid=%d,03' %ev.msg.datapath.id
            
            #in_port=2,src=10.0.0.2,dst=10.0.0.4
            match = parser.OFPMatch(in_port=2, eth_type=0x0800, ipv4_src="10.0.0.2", ipv4_dst="10.0.0.4")
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 3, match, actions)
            
            #in_port=3,src=10.0.0.4,dst=10.0.0.2
            match = parser.OFPMatch(in_port=3, eth_type=0x0800, ipv4_src="10.0.0.4", ipv4_dst="10.0.0.2")
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 3, match, actions)
            print 'dpid=%d,04' %ev.msg.datapath.id

        # add rule for multipath transmission in s2     
        if ev.msg.datapath.id == 2:
            #in_port=1,src=10.0.0.1,dst=10.0.0.3--->output port:2
            match = parser.OFPMatch(in_port=1, eth_type=0x0800, ipv4_src="10.0.0.1", ipv4_dst="10.0.0.3")
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 3, match, actions)
            
            #in_port=2,src=10.0.0.3,dst=10.0.0.1
            match = parser.OFPMatch(in_port=2, eth_type=0x0800, ipv4_src="10.0.0.3", ipv4_dst="10.0.0.1")
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 3, match, actions)
            print 'dpid=%d,01' %ev.msg.datapath.id
           

            #in_port=1,src=10.0.0.2,dst=10.0.0.4--->output port:2
            match = parser.OFPMatch(in_port=1, eth_type=0x0800, ipv4_src="10.0.0.2", ipv4_dst="10.0.0.4")
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 3, match, actions)
            
            #in_port=2,src=10.0.0.4,dst=10.0.0.2
            match = parser.OFPMatch(in_port=2, eth_type=0x0800, ipv4_src="10.0.0.4", ipv4_dst="10.0.0.2")
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 3, match, actions)
            print 'dpid=%d,02' %ev.msg.datapath.id
       
        # add rule for multipath transmission in s3
        if ev.msg.datapath.id == 3:
            #in_port=1,src=10.0.0.1,dst=10.0.0.4--->output port:2
            match = parser.OFPMatch(in_port=1, eth_type=0x0800, ipv4_src="10.0.0.1", ipv4_dst="10.0.0.4")
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 3, match, actions)
            
            #in_port=2,src=10.0.0.4,dst=10.0.0.1
            match = parser.OFPMatch(in_port=2, eth_type=0x0800, ipv4_src="10.0.0.4", ipv4_dst="10.0.0.1")
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 3, match, actions)
            print 'dpid=%d,01' %ev.msg.datapath.id
           

            #in_port=1,src=10.0.0.2,dst=10.0.0.3--->output port:2
            match = parser.OFPMatch(in_port=1, eth_type=0x0800, ipv4_src="10.0.0.2", ipv4_dst="10.0.0.3")
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 3, match, actions)
            
            #in_port=2,src=10.0.0.3,dst=10.0.0.2
            match = parser.OFPMatch(in_port=2, eth_type=0x0800, ipv4_src="10.0.0.3", ipv4_dst="10.0.0.2")
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 3, match, actions)
            print 'dpid=%d,02' %ev.msg.datapath.id
        
        # add rule for multipath transmission in s4
        if ev.msg.datapath.id == 4:
            #in_port=1,src=10.0.0.1,dst=10.0.0.3--->output port:3
            match = parser.OFPMatch(in_port=1, eth_type=0x0800, ipv4_src="10.0.0.1", ipv4_dst="10.0.0.3")
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 3, match, actions)
            
            #in_port=3,src=10.0.0.3,dst=10.0.0.1
            match = parser.OFPMatch(in_port=3, eth_type=0x0800, ipv4_src="10.0.0.3", ipv4_dst="10.0.0.1")
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 3, match, actions)
            print 'dpid=%d,01' %ev.msg.datapath.id
            

            #in_port=2,src=10.0.0.1,dst=10.0.0.4--->output port:4
            match = parser.OFPMatch(in_port=2, eth_type=0x0800, ipv4_src="10.0.0.1", ipv4_dst="10.0.0.4")
            actions = [parser.OFPActionOutput(4)]
            self.add_flow(datapath, 3, match, actions)
            
            #in_port=4,src=10.0.0.4,dst=10.0.0.1
            match = parser.OFPMatch(in_port=4, eth_type=0x0800, ipv4_src="10.0.0.4", ipv4_dst="10.0.0.1")
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 3, match, actions)
            print 'dpid=%d,02' %ev.msg.datapath.id
           

            #in_port=2,src=10.0.0.2,dst=10.0.0.3--->output port:3
            match = parser.OFPMatch(in_port=2, eth_type=0x0800, ipv4_src="10.0.0.2", ipv4_dst="10.0.0.3")
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 3, match, actions)
            
            #in_port=3,src=10.0.0.3,dst=10.0.0.2
            match = parser.OFPMatch(in_port=3, eth_type=0x0800, ipv4_src="10.0.0.3", ipv4_dst="10.0.0.2")
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 3, match, actions)
            print 'dpid=%d,03' %ev.msg.datapath.id
           

            #in_port=1,src=10.0.0.2,dst=10.0.0.4--->output port:4
            match = parser.OFPMatch(in_port=1, eth_type=0x0800, ipv4_src="10.0.0.2", ipv4_dst="10.0.0.4")
            actions = [parser.OFPActionOutput(4)]
            self.add_flow(datapath, 3, match, actions)
            
            #in_port=4,src=10.0.0.4,dst=10.0.0.2
            match = parser.OFPMatch(in_port=4, eth_type=0x0800, ipv4_src="10.0.0.4", ipv4_dst="10.0.0.2")
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 3, match, actions)
            print 'dpid=%d,04' %ev.msg.datapath.id
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
 
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
 
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        
        header_list = dict(
            (p.protocol_name,p)for p in pkt.protocols if type(p) != str)
        if ARP in header_list:
            self.arp_table[header_list[ARP].src_ip] = src  # ARP learning 
        
        self.mac_to_port.setdefault(dpid, {})
        
        if re.match(r'^33:33',dst):
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 3, match, actions=[])
            print "666666666"
        else:
            self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)
        
        self.mac_to_port[dpid][src] = in_port
        
        
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            if self.arp_handler(header_list, datapath, in_port, msg.buffer_id):
                # 1:reply or drop;  0: flood
                return None
            else:
                out_port = ofproto.OFPP_FLOOD
                print 'OFPP_FLOOD'
    
        actions = [parser.OFPActionOutput(out_port)]
        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)
        
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, 
                        in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def arp_handler(self, header_list, datapath, in_port, msg_buffer_id):
        header_list = header_list
        datapath = datapath
        in_port = in_port

        if ETHERNET in header_list:
            eth_dst = header_list[ETHERNET].dst
            eth_src = header_list[ETHERNET].src

        if eth_dst == ETHERNET_MULTICAST and ARP in header_list:
#            arp_src_ip = header_list[ARP].src_ip
            arp_dst_ip = header_list[ARP].dst_ip

            if (datapath.id, eth_src, arp_dst_ip) in self.sw:  # Break the loop
                if self.sw[(datapath.id, eth_src, arp_dst_ip)] != in_port:
                    out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath,
                                    buffer_id=datapath.ofproto.OFP_NO_BUFFER,
                                    in_port=in_port, actions=[], data=None)
                    datapath.send_msg(out)
                    return True
            else:
                self.sw[(datapath.id, eth_src, arp_dst_ip)] = in_port

        
        if ARP in header_list:
            hwtype = header_list[ARP].hwtype
            proto = header_list[ARP].proto
            hlen = header_list[ARP].hlen
            plen = header_list[ARP].plen
            opcode = header_list[ARP].opcode

            arp_src_ip = header_list[ARP].src_ip
            arp_dst_ip = header_list[ARP].dst_ip

            actions = []

            if opcode == arp.ARP_REQUEST:
                if arp_dst_ip in self.arp_table:  # arp reply
                    actions.append(datapath.ofproto_parser.OFPActionOutput(in_port) )

                    ARP_Reply = packet.Packet()
                    ARP_Reply.add_protocol(ethernet.ethernet(ethertype=header_list[ETHERNET].ethertype,
                                            dst=eth_src, src=self.arp_table[arp_dst_ip]))
                    ARP_Reply.add_protocol(arp.arp(opcode=arp.ARP_REPLY, src_mac=self.arp_table[arp_dst_ip], 
                                            src_ip=arp_dst_ip, dst_mac=eth_src, dst_ip=arp_src_ip))

                    ARP_Reply.serialize()

                    out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath, buffer_id=datapath.ofproto.OFP_NO_BUFFER, 
                                    in_port=datapath.ofproto.OFPP_CONTROLLER, actions=actions, data=ARP_Reply.data)
                    datapath.send_msg(out)
                    return True
        return False
        
    
    
