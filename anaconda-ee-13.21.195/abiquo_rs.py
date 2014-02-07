#
# Copyright 2013 Abiquo, Inc.
#
# This software may be freely redistributed under the terms of the GNU
# library public license.
#
# You should have received a copy of the GNU Library Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import shutil
import iutil
import os
from flags import flags
import re

import logging
log = logging.getLogger("anaconda")

class AbiquoRS:

    def write(self, instPath):
        # HACK
        # Make sure abiquo.appliancemanager.repositoryLocation
        # is a valid NFS URL
        nfs_url = re.search("nfs-server-ip", self.abiquo_nfs_repository)
        if nfs_url:
            self.abiquo_nfs_repository = "127.0.0.1:/opt/vm_repository"
                
        # dont do this in test mode!
        if flags.test:
            return

        if os.path.isdir(instPath + "/opt/abiquo/config/"):
            f = open(instPath + "/opt/abiquo/config/abiquo.properties", 'a')
            f.write("[remote-services]\n")
            f.write("abiquo.rabbitmq.username = %s\n" %
                    self.abiquo_rabbitmq_username)
            f.write("abiquo.rabbitmq.password = %s\n" %
                    self.abiquo_rabbitmq_password)
            f.write("abiquo.rabbitmq.host = %s\n" %
                    self.abiquo_rabbitmq_host)
            f.write("abiquo.rabbitmq.port = %s\n" %
                    self.abiquo_rabbitmq_port)
            f.write("abiquo.appliancemanager.localRepositoryPath = %s\n" %
                    self.abiquo_appliancemanager_localRepositoryPath)
            f.write("abiquo.appliancemanager.repositoryLocation = %s\n" %
                    self.abiquo_nfs_repository)
            f.write("#abiquo.virtualfactory.xenserver.repositoryLocation = %s\n" %
                    self.abiquo_nfs_repository)
            f.write("abiquo.redis.port = %s\n" %
                    self.abiquo_redis_port)
            f.write("abiquo.redis.host = %s\n" %
                    self.abiquo_redis_host)
            f.write("#abiquo.storagemanager.netapp.user = %s\n" %
                    "root")
            f.write("#abiquo.storagemanager.netapp.password= %s\n" %
                    "temporal")
            f.write("#abiquo.dvs.enabled = %s\n" %
                    self.abiquo_dvs_enabled)
            f.write("#abiquo.dvs.vcenter.user = %s\n" %
                    self.abiquo_dvs_vcenter_user)
            f.write("#abiquo.dvs.vcenter.password = %s\n" %
                    self.abiquo_dvs_vcenter_password)
            f.write("abiquo.datacenter.id = %s\n" %
                    self.abiquo_datacenter_id)
            f.write("#abiquo.virtualfactory.hyperv.repositoryLocation = //127.0.0.1/vm_repository\n")
            f.close()

    def writeKS(self, f):
        f.write("abiquo-remote-services --nfsrepository=%s\n" %
                self.abiquo_nfs_repository)

    def __init__(self):
        self.abiquo_nfs_repository = '<nfs-server-ip>:/opt/vm_repository'
        self.ontap_user = 'root'
        self.ontap_password = ''
        self.ontap_server_ip = '127.0.0.1'
        self.abiquo_rabbitmq_username = 'guest'
        self.abiquo_rabbitmq_password = 'guest'
        self.abiquo_rabbitmq_host = '127.0.0.1'
        self.abiquo_rabbitmq_port = '5672'
        self.abiquo_appliancemanager_localRepositoryPath = '/opt/vm_repository/'
        self.abiquo_appliancemanager_repositoryLocation  = '<nfs-server-ip>:/opt/vm_repository/'
        self.abiquo_virtualfactory_hyperv_repositoryLocation = '//127.0.0.1/vm_repository/'
        self.abiquo_virtualfactory_xenserver_repositoryLocation = '127.0.0.1:/opt/vm_repository/'
        self.abiquo_redis_host =  '127.0.0.1'
        self.abiquo_redis_port = '6379'
        self.abiquo_dvs_vcenter_password = 'change-me'
        self.abiquo_dvs_vcenter_user = 'change-me'
        self.abiquo_dvs_enabled = 'false'
	self.abiquo_datacenter_id = 'Abiquo'
