import config
import logging
import time


class Runner:
    def __init__(self, context):
        self.context = context
        self.prepare = None
        self.event = None
        self.post_processing = None

    def run(self):
        try:
            self.context.general_infos['step_times'] = {}
            self.context.general_infos['step_times']['preparation_start'] = time.time()
            self.prepare.execute()

            self.context.general_infos['step_times']['simulation_start'] = time.time()
            logging.info(config.log_line_sim_start)
            self.event.execute()
            logging.info(config.log_line_sim_end)

            self.context.general_infos['step_times']['postprocessing_start'] = time.time()
            self.post_processing.execute()
        except Exception as exce:
            self.post_processing.clean_up_docker()
            logging.error('Simulation terminated because of exception={}'.format(exce))
