#
# abiquo_password.py: gui root password and user creation dialog
#
# Copyright 20011 Abiquo, Inc.
#
# This software may be freely redistributed under the terms of the GNU
# library public license.
#
# You should have received a copy of the GNU Library Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import gtk
import gobject
import re
import string
import gui
from iw_gui import *
from flags import flags
import hashlib

class AbiquoPasswordWindow (InstallWindow):

    windowTitle = "Set Abiquo Cloud Administrator Password"

    def getNext (self):
        def passwordError():
            self.pw.set_text("")
            self.confirm.set_text("")
            self.pw.grab_focus()            
            raise gui.StayOnScreen
            
	if not self.__dict__.has_key("pw"): return None

        pw = self.pw.get_text()
        confirm = self.confirm.get_text()

        if not pw or not confirm:
            self.intf.messageWindow("Error with Password",
                                    "You must enter your cloud admin password "
                                      "and confirm it by typing it a second "
                                      "time to continue.",
                                    custom_icon="error")
            passwordError()

        if pw != confirm:
            self.intf.messageWindow("Error with Password",
                                    "The passwords you entered were "
                                      "different.  Please try again.",
                                    custom_icon="error")
            passwordError()

        if len(pw) < 6:
            self.intf.messageWindow("Error with Password",
                                    "The cloud admin password must be at least "
                                      "six characters long.",
                                    custom_icon="error")
            passwordError()
        
        allowed = string.digits + string.ascii_letters + string.punctuation + " "
        for letter in pw:
            if letter not in allowed:
                self.intf.messageWindow("Error with Password",
                                        "Requested password contains "
                                          "non-ascii characters which are "
                                          "not allowed for use in password.",
                                        custom_icon="error")
                passwordError()

	passwd = self.pw.get_text()
	m = hashlib.md5()
	m.update(passwd)
        self.idata.abiquoPasswordHex = m.hexdigest()
	self.idata.abiquoPassword = passwd
        return None

    def setFocus (self, area, data):
        self.pw.grab_focus ()

    # AccountWindow tag="accts"
    def getScreen (self, anaconda):
	self.abiquoPassword = anaconda.id.abiquoPassword
        self.intf = anaconda.intf
	self.idata = anaconda.id

        box = gtk.VBox (spacing=6)
        box.set_border_width(5)

        #hbox = gtk.HBox()
        #pix = gui.readImageFromFile ("root-password.png")
        #if pix:
        #    hbox.pack_start (pix, False)

	label = gtk.Label("")
	label.set_markup("<b><big>Abiquo Cloud Administrator (admin) password</big></b>")
        label.set_alignment(0.0, 0.5)
	box.pack_start(label, False)

        #box.pack_start(hbox, False)
       
        self.forward = lambda widget, box=box: box.emit('focus', gtk.DIR_TAB_FORWARD)
        
        table = gtk.Table (2, 2)
        table.set_size_request(365, -1)
        table.set_row_spacings (5)
	table.set_col_spacings (5)

        pass1 = gui.MnemonicLabel("Password: ")
        pass1.set_alignment (0.0, 0.5)
        table.attach (pass1, 0, 1, 0, 1, gtk.FILL, 0, 10)
        pass2 = gui.MnemonicLabel("Confirm: ")
        pass2.set_alignment (0.0, 0.5)
        table.attach (pass2, 0, 1, 1, 2, gtk.FILL, 0, 10)
        self.pw = gtk.Entry (128)
        pass1.set_mnemonic_widget(self.pw)
        
        self.pw.connect ("activate", self.forward)
        self.pw.connect ("map-event", self.setFocus)
        self.pw.set_visibility (False)
        self.confirm = gtk.Entry (128)
        pass2.set_mnemonic_widget(self.confirm)
        self.confirm.connect ("activate", self.forward)
        self.confirm.set_visibility (False)
        table.attach (self.pw,      1, 2, 0, 1, gtk.FILL|gtk.EXPAND, 5)
        table.attach (self.confirm, 1, 2, 1, 2, gtk.FILL|gtk.EXPAND, 5)

        hbox = gtk.HBox()
        hbox.pack_start(table, False)
        box.pack_start (hbox, False)
	
# Description
	label = gtk.Label("")
        label.set_markup("The Cloud Administrator account is used for "
                           "administering Abiquo.\n\n"
                           "<b>Default user:</b> admin\n"
                           "<b>Default password:</b> xabiquo")
        label.set_line_wrap(True)
        label.set_size_request(400, -1)
        label.set_alignment(0.0, 0.5)
        box.pack_start(label, False)

        # root password statusbar
        self.rootStatus = gtk.Label ("")
        wrapper = gtk.HBox(0, False)
        wrapper.pack_start (self.rootStatus)
        box.pack_start (wrapper, False)

	self.pw.set_text(self.abiquoPassword)
	self.confirm.set_text(self.abiquoPassword)
        
        return box
