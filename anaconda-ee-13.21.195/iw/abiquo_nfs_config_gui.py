#
# abiquo_nfs_config_ui.py: NFS Configuration
#
# Copyright 2012 Abiquo
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
#from rhpl.translate import _, N_
import re
import socket

import network

import logging
log = logging.getLogger("anaconda")

class AbiquoNFSConfigWindow(InstallWindow):
    def getNext(self):
        nfsUrl = self.xml.get_widget('abiquo_nfs_repository').get_text()

        if re.search('(localhost|127\.0\.0\.1)', nfsUrl):
            self.intf.messageWindow("<b>NFS Repository Error</b>",
                       "<b>127.0.0.1 or localhost detected</b>\n\n"
                         "127.0.0.1 or localhost values are not allowed here. "
                         "Use an IP address reachable by other hosts "
                         "in your LAN.",
                            type="warning")
            raise gui.StayOnScreen

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

        if not re.search('.+:\/.*', nfsUrl):
            self.intf.messageWindow("<b>NFS Repository Error</b>",
                         "<b>Invalid NFS URL</b>\n\n"
                         "%s is not a valid NFS URL" % nfsUrl,
                                type="warning")
            raise gui.StayOnScreen

        self.data.abiquo_rs.abiquo_nfs_repository = nfsUrl

    def helpButtonClicked(self, data):
        log.info("helpButtonClicked")
        msg = (
        "<b>NFS Repository</b>\n"
        "The NFS URI where the Abiquo NFS repository is located.\n"
        "i.e.\n"
        "my-nfs-server-ip:/opt/vm_repository\n"
        "\n"
        )
        self.intf.messageWindow("<b>NFS Configuration</b>", msg, type="ok")

    def getScreen (self, anaconda):
        self.intf = anaconda.intf
        self.dispatch = anaconda.dispatch
        self.backend = anaconda.backend
        self.anaconda = anaconda
        self.data = anaconda.id

        (self.xml, vbox) = gui.getGladeWidget("abiquo_nfs_config.glade", "settingsBox")
        self.helpButton = self.xml.get_widget("helpButton")
        self.helpButton.connect("clicked", self.helpButtonClicked)
        self.xml.get_widget('abiquo_nfs_repository').set_text(self.data.abiquo_rs.abiquo_nfs_repository)
        return vbox
