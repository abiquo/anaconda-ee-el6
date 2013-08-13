#
# platform.py:  Architecture-specific information
#
# Copyright (C) 2009
# Red Hat, Inc.  All rights reserved.
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
# Authors: Chris Lumens <clumens@redhat.com>
#

import iutil
import parted
import storage
from flags import flags
from storage.errors import *
from storage.formats import *
from storage.partspec import *

import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)
N_ = lambda x: x

class Platform(object):
    """Platform

       A class containing platform-specific information and methods for use
       during installation.  The intent is to eventually encapsulate all the
       architecture quirks in one place to avoid lots of platform checks
       throughout anaconda."""
    _bootFSTypes = ["ext3"]
    _disklabel_types = ["msdos"]
    _isEfi = iutil.isEfi()
    _minimumSector = 0
    _packages = []
    _supportsLvmBoot = False
    _supportsMdRaidBoot = False
    _minBootPartSize = 50
    _maxBootPartSize = 0

    def __init__(self, anaconda):
        """Creates a new Platform object.  This is basically an abstract class.
           You should instead use one of the platform-specific classes as
           returned by getPlatform below.  Not all subclasses need to provide
           all the methods in this class."""
        self.anaconda = anaconda

    def _mntDict(self):
        """Return a dictionary mapping mount points to devices."""
        ret = {}
        for device in [d for d in self.anaconda.id.storage.devices if d.format.mountable]:
            ret[device.format.mountpoint] = device

        return ret

    def bootDevice(self):
        """Return the device where /boot is mounted."""
        if self.__class__ is Platform:
            raise NotImplementedError("bootDevice not implemented for this platform")

        mntDict = self._mntDict()
        return mntDict.get("/boot", mntDict.get("/"))

    @property
    def defaultBootFSType(self):
        """Return the default filesystem type for the boot partition."""
        return self._bootFSTypes[0]

    @property
    def bootFSTypes(self):
        """Return a list of all valid filesystem types for the boot partition."""
        return self._bootFSTypes

    def bootloaderChoices(self, bl):
        """Return the default list of places to install the bootloader.
           This is returned as a dictionary of locations to (device, identifier)
           tuples.  If there is no boot device, an empty dictionary is
           returned."""
        if self.__class__ is Platform:
            raise NotImplementedError("bootloaderChoices not implemented for this platform")

        bootDev = self.bootDevice()
        ret = {}

        if not bootDev:
            return ret

        if bootDev.type == "mdarray":
            ret["boot"] = (bootDev.name, N_("RAID Device"))
            ret["mbr"] = (bl.drivelist[0], N_("Master Boot Record (MBR)"))
        else:
            ret["boot"] = (bootDev.name, N_("First sector of boot partition"))
            ret["mbr"] = (bl.drivelist[0], N_("Master Boot Record (MBR)"))

        return ret

    def checkBootRequest(self, req):
        """Perform an architecture-specific check on the boot device.  Not all
           platforms may need to do any checks.  Returns a list of errors if
           there is a problem, or [] otherwise."""
        errors = []

        if not req:
            return [_("You have not created a bootable partition.")]

        # most arches can't have boot on a logical volume
        if req.type == "lvmlv" and not self.supportsLvmBoot:
            errors.append(_("Bootable partitions cannot be on a logical volume."))

        # most arches can't have boot on RAID
        if req.type == "mdarray":
            if not self.supportsMdRaidBoot:
                errors.append(_("Bootable partitions cannot be on a RAID device."))
            elif req.level != 1:
                errors.append(_("Bootable partitions can only be on RAID1 devices."))

        # Make sure /boot is on a supported FS type.  This prevents crazy
        # things like boot on vfat.
        if not req.format.bootable or \
           (getattr(req.format, "mountpoint", None) == "/boot" and
            req.format.type not in self.bootFSTypes):
            errors.append(_("Bootable partitions cannot be on an %s filesystem.") % req.format.type)

        if req.type == "luks/dm-crypt":
            # Handle encrypted boot on a partition.
            errors.append(_("Bootable partitions cannot be on an encrypted block device"))
        else:
            # Handle encrypted boot on more complicated devices.
            for dev in filter(lambda d: d.type == "luks/dm-crypt", self.anaconda.id.storage.devices):
                if req in self.anaconda.id.storage.deviceDeps(dev):
                    errors.append(_("Bootable partitions cannot be on an encrypted block device"))

        return errors

    @property
    def diskLabelTypes(self):
        """A list of valid disklabel types for this architecture."""
        return self._disklabel_types

    @property
    def defaultDiskLabelType(self):
        """The default disklabel type for this architecture."""
        return self.diskLabelTypes[0]

    def requiredDiskLabelType(self, device_type):
        return None

    def bestDiskLabelType(self, device):
        """The best disklabel type for the specified device."""
        # if there's a required type for this device type, use that
        labelType = self.requiredDiskLabelType(device.partedDevice.type)
        log.debug("required disklabel type for %s (%s) is %s"
                  % (device.name, device.partedDevice.type, labelType))
        if not labelType:
            # otherwise, use the first supported type for this platform
            # that is large enough to address the whole device
            labelType = self.defaultDiskLabelType
            log.debug("default disklabel type for %s is %s" % (device.name,
                                                               labelType))
            for lt in self.diskLabelTypes:
                l = parted.freshDisk(device=device.partedDevice, ty=lt)
                if l.maxPartitionStartSector > device.partedDevice.length:
                    labelType = lt
                    log.debug("selecting %s disklabel for %s based on size"
                              % (labelType, device.name))
                    break

        return labelType

    @property
    def isEfi(self):
        return self._isEfi

    @property
    def minimumSector(self, disk):
        """Return the minimum starting sector for the provided disk."""
        return self._minimumSector

    @property
    def packages (self):
        if flags.cmdline.get('fips', None) == '1':
            return self._packages + ['dracut-fips']
        return self._packages

    def setDefaultPartitioning(self):
        """Return the default platform-specific partitioning information."""
        return [PartSpec(mountpoint="/boot", fstype=self.defaultBootFSType, size=500,
                         weight=self.weight(mountpoint="/boot"))]

    @property
    def supportsLvmBoot(self):
        """Does the platform support /boot on LVM logical volume?"""
        return self._supportsLvmBoot

    @property
    def supportsMdRaidBoot(self):
        """Does the platform support /boot on MD RAID?"""
        return self._supportsMdRaidBoot

    @property
    def minBootPartSize(self):
        return self._minBootPartSize

    @property
    def maxBootPartSize(self):
        return self._maxBootPartSize

    def validBootPartSize(self, size):
        """ Is the given size (in MB) acceptable for a boot device? """
        if not isinstance(size, int) and not isinstance(size, float):
            return False

        return ((not self.minBootPartSize or size >= self.minBootPartSize)
                and
                (not self.maxBootPartSize or size <= self.maxBootPartSize))

    def weight(self, fstype=None, mountpoint=None):
        """ Given an fstype (as a string) or a mountpoint, return an integer
            for the base sorting weight.  This is used to modify the sort
            algorithm for partition requests, mainly to make sure bootable
            partitions and /boot are placed where they need to be."""
        if mountpoint and mountpoint == "/boot":
            return 2000
        else:
            return 0

class EFI(Platform):
    _bootFSTypes = ["ext4", "ext3", "ext2"]
    _disklabel_types = ["gpt"]
    _minBootPartSize = 50

    def bootDevice(self):
        """
        Return the boot device. The bootloader.drivelist is used to
        set the precedence in cases where multiple partitions are
        available from multiple devices.
        """
        drive = self.anaconda.id.bootloader.drivelist[0]
        for part in self.anaconda.id.storage.partitions:
           if part.disk and part.disk.name == drive \
               and part.format.type == "efi" \
               and self.validBootPartSize(part.size):
                return part
        return None

    def bootloaderChoices(self, bl):
        bootDev = self.bootDevice()
        ret = {}

        if not bootDev:
            return ret

        ret["boot"] = (bootDev.name, N_("EFI System Partition"))
        return ret

    def checkBootRequest(self, req):
        """ Perform architecture-specific checks on the boot device.

            Returns a list of error strings.

            NOTE: X86 does not have a separate checkBootRequest method,
                  so this one must work for x86 as well as EFI.
        """
        if not req and self.isEfi:
            return [_("You have not created a /boot/efi partition.")]
        elif not req:
            return [_("You have not created a bootable partition.")]

        errors = Platform.checkBootRequest(self, req)

        if req.format.mountpoint == "/boot/efi":
            if req.format.type != "efi":
                errors.append(_("/boot/efi is not EFI."))

            # EFI also needs /boot to be on an extX partition, either as its own
            # partition or with / on extX. Get the format of whatever /boot is on
            mntDict = self._mntDict()
            boot_device = mntDict.get("/boot", mntDict.get("/"))
            boot_errors = Platform.checkBootRequest(self, boot_device)
            errors += boot_errors

        # Don't try to check the disklabel on lv's etc.
        partitions = []
        if req.type == "partition":
            partitions = [ req ]
        elif req.type == "mdarray":
            partitions = filter(lambda d: d.type == "partition", req.parents)

        # Check that we've got a correct disk label.
        for p in partitions:
            partedDisk = p.disk.format.partedDisk
            labelType = self.defaultDiskLabelType
            # Allow using gpt with x86, but not msdos with EFI
            if partedDisk.type != labelType and partedDisk.type != "gpt":
                errors.append(_("%s must have a %s disk label.")
                              % (p.disk.name, labelType.upper()))

        return errors

    def setDefaultPartitioning(self):
        ret = Platform.setDefaultPartitioning(self)
        ret.append(PartSpec(mountpoint="/boot/efi", fstype="efi", size=self._minBootPartSize,
                            maxSize=200, grow=True, weight=self.weight(fstype="efi")))
        return ret

    def weight(self, fstype=None, mountpoint=None):
        if fstype and fstype == "efi" or mountpoint and mountpoint == "/boot/efi":
            return 5000
        elif mountpoint and mountpoint == "/boot":
            return 2000
        else:
            return 0

class Alpha(Platform):
    _disklabel_types = ["bsd"]

    def checkBootRequest(self, req):
        errors = Platform.checkBootRequest(self, req)

        if not req or req.type != "partition" or not req.disk:
            return errors

        disk = req.disk.format.partedDisk

        # Check that we're a BSD disk label
        if not disk.type in self.diskLabelTypes:
            errors.append(_("%s must have a bsd disk label.") % req.disk.name)

        # The first free space should start at the beginning of the drive and
        # span for a megabyte or more.
        free = disk.getFirstPartition()
        while free:
            if free.type & parted.PARTITION_FREESPACE:
                break

            free = free.nextPartition()

        if not free or free.geoemtry.start != 1L or free.getSize(unit="MB") < 1:
            errors.append(_("The disk %s requires at least 1MB of free space at the beginning.") % req.disk.name)

        return errors

class IA64(EFI):
    _packages = ["elilo"]

    def __init__(self, anaconda):
        EFI.__init__(self, anaconda)

class PPC(Platform):
    _bootFSTypes = ["ext4", "ext3", "ext2"]
    _packages = ["yaboot"]
    _ppcMachine = iutil.getPPCMachine()
    _supportsMdRaidBoot = True

    @property
    def ppcMachine(self):
        return self._ppcMachine

    def checkBootRequest(self, req):
        errors = Platform.checkBootRequest(self, req)

        if req != self.bootDevice():
            # yaboot cannot find /boot on a logical partition
            if hasattr(req, "partedPartition") and req.isLogical:
                errors.append(_("The boot partition must be a primary partition."))

        return errors

class IPSeriesPPC(PPC):
    _minBootPartSize = 4
    _maxBootPartSize = 10

    def bootDevice(self):
        bootDev = None

        # We want the first PReP partition.
        for device in self.anaconda.id.storage.partitions:
            if device.format.type == "prepboot":
                bootDev = device
                break

        return bootDev

    def bootloaderChoices(self, bl):
        ret = {}

        bootDev = self.bootDevice()
        if not bootDev:
            return ret

        if bootDev.type == "mdarray":
            ret["boot"] = (bootDev.name, N_("RAID Device"))
            ret["mbr"] = (bl.drivelist[0], N_("Master Boot Record (MBR)"))
        else:
            ret["boot"] = (bootDev.name, N_("PPC PReP Boot"))

        return ret

    def checkBootRequest(self, req):
        errors = PPC.checkBootRequest(self, req)

        bootPart = getattr(req, "partedPartition", None)
        if not bootPart:
            return errors

        # All of the above just checks the PPC PReP boot partitions.  We still
        # need to make sure that whatever /boot is on also meets these criteria.
        if req == self.bootDevice():
            # However, this check only applies to prepboot.
            if bootPart.geometry.end * bootPart.geometry.device.sectorSize / (1024.0 * 1024) > 4096:
                errors.append(_("The boot partition must be within the first 4MB of the disk."))

            try:
                req = self.anaconda.id.storage.mountpoints["/boot"]
            except KeyError:
                req = self.anaconda.id.storage.rootDevice

            return errors + self.checkBootRequest(req)
        else:
            return errors

    def setDefaultPartitioning(self):
        ret = PPC.setDefaultPartitioning(self)
        ret.append(PartSpec(fstype="prepboot", size=4,
                            weight=self.weight(fstype="prepboot")))
        return ret

    def weight(self, fstype=None, mountpoint=None):
        if fstype and fstype == "prepboot":
            return 5000
        elif mountpoint and mountpoint == "/boot":
            return 2000
        else:
            return 0

class NewWorldPPC(PPC):
    _disklabel_types = ["mac"]
    _minBootPartSize = (800.00 / 1024.00)
    _maxBootPartSize = 1

    def bootDevice(self):
        bootDev = None

        for part in self.anaconda.id.storage.partitions:
            if part.format.type == "appleboot" and self.validBootPartSize(part.size):
                bootDev = part
                # if we're only picking one, it might as well be the first
                break

        return bootDev

    def bootloaderChoices(self, bl):
        ret = {}

        bootDev = self.bootDevice()
        if not bootDev:
            return ret

        if bootDev.type == "mdarray":
            ret["boot"] = (bootDev.name, N_("RAID Device"))
            ret["mbr"] = (bl.drivelist[0], N_("Master Boot Record (MBR)"))
        else:
            ret["boot"] = (bootDev.name, N_("Apple Bootstrap"))
            for (n, device) in enumerate(self.anaconda.id.storage.partitions):
                if device.format.type == "appleboot" and device.path != bootDev.path:
                    ret["boot%d" % n] = (device.path, N_("Apple Bootstrap"))

        return ret

    def checkBootRequest(self, req):
        errors = PPC.checkBootRequest(self, req)

        if not req or req.type != "partition" or not req.disk:
            return errors

        disk = req.disk.format.partedDisk

        # Check that we're a Mac disk label
        if not disk.type in self.diskLabelTypes:
            errors.append(_("%s must have a mac disk label.") % req.disk.name)

        # All of the above just checks the appleboot partitions.  We still
        # need to make sure that whatever /boot is on also meets these criteria.
        if req == self.bootDevice():
            try:
                req = self.anaconda.id.storage.mountpoints["/boot"]
            except KeyError:
                req = self.anaconda.id.storage.rootDevice

            return errors + self.checkBootRequest(req)
        else:
            return errors

    def setDefaultPartitioning(self):
        ret = Platform.setDefaultPartitioning(self)
        ret.append(PartSpec(fstype="appleboot", size=1, maxSize=1,
                            weight=self.weight(fstype="appleboot")))
        return ret

    def weight(self, fstype=None, mountpoint=None):
        if fstype and fstype == "appleboot":
            return 5000
        elif mountpoint and mountpoint == "/boot":
            return 2000
        else:
            return 0

class PS3(PPC):
    _disklabel_types = ["msdos"]

    def __init__(self, anaconda):
        PPC.__init__(self, anaconda)

class S390(Platform):
    _bootFSTypes = ["ext4", "ext3", "ext2"]
    _packages = ["s390utils"]
    _supportsLvmBoot = True

    def __init__(self, anaconda):
        Platform.__init__(self, anaconda)

    def requiredDiskLabelType(self, device_type):
        """The required disklabel type for the specified device type."""
        if device_type == parted.DEVICE_DASD:
            return "dasd"

        return super(S390, self).requiredDiskLabelType(device_type)

    def setDefaultPartitioning(self):
        """Return the default platform-specific partitioning information."""
        return [PartSpec(mountpoint="/boot", fstype=self.defaultBootFSType, size=500,
                         weight=self.weight(mountpoint="/boot"), asVol=True,
                         singlePV=True)]

    def weight(self, fstype=None, mountpoint=None):
        if mountpoint and mountpoint == "/boot":
            return 5000
        else:
            return 0

class Sparc(Platform):
    _disklabel_types = ["sun"]

    @property
    def minimumSector(self, disk):
        (cylinders, heads, sectors) = disk.device.biosGeometry
        start = long(sectors * heads)
        start /= long(1024 / disk.device.sectorSize)
        return start+1

class X86(EFI):
    _bootFSTypes = ["ext4", "ext3", "ext2"]
    _packages = ["grub"]
    _supportsMdRaidBoot = True

    def __init__(self, anaconda):
        EFI.__init__(self, anaconda)

        if self.isEfi:
            self._disklabel_types = ["gpt"]
        else:
            self._disklabel_types = ["msdos", "gpt"]

    def bootDevice(self):
        if self.isEfi:
            return EFI.bootDevice(self)
        else:
            return Platform.bootDevice(self)

    def bootloaderChoices(self, bl):
        if self.isEfi:
            return EFI.bootloaderChoices(self, bl)

        bootDev = self.bootDevice()
        ret = {}

        if not bootDev:
            return {}

        if bootDev.type == "mdarray":
            ret["boot"] = (bootDev.name, N_("RAID Device"))
            ret["mbr"] = (bl.drivelist[0], N_("Master Boot Record (MBR)"))
        else:
            ret["boot"] = (bootDev.name, N_("First sector of boot partition"))
            ret["mbr"] = (bl.drivelist[0], N_("Master Boot Record (MBR)"))

        return ret

    @property
    def maxBootPartSize(self):
        if self.isEfi:
            return EFI._maxBootPartSize
        else:
            return Platform._maxBootPartSize

    @property
    def minBootPartSize(self):
        if self.isEfi:
            return EFI._minBootPartSize
        else:
            return Platform._minBootPartSize

    def setDefaultPartitioning(self):
        if self.isEfi:
            return EFI.setDefaultPartitioning(self)
        else:
            return Platform.setDefaultPartitioning(self)

def getPlatform(anaconda):
    """Check the architecture of the system and return an instance of a
       Platform subclass to match.  If the architecture could not be determined,
       raise an exception."""
    if iutil.isAlpha():
        return Alpha(anaconda)
    elif iutil.isIA64():
        return IA64(anaconda)
    elif iutil.isPPC():
        ppcMachine = iutil.getPPCMachine()

        if (ppcMachine == "PMac" and iutil.getPPCMacGen() == "NewWorld"):
            return NewWorldPPC(anaconda)
        elif ppcMachine in ["iSeries", "pSeries"]:
            return IPSeriesPPC(anaconda)
        elif ppcMachine == "PS3":
            return PS3(anaconda)
        else:
            raise SystemError, "Unsupported PPC machine type"
    elif iutil.isS390():
        return S390(anaconda)
    elif iutil.isSparc():
        return Sparc(anaconda)
    elif iutil.isX86():
        return X86(anaconda)
    else:
        raise SystemError, "Could not determine system architecture."
