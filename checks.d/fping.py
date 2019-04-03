#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import time
from hashlib import md5
from checks import AgentCheck


class FpingCheck(AgentCheck):
    def __init__(self, name, init_config, agentConfig, instances):
        AgentCheck.__init__(self, name, init_config, agentConfig, instances)

        # instance config
        self._basename = self.init_config.get('basename', 'ping')
        self._ping_timeout = float(self.init_config.get('ping_timeout', 2.0))
        self._last_check_time = int(self.init_config.get('check_interval', 10)) - self._ping_timeout
        self._global_tags = self.init_config.get('tags', {}).copy()
        self._use_failure_log = self.init_config.get('use_failure_log', False)

        try:
            addr_list = [i['addr'] for i in instances]
        except KeyError:
            raise Exception("All instances should have a 'addr' parameter")
        if len(sorted(set(addr_list))) != len(instances):
            raise Exception("Duplicate address found: {}".format(",".join(sorted(set(addr_list), key=addr_list.index))))
        self._addr_list = addr_list

        for instance in instances:
            # for initialize loss cnt
            self._increment_with_tags('loss_cnt', instance, 0)

    def _instance_tags(self, instance):
        if 'tags' not in instance.keys():
            raise Exception("All instances should have a 'tags' parameter")
        dd_tags = []
        tags = self._global_tags.copy()
        tags.update(instance['tags'])
        tags['dst_addr'] = instance['addr']
        for key, value in tags.items():
            dd_tags.append('{}:{}'.format(key, value))
        return dd_tags

    def _increment_with_tags(self, name, instance, value=1):
        self.increment(
            '{}.{}'.format(self._basename, name),
            value,
            tags=self._instance_tags(instance)
        )

    def get_instance_by_addr(self, addr):
        return self.instances[self._addr_list.index(addr)]

    def run(self):
        """ Run all instances. """
        # record elapsed time for fping
        check_start_time = time.time()

        fping = Fping(self._addr_list, self._ping_timeout)

        num = 0
        failures = {}
        while time.time() - check_start_time < self._last_check_time:
            result = fping.run()
            num += 1

            for addr, v in result.items():
                instance = self.get_instance_by_addr(addr)
                if v is None:
                    # PacketLoss
                    self._increment_with_tags('loss_cnt', instance)
                    failures[addr] = failures.get(addr, 0) + 1
                else:
                    # Ping Success
                    self.histogram(
                        '{}.rtt'.format(self._basename),
                        v,
                        tags=self._instance_tags(instance)
                    )
                self._increment_with_tags('total_cnt', instance)
                self._roll_up_instance_metadata()

        exec_time = time.time()
        if self._use_failure_log:
            for addr in failures.keys():
                self.event({
                    'timestamp': int(exec_time),
                    'event_type': self._basename,
                    'msg_title': 'fping timeout',
                    'msg_text': 'ICMP Network Unreachable for ICMP Echo sent to {} {} times'.format(addr,
                                                                                                    failures[addr]),
                    'aggregation_key': md5(addr).hexdigest()
                })
        self.log.info("elapsed_time:{}[sec] check_times: {}".format(round(time.time() - check_start_time, 2), num))


class Fping(object):
    def __init__(self, hosts, timeout):
        self._hosts = hosts
        self._timeout = int(float(timeout)*1000)

    def run(self):
        result = {}
        try:
            ping = subprocess.Popen(
                ["fping", "-C1", "-q", "-B1", "-r1", "-i10", "-t", str(self._timeout)] + self._hosts,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except OSError:
            raise Exception("Command not found: fping")

        out, error = ping.communicate()
        # Result of fping is output to stderr
        for line in error.splitlines():
            line = line.decode('utf-8')
            if line.find(':') == -1:
                # skip if line is not contain ":"
                continue
            try:
                addr, rtt = line.split(':', 1)
                result[addr.strip()] = float(rtt)
            except ValueError:
                result[addr.strip()] = None
        if len(result) == 0:
            raise Exception("Invalid addresses : {}".format(",".join(self._hosts)))
        return result
