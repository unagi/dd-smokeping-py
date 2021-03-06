#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import timeit
from checks import check_status, AgentCheck
from hashlib import md5


class FpingCheck(AgentCheck):
    def __init__(self, name, init_config, agentConfig, instances):
        AgentCheck.__init__(self, name, init_config, agentConfig, instances)

        # instance config
        self._basename = self.init_config.get('basename', 'ping')
        self._ping_timeout = float(self.init_config.get('ping_timeout', 2.0))
        self._last_check_time = int(self.init_config.get('check_interval', 10)) - self._ping_timeout
        self._global_tags = self.init_config.get('tags', {}).copy()

        hosts = []
        for instance in instances:
            if not instance.get('addr', None):
                raise Exception("All instances should have a 'addr' parameter")
            if instance['addr'] in hosts:
                raise Exception("Duplicate address :%s" % instance['addr'])

            hosts.append(instance['addr'])
            # for initialize loss cnt
            self._increment_with_tags('loss_cnt', instance, 0)

    def _instance_tags(self, instance):
        if 'tags' not in instance.keys():
            raise Exception("All instances should have a 'tags' parameter")
        dd_tags = []
        tags = self._global_tags.copy()
        tags.update(instance['tags'])
        tags['dst_addr'] = instance['addr']
        for key, value in tags.iteritems():
            dd_tags.append('%s:%s' % (key, value))
        return dd_tags

    def _increment_with_tags(self, name, instance, value=1):
        self.increment(
            '%s.%s' % (self._basename, name),
            value,
            tags=self._instance_tags(instance)
        )

    def run(self):
        """ Run all instances. """

        inst = {}
        hosts = []
        for i, instance in enumerate(self.instances):
            inst[instance['addr']] = instance
            hosts.append(instance['addr'])
        instance_statuses = [None]*len(hosts)

        fping = Fping(hosts, self._ping_timeout)

        # record elapsed time for fping
        check_start_time = timeit.default_timer()
        elapsed_time = 0
        num = 0
        failures = {}
        while elapsed_time < self._last_check_time:
            result = fping.run()
            exec_time = timeit.default_timer()
            elapsed_time = exec_time - check_start_time
            num += 1

            instance_check_stats = {'run_time': timeit.default_timer() - check_start_time}
            for addr, v in result.items():
                instance = inst[addr]
                if v is None:
                    self._increment_with_tags('loss_cnt', instance)
                    failures[addr] = failures.get(addr, 0) + 1
                    if num == 1:
                        instance_status = check_status.InstanceStatus(
                            hosts.index(addr), check_status.STATUS_WARNING,
                            warnings=self.get_warnings(), instance_check_stats=instance_check_stats
                        )
                else:
                    self.histogram(
                        '%s.rtt' % self._basename,
                        v,
                        tags=self._instance_tags(instance)
                    )
                    if num == 1:
                        instance_status = check_status.InstanceStatus(
                            hosts.index(addr), check_status.STATUS_OK,
                            instance_check_stats=instance_check_stats
                        )
                self._increment_with_tags('total_cnt', instance)
                self._roll_up_instance_metadata()
                if num == 1:
                    instance_statuses[hosts.index(addr)] = instance_status

        for addr in failures.keys():
            self.event({
                'timestamp': int(exec_time),
                'event_type': self._basename,
                'msg_title': 'fping timeout',
                'msg_text': 'ICMP Network Unreachable for ICMP Echo sent to %s %d times' % (addr, failures[addr]),
                'aggregation_key': md5(addr).hexdigest()
            })
        elapsed_time = timeit.default_timer() - check_start_time
        self.log.info("elapsed_time:%s[sec] check_times: %d" % (round(elapsed_time, 2), num))
        return instance_statuses


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
            raise StandardError("Command not found: fping")

        out, error = ping.communicate()
        # Result of fping is output to stderr
        for line in error.splitlines():
            if line.find(':') == -1:
                # skip if line is not contain ":"
                continue
            try:
                addr, rtt = line.split(':', 1)
                result[addr.strip()] = float(rtt)
            except ValueError:
                result[addr.strip()] = None
        if len(result) == 0:
            raise StandardError("Invalid addresses : %s" % ",".join(self._hosts))
        return result
