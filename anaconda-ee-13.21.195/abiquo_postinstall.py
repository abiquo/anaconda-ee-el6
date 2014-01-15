import os
import iutil
import types
import re
import shutil
import logging
import glob
import network
import isys
import stat
log = logging.getLogger("anaconda")
import fileinput

def abiquoPostInstall(anaconda):
    log.info("Abiquo postinstall")

    # Enable MOTD
    iutil.execWithRedirect("/bin/chmod",
                                ['a+x', "/etc/rc.d/init.d/motd"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                root=anaconda.rootPath)
    iutil.execWithRedirect("/sbin/chkconfig",
                                ['--add', "motd"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                root=anaconda.rootPath)
    iutil.execWithRedirect("/sbin/chkconfig",
                                ['motd', "on"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                root=anaconda.rootPath)

    # Select first dev with link and change ifcfg to start on boot
    for device in anaconda.id.network.netdevices:
        if isys.getLinkStatus(device):
            dev = network.NetworkDevice(anaconda.rootPath + network.netscriptsDir, device)
            dev.loadIfcfgFile()
            dev.set(('ONBOOT', 'yes'))
            dev.writeIfcfgFile()
            log.info("Setting ONBOOT=yes for network device with link: %s " % device)

    # loopback up
    iutil.execWithRedirect("/sbin/ifconfig",
                            ['lo', 'up'],
                            stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="//mnt/sysimage/var/log/abiquo-postinst.log",
                            root=anaconda.rootPath)
    # Disable firewall
    iutil.execWithRedirect("/sbin/chkconfig",
                            ['iptables', "off"],
                            stdout="/dev/tty5", stderr="/dev/tty5",
                            root=anaconda.rootPath)

    iutil.execWithRedirect("/sbin/chkconfig",
                            ['ip6tables', "off"],
                            stdout="/dev/tty5", stderr="/dev/tty5",
                            root=anaconda.rootPath)

    # Disable SElinux
    f = fileinput.FileInput(anaconda.rootPath + "/etc/sysconfig/selinux",inplace=1)
    for line in f:
        line = line.replace("=enforcing","=disabled")
        print line.rstrip()
    f.close()

    f = fileinput.FileInput(anaconda.rootPath + "/etc/selinux/config",inplace=1)
    for line in f:
        line = line.replace("=enforcing","=disabled")
        print line.rstrip()
    f.close()

    # Add bash completion for root
    if ( os.path.exists(anaconda.rootPath + '/etc/bash_completion') and os.path.exists(anaconda.rootPath + '/root/.bashrc') ):
        f = open(anaconda.rootPath + "/root/.bashrc", "a")
        f.write("source /etc/bash_completion\n")
        f.close()

    # DHCP is set at installer
    if anaconda.backend.isGroupSelected('abiquo-dhcp-relay'):
        vrange1 = anaconda.id.abiquo.abiquo_dhcprelay_vrange_1
        vrange2 = anaconda.id.abiquo.abiquo_dhcprelay_vrange_2
        mgm_if = anaconda.id.abiquo.abiquo_dhcprelay_management_if
        service_if = anaconda.id.abiquo.abiquo_dhcprelay_service_if
        dhcpd_ip = anaconda.id.abiquo.abiquo_dhcprelay_dhcpd_ip
        relay_net = anaconda.id.abiquo.abiquo_dhcprelay_service_network 
        log.info("abiquo-dhcp-relay %s %s %s %s %s %s %s %s %s %s" % ('-r', mgm_if, '-s', service_if, '-v', "%s-%s" % (vrange1, vrange2), '-x', dhcpd_ip, '-n', relay_net))
        iutil.execWithRedirect("/usr/bin/abiquo-dhcp-relay",
                            ['-r', mgm_if, '-s', service_if, '-v', "%s-%s" % (vrange1, vrange2), '-x', dhcpd_ip, '-n', relay_net],
                            stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="//mnt/sysimage/var/log/abiquo-postinst.log",
                            root=anaconda.rootPath)
        shutil.move(anaconda.rootPath + '/relay-config', anaconda.rootPath + '/etc/init.d/relay-config')
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['relay-config', "on"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                root=anaconda.rootPath)
    # Export NFS
    if anaconda.backend.isGroupSelected('abiquo-nfs-repository') and not \
            anaconda.backend.isGroupSelected('abiquo-monolithic'):
        f = open(anaconda.rootPath + "/etc/exports", "a")
        f.write("/opt/vm_repository    *(rw,no_root_squash,subtree_check,insecure)\n")
        f.close()

    # Don't check NFS in monolithic+nfs (local repo)
    if anaconda.backend.isGroupSelected('abiquo-nfs-repository') and \
            anaconda.backend.isGroupSelected('abiquo-monolithic'):
        f = open(anaconda.rootPath + "/opt/abiquo/config/abiquo.properties", "a")
        f.write("abiquo.appliancemanager.checkMountedRepository = false\n")
        f.close()

    if anaconda.backend.isGroupSelected('abiquo-nfs-repository'):
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['nfs', "on"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                root=anaconda.rootPath)
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['smb', "on"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                root=anaconda.rootPath)
        if not os.path.exists(anaconda.rootPath + '/opt/vm_repository'):
            os.makedirs(anaconda.rootPath + '/opt/vm_repository')
        if not os.path.exists(anaconda.rootPath + '/opt/vm_repository/.abiquo_repository'):
            open(anaconda.rootPath + '/opt/vm_repository/.abiquo_repository', 'w').close()

    if anaconda.backend.isGroupSelected('abiquo-remote-services'):
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['dhcpd', "on"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                root=anaconda.rootPath)

    if anaconda.backend.isGroupSelected('abiquo-server') or \
            anaconda.backend.isGroupSelected('abiquo-monolithic'):
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['rabbitmq-server', "on"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                root=anaconda.rootPath)
        # start MariaDB to create the schema
        iutil.execWithRedirect("/etc/init.d/mysql",
                                ['start'],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['mysql', "on"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                root=anaconda.rootPath)
        schema = open(anaconda.rootPath + "/usr/share/doc/abiquo-server/database/kinton-schema.sql")
 
        # md5 hash is replaced by bcrypt salted hash at first login
        newschema = open(anaconda.rootPath + "/tmp/kinton-schema.sql", 'w')
        for line in schema.readlines():
            newschema.write(re.sub('c69a39bd64ffb77ea7ee3369dce742f3', anaconda.id.abiquoPasswordHex, line))
            newschema.write("\n")   
        newschema.close()
        # create the schema
        newschema = open(anaconda.rootPath + "/tmp/kinton-schema.sql")
        iutil.execWithRedirect("/usr/bin/mysql",
                                [],
                                stdin=newschema,
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        schema.close()
        newschema.close()
    if anaconda.backend.isGroupSelected('abiquo-server') or \
            anaconda.backend.isGroupSelected('abiquo-monolithic') or \
            anaconda.backend.isGroupSelected('abiquo-standalone-ui') :
        if os.path.exists(anaconda.rootPath + '/etc/httpd/conf.d/welcome.conf'):
            shutil.move(anaconda.rootPath + '/etc/httpd/conf.d/welcome.conf',anaconda.rootPath + '/etc/httpd/conf.d/welcome.conf.backup')
        shutil.copy2(anaconda.rootPath + '/usr/share/doc/abiquo-ui/abiquo.conf',anaconda.rootPath + '/etc/httpd/conf.d/abiquo.conf')
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['httpd', "on"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                root=anaconda.rootPath)

    if anaconda.backend.isGroupSelected('abiquo-lvm-storage-server'):
                iutil.execWithRedirect("/sbin/chkconfig",
                            ['tgtd', "on"],
                            stdout="/dev/tty5", stderr="/dev/tty5",
                            root=anaconda.rootPath)
                iutil.execWithRedirect("/sbin/chkconfig",
                                        ['abiquo-lvmiscsi', "on"],
                                        stdout="/dev/tty5", stderr="/dev/tty5",
                                        root=anaconda.rootPath)

    if anaconda.backend.isGroupSelected('abiquo-server'):
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['zookeeper', "off"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                        root=anaconda.rootPath)
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['redis', "on"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                        root=anaconda.rootPath)
    if anaconda.backend.isGroupSelected('abiquo-standalone-api'):
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['zookeeper', "on"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                        root=anaconda.rootPath)
    if anaconda.backend.isGroupSelected('abiquo-monolithic'):
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['redis', "on"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                root=anaconda.rootPath)
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['httpd', "on"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                root=anaconda.rootPath)
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['dhcpd', "on"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                root=anaconda.rootPath)
    if anaconda.backend.isGroupSelected('abiquo-remote-services') or \
            anaconda.backend.isGroupSelected('abiquo-public-services'):
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['redis', "on"],
                                stdout="/dev/tty5", stderr="/dev/tty5",
                                root=anaconda.rootPath)

    f = open(anaconda.rootPath + '/etc/abiquo-installer', 'a')
    f.write('Installed Profiles: %s\n' %
            str(anaconda.id.abiquo.selectedGroups))
    f.close()