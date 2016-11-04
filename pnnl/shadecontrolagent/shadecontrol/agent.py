# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright (c) 2016, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#

# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# r favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830

#}}}

from __future__ import absolute_import


import logging
import sys
from datetime import datetime
from volttron.platform.agent import utils
from volttron.platform.vip.agent import Core
from volttron.platform.messaging import headers as headers_mod
from pnnl.pubsubagent.pubsub.agent import SynchronizingPubSubAgent


utils.setup_logging()
log = logging.getLogger(__name__)


class ShadeControlAgent(SynchronizingPubSubAgent):


    def __init__(self, config_path, **kwargs):
        super(ShadeControlAgent, self).__init__(config_path, **kwargs)
        

    @Core.receiver('onsetup')
    def setup(self, sender, **kwargs):
        super(ShadeControlAgent, self).setup(sender, **kwargs)
        

    def onUpdateTopic(self, peer, sender, bus, topic, headers, message):
        value = 1 if self.input("outdoorDryBulb", "value") > 10 and self.input("incidentRadiation", "value") > 200 else 0
        self.output("shadeSchedule", "value", value)
        super(ShadeControlAgent, self).onUpdateTopic(peer, sender, bus, topic, headers, message)
    
    
    def publish(self, *args):
        #Publish message
        things = args
        pub = []
        rpc = []
        for thing in things:
            obj = self.output(thing) if type(thing) == str else thing
            if obj.get('target', None):
                rpc.append(obj)
            else:
                pub.append(obj) 
        for obj in rpc:
            if obj.has_key('topic') and obj.has_key('value'):
                topic = obj.get('topic', None)
                field = obj.get('field', None)
                topic = topic+"/"+field if field is not None else topic
                value = obj.get('value', None)
                target = obj.get('target', None)
                if (topic is not None) and (value is not None) and (target is not None):
                    log.info('Attempting to set: ' + topic + ' ' + str(value))
                    try:
                        result = self.vip.rpc.call(
                           target,    #Target agent
                           'set_point',            #Method to call
                           self.core.identity,               #Requestor
                           topic,       #Point to set
                           value,                  #New value
                           ).get(timeout=10)
                        if self.rpcFailed(result):
                            log.warn('Failed to set {} on {} (unavailable) '.format(value, topic))
                    except Exception as ex:
                        log.warning("Failed to set {} on {} (Exception): {}".format(value, topic, str(ex)))
        super(ShadeControlAgent, self).publish(*pub)
    
    
    def rpcFailed(self, result):
        if isinstance(result, dict):
            if 'result' in result:
                if result['result'] != 'FAILURE':
                    return True
        return False


def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.vip_main(ShadeControlAgent)
    except Exception as e:
        log.exception(e)


if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())
