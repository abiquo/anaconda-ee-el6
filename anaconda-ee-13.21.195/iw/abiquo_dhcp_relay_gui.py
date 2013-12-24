#
# abiquo_gui.py: Choose tasks for installation
#
# Copyright 2010 Abiquo
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import gtk
import gtk.glade
import gobject
import gui
from iw_gui import *
from constants import productName

import network
import socket

import logging
log = logging.getLogger("anaconda")

class AbiquoDHCPRelayWindow(InstallWindow):
    def getNext(self):
        self.data.abiquo.abiquo_dhcprelay_vrange_1 = self.xml.get_widget('vrange_1').get_text()
        
        self.data.abiquo.abiquo_dhcprelay_vrange_2 = self.xml.get_widget('vrange_2').get_text()

        if int(self.data.abiquo.abiquo_dhcprelay_vrange_1) >= int(self.data.abiquo.abiquo_dhcprelay_vrange_2):
            self.intf.messageWindow("VLAN Range Error",
                       "Invalid Range\n\n"
                         "VLAN Range 1 is equal or greater than VLAN Range 2",
                                type="warning")
            raise gui.StayOnScreen
            
        combo = self.xml.get_widget('management_if')
        iter = combo.get_active_iter()
        if not iter:
            self.intf.messageWindow("Invalid Interface",
                       "Invalid management interface selected",
                                type="warning")
            raise gui.StayOnScreen
        self.data.abiquo.abiquo_dhcprelay_management_if = combo.get_model().get_value(iter, 0)

        combo = self.xml.get_widget('service_if')
        iter = combo.get_active_iter()
        if not iter:
            self.intf.messageWindow("Invalid Interface",
                       "Invalid relay interface selected",
                                type="warning")
            raise gui.StayOnScreen
        self.data.abiquo.abiquo_dhcprelay_service_if = combo.get_model().get_value(iter, 0)

        # DHCP Server IP
        self.data.abiquo.abiquo_dhcprelay_dhcpd_ip = self.xml.get_widget('dhcpd_ip').get_text()
        try:
            socket.inet_aton(self.data.abiquo.abiquo_dhcprelay_dhcpd_ip.strip())
        except socket.error:
            self.intf.messageWindow("IP Error",
                       "Invalid DHCP Server IP Address\n\n"
                         "%s is not a valid IP Address" % self.data.abiquo.abiquo_dhcprelay_dhcpd_ip,
                                type="warning")
            raise gui.StayOnScreen

        self.data.abiquo.abiquo_dhcprelay_service_network = self.xml.get_widget('service_network').get_text()

    def getScreen (self, anaconda):
        self.intf = anaconda.intf
        self.anaconda = anaconda
        self.data = anaconda.id

        (self.xml, vbox) = gui.getGladeWidget("abiquo_dhcp_relay.glade", "settingsBox")
        service_if_combo = self.xml.get_widget('service_if')
        management_if_combo = self.xml.get_widget('management_if')
        netinfo = network.Network()
        management_if_store = gtk.ListStore(gobject.TYPE_STRING)
        service_if_store = gtk.ListStore(gobject.TYPE_STRING)
        
        # Avaliable devices
        for dev in anaconda.id.network.netdevices:
            service_if_store.append([dev])
            management_if_store.append([dev])
            
        service_if_combo.set_model(service_if_store)
        cell = gtk.CellRendererText()
        service_if_combo.pack_start(cell, True)
        service_if_combo.add_attribute(cell, 'text',0)
        management_if_combo.set_model(management_if_store)
        cell = gtk.CellRendererText()
        management_if_combo.pack_start(cell, True)
        management_if_combo.add_attribute(cell, 'text',0)

        return vbox
