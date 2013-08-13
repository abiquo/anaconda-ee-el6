import os
import iutil
import shutil
import logging
import ConfigParser
import time
import re
from subprocess import *

log = logging.getLogger("anaconda")

def abiquo_upgrade_post(anaconda):

    schema_path = anaconda.rootPath + "/usr/share/doc/abiquo-server/database/kinton-delta-2.4.0_to_2.6.0.sql"
    api_path = anaconda.rootPath + "/opt/abiquo/tomcat/webapps/api"
    work_path = anaconda.rootPath + "/opt/abiquo/tomcat/work"
    temp_path = anaconda.rootPath + "/opt/abiquo/tomcat/temp"
    mysql_path = anaconda.rootPath + "/etc/init.d/mysql"
    redis_path = "/usr/share/doc/abiquo-server/database/redis-delta-2.4.0_to_2.6.0.py"

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

    # Upgrade database if this is a server install and MariaDB exists
    if os.path.exists(api_path):
        log.info("ABIQUO: Updating Abiquo database...")
        # log debug
        iutil.execWithRedirect("/sbin/ifconfig",
                                ['lo', 'up'],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log",stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        iutil.execWithRedirect("/etc/init.d/mysql",
                                ['start'],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log",stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        time.sleep(6)
        schema = open(schema_path)
        iutil.execWithRedirect("/usr/bin/mysql",
                                ['kinton'],
                                stdin=schema,
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log",stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        schema.close()


    # Redis delta

    if os.path.exists(api_path):
        log.info("ABIQUO: Starting redis ...")
        iutil.execWithRedirect("/etc/init.d/redis",
                                ['start'],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        # Wait for start
        time.sleep(3)
        log.info("ABIQUO: Updating redis ...")
        iutil.execWithRedirect("/usr/bin/python",
                                [redis_path],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)


    # restore fstab
    backup_dir = anaconda.rootPath + '/opt/abiquo/backup/2.4.0'
    if os.path.exists('%s/fstab.anaconda' % backup_dir):
        shutil.copyfile('%s/fstab.anaconda' % backup_dir,'%s/etc/fstab' % anaconda.rootPath)


    # Tweak loglevel to avoid kernel warnings
    rc = open(anaconda.rootPath + '/etc/rc.local', 'a')
    rc.write('echo 3 > /proc/sys/kernel/printk\n')
    rc.close()

