from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER,MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

class L2SwitchWithQos_v13(app_manager.RyuApp):
	OFP_VERSIONS=[ofproto_v1_3.OFP_VERSION]
	def __init__(self,*args,**kwargs):
		super(L2SwitchWithQos_v13,self).__init__(*args,**kwargs)
		self.mac_to_port={}
		self.qos_list=['00:00:00:00:00:10']
		self.qid=1
		self.qoshost_switch_port={}
		self.qos_flow={}
		self.todelete=None
	@set_ev_cls(ofp_event.EventOFPSwitchFeatures,CONFIG_DISPATCHER)
	def switch_features_handler(self,ev):
		datapath=ev.msg.datapath
		ofproto=datapath.ofproto
		parser=datapath.ofproto_parser
		match=parser.OFPMatch()
		actions=[parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,ofproto.OFPCML_NO_BUFFER)]
		self.add_flow(datapath,0,match,actions)
		print "66666"
	def add_flow(self,datapath,priority,match,actions):
		ofproto=datapath.ofproto
		parser=datapath.ofproto_parser
		inst=[parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]
		mod=parser.OFPFlowMod(datapath=datapath,idle_timeout=0,hard_timeout=0,priority=priority,match=match,instructions=inst)
		datapath.send_msg(mod)
	def remove_flow(self,datapath,match):
		ofproto=datapath.ofproto
		parser=datapath.ofproto_parser
		mod=parser.OFPFlowMod(datapath=datapath,command=ofproto.OFPFC_DELETE,out_group=ofproto.OFPG_ANY,out_port=ofproto.OFPP_ANY,match=match)
		datapath.send_msg(mod)
	@set_ev_cls(ofp_event.EventOFPPacketIn,MAIN_DISPATCHER)
	def _packet_in_handler(self,ev):
		msg=ev.msg
		datapath=msg.datapath
		ofproto=datapath.ofproto
		parser=datapath.ofproto_parser
		in_port=msg.match['in_port']
		pkt=packet.Packet(msg.data)
		eth=pkt.get_protocols(ethernet.ethernet)[0]
		dst=eth.dst
		src=eth.src
		dpid=datapath.id
		self.mac_to_port.setdefault(dpid,{})
		self.qos_flow.setdefault(datapath,{})
		self.logger.info("packet in %s %s %s %s",dpid,src,dst,in_port)
		#learn a mac address to avoid FLOOD next time.
		self.mac_to_port[dpid][src]=in_port
		if src in self.qos_list:
			if src not in self.qoshost_switch_port:
				self.qoshost_switch_port[src]=(dpid,in_port)
		if dst in self.mac_to_port[dpid]:
			out_port=self.mac_to_port[dpid][dst]
		else:
			out_port=ofproto.OFPP_FLOOD
		actions=[parser.OFPActionOutput(out_port)]
		match=parser.OFPMatch(in_port=in_port,eth_src=src,eth_dst=dst)
		#install a flow to avoid packet_in next time
		if out_port!=ofproto.OFPP_FLOOD:
			if src in self.qos_list:
				self.logger.info("!!!!!!")
				actions.insert(0,parser.OFPActionSetQueue(2))
				self.qos_flow[datapath].setdefault(src,[])
				self.qos_flow[datapath][src].append((match,actions))
			else:
				if dst in self.qos_list:
					self.qos_flow[datapath].setdefault(dst,[])
					self.qos_flow[datapath][dst].append((match,actions))
			#self.logger.info("%s",datapath)
			self.add_flow(datapath,1,match,actions)
		data=None
		if msg.buffer_id==ofproto.OFP_NO_BUFFER:
			data=msg.data
		out=parser.OFPPacketOut(datapath=datapath,buffer_id=msg.buffer_id,in_port=in_port,actions=actions,data=data)
		datapath.send_msg(out)
	@set_ev_cls(ofp_event.EventOFPPortStatus,MAIN_DISPATCHER)
	def _port_status_handler(self,ev):
		msg=ev.msg
		parser=msg.datapath.ofproto_parser
		reason=msg.reason
		port_no=msg.desc.port_no
		dpid=msg.datapath.id
		ofproto=msg.datapath.ofproto
		if reason==ofproto.OFPPR_ADD:
			self.logger.info("port %s added to switch %s",port_no,dpid)
		elif reason==ofproto.OFPPR_DELETE:
			self.logger.info("port %s of switch %s is deleted",port_no,dpid)
			self.logger.info("qoshost_switch_port:%s",self.qoshost_switch_port)
			for qoshost in self.qoshost_switch_port:
				if self.qoshost_switch_port[qoshost]==(dpid,port_no):
					self.todelete=qoshost
					for dpid in self.mac_to_port:
						if qoshost in self.mac_to_port[dpid]:
							self.mac_to_port[dpid].pop(qoshost)
					for datapath in self.qos_flow:
						self.logger.info("%s",self.mac_to_port[dpid])
						#self.logger.info("%s",datapath)
						match=parser.OFPMatch(eth_dst=qoshost)
						self.remove_flow(datapath,match)
						match=parser.OFPMatch(eth_src=qoshost)
						self.remove_flow(datapath,match)
			if self.todelete!=None:
				self.qoshost_switch_port.pop(self.todelete)
				self.todelete=None
		elif reason==ofproto.OFPPR_MODIFY:
			self.logger.info("port %s of switch %s is modified",port_no,dpid)
		else:
			self.logger.info("Illeagal port state %s %s",port_no,reason)
