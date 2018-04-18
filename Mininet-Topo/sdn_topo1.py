from mininet.topo import Topo

class MyTopo(Topo):
    "custom a simple topo"

    def __init__(self):
        "creat custom topo"
        
        # Initialize topolopy
        super(MyTopo,self).__init__()

        # add switch 
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        # add host
        h1 = self.addHost('h1',mac = '00:00:00:00:00:01')
        h2 = self.addHost('h2',mac = '00:00:00:00:00:02')
        h3 = self.addHost('h3',mac = '00:00:00:00:00:03')
        h4 = self.addHost('h4',mac = '00:00:00:00:00:04')

        # add links 
        self.addLink(s1,h1,1,1)
        self.addLink(s1,h2,2,1)
        self.addLink(s2,h3,1,1)
        self.addLink(s2,h4,2,1)
        self.addLink(s1,s2,3,3)

topos = { 'mytopo': ( lambda: MyTopo() ) }

