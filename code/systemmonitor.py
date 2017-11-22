import sched
import time
import logging
import bash
import re

PRIORITY = 1


def run(stop_event, frequency, q_cpu_time, q_memory):
    logging.info('Starting system monitor with frequency={}s'.format(str(frequency)))
    scheduler = sched.scheduler(time.time, time.sleep)
    next_execution = time.time()

    while not stop_event.wait(0):
        scheduler.enterabs(next_execution, PRIORITY, _collect, (q_cpu_time, q_memory,))
        scheduler.run()
        next_execution += frequency


def _collect(q_cpu_time, q_memory):
    cpu_time = bash.check_output('cat /proc/stat | head -1')
    memory = bash.check_output('cat /proc/meminfo | head -3')
    q_cpu_time.put(CpuTimeSnapshot.from_bash(cpu_time))
    q_memory.put(MemorySnapshot.from_bash(memory))

    logging.info('Collected cpu_time and memory usage')


class CpuTimeSnapshot:
    __slots__ = ['_timestamp', '_user', '_nice', '_system', '_idle']
    file_name = 'cpu_time.csv'
    csv_header = ['timestamp', 'user', 'nice', 'system', 'idle']

    def __init__(self, timestamp, user, nice, system, idle):
        self._timestamp = timestamp
        self._user = user
        self._nice = nice
        self._system = system
        self._idle = idle

    @classmethod
    def from_bash(cls, cpu_time):
        cpu_matched = re.match('cpu\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)', cpu_time)
        snapshot = cls(time.time(), cpu_matched.group(1), cpu_matched.group(2), cpu_matched.group(3), cpu_matched.group(4))
        return snapshot

    def vars_to_array(self):
        return [self._timestamp, self._user, self._nice, self._system, self._idle]


class MemorySnapshot:
    __slots__ = ['_timestamp', '_total', '_available']

    file_name = 'memory.csv'
    csv_header = ['timestamp', 'total', 'available']

    def __init__(self, timestamp, total, available):
        self._timestamp = timestamp
        self._total = total
        self._available = available

    @classmethod
    def from_bash(cls, memory):
        memory_matched = re.match('MemTotal:\s+([0-9]+)\s+kB\n.*\nMemAvailable:\s+([0-9]+)\s+kB', memory)
        snapshot = cls(time.time(), memory_matched.group(1), memory_matched.group(2))
        return snapshot

    def vars_to_array(self):
        return [self._timestamp, self._total, self._available]
