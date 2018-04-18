from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.ofproto import inet
from ryu.ofproto import ether

from ryu.lib import hub

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSION = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__()
        self.mac_to_port = {}
        self.limit = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss table
        match= parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

        if ev.msg.datapath.id == 1:
            match = parser.OFPMatch(eth_type=0x0800, ipv4_src='10.0.0.1', ipv4_dst='10.0.0.5')
            actions = []
            self.add_flow(datapath, 3, match, actions)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_src='10.0.0.5', ipv4_dst='10.0.0.1')
            actions = []
            self.add_flow(datapath, 3, match, actions)
            
            match = parser.OFPMatch(eth_type=0x0800, ipv4_src='10.0.0.2', ipv4_dst='10.0.0.5')
            actions = []
            self.add_flow(datapath, 3, match, actions)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_src='10.0.0.5', ipv4_dst='10.0.0.2')
            actions = []
            self.add_flow(datapath, 3, match, actions)
            

    def add_flow(self, datapath, priority, match, actions, idle_timeout=0, hard_timeout=0, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, idle_timeout=idle_timeout, hard_timeout=hard_timeout, 
                            buffer_id=buffer_id, priority=priority, match=match, instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, idle_timeout=idle_timeout, hard_timeout=hard_timeout, 
                            priority=priority, match=match, instructions=inst)
        
        datapath.send_msg(mod)

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
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time.
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, buffer_id = msg.buffer_id)
                return 
            else:
                self.add_flow(datapath, 1, match, actions)
        
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
'''
        # judge "access deny"
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        if pkt_ipv4:
            if (pkt_ipv4.proto == inet.IPPORO_TCP):
                pkt_tcp = pkt.get_protocol(tcp.tcp)
                if 80 == pkt_tcp.dst_port:
                    print " tcp dst_prot~~~~~~~~~~~~~", pkt_tcp.dst_port
                    
                    if (pkt_ipv4.src, pkt_ipv4.dst, pkt_tcp.dst_port) not in self.limit.keys():
                        self.limit[(pkt_ipv4.src, pkt_ipv4.dst, pkt_tcp.dst_port)] = True
                    
                    if self.limit[(pkt_ipv4.src, pkt_ipv4.dst, pkt_tcp.dst_port)]:
                        
                        # set FLASE , don`t "access deny" next time.
                        self.limit[(pkt_ipv4.src, pkt_ipv4.dst, pkt_tcp.dst_port)] = False
                        # can` have value in monitor!!!
                        hub.spawn(self._monitor, datapath, pkt_ipv4, pkt_tcp)

    # function:limit 60 s
    def _monitor(self, datapath, pkt_ipv4, pkt_tcp):
        hub.sleep(10)
        ipv4_src = pkt_ipv4.src
        ipv4_dst = pkt_ipv4.dst
        dst_port = pkt_tcp.dst_port
        src_port = pkt_tcp.src_port
        parser = datapath.ofproto_parser
        actions = []
        match = parser.OFPMatch(eth_type=ether.ETH_TYPE_IP, ipv4_src=ipv4_src, 
                        ipv4_dst=ipv4_dst, ip_proto=inet.IPPROTO_TCP, tcp_dst=dst_port)
        
        self.add_flow(datapath, 3, match, actions, idle_timeout=60, hard_timeout=60)
        
        match = parser.OFPMatch(eth_type=ether.ETH_TYPE_IP, ipv4_src=ipv4_dst, 
                        ipv4_dst=ipv4_src, ip_proto=inet.IPPROTO_TCP, tcp_src=src_port)
        
        self.add_flow(datapath, 3, match, actions, idle_timeout=60, hard_timeout=60)
        print "add drop flow ~~~~~~~~"

'''
