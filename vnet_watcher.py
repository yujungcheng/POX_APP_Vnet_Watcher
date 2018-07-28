#!/usr/bin/python2.7

import os, sys, time, socket, json

from pox.core import core
from pox.lib.util import dpid_to_str
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.arp import arp
from pox.lib.recoco import Timer
from threading import Thread


log = core.getLogger()

monitorInterval       = 5  # set to 0 to disable monitoring output
vNetNamePrefix        = ""  # set to "" to show all ports
ignoreSrcIP           = ['0.0.0.0']
ignoreDesIP           = ['255.255.255.0']


class VnetWatcher(object):

    def __init__(self):
        core.openflow.addListeners(self)
        self.vswitchPort = dict()
        self.vswitchName = dict()
        self.nameColLen  = 20
        self.portColLen  = 9
        self.ipColLen    = 19

        self.server_port = 9989

        if monitorInterval != 0:
            self.show_t = Thread(target=self.showPorts, args=())
            self.show_t.start()

        self.server_t = Thread(target=self.run_server, args=())
        self.server_t.start()

    def _handle_ConnectionUp(self, event):
        self.updatePorts(event)

    def _handle_ConnectionDown(self, event):
        self.removePorts(event)
        
    def _handle_PortStatus(self, event):
        action = None
        dpid   = dpid_to_str(event.dpid)
        if event.added:
            action = "added"
            port_info = dict()
            port_info['port_no'] = str(event.ofp.desc.port_no)
            port_info['hw_addr'] = str(event.ofp.desc.hw_addr)
            port_info['name']    = str(event.ofp.desc.name)
            port_info['ip']      = str()
            self.vswitchPort[dpid].append(port_info)
        elif event.deleted:
            action = "removed"
            index = 0
            for item in self.vswitchPort[dpid_to_str(event.dpid)]:
                port_no = event.ofp.desc.port_no
                if str(item['port_no']) == str(port_no):
                    break
                index += 1
            self.vswitchPort[dpid].pop(index)
        elif event.modified:
            action = "modified"

    def _handle_PacketIn(self, event):
        dpid   = dpid_to_str(event.connection.dpid)
        inport = event.port
        packet = event.parse() 
        if not packet.parsed:
            return
        if isinstance(packet.next, ipv4):
            srcMAC = packet.src
            srcIP  = packet.next.srcip
            dstIP  = packet.next.dstip
            if str(srcIP) in ignoreSrcIP:
                return
            if str(dstIP) in ignoreDstIP:
                return
            if dpid in self.vswitchPort.keys():
                for item in self.vswitchPort[dpid]:
                    listMAC = list(str(srcMAC))
                    listMAC[0] = 'f'
                    listMAC[1] = 'e'
                    srcMAC = ''.join(listMAC)
                    if str(item['hw_addr']) == str(srcMAC):
                        item['ip'] = str(srcIP)
                        break

    def run_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_address = ('0.0.0.0', self.server_port)
        print("Start up server on %s port %s." % (server_address, sock.bind(server_address)))

        sock.listen(1)

        while True:
            print("Waiting for client connection.")
            connection, client_address = sock.accept()

            try:
                print("Connection from %s." % str(client_address))
                while True:
                    data = connection.recv(32)

                    if data == 'get_vswitch_port':
                        data_str = json.dumps(self.vswitchPort)
                        connection.sendall(data_str)

                    if data == 'client_close':
                        print("Connection closed.")
                        break
            finally:
                connection.close()

        sock.close()

    def showPorts(self):
        while True:
            os.system('clear')
            title = "[Switch Name: (MAC Address)]\n"
            title = title + "  [Port Name]"
            title = title + " "*9 + "[MAC Address]"
            title = title + " "*8 + "[IP Address]"
            title = title + " "*7 + "[Port No]"
            print title
            print "="*75
            index = 0
            for dpid in self.vswitchPort:
                 name, ports = self.vswitchPort[dpid]
                 print("%s: (%s)" % (name, dpid))
                 for port in ports:
                     nameLen   = len(str(port['name']))
                     portLen   = len(str(port['port_no']))
                     ipLen     = len(str(port['ip']))
                     nameSpace = " "*(self.nameColLen-nameLen)
                     portSpace = " "*(self.portColLen-portLen)
                     ipSpace   = " "*(self.ipColLen-ipLen)
                     outstr = " "*2
                     outstr = outstr + port['name']    + nameSpace
                     outstr = outstr + port['hw_addr'] + " "*4
                     outstr = outstr + port['ip'] + ipSpace 
                     outstr = outstr + port['port_no'] + portSpace
                     print("%s" %outstr)
                     index += 1
            print("\nTotal %s ports.\n" % index)
            time.sleep(monitorInterval)

    def updatePorts(self, event):
        ports = event.ofp.ports 
        port_data = list()
        name = None
        dpid = None
        for item in ports:
            if str(item.port_no) != "65534":
                if vNetNamePrefix in str(item.name) or vNetNamePrefix == "":
                    port_info = dict()
                    port_info['port_no'] = str(item.port_no)
                    port_info['hw_addr'] = str(item.hw_addr)
                    port_info['name']    = str(item.name)
                    port_info['ip']      = str()
                    port_data.append(port_info)
            else:
                dpid = dpid_to_str(event.dpid)
                name = str(item.name)

        if dpid != None and name != None:
            self.vswitchPort[dpid] = (name, port_data)

    def removePorts(self, event):
        dpid = dpid_to_str(event.dpid)
        self.vswitchPort.pop(dpid)
        self.vswitchName.pop(dpid)


def launch():
    core.registerNew(VnetWatcher)
  
