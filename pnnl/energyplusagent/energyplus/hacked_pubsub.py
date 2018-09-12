# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:

# Copyright (c) 2017, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation
# are those of the authors and should not be interpreted as representing
# official policies, either expressed or implied, of the FreeBSD
# Project.
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization that
# has cooperated in the development of these materials, makes any
# warranty, express or implied, or assumes any legal liability or
# responsibility for the accuracy, completeness, or usefulness or any
# information, apparatus, product, software, or process disclosed, or
# represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does not
# necessarily constitute or imply its endorsement, recommendation, or
# favoring by the United States Government or any agency thereof, or
# Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
#}}}

from inspect import getcallargs
import collections, sys, logging
from datetime import datetime, timedelta
from volttron.platform.agent import utils
from volttron.platform.messaging import headers as headers_mod
from volttron.platform.vip.agent import Agent, Core
import time
from datetime import timedelta as td


utils.setup_logging()
log = logging.getLogger(__name__)


class PubSubAgent(Agent):       
    def __init__(self, config_path, **kwargs):
        self.config = utils.load_config(config_path)
        self.inputs = collections.OrderedDict()
        self.outputs = collections.OrderedDict()
        kwargs = self.update_kwargs_from_config(**kwargs)
        super(PubSubAgent, self).__init__(**kwargs)
        self._now = datetime.utcnow()

    
    def update_kwargs_from_config(self, **kwargs):
        signature = getcallargs(super(PubSubAgent, self).__init__)
        for arg in signature:
            if self.config.has_key('properties'):
                properties = self.config.get('properties')
                if isinstance(properties, dict) and properties.has_key(arg):
                    kwargs[arg] = properties.get(arg)
        return kwargs
    
    
    @Core.receiver('onsetup')
    def setup(self, sender, **kwargs):
        if 'inputs' in self.config: 
            self.inputs = self.config['inputs']
        if 'outputs' in self.config:
            outputs = self.config['outputs']
            self.outputs = self.create_ordered_output(outputs)
        if 'properties' in self.config and isinstance(self.config['properties'], dict):
            self.__dict__.update(self.config['properties'])
        self.cosimulation_advance = self.config.get('cosimulation_advance', None)


    @Core.receiver('onstart')  
    def start(self, sender, **kwargs):
        self.subscribe()


    def create_ordered_output(self, output):
        last_key = None
        ordered_out = collections.OrderedDict()
        for key, value in output.items():
            if not value.has_key('publish_last'):
                ordered_out[key] = value
            else:
                last_key = key
                last_value = value
        if last_key is not None:
            ordered_out[last_key] = last_value
        return ordered_out
        
    
    def input(self, *args):
        if len(args) == 0:
            return self.inputs
        return self.input_output(self.inputs, *args)
 
 
    def output(self, *args):
        if len(args) == 0:
            return self.outputs
        return self.input_output(self.outputs, *args) 
 
 
    def input_output(self, dct, *args):
        if len(args) >= 1:
            key = args[0]
            if dct.has_key(key):
                if len(args) >= 2:
                    field = args[1]
                    if len(args) >= 3:
                        dct.get(key)[field] = args[2]
                        return args[2]
                    return dct.get(key).get(field)
                return dct.get(key)
        return None
    
    
    def subscribe(self):
        for key, obj in self.input().iteritems():
            if obj.has_key('topic'):
                callback = self.on_match_topic
                topic = obj.get('topic')
                key_caps = 'onMatch' + key[0].upper() + key[1:]
                if obj.has_key('callback'):
                    callbackstr = obj.get('callback')
                    if hasattr(self, callbackstr) and callable(getattr(self, callbackstr, None)):
                        callback = getattr(self, callbackstr)
                elif hasattr(self, key_caps) and callable(getattr(self, key_caps, None)):
                    callback = getattr(self, key_caps)
                log.info('subscribed to ' + topic)
                self.vip.pubsub.subscribe(peer='pubsub', prefix=topic, callback=callback)
        if self.cosimulation_advance is not None:
            self.vip.pubsub.subscribe(peer='pubsub', prefix=self.cosimulation_advance, callback=self.advance_simulation)

    def publish_all_outputs(self):
        #Publish messages
        self.publish(*self.output().values())


    def publish(self, *args):
        #Publish message
        _now = self._now + td(minutes=1)
        self._now = _now

        time_stamp_object_names = ("month", "day", "hour", "minute")

        time_stamp_objects =[self.output(name) for name in time_stamp_object_names]

        if all(time_stamp_objects):
            time_stamp_values = [obj.get("value") for obj in time_stamp_objects]
            if None not in time_stamp_values:
                # We handle minutes separately for eplus interface
                minutes = time_stamp_values[-1]
                _now = datetime(2017, *(int(round(x)) for x in time_stamp_values[:-1]))
                _now += timedelta(minutes=minutes)

        _now = utils.format_timestamp(_now)
        
        headers = {headers_mod.DATE: _now, headers_mod.TIMESTAMP: _now}
        topics = {}
        for arg in args:
            obj = self.output(arg) if type(arg) == str else arg
            if obj.has_key('topic') and obj.has_key('value'):
                topic = obj.get('topic', None)
                value = obj.get('value', None)
                field = obj.get('field', None)
                metadata = obj.get('meta', {})
                if topic is not None and value is not None:
                    if not topics.has_key(topic):
                        topics[topic] = {'values': None, 'fields': None}
                    if field is not None:
                        if topics[topic]['fields'] is None:
                            topics[topic]['fields'] = [{}, {}]
                        topics[topic]['fields'][0][field] = value
                        topics[topic]['fields'][1][field] = metadata
                    else:
                        if topics[topic]['values'] is None:
                            topics[topic]['values'] = []
                        topics[topic]['values'].append([value, metadata])


        for topic, obj in topics.iteritems():
           if obj['values'] is not None:
              for value in obj['values']:
                  out = value
                  log.info('Sending: ' + topic + ' ' + str(out))
                  self.vip.pubsub.publish('pubsub', topic, headers, out).get()
           if obj['fields'] is not None:
                  out = obj['fields']
                  log.info('Sending: ' + topic + ' ' + str(out))
                  self.vip.pubsub.publish('pubsub', topic, headers, out).get()

        self.vip.pubsub.publish('pubsub', "eplus-simulation", headers, None).get()


    def on_match_topic(self, peer, sender, bus, topic, headers, message):
        msg = message if type(message) == type([]) else [message]
        log.info('Received: ' + topic + ' ' + str(msg))
        self.update_topic(peer, sender, bus, topic, headers, msg)
        

    def update_topic(self, peer, sender, bus, topic, headers, message):
        objs = self.get_inputs_from_topic(topic)
        if objs is None:
            return
        for obj in objs:
            value = message[0]
            if type(value) is dict and obj.has_key('field') and value.has_key(obj.get('field')):
                value = value.get(obj.get('field'))
            obj['value'] = value
            obj['message'] = message[0]
            obj['message_meta'] = message[1]
            obj['last_update'] = headers.get(headers_mod.DATE, datetime.utcnow().isoformat(' ') + 'Z')
            self.on_update_topic(peer, sender, bus, topic, headers, message)


    def on_update_topic(self, peer, sender, bus, topic, headers, message):
        self.update_complete()
        
        
    def update_complete(self):
        self.on_update_complete()
        
        
    def on_update_complete(self):
        pass
        
        
    def clear_last_update(self):
        for obj in self.input().itervalues():
            if obj.has_key('topic'):
                obj['last_update'] = None


    def get_inputs_from_topic(self, topic):
        objs = []
        for obj in self.input().itervalues():
            if (obj.get('topic') == topic):
                    objs.append(obj)
        if len(objs):
            return objs
        return None
        
    def get_outputs_from_topic(self, topic):
        objs = []
        for obj in self.output().itervalues():
            if (obj.get('topic') == topic):
                    objs.append(obj)
        if len(objs):
            return objs
        return None


    def find_best_match(self, topic):
        # find match on inputs
        topic = topic.strip('/')
        device_name, point_name = topic.rsplit('/', 1)
        objs = self.get_inputs_from_topic(device_name)
        if objs is not None:
            for obj in objs:
                if obj.has_key('field') and obj.get('field', None) == point_name: # we have matches to the <device topic>, so get the first one has a field matching <point name>
                    return obj
        objs = self.get_inputs_from_topic(topic)
        if objs is not None and len(objs): # we have exact matches to the topic
            return objs[0]
        #if no inputs match check outputs
        if objs is None:
            device_name = ''.join(['devices', '/', device_name, '/', 'all'])
            objs = self.get_outputs_from_topic(device_name)
            if objs is not None:
                for obj in objs:
                    if obj.has_key('field') and obj.get('field', None) == point_name: # we have matches to the <device topic>, so get the first one has a field matching <point name>
                        return obj
            objs = self.get_outputs_from_topic(topic)
            if objs is not None and len(objs): # we have exact matches to the topic
                return objs[0]
        return None


class SynchronizingPubSubAgent(PubSubAgent):

    def __init__(self, config_path, **kwargs):
        super(SynchronizingPubSubAgent, self).__init__(config_path, **kwargs)
        
    
    @Core.receiver('onstart')  
    def start(self, sender, **kwargs):
        super(SynchronizingPubSubAgent, self).start(sender, **kwargs)
        self.update_complete()
        
    
    def update_complete(self):
        if self.all_topics_updated():
            self.clear_last_update()
            self.on_update_complete()
            
            
    def all_topics_updated(self):
        for obj in self.input().itervalues():
            if obj.has_key('topic'):
                if (obj.has_key('blocking') and obj.get('blocking')) or not obj.has_key('blocking'):
                    if obj.has_key('last_update'):
                        if obj.get('last_update') is None:
                            return False
                    else:
                        return False
        return True


    def on_update_complete(self):
        self.publish_all_outputs()


class Event(object):
        
    @staticmethod
    def post(function, callback, *args):
        condition = True if len(args) == 0 else args[0]
        setattr(function.__self__, function.__name__, Event.__post(function, callback, condition))
    
    
    @staticmethod      
    def __post(function, callback, condition):
        def __wrapper(*args, **kwargs):
            result = function(*args, **kwargs)
            if type(condition) == bool: istrue = condition
            else: istrue = condition()
            if istrue: callback()
            return result
        __wrapper.__name__ = function.__name__
        __wrapper.__self__ = function.__self__
        return __wrapper
    
    
    @staticmethod
    def pre(function, callback, *args):
        condition = True if len(args) == 0 else args[0]
        setattr(function.__self__, function.__name__, Event.__pre(function, callback, condition))
    
    
    @staticmethod      
    def __pre(function, callback, condition):
        def __wrapper(*args, **kwargs):
            if type(condition) == bool: istrue = condition
            else: istrue = condition()
            if istrue: callback()
            result = function(*args, **kwargs)
            return result
        __wrapper.__name__ = function.__name__
        __wrapper.__self__ = function.__self__
        return __wrapper


def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.vip_main(PubSubAgent)
    except Exception as e:
        log.exception(e)


if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())
