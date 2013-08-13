import isys
import shutil
import glob
import os
import iutil
import time
import sys
import os.path

def abiquo_upgrade_pre(anaconda):
    backup_dir = anaconda.rootPath + '/opt/abiquo/backup/2.4.0' 
    if os.path.exists(backup_dir):
        anaconda.intf.messageWindow("Upgrade not possible",
                                    "Previous upgrade directory found. Aborting.")
	sys.exit(0)

    win = anaconda.intf.progressWindow("Upgrading",
                              "Previous installation detected, upgrading to 2.6.0...", 
                              5)
    abiquo_config_dir = anaconda.rootPath + '/opt/abiquo/config'
    db_dir = anaconda.rootPath + '/var/lib/mysql/kinton'
    db_backup_dir = "%s/database/" % backup_dir
    old_configs_dir = "%s/configs" % backup_dir
    sysconfig_dir = anaconda.rootPath + "/etc/sysconfig"
    redis_db_file = anaconda.rootPath + '/var/lib/redis/dump.rdb'
    redis_backup_dir = backup_dir + "/redis"

    # create backup dir
    os.makedirs(backup_dir)

    # Backup config files
    if os.path.exists(abiquo_config_dir):
        if not os.path.exists(old_configs_dir):
            os.makedirs(old_configs_dir)
            for file in glob.glob(abiquo_config_dir + '/*.properties'):
                shutil.copy(file, old_configs_dir)

    # backup fstab
    if os.path.exists(anaconda.rootPath + '/etc/fstab'):
        shutil.copyfile("%s/etc/fstab" % anaconda.rootPath,
                '%s/fstab.anaconda' % backup_dir)

    # Backup kinton database
    #if os.path.isdir(db_dir):
    #    os.makedirs(db_backup_dir)
    #    shutil.copytree(db_dir, db_backup_dir + '/kinton')

    # Backup redis
    if os.path.exists(redis_db_file):
        os.makedirs(redis_backup_dir)
        shutil.copy(redis_db_file, redis_backup_dir)

    for i in range(1, 6):
        time.sleep(0.50)
        win.set(i)

    win.pop()
