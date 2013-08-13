#
# Copyright 2011 Abiquo, Inc.
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

class AbiquoV2V:

    def write(self, instPath):
        log.info("Writing abiquo_v2v settings")
        # dont do this in test mode!
        if flags.test:
            return

	# Write only if V2V present and remote services not installed
        if os.path.isdir(instPath + "/opt/abiquo/tomcat/webapps/bpm-async") and not \
			os.path.isdir(instPath + "/opt/abiquo/tomcat/webapps/vsm"):
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
            f.write("abiquo.datacenter.id = %s\n" %
                    self.abiquo_datacenter_id)
            f.close()

    def writeKS(self, f):
	    pass

    def __init__(self):
        self.abiquo_rabbitmq_username = 'guest'
        self.abiquo_rabbitmq_password = 'guest'
        self.abiquo_rabbitmq_host = '127.0.0.1'
        self.abiquo_rabbitmq_port = '5672'
	self.abiquo_datacenter_id = 'Abiquo'
