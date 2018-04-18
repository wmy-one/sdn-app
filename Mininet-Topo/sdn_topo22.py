from mininet.topo import Topo

class MyTopo(Topo):
    "A simple topolopy!"

    def __init__(self):
        " Creat a simple topo"
        super(MyTopo,self).__init__()

        # Add switchs
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')

        # Add hosts
        h1 = self.addHost('h1', mac = "00:00:00:00:00:01", ip = '10.0.0.1/24')
        h2 = self.addHost('h2', mac = "00:00:00:00:00:02", ip = '10.0.0.2/24')
        h3 = self.addHost('h3', mac = "00:00:00:00:00:03", ip = '10.0.0.3/24')
        h4 = self.addHost('h4', mac = "00:00:00:00:00:04", ip = '10.0.0.4/24')

        # Add link
        self.addLink(s1,h1,1,1)
        self.addLink(s1,h2,2,1)
        self.addLink(s1,s2,3,1)
        self.addLink(s1,s3,4,1)
        
        self.addLink(s2,s4,2,1)
        self.addLink(s3,s4,2,2)

        self.addLink(s4,h3,3,1)
        self.addLink(s4,h4,4,1)

topos = { 'mytopo': ( lambda: MyTopo() ) }
