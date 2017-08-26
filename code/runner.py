from cmd import dockercmd
import config
import logging
import bash
import utils
from clistats import CliStats


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

            cli_stats = CliStats(self.context)
            cli_stats.execute()

            for node in self.context.all_nodes.values():
                node.rm_silent()
            utils.sleep(3 + len(self.context.all_nodes) * 0.2)
            logging.info('Removed all docker containers')

            bash.call_silent(dockercmd.rm_network())
            logging.info('Deleted docker network')

            bash.check_output(dockercmd.fix_data_dirs_permissions())
            logging.info('Fixed data permission of container folders')

            for node in self.context.all_nodes.values():
                node.grep_log_for_errors()

            self.post_processing.execute()
