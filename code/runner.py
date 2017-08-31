import config
import logging
import time
import analyze


class Runner:
    def __init__(self):
        self.general_infos = {}
        self.prepare = None
        self.event = None
        self.post_processing = None

    def run(self):
        try:
            self.general_infos['preparation_start'] = time.time()
            self.prepare.execute()

            self.general_infos['simulation_start'] = time.time()
            logging.info(config.log_line_sim_start)
            self.event.execute()
            logging.info(config.log_line_sim_end)

            self.general_infos['postprocessing_start'] = time.time()
            self.post_processing.execute()
            self.general_infos['postprocessing_end'] = time.time()
            analyze.create_general_infos_json(self.general_infos)
        except Exception as exce:
            self.post_processing.clean_up_docker()
            logging.error('Simulation terminated because of exception={}'.format(exce))
