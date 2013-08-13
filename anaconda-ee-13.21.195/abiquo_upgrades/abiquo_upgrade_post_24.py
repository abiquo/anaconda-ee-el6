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

    schema_path = anaconda.rootPath + "/usr/share/doc/abiquo-server/database/kinton-2.4.0-delta.sql"
    work_path = anaconda.rootPath + "/opt/abiquo/tomcat/work"
    temp_path = anaconda.rootPath + "/opt/abiquo/tomcat/temp"
    mysql_path = anaconda.rootPath + "/etc/init.d/mysql"
    xen_path = anaconda.rootPath + "/etc/xen"
    xen_kernel = '/xen.gz-3.4.2'

    redis_port = 6379
    redis_sport = str(redis_port)
    redis_host = '127.0.0.1'

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
    if os.path.exists(schema_path) and os.path.exists(mysql_path):
        log.info("ABIQUO: Updating Abiquo database...")
        # log debug
        iutil.execWithRedirect("/sbin/ifconfig",
                                ['lo', 'up'],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        iutil.execWithRedirect("/etc/init.d/mysql",
                                ['start'],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        time.sleep(6)
        schema = open(schema_path)
        iutil.execWithRedirect("/usr/bin/mysql",
                                ['kinton'],
                                stdin=schema,
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        schema.close()


    # Redis delta

    if os.path.exists(schema_path):
        log.info("ABIQUO: Starting redis ...")
        iutil.execWithRedirect("/etc/init.d/redis",
                                ['start'],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        # Wait for start
        time.sleep(3)
        log.info("ABIQUO: Updating redis ...")
        iutil.execWithRedirect("/usr/bin/redis-cli",
                                ['-h', redis_host, '-p', redis_sport ,"PING"],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath) 
        # Update tasks
        cmd = iutil.execWithRedirect("/usr/bin/redis-cli",
                                ['-h', redis_host, '-p', redis_sport ,'keys','Task:*'],
                                stdout="/mnt/sysimage/tmp/redis_tasks", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        for task in open('/mnt/sysimage/tmp/redis_tasks','r').readlines() :
            task = task.strip()
            tasktype = Popen(["redis-cli", "-h", redis_host, "-p", redis_sport, "hget", task, "type"], stdout=PIPE).communicate()[0].strip()
            if 'SNAPSHOT' == tasktype:
                iutil.execWithRedirect("/usr/bin/redis-cli",
                                    ["-h", redis_host, "-p", redis_sport ,"hset",task,"type","INSTANCE"],
                                    stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="//mnt/sysimage/var/log/abiquo-postinst.log",
                                    root=anaconda.rootPath)
                log.info("ABIQUO: Task "+task+" updated.")

        # Update jobs
        cmd = iutil.execWithRedirect("/usr/bin/redis-cli",
                                ['-h', redis_host, '-p', redis_sport ,'keys','Job:*'],
                                stdout="/mnt/sysimage/tmp/redis_jobs", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        for job in open('/mnt/sysimage/tmp/redis_jobs','r').readlines() :
            job = job.strip()
            jobtype = Popen(["redis-cli", "-h", redis_host, "-p", redis_sport, "hget", job, "type"], stdout=PIPE).communicate()[0].strip()
            if 'SNAPSHOT' == jobtype:
                iutil.execWithRedirect("/usr/bin/redis-cli",
                                    ["-h", redis_host, "-p", redis_sport ,"hset",job,"type","INSTANCE"],
                                    stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="//mnt/sysimage/var/log/abiquo-postinst.log",
                                    root=anaconda.rootPath)
                log.info("ABIQUO: Job "+job+" updated.")


    if os.path.exists(xen_path):
        # replace default kernel entry 
        log.info("ABIQUO: Updating XEN grub entry ...")
        f = open(anaconda.rootPath + '/boot/grub/menu.lst')
        buf = f.readlines()
        f.close()
        fw = open(anaconda.rootPath + '/boot/grub/menu.lst', 'w')
        for line in buf:
            fw.write(re.sub('\/xen.gz-2.6.18.*',
                            xen_kernel,
                            line))
        fw.close()


    # restore fstab
    backup_dir = anaconda.rootPath + '/opt/abiquo/backup/2.3.0'
    if os.path.exists('%s/fstab.anaconda' % backup_dir):
        shutil.copyfile("%s/fstab.anaconda" % backup_dir,
                '%s/etc/fstab' % anaconda.rootPath)
