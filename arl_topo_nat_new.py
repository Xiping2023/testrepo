from mininet.cli import CLI
from mininet.log import lg, info
from mininet.topolib import TreeNet
from mininet.node import OVSBridge
from mininet.link import TCLink
import time
from threading import Timer
import argparse
import sys


def create_event(net):

    if net is not None:
        h1 = net.get('h1')
        h2 = net.get('h2')
        h3 = net.get('h3')

        h1_links = h1.intfList()
        h1_links[1].config(delay='200ms')
        h2_links = h2.intfList()
        h2_links[1].config(delay='200ms')
        h2_links[2].config(delay='400ms')
        h3_links = h3.intfList()
        h3_links[1].config(delay='400ms')


def main():    
    parser = argparse.ArgumentParser(description='Custom topology')
    parser.add_argument('-d','--delay', help='Modify link properties after delay seconds', default=60, type=int)
    args = vars(parser.parse_args())
    TRIGGER_EVENT_AFTER_SEC = args['delay']
    if TRIGGER_EVENT_AFTER_SEC <= 0:
        print('delay must be a positive number')
        sys.exit(0)

    print('the link h1<->h2<->h3 will be modified in', TRIGGER_EVENT_AFTER_SEC, 'seconds')

    lg.setLogLevel('info')
    net = TreeNet(depth=1, fanout=4, waitConnected=True, switch=OVSBridge)

    # Add NAT connectivity
    net.addNAT().configDefault()

    h1 = net.get('h1')
    h2 = net.get('h2')
    h3 = net.get('h3')
    h4 = net.get('h4')

    # Add links
    net.addLink(h1, h2, intfName1='h1-eth1', params1={'ip': '10.0.1.1/24'}, intfName2='h2-eth1', params2={'ip': '10.0.1.2/24'}, cls=TCLink, bw=10, delay='50ms')
    net.addLink(h3, h2, intfName1='h3-eth1', params1={'ip': '10.0.2.3/24'}, intfName2='h2-eth2', params2={'ip': '10.0.2.2/24'}, cls=TCLink, bw=5, delay='100ms')
    net.addLink(h1, h4, intfName1='h1-eth2', params1={'ip': '10.0.5.1/24'}, intfName2='h4-eth1', params2={'ip': '10.0.5.4/24'}, cls=TCLink, bw=10, delay='50ms')
    net.addLink(h3, h4, intfName1='h3-eth2', params1={'ip': '10.0.4.3/24'}, intfName2='h4-eth2', params2={'ip': '10.0.4.4/24'}, cls=TCLink, bw=5, delay='100ms')

    # Confidure IP tables
    info(net['h1'].cmd("ip route add 10.0.2.0/24 via 10.0.1.2 dev h1-eth1"))
    info(net['h3'].cmd("ip route add 10.0.1.0/24 via 10.0.2.2 dev h3-eth1"))
    info(net['h1'].cmd("ip route add 10.0.4.0/24 via 10.0.5.4 dev h1-eth2"))
    info(net['h3'].cmd("ip route add 10.0.5.0/24 via 10.0.4.4 dev h3-eth2"))
    info(net['h2'].cmd("sysctl net.ipv4.ip_forward=1"))
    info(net['h4'].cmd("sysctl net.ipv4.ip_forward=1"))

    # Start network 
    net.start()
    info( "*** Hosts are running and should have internet connectivity\n" )
    info( "*** Type 'exit' or control-D to shut down network\n" )

    # Change link properties after TRIGGER_EVENT_SEC
    t = Timer(TRIGGER_EVENT_AFTER_SEC, create_event, [net])
    t.start()    

    CLI(net)

    # Shut down NAT
    net.stop()

if __name__ == "__main__":
    main()
