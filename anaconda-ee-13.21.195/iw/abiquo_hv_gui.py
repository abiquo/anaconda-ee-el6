#
# abiquo_gui.py: Choose tasks for installation
#
# Copyright 2013 Abiquo
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

from yuminstall import AnacondaYumRepo
import yum.Errors

import logging
log = logging.getLogger("anaconda")

class AbiquoHVWindow(InstallWindow):
    def getNext(self):
        self.data.abiquo_rs.abiquo_nfs_repository = \
                self.xml.get_widget('abiquo_nfs_repository').get_text()
        self.data.abiquo.abiquo_rs_ip = \
                self.xml.get_widget('abiquo_rs_ip').get_text()

    def getScreen (self, anaconda):
        self.intf = anaconda.intf
        self.dispatch = anaconda.dispatch
        self.backend = anaconda.backend
        self.anaconda = anaconda
        self.data = anaconda.id

        (self.xml, vbox) = gui.getGladeWidget("abiquo_hv.glade", "settingsBox")
        self.xml.get_widget('abiquo_nfs_repository').set_text(self.data.abiquo_rs.abiquo_nfs_repository)
        self.xml.get_widget('abiquo_rs_ip').set_text(self.data.abiquo.abiquo_rs_ip)
        return vbox
