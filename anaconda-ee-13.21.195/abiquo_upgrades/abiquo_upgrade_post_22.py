import os
import iutil
import shutil
import logging
import ConfigParser

log = logging.getLogger("anaconda")

def abiquo_upgrade_post(anaconda):

    schema_path = anaconda.rootPath + "/usr/share/doc/abiquo-server/database/kinton-latest-delta.sql"
    work_path = anaconda.rootPath + "/opt/abiquo/tomcat/work"
    temp_path = anaconda.rootPath + "/opt/abiquo/tomcat/temp"
    server_xml_path = anaconda.rootPath + "/opt/abiquo/tomcat/conf/Catalina/localhost/server.xml.rpmsave"
    client_xml_path = anaconda.rootPath + "/opt/abiquo/tomcat/conf/Catalina/localhost/client-premium.xml"
    server_path = anaconda.rootPath + "/opt/abiquo/tomcat/webapps/server"
    lvm_path = anaconda.rootPath + "/opt/abiquo/lvmiscsi"

    # redis vars
    redis_port = 6379
    redis_sport = str(redis_port)

    log.info("ABIQUO: Post install steps")
    # Move server.xml to client-premium.xml and remove deprecated server webapp
    if os.path.exists(server_xml_path):
        log.info("ABIQUO: Moving old server.xml to client-premium.xml...")
        iutil.execWithRedirect("/bin/mv",
                                [server_xml_path,client_xml_path],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        log.info("ABIQUO: Removing server webapp...")
        iutil.execWithRedirect("/bin/rm",
                                ['-rf',server_path],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
    # Clean tomcat 
    if os.path.exists(work_path):
        log.info("ABIQUO: Cleaning work folder...")
        shutil.rmtree(work_path)
    if os.path.exists(temp_path):
        log.info("ABIQUO: Cleaning temp folder...")
        shutil.rmtree(temp_path)
    # Upgrade database if this is a server install
    if os.path.exists(schema_path):
        schema = open(schema_path)
        log.info("ABIQUO: Updating Abiquo database (community delta)...")
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


    # Redis patch on server
    if os.path.exists(schema_path):
        log.info("ABIQUO: Applying redis patch...")
        iutil.execWithRedirect("/etc/init.d/redis",
                                ['start'],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="//mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        iutil.execWithRedirect("/usr/bin/redis-cli",
                                ['-h', 'localhost', '-p', redis_sport ,"PING"],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="//mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)      

        cmd = iutil.execWithRedirect("/usr/bin/redis-cli",
                                ['-h', 'localhost', '-p', redis_sport ,'keys','Owner:*:*'],
                                stdout="/mnt/sysimage/tmp/redis_owners", stderr="//mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        for owner in open('/mnt/sysimage/tmp/redis_owners','r').readlines() :
            owner = owner.strip()
            key = owner[:owner.rfind(":")]
            iutil.execWithRedirect("/usr/bin/redis-cli",
                                ['-h', 'localhost', '-p', redis_sport ,'sadd',key,owner],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="//mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
            log.info("ABIQUO: "+owner+" indexed.")

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
    backup_dir = anaconda.rootPath + '/opt/abiquo/backup/2.0'
    if os.path.exists('%s/fstab.anaconda' % backup_dir):
        shutil.copyfile("%s/fstab.anaconda" % backup_dir,
                '%s/etc/fstab' % anaconda.rootPath)
