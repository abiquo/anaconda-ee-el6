#
# lvm.py
# lvm functions
#
# Copyright (C) 2009  Red Hat, Inc.  All rights reserved.
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
# Author(s): Dave Lehman <dlehman@redhat.com>
#

import os
import math
import re

import iutil
import logging
log = logging.getLogger("storage")

from ..errors import *
from constants import *

import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)

MAX_LV_SLOTS = 256

def has_lvm():
    has_lvm = False
    for path in os.environ["PATH"].split(":"):
        if os.access("%s/lvm" % path, os.X_OK):
            has_lvm = True
            break

    if has_lvm:
        has_lvm = False
        for line in open("/proc/devices").readlines():
            if "device-mapper" in line.split():
                has_lvm = True
                break

    return has_lvm

# Start config_args handling code
#
# Theoretically we can handle all that can be handled with the LVM --config
# argument.  For every time we call an lvm_cc (lvm compose config) funciton
# we regenerate the config_args with all global info.
config_args = [] # Holds the final argument list
config_args_data = { "filterRejects": [],    # regular expressions to reject.
                            "filterAccepts": [] }   # regexp to accept

def _composeConfig():
    """lvm command accepts lvm.conf type arguments preceded by --config. """
    global config_args, config_args_data
    config_args = []

    filter_string = ""
    # we don't need the accept for now.
    # accepts = config_args_data["filterAccepts"]
    # if len(accepts) > 0:
    #   for i in range(len(rejects)):
    #       filter_string = filter_string + ("\"a|/%s$|\", " % accepts[i])

    rejects = config_args_data["filterRejects"]
    for reject in rejects:
        filter_string += ("\"r|/%s$|\"," % reject)

    filter_string = " filter=[%s] " % filter_string.strip(",")

    # As we add config strings we should check them all.
    if filter_string == "":
        # Nothing was really done.
        return

    # devices_string can have (inside the brackets) "dir", "scan",
    # "preferred_names", "filter", "cache_dir", "write_cache_state",
    # "types", "sysfs_scan", "md_component_detection".  see man lvm.conf.
    devices_string = " devices {%s} " % (filter_string) # strings can be added
    config_string = devices_string # more strings can be added.
    config_args = ["--config", config_string]

def lvm_cc_addFilterRejectRegexp(regexp):
    """ Add a regular expression to the --config string."""
    global config_args_data
    log.debug("lvm filter: adding %s to the reject list" % regexp)
    config_args_data["filterRejects"].append(regexp)

    # compoes config once more.
    _composeConfig()

def lvm_cc_resetFilter():
    global config_args, config_args_data
    config_args_data["filterRejects"] = []
    config_args_data["filterAccepts"] = []
    config_args = []
# End config_args handling code.

# Names that should not be used int the creation of VGs
lvm_vg_blacklist = []
def blacklistVG(name):
    global lvm_vg_blacklist
    lvm_vg_blacklist.append(name)

def getPossiblePhysicalExtents(floor=0):
    """Returns a list of integers representing the possible values for
       the physical extent of a volume group.  Value is in KB.

       floor - size (in KB) of smallest PE we care about.
    """

    possiblePE = []
    curpe = 8
    while curpe <= 16384*1024:
	if curpe >= floor:
	    possiblePE.append(curpe)
	curpe = curpe * 2

    return possiblePE

def getMaxLVSize():
    """ Return the maximum size (in MB) of a logical volume. """
    if iutil.getArch() in ("x86_64", "ppc64", "alpha", "ia64", "s390", "sparc"): #64bit architectures
        return (8*1024*1024*1024*1024) #Max is 8EiB (very large number..)
    else:
        return (16*1024*1024) #Max is 16TiB

# apparently lvm has a limit of 126 chars for combined vg-lv names:
# https://bugzilla.redhat.com/show_bug.cgi?id=747278#c6
# https://bugzilla.redhat.com/show_bug.cgi?id=747278#c7
# since dashes get escaped they count double -- allow for six of them since
# a dhcp-provided hostname could easily contain five dashes ("dhcp-xx-xx-xx-xx")
LVM_MAX_NAME_LEN = 50

def safeLvmName(name, maxlen=LVM_MAX_NAME_LEN):
    tmp = name.strip()
    tmp = tmp.replace("/", "_")
    tmp = re.sub("[^0-9a-zA-Z._]", "", tmp)
    tmp = tmp.lstrip("_")

    if len(tmp) > maxlen:
        tmp = tmp[:maxlen]

    return tmp

def clampSize(size, pesize, roundup=None):
    if roundup:
        round = math.ceil
    else:
        round = math.floor

    return long(round(float(size)/float(pesize)) * pesize)

def lvm(args, progress=None):
    rc = iutil.execWithPulseProgress("lvm", args,
                                     stdout = "/dev/tty5",
                                     stderr = "/dev/tty5",
                                     progress=progress)
    if not rc:
        return

    try:
        msg = open("/tmp/program.log").readlines()[-1].strip()
    except Exception:
        msg = ""

    raise LVMError(msg)

def pvcreate(device, progress=None):
    # we force dataalignment=1024k since we cannot get lvm to tell us what
    # the pe_start will be in advance
    args = ["pvcreate"] + \
            config_args + \
            ["--dataalignment", "1024k"] + \
            [device]

    try:
        lvm(args, progress=progress)
    except LVMError as msg:
        raise LVMError("pvcreate failed for %s: %s" % (device, msg))

def pvresize(device, size):
    args = ["pvresize"] + \
            ["--setphysicalvolumesize", ("%dm" % size)] + \
            config_args + \
            [device]

    try:
        lvm(args)
    except LVMError as msg:
        raise LVMError("pvresize failed for %s: %s" % (device, msg))

def pvremove(device):
    args = ["pvremove"] + \
            config_args + \
            [device]

    try:
        lvm(args)
    except LVMError as msg:
        raise LVMError("pvremove failed for %s: %s" % (device, msg))

def pvinfo(device):
    """
        If the PV was created with '--metadacopies 0', lvm will do some
        scanning of devices to determine from their metadata which VG
        this PV belongs to.

        pvs -o pv_name,pv_mda_count,vg_name,vg_uuid --config \
            'devices { scan = "/dev" filter = ["a/loop0/", "r/.*/"] }'
    """
    #cfg = "'devices { scan = \"/dev\" filter = [\"a/%s/\", \"r/.*/\"] }'" 
    args = ["pvs", "--noheadings"] + \
            ["--units", "m"] + \
            ["-o", "pv_name,pv_mda_count,vg_name,vg_uuid"] + \
            config_args + \
            [device]

    rc = iutil.execWithCapture("lvm", args,
                                stderr = "/dev/tty5")
    vals = rc.split()
    if not vals:
        raise LVMError("pvinfo failed for %s" % device)

    # don't raise an exception if pv is not a part of any vg
    pv_name = vals[0]
    try:
        vg_name, vg_uuid = vals[2], vals[3]
    except IndexError:
        vg_name, vg_uuid = "", ""
    
    info = {'pv_name': pv_name,
            'vg_name': vg_name,
            'vg_uuid': vg_uuid}

    return info

def vgcreate(vg_name, pv_list, pe_size, progress=None):
    argv = ["vgcreate"]
    if pe_size:
        argv.extend(["-s", "%dm" % pe_size])
    argv.extend(config_args)
    argv.append(vg_name)
    argv.extend(pv_list)

    try:
        lvm(argv, progress=progress)
    except LVMError as msg:
        raise LVMError("vgcreate failed for %s: %s" % (vg_name, msg))

def vgremove(vg_name):
    args = ["vgremove", "--force"] + \
            config_args +\
            [vg_name]

    try:
        lvm(args)
    except LVMError as msg:
        raise LVMError("vgremove failed for %s: %s" % (vg_name, msg))

def vgactivate(vg_name):
    args = ["vgchange", "-a", "y"] + \
            config_args + \
            [vg_name]

    try:
        lvm(args)
    except LVMError as msg:
        raise LVMError("vgactivate failed for %s: %s" % (vg_name, msg))

def vgdeactivate(vg_name):
    args = ["vgchange", "-a", "n"] + \
            config_args + \
            [vg_name]

    try:
        lvm(args)
    except LVMError as msg:
        raise LVMError("vgdeactivate failed for %s: %s" % (vg_name, msg))

def vgreduce(vg_name, pv_list, rm=False):
    """ Reduce a VG.

    rm -> with RemoveMissing option.
    Use pv_list when rm=False, otherwise ignore pv_list and call vgreduce with
    the --removemissing option.
    """
    args = ["vgreduce"]
    args.extend(config_args)
    if rm:
        args.extend(["--removemissing", vg_name])
    else:
        args.extend([vg_name] + pv_list)

    try:
        lvm(args)
    except LVMError as msg:
        raise LVMError("vgreduce failed for %s: %s" % (vg_name, msg))

def vginfo(vg_name):
    args = ["vgs", "--noheadings", "--nosuffix"] + \
            ["--units", "m"] + \
            ["-o", "uuid,size,free,extent_size,extent_count,free_count,pv_count"] + \
            config_args + \
            [vg_name]

    buf = iutil.execWithCapture("lvm",
                                args,
                                stderr="/dev/tty5")
    info = buf.split()
    if len(info) != 7:
        raise LVMError(_("vginfo failed for %s" % vg_name))

    d = {}
    (d['uuid'],d['size'],d['free'],d['pe_size'],
     d['pe_count'],d['pe_free'],d['pv_count']) = info
    return d

def lvs(vg_name):
    args = ["lvs", "--noheadings", "--nosuffix"] + \
            ["--units", "m"] + \
            ["-o", "lv_name,lv_uuid,lv_size,lv_attr"] + \
            config_args + \
            [vg_name]

    buf = iutil.execWithCapture("lvm",
                                args,
                                stderr="/dev/tty5")

    lvs = {}
    for line in buf.splitlines():
        line = line.strip()
        if not line:
            continue
        (name, uuid, size, attr) = line.split()
        lvs[name] = {"size": size,
                     "uuid": uuid,
                     "attr": attr}

    if not lvs:
        raise LVMError(_("lvs failed for %s" % vg_name))

    return lvs

def lvorigin(vg_name, lv_name):
    args = ["lvs", "--noheadings", "-o", "origin"] + \
            config_args + \
            ["%s/%s" % (vg_name, lv_name)]

    buf = iutil.execWithCapture("lvm",
                                args,
                                stderr="/dev/tty5")

    try:
        origin = buf.splitlines()[0].strip()
    except IndexError:
        origin = ''

    return origin

def lvcreate(vg_name, lv_name, size, progress=None, pvs=[]):
    args = ["lvcreate"] + \
            ["-L", "%dm" % size] + \
            ["-n", lv_name] + \
            config_args + \
            [vg_name] + pvs

    try:
        lvm(args, progress=progress)
    except LVMError as msg:
        raise LVMError("lvcreate failed for %s/%s: %s" % (vg_name, lv_name, msg))

def lvremove(vg_name, lv_name):
    args = ["lvremove"] + \
            config_args + \
            ["%s/%s" % (vg_name, lv_name)]

    try:
        lvm(args)
    except LVMError as msg:
        raise LVMError("lvremove failed for %s: %s" % (lv_name, msg))

def lvresize(vg_name, lv_name, size):
    args = ["lvresize"] + \
            ["--force", "-L", "%dm" % size] + \
            config_args + \
            ["%s/%s" % (vg_name, lv_name)]

    try:
        lvm(args)
    except LVMError as msg:
        raise LVMError("lvresize failed for %s: %s" % (lv_name, msg))

def lvactivate(vg_name, lv_name):
    # see if lvchange accepts paths of the form 'mapper/$vg-$lv'
    args = ["lvchange", "-a", "y"] + \
            config_args + \
            ["%s/%s" % (vg_name, lv_name)]

    try:
        lvm(args)
    except LVMError as msg:
        raise LVMError("lvactivate failed for %s: %s" % (lv_name, msg))

def lvdeactivate(vg_name, lv_name):
    args = ["lvchange", "-a", "n"] + \
            config_args + \
            ["%s/%s" % (vg_name, lv_name)]

    try:
        lvm(args)
    except LVMError as msg:
        raise LVMError("lvdeactivate failed for %s: %s" % (lv_name, msg))

