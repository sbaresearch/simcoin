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
            self.event.execute()
            logging.info(config.log_line_sim_end)

            self.post_processing.execute()
        except Exception as exce:
            self.post_processing.clean_up_docker()
            logging.error('Simulation terminated because of exception={}'.format(exce))
