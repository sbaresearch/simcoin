from cmd import dockercmd
import config
import logging
import bash
import utils


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
            # TODO add line number to log lines.
            utils.sleep(1)
            logging.info(config.log_line_sim_end)

            self.post_processing.execute()

            for node in self.context.all_nodes.values():
                node.grep_log_for_errors()

            bash.check_output(dockercmd.fix_data_dirs_permissions())

            # remove proxies first. if not proxies could be already stopped when trying to remove
            for node in self.context.selfish_node_proxies.values():
                node.rm_silent()
            for node in self.context.all_bitcoin_nodes.values():
                node.rm_silent()
            utils.sleep(3 + len(self.context.all_nodes) * 0.2)

            bash.call_silent(dockercmd.rm_network())
