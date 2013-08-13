#
# backend.py: Interface for installation backends
#
# Copyright (C) 2005, 2006, 2007  Red Hat, Inc.  All rights reserved.
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
# Author(s): Paul Nasrat <pnasrat@redhat.com>
#            Jeremy Katz <katzj@redhat.com>
#

import glob
import shutil
import iutil
import os, sys
import logging
from syslogd import syslog
from constants import *

import isys
import kickstart
import packages
import storage

from flags import flags
log = logging.getLogger("anaconda")

import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)

class AnacondaBackend:
    def __init__(self, anaconda):
        """Abstract backend class all backends should inherit from this
           @param instPath: root path for the installation to occur"""

        self.instPath = anaconda.rootPath
        self.instLog = None
        self.modeText = ""

        # some backends may not support upgrading
        self.supportsUpgrades = True
        self.supportsPackageSelection = False

        # some backends may have a special case for rootfs formatting
        # FIXME: we should handle this a little more elegantly
        self.skipFormatRoot = False
        self.rootFsType = None

        self._loopbackFile = None

    def postAction(self, anaconda):
        pass

    def doPreSelection(self, intf, id, instPath):
        pass

    def doPostSelection(self, anaconda):
        pass

    def doPreInstall(self, anaconda):
        self.initLog(anaconda.id, anaconda.rootPath)

    def copyFirmware(self, anaconda):
        # Multiple driver disks may be loaded, so we need to glob for all
        # the firmware files in the common DD firmware directory
        for f in glob.glob(DD_FIRMWARE+"/*"):
            try:
                shutil.copyfile(f, "%s/lib/firmware/" % anaconda.rootPath)
            except IOError, e:
                log.error("Could not copy firmware file %s: %s" % (f, e.strerror))

    def doPostInstall(self, anaconda):
        has_iscsi_disk = False

        # See if we have an iscsi disk. If we do we rerun mkinitrd, as
        # the initrd might need iscsi-initiator-utils, and chances are
        # it was not installed yet the first time mkinitrd was run, as
        # mkinitrd does not require it.
        root = anaconda.id.storage.rootDevice
        disks = anaconda.id.storage.devicetree.getDevicesByType("iscsi")
        for disk in disks:
            if root.dependsOn(disk):
                has_iscsi_disk = True
                break

        #always copy the firmware files from DD
        self.copyFirmware(anaconda)

        if anaconda.id.extraModules or has_iscsi_disk:
            for (n, arch, tag) in self.kernelVersionList(anaconda.rootPath):
                packages.recreateInitrd(n, anaconda.rootPath)

        #copy RPMS
        for d in glob.glob(DD_RPMS):
            try:
                shutil.copytree(d, anaconda.rootPath + "/root/" + os.path.basename(d))
            except OSError:
                log.error("Couldn't copy %s to %s" % (d, anaconda.rootPath + "/root/" + os.path.basename(d)))

        #copy modules and firmware
        if os.path.exists(DD_ALL):
            try:
                shutil.copytree(DD_ALL, anaconda.rootPath + "/root/DD")
            except OSError, e:
                log.error("Couldn't copy %s to %s" % (DD_ALL, anaconda.rootPath + "/root/DD"))

        storage.writeEscrowPackets(anaconda)

        sys.stdout.flush()
        syslog.stop()

    def doInstall(self, anaconda):
        log.warning("doInstall not implemented for backend!")
        raise NotImplementedError

    def initLog(self, id, instPath):
        upgrade = id.getUpgrade()

        if not os.path.isdir(instPath + "/root"):
            iutil.mkdirChain(instPath + "/root")

        if upgrade:
            logname = '/root/upgrade.log'
        else:
            logname = '/root/install.log'

        instLogName = instPath + logname
        try:
            shutil.rmtree (instLogName)
        except OSError:
            pass

        self.instLog = open(instLogName, "w+")

        syslogname = "%s%s.syslog" % (instPath, logname)
        try:
            shutil.rmtree (syslogname)
        except OSError:
            pass
        syslog.start (instPath, syslogname)

        if upgrade:
            self.modeText = _("Upgrading %s\n")
        else:
            self.modeText = _("Installing %s\n")

    def kernelVersionList(self, rootPath="/"):
        return []

    def getMinimumSizeMB(self, part):
        """Return the minimal size for part in megabytes if we can."""
        return 0

    def doBackendSetup(self, anaconda):
        log.warning("doBackendSetup not implemented for backend!")
        raise NotImplementedError

    def groupExists(self, group):
        log.warning("groupExists not implemented for backend!")
        raise NotImplementedError

    def selectGroup(self, group, *args):
        log.warning("selectGroup not implemented for backend!")
        raise NotImplementedError

    def deselectGroup(self, group, *args):
        log.warning("deselectGroup not implemented for backend!")
        raise NotImplementedError

    def packageExists(self, pkg):
        log.warning("packageExists not implemented for backend!")
        raise NotImplementedError
    
    def selectPackage(self, pkg, *args):
        log.warning("selectPackage not implemented for backend!")
        raise NotImplementedError

    def deselectPackage(self, pkg, *args):
        log.warning("deselectPackage not implemented for backend!")
        raise NotImplementedError

    def getDefaultGroups(self, anaconda):
        log.warning("getDefaultGroups not implemented for backend!")
        raise NotImplementedError

    def resetPackageSelections(self):
        # we just leave this one unimplemented if it's not needed
        pass

    # write out the %packages section of anaconda-ks.cfg
    def writePackagesKS(self, f, anaconda):
        log.warning("writePackagesKS not implemented for backend!")
        raise NotImplementedError

    # write out any config files that live on the installed system
    # (e.g., /etc/yum.repos.d/* files)
    def writeConfiguration(self):
        log.warning("writeConfig not implemented for backend!")
        raise NotImplementedError

    # write out any other kickstart bits the backend requires - no warning
    # here because this may not be needed
    def writeKS(self, f):
        pass

    def getRequiredMedia(self):
        log.warning("getRequiredMedia not implmented for backend!")
        raise NotImplementedError

    def complete(self, anaconda):
        pass

def doBackendSetup(anaconda):
    if anaconda.backend.doBackendSetup(anaconda) == DISPATCH_BACK:
        return DISPATCH_BACK

    if anaconda.id.upgrade:
        anaconda.backend.checkSupportedUpgrade(anaconda)
        iutil.writeRpmPlatform(anaconda.rootPath)

def doPostSelection(anaconda):
    return anaconda.backend.doPostSelection(anaconda)

def doPreInstall(anaconda):
    anaconda.backend.doPreInstall(anaconda)

def doPostInstall(anaconda):
    anaconda.backend.doPostInstall(anaconda)

def doInstall(anaconda):
    return anaconda.backend.doInstall(anaconda)

# does this need to be per-backend?  we'll just leave here until it does :)
def doBasePackageSelect(anaconda):
    if anaconda.isKickstart:
        anaconda.backend.resetPackageSelections()
        kickstart.selectPackages(anaconda)
    elif anaconda.id.displayMode != 't':
        anaconda.backend.resetPackageSelections()
        anaconda.id.instClass.setPackageSelection(anaconda)
        anaconda.id.instClass.setGroupSelection(anaconda)

def writeConfiguration(anaconda):
    log.info("Writing main configuration")
    anaconda.id.write()
    anaconda.backend.writeConfiguration()
