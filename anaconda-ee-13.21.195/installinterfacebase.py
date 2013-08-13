#
# installinterfacebase.py: a baseclass for anaconda interface classes
#
# Copyright (C) 2010  Red Hat, Inc.  All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author(s): Hans de Goede <hdegoede@redhat.com>

import gettext
import sys

_ = lambda x: gettext.ldgettext("anaconda", x)
P_ = lambda x, y, z: gettext.ldngettext("anaconda", x, y, z)

class InstallInterfaceBase(object):
    def __init__(self):
        self._warnedUnusedRaidMembers = []

    def messageWindow(self, title, text, type="ok", default = None,
             custom_buttons=None,  custom_icon=None):
        raise NotImplementedError

    def detailedMessageWindow(self, title, text, longText=None, type="ok",
                              default=None, custom_icon=None,
                              custom_buttons=[]):
        raise NotImplementedError

    def methodstrRepoWindow(self, methodstr, exception):
        """ Called when the repo specified by methodstr could not be found.

            Depending on the interface implementation terminates the program or
            gives user a chance to specify a new repo path it then returns. The
            default implementation is to terminate.
        """
        self.messageWindow(
            _("Error Setting Up Repository"),
            _("The following error occurred while setting up the "
              "installation repository:\n\n%(e)s\n\n"
              "Installation can not continue.")
            % {'e': exception},
            type = "custom",
            custom_icon="info",
            custom_buttons=[_("Exit installer")])
        sys.exit(0)

    def unusedRaidMembersWarning(self, unusedRaidMembers):
        """Warn about unused BIOS RAID members"""
        unusedRaidMembers = \
            filter(lambda m: m not in self._warnedUnusedRaidMembers,
                   unusedRaidMembers)
        if unusedRaidMembers:
            self._warnedUnusedRaidMembers.extend(unusedRaidMembers)
            unusedRaidMembers.sort()
            self.messageWindow(_("Warning"),
                P_("Disk %s contains BIOS RAID metadata, but is not part of "
                   "any recognized BIOS RAID sets. Ignoring disk %s." %
                   (", ".join(unusedRaidMembers),
                    ", ".join(unusedRaidMembers)),
                   "Disks %s contain BIOS RAID metadata, but are not part of "
                   "any recognized BIOS RAID sets. Ignoring disks %s." %
                   (", ".join(unusedRaidMembers),
                    ", ".join(unusedRaidMembers)),
                   len(unusedRaidMembers)),
                custom_icon="warning")

    def questionInitializeDASD(self, c, devs):
        """Ask if unformatted DASD's should be formatted"""
        title = P_("Unformatted DASD Device Found",
                   "Unformatted DASD Devices Found", c)
        msg = P_("Format uninitialized DASD device?\n\n"
                 "There is %d uninitialized DASD device on this "
                 "system.  To continue installation, the device must "
                 "be formatted.  Formatting will remove any data on "
                 "this device." % c,
                 "Format uninitialized DASD devices?\n\n"
                 "There are %d uninitialized DASD devices on this "
                 "system.  To continue installation, the devices must "
                 "be formatted.  Formatting will remove any data on "
                 "these devices." % c,
                 c)
        icon = "/usr/share/icons/gnome/32x32/status/dialog-error.png"
        buttons = [_("_Format"), _("_Ignore")]
        return self.detailedMessageWindow(title, msg, devs.strip(),
                                             type="custom",
                                             custom_icon=icon,
                                             custom_buttons=buttons,
                                             expanded=True)

    def hardwareError(self, exception):
        text=_("The installation was stopped due to what seems to be a problem "
               "with your hardware. The exact error message is:\n\n%s.\n\n "
               "The installer will now terminate.") % str(exception)
        self.messageWindow(title=_("Hardware Error Encountered"),
                           text=text,
                           type="custom",
                           custom_icon="error",
                           custom_buttons=[_("_Exit installer")])
        sys.exit(0)
