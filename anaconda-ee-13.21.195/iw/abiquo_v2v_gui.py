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
# from rhpl.translate import _, N_
import re
import socket
import network

import logging
log = logging.getLogger("anaconda")

import urlparse

class AbiquoV2VWindow(InstallWindow):
    def getNext(self):
        nfsUrl = self.xml.get_widget('abiquo_nfs_repository').get_text()
        datacenterId = self.xml.get_widget('datacenterId').get_text()
        nfs_repo_selected = ('abiquo-nfs-repository' in self.anaconda.id.abiquo.selectedGroups)

        if re.search('(localhost|127\.0\.0\.1)', nfsUrl) and not nfs_repo_selected:
            self.intf.messageWindow("<b>NFS Repository Error</b>",
                         "<b>127.0.0.1 or localhost detected</b>\n\n"
                         "127.0.0.1 or localhost values are not allowed here. "
                         "Use an IP address reachable by other hosts "
                         "in your LAN.",
                            type="warning")
            raise gui.StayOnScreen

        serverIP = self.xml.get_widget('abiquo_server_ip').get_text()
        if re.search('(localhost|127\.0\.0\.1)', serverIP):
            self.intf.messageWindow("<b>Abiquo Server IP Error</b>",
                         "<b>127.0.0.1 or localhost detected</b>\n\n"
                         "127.0.0.1 or localhost values are not allowed here. "
                         "Use an IP address reachable by other hosts "
                         "in your LAN.",
                                type="warning")
            raise gui.StayOnScreen

        if not nfs_repo_selected:
            # validate the host
            host = nfsUrl.split(":")[0]
            try:
                network.sanityCheckIPString(host)
            except:
                if network.sanityCheckHostname(host) is not None:
                    self.intf.messageWindow("<b>Invalid NFS URL</b>",
                         "NFS Repository URL is invalid.",
                            type="warning")
                    raise gui.StayOnScreen

        # validate the abiquo server IP
        try:
            socket.inet_aton(serverIP.strip())
        except socket.error:
            self.intf.messageWindow("<b>Abiquo Server IP Error</b>",
                         "Invalid Abiquo Server IP address",
                                type="warning")
            raise gui.StayOnScreen

        if not re.search('.+:\/.*', nfsUrl):
            self.intf.messageWindow("<b>NFS Repository Error</b>",
                         "<b>Invalid NFS URL</b>\n\n"
                         "%s is not a valid NFS URL" % nfsUrl,
                                type="warning")
            raise gui.StayOnScreen


        self.data.abiquo_rs.abiquo_nfs_repository = nfsUrl
        self.data.abiquo_v2v.abiquo_rabbitmq_host = serverIP
        self.data.abiquo_v2v.abiquo_datacenter_id = datacenterId

    def helpButtonClicked(self, data):
        log.info("helpButtonClicked")
        nfs_help = (
        "<b>NFS Repository</b>\n"
        "The NFS URI where the Abiquo NFS repository is located.\n"
        "i.e.\n"
        "my-nfs-server-ip:/opt/vm_repository\n"
        "\n"
        )
        msg = (
        "<b>Abiquo Server IP</b>\n"
        "Abiquo Server (management server) IP address.\n\n"
        "<b>Datacenter ID</b>\n"
        "A unique identifier for this datacenter.\n"
        "If you are installing Remote Services in a different server,\n"
        "make sure you use the same Datacenter ID when installing Remote Services.\n"
        "\n"
        )

        if not ('abiquo-nfs-repository' in self.anaconda.id.abiquo.selectedGroups):
            msg = nfs_help + msg
        
        self.intf.messageWindow("<b>V2V Services Settings</b>", msg, type="ok")

    def getScreen (self, anaconda):
        self.intf = anaconda.intf
        self.dispatch = anaconda.dispatch
        self.backend = anaconda.backend
        self.anaconda = anaconda
        self.data = anaconda.id

        (self.xml, vbox) = gui.getGladeWidget("abiquo_v2v.glade", "settingsBox")
        self.helpButton = self.xml.get_widget("helpButton")
        self.helpButton.connect("clicked", self.helpButtonClicked)
        self.xml.get_widget('abiquo_nfs_repository').set_text(self.data.abiquo_rs.abiquo_nfs_repository)
        self.xml.get_widget('datacenterId').set_text(self.data.abiquo_v2v.abiquo_datacenter_id)
        
        server_ip = self.data.abiquo_v2v.abiquo_rabbitmq_host
        if server_ip == '127.0.0.1':
            server_ip = '<server-ip>'
        self.xml.get_widget('abiquo_server_ip').set_text(server_ip)
        # We don't need to enter NFS info if nfs-repository selected
        if 'abiquo-nfs-repository' in self.anaconda.id.abiquo.selectedGroups:
            box = self.xml.get_widget("serverSettingsBox")
            hbox = self.xml.get_widget("hbox1")
            box.remove(hbox)

        return vbox
