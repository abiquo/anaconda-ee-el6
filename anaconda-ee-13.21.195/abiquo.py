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

import logging
log = logging.getLogger("anaconda")

def bool(val):
    if val: return "true"
    return "false"

class Abiquo:

    def writeKS(self, f):
	f.write("abiquo-server --ip=%s --dbhost=%s --dbpassword=%s --dbuser=%s\n" % \
                (self.abiquo_server_ip,
                 self.abiquo_db_host,
                 self.abiquo_db_password,
                 self.abiquo_db_user
                 )
                )

    def write(self, instPath):
        # dont do this in test mode!
        if flags.test:
            return

        #
        # if abiquo config directory does not exist, we are installing a HV
        # don't need this
        #
        if os.path.isdir(instPath + '/opt/abiquo/config/'):
            f = open(instPath + "/opt/abiquo/config/abiquo.properties", 'a')
            f.write("[server]\n")
            f.write("abiquo.server.sessionTimeout = %s\n" %
                    self.abiquo_server_sessionTimeout)
            f.write("abiquo.server.mail.server = %s\n" % self.abiquo_server_mail_server)
            f.write("abiquo.server.mail.user = %s\n" % self.abiquo_server_mail_user )
            f.write("abiquo.server.mail.password = %s\n" %
                    self.abiquo_server_mail_password )
            f.write("abiquo.rabbitmq.username = %s\n" %
                    self.abiquo_rabbitmq_username)
            f.write("abiquo.rabbitmq.password = %s\n" %
                    self.abiquo_rabbitmq_password)
            f.write("abiquo.rabbitmq.host = %s\n" %
                    self.abiquo_rabbitmq_host)
            f.write("abiquo.rabbitmq.port = %s\n" %
                    self.abiquo_rabbitmq_port)
            f.write("abiquo.database.host = %s\n" %
                    self.abiquo_database_host )
            f.write("abiquo.auth.module = %s\n" %
                    self.abiquo_auth_module )
            f.write("abiquo.server.api.location = http://%s:8009/api\n" %
                    self.abiquo_server_ip )
            # add redis props if not instaling remote services
            if not os.path.isdir(instPath + '/opt/abiquo/tomcat/webapps/virtualfactory'):
                    f.write("abiquo.redis.port = %s\n" %
                            self.abiquo_redis_port)
                    f.write("abiquo.redis.host = %s\n" %
                            self.abiquo_redis_host)
            f.close()


    def __init__(self):
        self.logo = 'abiquo'
        self.abiquo_server_ip = '127.0.0.1'
        self.abiquo_db_user = 'root'
        self.abiquo_db_password = ''
        self.abiquo_db_host = 'localhost'
        self.abiquo_rs_ip = '127.0.0.1'
        self.selectedGroups = []
        self.abiquo_server_sessionTimeout = '60'
        self.abiquo_server_mail_server= '127.0.0.1'
        self.abiquo_server_mail_user= 'none@none.es'
        self.abiquo_server_mail_password = 'none'
        self.abiquo_rabbitmq_username = 'guest'
        self.abiquo_rabbitmq_password = 'guest'
        self.abiquo_rabbitmq_host = '127.0.0.1'
        self.abiquo_rabbitmq_port = '5672'
        self.abiquo_database_host = '127.0.0.1'
        self.abiquo_database_user = 'root'
        self.abiquo_database_password = ''
        self.abiquo_dhcprelay_vrange_1 = 1
        self.abiquo_dhcprelay_vrange_2 = 100
        self.abiquo_dhcprelay_management_if = 'eth0'
        self.abiquo_dhcprelay_service_if = 'eth0'
        self.abiquo_dhcprelay_relay_ip = ''
        self.abiquo_dhcprelay_dhcpd_ip = ''
        self.abiquo_dhcprelay_service_network = '10.0.0.0'
        self.abiquo_auth_module = 'abiquo'
        self.abiquo_redis_host =  '127.0.0.1'
        self.abiquo_redis_port = '6379'
        self.install_type = 'abiquo-monolithic'

