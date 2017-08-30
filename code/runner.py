import config
import logging


class Runner:
    def __init__(self, context):
        self.context = context
        self.prepare = None
        self.event = None
        self.post_processing = None

    def run(self):
        try:
            self.prepare.execute()
            logging.info(config.log_line_sim_start)
            try:
                self.event.execute()
            finally:
                logging.info(config.log_line_sim_end)

                self.post_processing.execute()
        except Exception as exce:
            self.post_processing.rm_nodes_and_network()
            logging.error('Simulation could not be started because of exception={}'.format(exce))
