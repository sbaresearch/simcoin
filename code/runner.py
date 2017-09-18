import config
import logging
import time
import systemmonitor
import threading
import queue


class Runner:
    def __init__(self, context):
        self.context = context
        self.prepare = None
        self.event = None
        self.post_processing = None
        self.pill2kill = threading.Event()
        self.q_cpu_time = queue.Queue()
        self.q_memory = queue.Queue()
        self.system_monitor = threading.Thread(
            target=systemmonitor.run, args=(self.pill2kill, self.context.args.system_snapshots_frequency,
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

            self.pill2kill.set()
            self.system_monitor.join()
            self.context.cpu_time = list(self.q_cpu_time.queue)
            self.context.memory = list(self.q_memory.queue)

            self.context.step_times.append(StepTimes(time.time(), 'postprocessing_start'))
            self.post_processing.execute()
        except Exception as exce:
            self.post_processing.clean_up_docker()
            logging.error('Simulation terminated because of exception={}'.format(exce))


class StepTimes:
    def __init__(self, timestamp, type):
        self.timestamp = timestamp
        self.type = type

    @staticmethod
    def csv_header():
        return ['timestamp', 'type']

    def vars_to_array(self):
        return [self.timestamp, self.type]
