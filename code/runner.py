import config
import logging
import time
import systemmonitor
import threading


class Runner:
    def __init__(self, context):
        self.context = context
        self.prepare = None
        self.event = None
        self.post_processing = None
        self.pill2kill = threading.Event()
        self.system_monitor = threading.Thread(
            target=systemmonitor.run, args=(self.pill2kill, 5,
                                            self.context.path.postprocessing_dir, self.context.args.tag))

    def run(self):
        try:
            self.context.general_infos['step_times'] = {}
            self.context.general_infos['step_times']['preparation_start'] = time.time()
            self.prepare.execute()

            self.system_monitor.start()
            self.context.general_infos['step_times']['simulation_start'] = time.time()
            logging.info(config.log_line_sim_start)
            self.event.execute()
            logging.info(config.log_line_sim_end)

            self.pill2kill.set()
            self.system_monitor.join()

            self.context.general_infos['step_times']['postprocessing_start'] = time.time()
            self.post_processing.execute()
        except Exception as exce:
            self.post_processing.clean_up_docker()
            logging.error('Simulation terminated because of exception={}'.format(exce))
