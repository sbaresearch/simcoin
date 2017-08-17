import dockercmd
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

            # only use regular nodes since selfish nodes can trail back
            array = False
            while utils.check_equal(array) is False:
                logging.debug('Waiting for blocks to spread...')
                utils.sleep(0.2)
                array = [int(node.execute_rpc('getblockcount')) for node in self.context.nodes.values()]
            logging.info(config.log_line_sim_end)

            self.post_processing.execute()

            for node in self.context.all_nodes.values():
                node.grep_log_for_errors()
        finally:
            bash.check_output(dockercmd.fix_data_dirs_permissions())

            # remove proxies first. if not proxies could be already stopped when trying to remove
            for node in self.context.selfish_node_proxies.values():
                node.rm_silent()
            for node in self.context.all_bitcoin_nodes.values():
                node.rm_silent()
            utils.sleep(3 + len(self.context.all_nodes) * 0.2)

            bash.call_silent(dockercmd.rm_network())
