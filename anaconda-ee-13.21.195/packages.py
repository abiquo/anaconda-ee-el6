#
# packages.py: package management - mainly package installation
#
# Copyright (C) 2001, 2002, 2003, 2004, 2005, 2006  Red Hat, Inc.
# All rights reserved.
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
# Author(s): Erik Troan <ewt@redhat.com>
#            Matt Wilson <msw@redhat.com>
#            Michael Fulbright <msf@redhat.com>
#            Jeremy Katz <katzj@redhat.com>
#

import glob
import iutil
import isys
import os
import time
import sys
import string
import language
import shutil
import traceback
from flags import flags
from product import *
from constants import *
from upgrade import bindMountDevDirectory
from storage.errors import *
from abiquo_postinstall import *


import logging
log = logging.getLogger("anaconda")

import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)

def doPostAction(anaconda):
    abiquoPostInstall(anaconda)

def firstbootConfiguration(anaconda):
    if anaconda.id.firstboot == FIRSTBOOT_RECONFIG:
        f = open(anaconda.rootPath + '/etc/reconfigSys', 'w+')
        f.close()
    elif anaconda.id.firstboot == FIRSTBOOT_SKIP:
        f = open(anaconda.rootPath + '/etc/sysconfig/firstboot', 'w+')
        f.write('RUN_FIRSTBOOT=NO')
        f.close()

    return

def writeKSConfiguration(anaconda):
    log.info("Writing autokickstart file")
    fn = anaconda.rootPath + "/root/anaconda-ks.cfg"

    anaconda.id.writeKS(fn)

def copyAnacondaLogs(anaconda):
    log.info("Copying anaconda logs")
    for (fn, dest) in (("/tmp/anaconda.log", "anaconda.log"),
                       ("/tmp/syslog", "anaconda.syslog"),
                       ("/tmp/X.log", "anaconda.xlog"),
                       ("/tmp/program.log", "anaconda.program.log"),
                       ("/tmp/storage.log", "anaconda.storage.log"),
                       ("/tmp/ifcfg.log", "anaconda.ifcfg.log"),
                       ("/tmp/yum.log", "anaconda.yum.log")):
        if os.access(fn, os.R_OK):
            try:
                shutil.copyfile(fn, "%s/var/log/%s" %(anaconda.rootPath, dest))
                os.chmod("%s/var/log/%s" %(anaconda.rootPath, dest), 0600)
            except:
                pass

def turnOnFilesystems(anaconda):
    if anaconda.dir == DISPATCH_BACK:
        if not anaconda.id.upgrade:
            log.info("unmounting filesystems")
            anaconda.id.storage.umountFilesystems()
        return DISPATCH_NOOP

    if not anaconda.id.upgrade:
        if not anaconda.id.storage.fsset.active:
            # turn off any swaps that we didn't turn on
            # needed for live installs
            iutil.execWithRedirect("swapoff", ["-a"],
                                   stdout = "/dev/tty5", stderr="/dev/tty5")
        anaconda.id.storage.devicetree.teardownAll()

    upgrade_migrate = False
    if anaconda.id.upgrade:
        for d in anaconda.id.storage.migratableDevices:
            if d.format.migrate:
                upgrade_migrate = True

    title = None
    message = None
    details = None

    try:
        anaconda.id.storage.doIt()
    except DeviceResizeError as (msg, device):
        # XXX does this make any sense? do we support resize of
        #     devices other than partitions?
        title = _("Device Resize Failed")
        message = _("An error was encountered while "
                    "resizing device %s.") % (device,)
        details = msg
    except DeviceCreateError as (msg, device):
        title = _("Device Creation Failed")
        message = _("An error was encountered while "
                    "creating device %s.") % (device,)
        details = msg
    except DeviceDestroyError as (msg, device):
        title = _("Device Removal Failed")
        message = _("An error was encountered while "
                    "removing device %s.") % (device,)
        details = msg
    except DeviceError as (msg, device):
        title = _("Device Setup Failed")
        message = _("An error was encountered while "
                    "setting up device %s.") % (device,)
        details = msg
    except FSResizeError as (msg, device):
        title = _("Resizing Failed")
        message = _("There was an error encountered while "
                    "resizing the device %s.") % (device,)

        if os.path.exists("/tmp/resize.out"):
            details = open("/tmp/resize.out", "r").read()
        else:
            details = "%s" %(msg,)
    except FSMigrateError as (msg, device):
        title = _("Migration Failed")
        message = _("An error was encountered while "
                    "migrating filesystem on device %s.") % (device,)
        details = msg
    except FormatCreateError as (msg, device):
        title = _("Formatting Failed")
        message = _("An error was encountered while "
                    "formatting device %s.") % (device,)
        details = msg
    except Exception as e:
        # catch-all
        title = _("Storage Activation Failed")
        message = _("An error was encountered while "
                    "activating your storage configuration.")
        details = str(e)

    if title:
        rc = anaconda.intf.detailedMessageWindow(title, message, details,
                            type = "custom",
                            custom_buttons = [_("_File Bug"), _("_Exit installer")])

        if rc == 0:
            raise
        elif rc == 1:
            sys.exit(1)

    if not anaconda.id.upgrade:
        anaconda.id.storage.turnOnSwap()
        anaconda.id.storage.mountFilesystems(raiseErrors=False,
                                             readOnly=False,
                                             skipRoot=anaconda.backend.skipFormatRoot)
    else:
        if upgrade_migrate:
            # we should write out a new fstab with the migrated fstype
            shutil.copyfile("%s/etc/fstab" % anaconda.rootPath,
                            "%s/etc/fstab.anaconda" % anaconda.rootPath)
            anaconda.id.storage.fsset.write(anaconda.rootPath)

        # and make sure /dev is mounted so we can read the bootloader
        bindMountDevDirectory(anaconda.rootPath)


def setupTimezone(anaconda):
    # we don't need this on an upgrade or going backwards
    if anaconda.id.upgrade or anaconda.dir == DISPATCH_BACK:
        return

    os.environ["TZ"] = anaconda.id.timezone.tz
    tzfile = "/usr/share/zoneinfo/" + anaconda.id.timezone.tz
    tzlocalfile = "/etc/localtime"
    if not os.access(tzfile, os.R_OK):
        log.error("unable to set timezone")
    else:
        try:
            os.remove(tzlocalfile)
        except OSError:
            pass
        try:
            shutil.copyfile(tzfile, tzlocalfile)
        except OSError as e:
            log.error("Error copying timezone (from %s): %s" %(tzfile, e.strerror))

    if iutil.isS390():
        return
    args = [ "--hctosys" ]
    if anaconda.id.timezone.utc:
        args.append("-u")

    try:
        iutil.execWithRedirect("/usr/sbin/hwclock", args, stdin = None,
                               stdout = "/dev/tty5", stderr = "/dev/tty5")
    except RuntimeError:
        log.error("Failed to set clock")


# FIXME: this is a huge gross hack.  hard coded list of files
# created by anaconda so that we can not be killed by selinux
def setFileCons(anaconda):
    def lst(root):
        rc = [root]
        for (root, dirs, files) in os.walk(root):
            rc.extend(map(lambda d: root+"/"+d, dirs))
            rc.extend(map(lambda d: root+"/"+d, files))

        return rc

    if flags.selinux:
        log.info("setting SELinux contexts for anaconda created files")

        files = ["/etc/rpm/macros", "/etc/dasd.conf", "/etc/zfcp.conf",
                 "/etc/lilo.conf.anaconda", "/lib64", "/usr/lib64",
                 "/etc/blkid.tab", "/etc/blkid.tab.old", 
                 "/etc/mtab", "/etc/fstab", "/etc/resolv.conf",
                 "/etc/modprobe.conf", "/etc/modprobe.conf~",
                 "/var/log/wtmp", "/var/run/utmp", "/etc/crypttab",
                 "/dev/log", "/var/lib/rpm", "/", "/etc/raidtab",
                 "/etc/mdadm.conf", "/etc/sysconfig/network",
                 "/etc/udev/rules.d/70-persistent-net.rules",
                 "/root/install.log", "/root/install.log.syslog",
                 "/etc/shadow", "/etc/shadow-", "/etc/gshadow",
                 "/etc/zipl.conf"] + glob.glob('/etc/dhcp/dhclient-*.conf')

        vgs = ["/dev/%s" % vg.name for vg in anaconda.id.storage.vgs]
        for f in files + vgs:
            isys.resetFileContext(os.path.normpath(f), anaconda.rootPath)

        # ugh, this is ugly
        for d in ["/etc/sysconfig/network-scripts", "/var/cache/yum", "/var/lib/rpm", "/var/lib/yum", "/etc/lvm", "/dev/mapper", "/etc/iscsi", "/var/lib/iscsi", "/root", "/var/log", "/etc/modprobe.d", "/etc/sysconfig" ]:
            if not os.path.isdir(anaconda.rootPath + d):
                continue

            # This is stupid, but resetFileContext expects to get the path
            # without "/mnt/sysimage" in front, whereas everything else needs
            # it there.  So we add it to get the list of files, then
            # immediately remove it, then pass it back to resetFileContext
            # anyway.
            for f in map(lambda f: f.replace(anaconda.rootPath, ""),
                         filter(lambda f: os.access(f, os.R_OK),
                                lst(anaconda.rootPath+d))):
                ret = isys.resetFileContext(os.path.normpath(f),
                                            anaconda.rootPath)

    return

# FIXME: using rpm directly here is kind of lame, but in the yum backend
# we don't want to use the metadata as the info we need would require
# the filelists.  and since we only ever call this after an install is
# done, we can be guaranteed this will work.  put here because it's also
# used for livecd installs
def rpmKernelVersionList(rootPath = "/"):
    import rpm

    def get_version(header):
        for f in header['filenames']:
            if f.startswith('/boot/vmlinuz-'):
                return f[14:]
            elif f.startswith('/boot/efi/EFI/redhat/vmlinuz-'):
                return f[29:]
        return ""

    def get_tag(header):
        if header['name'] == "kernel":
            return "base"
        elif header['name'].startswith("kernel-"):
            return header['name'][7:]
        return ""

    versions = []

    iutil.resetRpmDb(rootPath)
    ts = rpm.TransactionSet(rootPath)

    mi = ts.dbMatch('provides', 'kernel')
    for h in mi:
        v = get_version(h)
        tag = get_tag(h)
        if v == "" or tag == "":
            log.warning("Unable to determine kernel type/version for %s-%s-%s.%s" %(h['name'], h['version'], h['release'], h['arch'])) 
            continue
        # rpm really shouldn't return the same kernel more than once... but
        # sometimes it does (#467822)
        if (v, h['arch'], tag) in versions:
            continue
        versions.append( (v, h['arch'], tag) )

    return versions

def rpmSetupGraphicalSystem(anaconda):
    import rpm

    iutil.resetRpmDb(anaconda.rootPath)
    ts = rpm.TransactionSet(anaconda.rootPath)

    if iutil.isConsoleOnVirtualTerminal() and \
       (ts.dbMatch('provides', 'rhgb').count() or \
        ts.dbMatch('provides', 'plymouth').count()):
        anaconda.id.bootloader.args.append("quiet")
        anaconda.id.bootloader.args.append("rhgb")

    if ts.dbMatch('provides', 'service(graphical-login)').count() and \
       ts.dbMatch('provides', 'xorg-x11-server-Xorg').count() and \
       anaconda.id.displayMode == 'g' and not flags.usevnc:
        anaconda.id.desktop.setDefaultRunLevel(5)

#Recreate initrd for use when driver disks add modules
def recreateInitrd (kernelTag, instRoot):
    log.info("recreating initrd for %s" % (kernelTag,))
    iutil.execWithRedirect("/sbin/new-kernel-pkg",
                           [ "--mkinitrd", "--dracut", "--depmod", "--install", kernelTag ],
                           stdout = "/dev/null", stderr = "/dev/null",
                           root = instRoot)

def betaNagScreen(anaconda):
    publicBetas = { "Red Hat Linux": "Red Hat Linux Public Beta",
                    "Red Hat Enterprise Linux": "Red Hat Enterprise Linux",
                    "Fedora Core": "Fedora Core",
                    "Fedora": "Fedora" }

    
    if anaconda.dir == DISPATCH_BACK:
	return DISPATCH_NOOP

    fileagainst = None
    for (key, val) in publicBetas.items():
        if productName.startswith(key):
            fileagainst = val
    if fileagainst is None:
        fileagainst = "%s Beta" %(productName,)
    
    while 1:
	rc = anaconda.intf.messageWindow( _("Warning! This is pre-release software!"),
				 _("Thank you for downloading this "
				   "pre-release of %(productName)s.\n\n"
				   "This is not a final "
				   "release and is not intended for use "
				   "on production systems.  The purpose of "
				   "this release is to collect feedback "
				   "from testers, and it is not suitable "
				   "for day to day usage.\n\n"
				   "To report feedback, please visit:\n\n"
				   "   %(bugzillaUrl)s\n\n"
				   "and file a report against '%(fileagainst)s'.\n")
				 % {'productName': productName,
				    'bugzillaUrl': bugzillaUrl,
				    'fileagainst': fileagainst},
				   type="custom", custom_icon="warning",
				   custom_buttons=[_("_Exit"), _("_Install anyway")])

	if not rc:
            msg =  _("Your system will now be rebooted...")
            buttons = [_("_Back"), _("_Reboot")]
	    rc = anaconda.intf.messageWindow( _("Warning! This is pre-release software!"),
                                     msg,
                                     type="custom", custom_icon="warning",
                                     custom_buttons=buttons)
	    if rc:
		sys.exit(0)
	else:
	    break

def doReIPL(anaconda):
    if not iutil.isS390() or anaconda.dir == DISPATCH_BACK:
        return DISPATCH_NOOP

    anaconda.reIPLMessage = iutil.reIPL(anaconda, os.getppid())

    return DISPATCH_FORWARD
