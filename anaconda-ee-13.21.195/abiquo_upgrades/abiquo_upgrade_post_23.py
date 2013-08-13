import os
import iutil
import shutil
import logging
import ConfigParser

log = logging.getLogger("anaconda")

def abiquo_upgrade_post(anaconda):

    schema_path = anaconda.rootPath + "/usr/share/doc/abiquo-server/database/kinton-2.3.0-delta.sql"
    work_path = anaconda.rootPath + "/opt/abiquo/tomcat/work"
    temp_path = anaconda.rootPath + "/opt/abiquo/tomcat/temp"
    lvm_path = anaconda.rootPath + "/opt/abiquo/lvmiscsi"
    log.info("ABIQUO: Post install steps")
    # Clean tomcat 
    if os.path.exists(work_path):
        log.info("ABIQUO: Cleaning work folder...")
        for f in os.listdir(work_path):
            fpath = os.path.join(work_path,f)
            try:
                if os.path.isfile(fpath):
                    os.unlink(fpath)
                else:
                    shutil.rmtree(fpath)
            except Exception, e:
                print e
    if os.path.exists(temp_path):
        log.info("ABIQUO: Cleaning temp folder...")
        for f in os.listdir(temp_path):
            fpath = os.path.join(temp_path,f)
            try:
                if os.path.isfile(fpath):
                    os.unlink(fpath)
                else:
                    shutil.rmtree(fpath)
            except Exception, e:
                print e
    # Upgrade database if this is a server install
    if os.path.exists(schema_path):
        schema = open(schema_path)
        log.info("ABIQUO: Updating Abiquo database ...")
        iutil.execWithRedirect("/sbin/ifconfig",
                                ['lo', 'up'],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        iutil.execWithRedirect("/etc/init.d/mysqld",
                                ['start'],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="//mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        iutil.execWithRedirect("/usr/bin/mysql",
                                ['kinton'],
                                stdin=schema,
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="//mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        schema.close()

    if os.path.exists(lvm_path):
        log.info("ABIQUO: Fixing lvmiscsi service...")
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['--add','abiquo-lvmiscsi'],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        iutil.execWithRedirect("/sbin/chkconfig",
                                ['abiquo-lvmiscsi','on'],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)

    # restore fstab
    backup_dir = anaconda.rootPath + '/opt/abiquo/backup/2.2.0'
    if os.path.exists('%s/fstab.anaconda' % backup_dir):
        shutil.copyfile("%s/fstab.anaconda" % backup_dir,
                '%s/etc/fstab' % anaconda.rootPath)
