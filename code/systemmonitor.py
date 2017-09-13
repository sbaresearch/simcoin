import sched
import time
import logging
import bash
import queue
import re
import filewriter
import config


def run(stop_event, frequency, path, tag):
    scheduler = sched.scheduler(time.time, time.sleep)
    next_execution = time.time()
    q_cpu_time = queue.Queue()
    q_memory = queue.Queue()

    while not stop_event.wait(0):
        scheduler.enterabs(next_execution, 1, collect, (q_cpu_time, q_memory,))
        scheduler.run()
        next_execution += frequency

    filewriter.write_csv(path + config.cpu_time_csv, CpuTimeSnapshot.csv_header(), list(q_cpu_time.queue), tag)
    filewriter.write_csv(path + config.memory_csv, MemorySnapshot.csv_header(), list(q_memory.queue), tag)


def collect(q_cpu_time, q_memory):
    cpu_time = bash.check_output('cat /proc/stat | head -1')
    memory = bash.check_output('cat /proc/meminfo | head -2')
    q_cpu_time.put(CpuTimeSnapshot.from_bash(cpu_time))
    q_memory.put(MemorySnapshot.from_bash(memory))

    logging.info('Collected cpu_time and memory usage')


class CpuTimeSnapshot:
    def __init__(self, timestamp, user, nice, system, idle):
        self.timestamp = timestamp
        self.user = user
        self.nice = nice
        self.system = system
        self.idle = idle

    @classmethod
    def from_bash(cls, cpu_time):
        cpu_matched = re.match('cpu\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)', cpu_time)
        snapshot = cls(time.time(), cpu_matched.group(1), cpu_matched.group(2), cpu_matched.group(3), cpu_matched.group(4))
        return snapshot

    @staticmethod
    def csv_header():
        return ['timestamp', 'user', 'nice', 'system', 'idle']

    def vars_to_array(self):
        return [self.timestamp, self.user, self.nice, self.system, self.idle]


class MemorySnapshot:
    def __init__(self, timestamp, total, free):
        self.timestamp = timestamp
        self.total = total
        self.free = free

    @classmethod
    def from_bash(cls, memory):
        memory_matched = re.match('MemTotal:\s+([0-9]+)\s+kB\nMemFree:\s+([0-9]+)\s+kB', memory)
        snapshot = cls(time.time(), memory_matched.group(1), memory_matched.group(2))
        return snapshot

    @staticmethod
    def csv_header():
        return ['timestamp', 'total', 'free']

    def vars_to_array(self):
        return [self.timestamp, self.total, self.free]
