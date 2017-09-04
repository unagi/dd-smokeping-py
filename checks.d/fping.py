#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import timeit
from checks import check_status, AgentCheck


class FpingCheck(AgentCheck):
    def __init__(self, name, init_config, agentConfig, instances):
        AgentCheck.__init__(self, name, init_config, agentConfig, instances)

        # instance config
        self._basename = self.init_config.get('basename', 'ping')
        self._ping_timeout = float(self.init_config.get('ping_timeout', 2.0))
        self._last_check_time = int(self.init_config.get('check_interval', 10)) - self._ping_timeout

        hosts = []
        for instance in instances:
            if not instance.get('isp', None):
                raise Exception("All instances should have a 'isp' parameter")
            if instance['addr'] in hosts:
                raise Exception("Duplicate address :%s" % instance['addr'])

            hosts.append(instance['addr'])
            # for initialize loss cnt
            self.increment(
                '%s.total_loss' % self._basename,
                0,
                tags=['isp:%s' % instance['isp'], 'locate:%s' % instance['name']]
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
        while elapsed_time < self._last_check_time:
            result = fping.run()
            exec_time = timeit.default_timer()
            elapsed_time = exec_time - check_start_time
            num += 1

            instance_check_stats = {'run_time': timeit.default_timer() - check_start_time}
            for addr, v in result.items():
                instance = inst[addr]
                if v is None:
                    self.increment(
                        '%s.loss_cnt' % self._basename,
                        tags=['isp:%s' % instance['isp'], 'locate:%s' % instance['name']]
                    )
                    self.event({
                        'timestamp': int(exec_time),
                        'event_type': self._basename,
                        'msg_title': 'fping timeout',
                        'msg_text': 'ICMP Network Unreachable for ICMP Echo sent to %s' % addr
                    })
                    if num == 1:
                        instance_status = check_status.InstanceStatus(
                            hosts.index(addr), check_status.STATUS_WARNING,
                            warnings=self.get_warnings(), instance_check_stats=instance_check_stats
                        )
                else:
                    self.histogram(
                        '%s.rtt' % self._basename,
                        v,
                        tags=['isp:%s' % instance['isp'], 'locate:%s' % instance['name']]
                    )
                    if num == 1:
                        instance_status = check_status.InstanceStatus(
                            hosts.index(addr), check_status.STATUS_OK,
                            instance_check_stats=instance_check_stats
                        )
                self.increment(
                    '%s.total_cnt' % self._basename,
                    tags=['isp:%s' % instance['isp'], 'locate:%s' % instance['name']]
                )
                self._roll_up_instance_metadata()
                if num == 1:
                    instance_statuses[hosts.index(addr)] = instance_status

        elapsed_time = timeit.default_timer() - check_start_time
        self.log.info("elapsed_time:%s[sec] check_times: %d" % (round(elapsed_time, 2), num))
        return instance_statuses


class Fping(object):
    def __init__(self, hosts, timeout):
        self._hosts = hosts
        self._timeout = int(float(timeout)*1000)

    def run(self):
        result = {}
        ping = subprocess.Popen(
            ["fping", "-C1", "-q", "-B1", "-r1", "-i10", "-t", str(self._timeout)] + self._hosts,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, error = ping.communicate()
        # Result of fping is output to stderr
        for line in error.splitlines():
            try:
                addr, rtt = line.split(':', 1)
                result[addr.strip()] = float(rtt)
            except:
                result[addr.strip()] = None
        return result
