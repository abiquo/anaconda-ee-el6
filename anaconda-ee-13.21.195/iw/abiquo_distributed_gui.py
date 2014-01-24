#
# abiquo_gui.py: Choose tasks for installation
#
# Copyright 2011 Abiquo
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# AbiquoServerRadio
#   AbiquoGUIRadio
#   AbiquoAPIRadio
# AbiquoRSRadio
#   AbiquoPublicRadio
# AbiquoV2VRadio

import gtk
import gtk.glade
import gui
from iw_gui import *

class AbiquoDistributedWindow(InstallWindow):
    def getNext(self):
        # remove previously selected group not present now
        map(self.backend.selectGroup, self.data.abiquo.selectedGroups)
        
        if ('abiquo-server' in self.anaconda.id.abiquo.selectedGroups):
            self.dispatch.skipStep("abiquo_password", skip = 0)
        else:
            self.dispatch.skipStep("abiquo_password", skip = 1)
        
        for g in ['abiquo-server', 'abiquo-remote-services', 'abiquo-v2v']:
            if g in self.anaconda.id.abiquo.selectedGroups:
                self.dispatch.skipStep("abiquo_nfs_config", skip = 1, permanent = 1)


        
	if ('abiquo-v2v' in self.anaconda.id.abiquo.selectedGroups) and not \
		('abiquo-remote-services' in self.anaconda.id.abiquo.selectedGroups):
        		self.dispatch.skipStep("abiquo_v2v", skip = 0)
    	else:
		self.dispatch.skipStep("abiquo_v2v", skip = 1)
        
    def _selectionChanged(self, btn):
        lbl = btn.get_name()
        if btn.get_active():
            if lbl == 'AbiquoServerRadio':
                self.data.abiquo.selectedGroups.append('abiquo-server')
                if ('abiquo-ui' in self.anaconda.id.abiquo.selectedGroups):
                    self.data.abiquo.selectedGroups.remove('abiquo-ui')
                if ('abiquo-standalone-api' in self.anaconda.id.abiquo.selectedGroups):
                    self.data.abiquo.selectedGroups.remove('abiquo-standalone-api')
                self.xml.get_widget('AbiquoGUIRadio').set_active(False)
                self.xml.get_widget('AbiquoGUIRadio').set_sensitive(False)
                self.xml.get_widget('AbiquoAPIRadio').set_active(False)
                self.xml.get_widget('AbiquoAPIRadio').set_sensitive(False)
            elif lbl == 'AbiquoRSRadio':
                self.data.abiquo.selectedGroups.append('abiquo-remote-services')
                if ('abiquo-public-cloud' in self.anaconda.id.abiquo.selectedGroups):
                    self.data.abiquo.selectedGroups.remove('abiquo-public-cloud')
                self.xml.get_widget('AbiquoPublicRadio').set_active(False)
                self.xml.get_widget('AbiquoPublicRadio').set_sensitive(False)
            elif lbl == 'AbiquoV2VRadio':
                self.data.abiquo.selectedGroups.append('abiquo-v2v')
            elif lbl == 'AbiquoGUIRadio':
                self.data.abiquo.selectedGroups.append('abiquo-ui')
            elif lbl == 'AbiquoAPIRadio':
                self.data.abiquo.selectedGroups.append('abiquo-standalone-api')
            elif lbl == 'AbiquoPublicRadio':
                self.data.abiquo.selectedGroups.append('abiquo-public-cloud')
        else:
            if lbl == 'AbiquoServerRadio':
                self.data.abiquo.selectedGroups.remove('abiquo-server')
                self.xml.get_widget('AbiquoGUIRadio').set_sensitive(True)
                self.xml.get_widget('AbiquoAPIRadio').set_sensitive(True)
            elif lbl == 'AbiquoRSRadio':
                self.data.abiquo.selectedGroups.remove('abiquo-remote-services')
                self.xml.get_widget('AbiquoPublicRadio').set_sensitive(True)
            elif lbl == 'AbiquoV2VRadio':
                self.data.abiquo.selectedGroups.remove('abiquo-v2v')
            elif lbl == 'AbiquoGUIRadio' and ('abiquo-ui' in self.anaconda.id.abiquo.selectedGroups):
                self.data.abiquo.selectedGroups.remove('abiquo-ui')
            elif lbl == 'AbiquoAPIRadio' and ('abiquo-standalone-api' in self.anaconda.id.abiquo.selectedGroups):
                self.data.abiquo.selectedGroups.remove('abiquo-standalone-api')
            elif lbl == 'AbiquoPublicRadio' and ('abiquo-public-cloud' in self.anaconda.id.abiquo.selectedGroups):
                self.data.abiquo.selectedGroups.remove('abiquo-public-cloud')

    def getScreen (self, anaconda):
        self.anaconda = anaconda
        self.data = anaconda.id
        self.backend = anaconda.backend
        self.dispatch = anaconda.dispatch
        (self.xml, vbox) = gui.getGladeWidget("abiquo_distributed.glade", "settingsBox")

        # Clean selections if we go back
        for g in ['abiquo-server','abiquo-ui','abiquo-standalone-api','abiquo-remote-services','abiquo-public-cloud','abiquo-v2v']:
            if g in self.anaconda.id.abiquo.selectedGroups:
                self.anaconda.id.abiquo.selectedGroups.remove(g)
                self.anaconda.backend.deselectGroup(g)
            if g in self.data.abiquo.selectedGroups:
                self.data.abiquo.selectedGroups.remove(g)
                self.anaconda.backend.deselectGroup(g)
        for btn in ['AbiquoServerRadio', 'AbiquoRSRadio', 'AbiquoV2VRadio', 'AbiquoGUIRadio', 'AbiquoAPIRadio','AbiquoPublicRadio']:
            self.xml.get_widget(btn).set_active(False)
            self.xml.get_widget(btn).set_sensitive(True)
            self.xml.get_widget(btn).connect(
                    'toggled',
                    self._selectionChanged)
        return vbox
