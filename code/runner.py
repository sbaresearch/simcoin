import config
import logging
import time
import systemmonitor
import threading
import queue
import math
import utils
from systemmonitor import CpuTimeSnapshot
from systemmonitor import MemorySnapshot


class Runner:
    def __init__(self, context, writer):
        self.context = context
        self.writer = writer
        self.prepare = None
        self.event = None
        self.post_processing = None
        self.pill2kill = threading.Event()
        self.q_cpu_time = queue.Queue()
        self.q_memory = queue.Queue()
        self.system_monitor = threading.Thread(
            target=systemmonitor.run, args=(self.pill2kill,
                                            calculate_frequency(
                                                self.context.args.tick_duration,
                                                self.context.args.amount_of_ticks),
                                            self.q_cpu_time, self.q_memory))

    def run(self):
        try:
            self.context.step_times.append(StepTimes(time.time(), 'preparation_start'))
            self.prepare.execute()

            self.system_monitor.start()
            self.context.step_times.append(StepTimes(time.time(), 'simulation_start'))
            logging.info(config.log_line_sim_start)
            self.event.execute()
            logging.info(config.log_line_sim_end)

            self.persist_system_snapshots()

            self.context.step_times.append(StepTimes(time.time(), 'postprocessing_start'))
            self.post_processing.execute()
        except Exception as exce:
            self.post_processing.clean_up_docker()
            raise exce

    def persist_system_snapshots(self):
        self.pill2kill.set()
        self.system_monitor.join()
        cpu_times = list(self.q_cpu_time.queue)
        memory = list(self.q_memory.queue)

        self.writer.write_csv(
            CpuTimeSnapshot.file_name,
            CpuTimeSnapshot.csv_header,
            cpu_times,
        )
        self.writer.write_csv(
            MemorySnapshot.file_name,
            MemorySnapshot.csv_header,
            memory,
        )
        logging.info('Persisted {} CPU time and {} memory snapshots'.format(len(cpu_times), len(memory)))


class StepTimes:
    csv_header = ['timestamp', 'type']

    def __init__(self, timestamp, type):
        self.timestamp = timestamp
        self.type = type

    def vars_to_array(self):
        return [self.timestamp, self.type]


def calculate_frequency(tick_duration, amount_of_ticks):
    frequency = math.ceil(tick_duration * amount_of_ticks / config.amount_of_system_snapshots)
    logging.info('With tick_duration={}, amount_of_ticks={} and amount_of_system_snapshots={}'
                 ' the system monitor needs to take every {}s a snapshot'
                 .format(tick_duration, amount_of_ticks, config.amount_of_system_snapshots, frequency))
    return frequency
