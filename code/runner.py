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

        finally:
            logging.info(config.log_line_sim_end)

            self.post_processing.execute()
