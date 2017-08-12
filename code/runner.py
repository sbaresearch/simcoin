import dockercmd
import config
import logging
import bash
import prepare
import utils


class Runner:
    def __init__(self, context):
        self.context = context
        self.event = None
        self.post_processing = None

    def run(self):
        try:
            prepare.execute(list(self.context.all_bitcoin_nodes.values()))

            for node in self.context.all_bitcoin_nodes.values():
                node.run()
            utils.sleep(4 + len(self.context.all_bitcoin_nodes) * 0.2)

            for node in self.context.all_bitcoin_nodes.values():
                prepare.wait_until_height_reached(node, self.context.first_block_height)

            start_hash = self.context.one_normal_node.execute_rpc('getbestblockhash')
            for node in self.context.selfish_node_proxies.values():
                node.run(start_hash)
            utils.sleep(2)
            for node in self.context.selfish_node_proxies.values():
                node.wait_for_highest_tip_of_node(self.context.one_normal_node)

            for node in self.context.nodes.values():
                node.connect()
            utils.sleep(4 + len(self.context.all_nodes) * 0.2)

            for node in self.context.all_public_nodes.values():
                node.add_latency(self.context.zone.zones)

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
