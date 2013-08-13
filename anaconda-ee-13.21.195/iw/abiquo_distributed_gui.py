#
# abiquo_gui.py: Choose tasks for installation
#
# Copyright 2011 Abiquo
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import gtk
import gtk.glade
import gui
from iw_gui import *

class AbiquoDistributedWindow(InstallWindow):
    def getNext(self):
        #self.data.abiquo.selectedGroups += self.selected_tasks
        #for g in ['abiquo-server', 'abiquo-remote-services', 'abiquo-v2']:
        #    if g not in self.data.abiquo.selectedGroups:
        #        map(self.backend.deselectGroup, [g])
        
        # remove previously selected group not present now
        map(self.backend.selectGroup, self.data.abiquo.selectedGroups)
        
        if ('abiquo-server' in self.anaconda.id.abiquo.selectedGroups):
            self.dispatch.skipStep("abiquo_password", skip = 0)
        else:
            self.dispatch.skipStep("abiquo_password", skip = 1)
        
        for g in ['abiquo-server', 'abiquo-remote-services', 'abiquo-v2v']:
            if g in self.anaconda.id.abiquo.selectedGroups:
                self.dispatch.skipStep("abiquo_nfs_config", skip = 1, permanent = 1)

        if ('abiquo-remote-services' in self.anaconda.id.abiquo.selectedGroups):
            self.dispatch.skipStep("abiquo_rs", skip = 0)
            self.dispatch.skipStep("abiquo_v2v", skip = 1)
        else:
            self.dispatch.skipStep("abiquo_rs", skip = 1)
        
	if ('abiquo-v2v' in self.anaconda.id.abiquo.selectedGroups) and not \
		('abiquo-remote-services' in self.anaconda.id.abiquo.selectedGroups):
        		self.dispatch.skipStep("abiquo_v2v", skip = 0)
    	else:
		self.dispatch.skipStep("abiquo_v2v", skip = 1)
        
    def _selectionChanged(self, btn):
        lbl = btn.get_label()
        if btn.get_active():
            if lbl == 'Abiquo Server':
                self.data.abiquo.selectedGroups.append('abiquo-server')
            elif lbl == 'Abiquo Remote Services':
                self.data.abiquo.selectedGroups.append('abiquo-remote-services')
            elif lbl == 'Abiquo V2V Services':
                self.data.abiquo.selectedGroups.append('abiquo-v2v')
        else:
            if lbl == 'Abiquo Server':
                self.data.abiquo.selectedGroups.remove('abiquo-server')
            elif lbl == 'Abiquo Remote Services':
                self.data.abiquo.selectedGroups.remove('abiquo-remote-services')
            elif lbl == 'Abiquo V2V Services':
                self.data.abiquo.selectedGroups.remove('abiquo-v2v')

    def getScreen (self, anaconda):
        self.anaconda = anaconda
        self.data = anaconda.id
        self.backend = anaconda.backend
        self.dispatch = anaconda.dispatch
        
        (self.xml, vbox) = gui.getGladeWidget("abiquo_distributed.glade", "settingsBox")
        for g in self.data.abiquo.selectedGroups:
            if g == 'abiquo-server':
                self.xml.get_widget('abiquoServerRadio').set_active(True)
            elif g == 'abiquo-v2v':
                self.xml.get_widget('abiquoV2VRadio').set_active(True)
            elif g == 'abiquo-remote-services':
                self.xml.get_widget('abiquoRSRadio').set_active(True)
            else:
                pass
        for btn in ['abiquoServerRadio', 'abiquoRSRadio', 'abiquoV2VRadio']:
            self.xml.get_widget(btn).connect(
                    'toggled',
                    self._selectionChanged)
        return vbox
