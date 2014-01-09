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


        
	if ('abiquo-v2v' in self.anaconda.id.abiquo.selectedGroups) and not \
		('abiquo-remote-services' in self.anaconda.id.abiquo.selectedGroups):
        		self.dispatch.skipStep("abiquo_v2v", skip = 0)
    	else:
		self.dispatch.skipStep("abiquo_v2v", skip = 1)
        
    def _selectionChanged(self, btn):
        lbl = btn.get_name()
        #if not btn.get_sensitive():
        #    btn.set_active(False)
        if btn.get_active():
            if lbl == 'AbiquoServerRadio':
                self.data.abiquo.selectedGroups.append('abiquo-server')
                if ('abiquo-standalone-ui' in self.anaconda.id.abiquo.selectedGroups):
                    self.data.abiquo.selectedGroups.remove('abiquo-standalone-ui')
                if ('abiquo-standalone-api' in self.anaconda.id.abiquo.selectedGroups):
                    self.data.abiquo.selectedGroups.remove('abiquo-standalone-api')
                self.xml.get_widget('AbiquoGUIRadio').set_active(False)
                self.xml.get_widget('AbiquoGUIRadio').set_sensitive(False)
                self.xml.get_widget('AbiquoAPIRadio').set_active(False)
                self.xml.get_widget('AbiquoAPIRadio').set_sensitive(False)
            elif lbl == 'AbiquoRSRadio':
                self.data.abiquo.selectedGroups.append('abiquo-remote-services')
                if ('abiquo-public-services' in self.anaconda.id.abiquo.selectedGroups):
                    self.data.abiquo.selectedGroups.remove('abiquo-public-services')
                self.xml.get_widget('AbiquoPublicRadio').set_active(False)
                self.xml.get_widget('AbiquoPublicRadio').set_sensitive(False)
            elif lbl == 'AbiquoV2VRadio':
                self.data.abiquo.selectedGroups.append('abiquo-v2v')
            elif lbl == 'AbiquoGUIRadio':
                self.data.abiquo.selectedGroups.append('abiquo-standalone-ui')
            elif lbl == 'AbiquoAPIRadio':
                self.data.abiquo.selectedGroups.append('abiquo-standalone-api')
            elif lbl == 'AbiquoPublicRadio':
                self.data.abiquo.selectedGroups.append('abiquo-public-services')
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
            elif lbl == 'AbiquoGUIRadio' and ('abiquo-standalone-ui' in self.anaconda.id.abiquo.selectedGroups):
                self.data.abiquo.selectedGroups.remove('abiquo-standalone-ui')
            elif lbl == 'AbiquoAPIRadio' and ('abiquo-standalone-api' in self.anaconda.id.abiquo.selectedGroups):
                self.data.abiquo.selectedGroups.remove('abiquo-standalone-api')
            elif lbl == 'AbiquoPublicRadio' and ('abiquo-public-services' in self.anaconda.id.abiquo.selectedGroups):
                self.data.abiquo.selectedGroups.remove('abiquo-public-services')

    def getScreen (self, anaconda):
        self.anaconda = anaconda
        self.data = anaconda.id
        self.backend = anaconda.backend
        self.dispatch = anaconda.dispatch
        (self.xml, vbox) = gui.getGladeWidget("abiquo_distributed.glade", "settingsBox")

        for g in self.data.abiquo.selectedGroups:
            if g == 'abiquo-server':
                self.xml.get_widget('AbiquoServerRadio').set_active(True)
                self.xml.get_widget('AbiquoGUIRadio').set_sensitive(False)
                self.xml.get_widget('AbiquoAPIRadio').set_sensitive(False)
            elif g == 'abiquo-v2v':
                self.xml.get_widget('AbiquoV2VRadio').set_active(True)
            elif g == 'abiquo-remote-services':
                self.xml.get_widget('AbiquoRSRadio').set_active(True)
                self.xml.get_widget('AbiquoPublicRadio').set_sensitive(False)
            elif g == 'abiquo-standalone-ui':
                self.xml.get_widget('AbiquoGUIRadio').set_active(True)
            elif g == 'abiquo-standalone-api':
                self.xml.get_widget('AbiquoAPIRadio').set_active(True)
            elif g == 'abiquo-public-services':
                self.xml.get_widget('AbiquoPublicRadio').set_active(True)
            else:
                pass
        for btn in ['AbiquoServerRadio', 'AbiquoRSRadio', 'AbiquoV2VRadio', 'AbiquoGUIRadio', 'AbiquoAPIRadio','AbiquoPublicRadio']:
            self.xml.get_widget(btn).connect(
                    'toggled',
                    self._selectionChanged)
        return vbox
