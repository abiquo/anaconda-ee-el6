#
# task_gui.py: Choose tasks for installation
#
# Copyright 2006 Red Hat, Inc.
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
from constants import *
import network

from yuminstall import AnacondaYumRepo
import yum.Errors

import logging
log = logging.getLogger("anaconda")

# !!! Complete description
DESC_ABI_PLATFORM = """
<b>Abiquo Platform</b>

The installation types and main components are as follows:

<u>Monolithic</u>
For small installations. Includes: Abiquo Server, Remote Services, V2V Services

<u>Distributed</u>
For large installations. Select combination of: Abiquo Server or only GUI or API, Abiquo Remote Services or Abiquo Public Cloud Services,  and Abiquo V2V Services.

"""

# Additional Components:
# NFS Repository
# DHCP Relay
# Remote HTTP repository not implemented yet
class AbiquoAdditionalTasks(gtk.TreeView):
    def __init__(self,anaconda):
        self.anaconda = anaconda
        self.selected_tasks = []
        gtk.TreeView.__init__(self)

        self._setupStore()
        cbr = gtk.CellRendererToggle()
        col = gtk.TreeViewColumn('', cbr, active = 0)
        cbr.connect("toggled", self._taskToggled)
        self.append_column(col)

        col = gtk.TreeViewColumn('Abiquo Additional Components', gtk.CellRendererText(), text = 1)
        col.set_clickable(False)
        self.append_column(col)

    def _setupStore(self):
        self.store = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING, gobject.TYPE_STRING)
        #self.store.append([('abiquo-remote-repository' in self.anaconda.id.abiquo.selectedGroups), "Abiquo Remote Repository", 'abiquo-remote-repository'])
        self.store.append([('abiquo-dhcp-relay' in self.anaconda.id.abiquo.selectedGroups), "Abiquo DHCP Relay", 'abiquo-dhcp-relay'])
        self.store.append([('abiquo-nfs-repository' in self.anaconda.id.abiquo.selectedGroups), "Abiquo NFS Repository", 'abiquo-nfs-repository'])
        self.set_model(self.store)

        # for g in ['abiquo-nfs-repository', 'abiquo-remote-repository', 'abiquo-dhcp-relay']:
        for g in ['abiquo-nfs-repository', 'abiquo-dhcp-relay']:
            if (g in self.anaconda.id.abiquo.selectedGroups):
                self.selected_tasks.append(g)

    def _taskToggled(self, path, row):
        i = self.store.get_iter(int(row))
        val = self.store.get_value(i, 0)
        self.store.set_value(i, 0, not val)
        comp = self.store.get_value(i, 2)
        if not val:
            self.selected_tasks.append(comp)
            self.anaconda.id.abiquo.selectedGroups.append(comp)
        else:
            self.selected_tasks.remove(comp)
            self.anaconda.id.abiquo.selectedGroups.remove(comp)


# Platform Task
# List of Abiquo Groups
# Abiquo Platform
# Abiquo Storage Server
# Abiquo Hypervisor
# Abiquo Additional Components

class AbiquoPlatformTasks(gtk.TreeView):
    def __init__(self, anaconda):
        self.anaconda = anaconda
        gtk.TreeView.__init__(self)

        self._setupStore()
        cbr = gtk.CellRendererToggle()
        cbr.set_radio(True)
        col = gtk.TreeViewColumn('', cbr, active = 0)
        cbr.connect("toggled", self._taskToggled)
        self.append_column(col)
        col = gtk.TreeViewColumn('Available Components', gtk.CellRendererText(), text = 1)
        col.set_clickable(False)
        self.append_column(col)

    def _setupStore(self):
        self.store = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING, gobject.TYPE_STRING)

        # Check if no abiquo groups have been selected
        sel = True
        for g in ['abiquo-server', 'abiquo-remote-services', 'abiquo-v2v', 'abiquo-monolithic','abiquo-ui','abiquo-standalone-api','abiquo-public-cloud']:
            if g in self.anaconda.id.abiquo.selectedGroups:
                sel = False
        self.store.append([sel, "None", 'none'])

        # check if monolithic previously selected
        self.store.append([('abiquo-monolithic' in self.anaconda.id.abiquo.selectedGroups), "Monolithic Install", 'abiquo-monolithic'])
        # self.store.append([sel, "Monolithic Install", 'abiquo-monolithic'])

        # check if distributed previously selected
        sel = False
        for g in ['abiquo-server', 'abiquo-remote-services', 'abiquo-v2v', 'abiquo-ui','abiquo-standalone-api','abiquo-public-cloud']:
            if g in self.anaconda.id.abiquo.selectedGroups:
                sel = True
        self.store.append([sel, "Distributed Install", 'abiquo-distributed'])
        self.set_model(self.store)

    def _taskToggled(self, path, row):
        i = self.store.get_iter(int(row))
        for row in self.store:
            row[0] = False
            
        val = self.store.get_value(i, 0)
        self.store.set_value(i, 0, not val)
        comp = self.store.get_value(i, 2)
        self.selected_task = comp
        if comp != 'none':
            log.info("Adding %s to selected groups" % self.selected_task)
            self.anaconda.id.abiquo.selectedGroups.append(self.selected_task)

        for row in self.store:
            if not row[0] and \
                    (row[2] != 'none') and \
                    (row[2] in self.anaconda.id.abiquo.selectedGroups):
                        self.anaconda.id.abiquo.selectedGroups.remove(row[2])

# KVM
# Legacy hypervisors XEN and VirtualBox not supported now
class AbiquoHypervisorTasks(AbiquoPlatformTasks):
 
     def __init__(self, anaconda):
        AbiquoPlatformTasks.__init__(self, anaconda)
     
     def _setupStore(self):
         self.store = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING, gobject.TYPE_STRING)
         
         sel = True
         # for g in ['abiquo-kvm', 'abiquo-xen', 'abiquo-virtualbox']:
         for g in ['abiquo-kvm']:
            if g in self.anaconda.id.abiquo.selectedGroups:
                sel = False
         self.store.append([sel, "None", 'none'])
         self.store.append([('abiquo-kvm' in self.anaconda.id.abiquo.selectedGroups), "KVM Cloud Node", 'abiquo-kvm'])
         # self.store.append([('abiquo-xen' in self.anaconda.id.abiquo.selectedGroups), "Xen Cloud Node", 'abiquo-xen'])
         # self.store.append([('abiquo-virtualbox' in self.anaconda.id.abiquo.selectedGroups), "VirtualBox Cloud Node", 'abiquo-virtualbox'])
         self.set_model(self.store)

class AbiquoStorageTasks(AbiquoPlatformTasks):

    def __init__(self, anaconda):
        AbiquoPlatformTasks.__init__(self, anaconda)
    
    def _setupStore(self):
        self.store = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING, gobject.TYPE_STRING)
        
        sel = True
        for g in ['abiquo-lvm-storage-server']:
            if g in self.anaconda.id.abiquo.selectedGroups:
                sel = False
        self.store.append([sel, "None", 'none'])
        self.store.append([('abiquo-lvm-storage-server' in self.anaconda.id.abiquo.selectedGroups), "Abiquo LVM Server", 'abiquo-lvm-storage-server'])
        self.set_model(self.store)

class TaskWindow(InstallWindow):

    def getNext(self):
        log.info('Finished group selection: %s' % self.anaconda.id.abiquo.selectedGroups)

        self.dispatch.skipStep("abiquo_password", skip = 1)
        self.dispatch.skipStep("abiquo_nfs_config", skip = 1)
        self.dispatch.skipStep("abiquo_rs", skip = 1)
        self.dispatch.skipStep("abiquo_v2v", skip = 1)
        self.dispatch.skipStep("abiquo_hv", skip = 1)
        self.dispatch.skipStep("abiquo_distributed", skip = 1)
        self.dispatch.skipStep("abiquo_dhcp_relay", skip = 1)

        for g in self.abiquo_groups:
            if g in self.anaconda.id.abiquo.selectedGroups:
                log.info("Selecting group: %s " % g)
                map(lambda x: self.backend.selectGroup(x), [g])
       
        for g in ['abiquo-server', 'abiquo-monolithic']:
            if g in self.anaconda.id.abiquo.selectedGroups:
                self.dispatch.skipStep("abiquo_password", skip = 0)

        if 'abiquo-distributed' in self.anaconda.id.abiquo.selectedGroups:
            self.dispatch.skipStep("abiquo_distributed", skip = 0)
        if 'abiquo-dhcp-relay' in self.anaconda.id.abiquo.selectedGroups:
            self.dispatch.skipStep("abiquo_dhcp_relay", skip = 0)
        
    def _task_store_sel_changed(self, tree_selection):
        lbl = self.xml.get_widget("taskDescLabel")
        model, iter = tree_selection.get_selected()
        selection = model.get_value(iter, 0)
        w = self.xml.get_widget("subtaskSW")
        if w.get_child():
            w.remove(w.get_child())
        if selection == "Abiquo Platform":
            w.add(self.abiquo_platform_tasks)
            self.abiquo_platform_tasks.show()
        elif selection == "Cloud Node":
            w.add(self.abiquo_hypervisor_tasks)
            self.abiquo_hypervisor_tasks.show()
        elif selection == "Storage Servers":
            w.add(self.abiquo_storage_tasks)
            self.abiquo_storage_tasks.show()
        elif selection == "Additional Components":
            w.add(self.abiquo_additional_tasks)
            self.abiquo_additional_tasks.show()
        else:
            pass

        lbl.set_markup(self.tasks_descriptions[selection])

    def _createTaskStore(self):
        store = gtk.ListStore(str)
        tl = self.xml.get_widget("taskList")
        tl.set_model(store)
        sel = tl.get_selection()
        sel.connect('changed', self._task_store_sel_changed)


        col = gtk.TreeViewColumn('Text', gtk.CellRendererText(), text = 0)
        col.set_clickable(False)
        tl.append_column(col)

        for k in self.installer_tasks:
            store.append([k])

    def getScreen (self, anaconda):
        self.intf = anaconda.intf
        self.dispatch = anaconda.dispatch
        self.backend = anaconda.backend
        self.anaconda = anaconda
        self.abiquo_groups = ['abiquo-monolithic',
                  'abiquo-server', 'abiquo-remote-services', 'abiquo-v2v',
                  'abiquo-ui','abiquo-standalone-api','abiquo-public-cloud',
                  'abiquo-lvm-storage-server', 'abiquo-kvm',
                  'abiquo-dhcp-relay', 'abiquo-nfs-repository',
                  'abiquo-remote-repository'
                  ]

        self.tasks = anaconda.id.instClass.tasks
        
        (self.xml, vbox) = gui.getGladeWidget("tasksel.glade", "mainWidget")
        (self.diag1_xml, diag) = gui.getGladeWidget("tasksel.glade", "dialog1")

        lbl = self.xml.get_widget("mainLabel")

        self.installer_tasks = ["Abiquo Platform", "Cloud Node", "Storage Servers", "Additional Components"]
        self.tasks_descriptions = {
            "Abiquo Platform": DESC_ABI_PLATFORM,
            "Cloud Node": "<b>Cloud Node</b>\nInstall Abiquo KVM (OpenSource hypervisor tested and supported by Abiquo).",
            "Storage Servers": "<b>Storage Servers</b>\nInstall required servers to manage external storage.",
            "Additional Components": "<b>Additional Components</b>\nNFS Repository, etc.",
        }

        self._createTaskStore()
        self.abiquo_platform_tasks = AbiquoPlatformTasks(anaconda)
        self.abiquo_hypervisor_tasks = AbiquoHypervisorTasks(anaconda)
        self.abiquo_storage_tasks = AbiquoStorageTasks(anaconda)
        self.abiquo_additional_tasks = AbiquoAdditionalTasks(anaconda)
        w = self.xml.get_widget("subtaskSW")
        w.add(self.abiquo_platform_tasks)
        self.abiquo_platform_tasks.show()
        return vbox
