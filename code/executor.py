import dockercmd
import ipaddress
import config
from node.bitcoinnode import PublicBitcoinNode
from node.selfishnode import SelfishPrivateNode
from node.selfishnode import ProxyNode
import logging
import bash
import prepare
import utils
import networktopology
import nodesconfig


class Executor:
    def __init__(self):
        self.count = 0
        self.post_processing = None
        self.event = None

        config_nodes = nodesconfig.read()
        nodes = [node for node in config_nodes if node.node_type == 'bitcoin']
        selfish_nodes = [node for node in config_nodes if node.node_type == 'selfish']
        ip_addresses = ipaddress.ip_network(config.ip_range).hosts()
        next(ip_addresses)  # skipping first ip address (docker fails with error "is in use")

        self.nodes = {node.name: PublicBitcoinNode(node.name, next(ip_addresses), node.latency) for node in nodes}

        self.selfish_node_private_nodes = {}
        self.selfish_node_proxies = {}
        for node in selfish_nodes:
            ip_private_node = next(ip_addresses)
            ip_proxy = next(ip_addresses)
            self.selfish_node_private_nodes[node.name] = SelfishPrivateNode(node.name, ip_private_node)

            self.selfish_node_proxies[node.name_proxy] = \
                ProxyNode(node.name_proxy, ip_proxy, ip_private_node, node.selfish_nodes_args, node.latency)

        self.all_bitcoin_nodes = dict(self.nodes, **self.selfish_node_private_nodes)

        self.all_public_nodes = dict(self.nodes, **self.selfish_node_proxies)
        self.all_nodes = dict(self.nodes, **self.selfish_node_private_nodes, **self.selfish_node_proxies)

        self.one_normal_node = next(iter(self.nodes.values()))

        connections = networktopology.read_connections()
        for node in self.all_public_nodes.values():
            node.outgoing_ips = [str(self.all_public_nodes[connection].ip) for connection in connections[node.name]]

        self.first_block_height = config.warmup_blocks + config.start_blocks_per_node * len(self.all_bitcoin_nodes)

    def execute(self):
        try:
            prepare.remove_old_containers_if_exists()
            prepare.recreate_network()
            prepare.prepare_simulation_dir()
            utils.sleep(4)

            prepare.give_nodes_spendable_coins(list(self.all_bitcoin_nodes.values()))

            for node in self.all_bitcoin_nodes.values():
                node.run()

            for node in self.all_bitcoin_nodes.values():
                prepare.wait_until_height_reached(node, self.first_block_height)

            start_hash = self.one_normal_node.get_best_block_hash()
            for node in self.selfish_node_proxies.values():
                node.run(start_hash)
            utils.sleep(2)
            for node in self.selfish_node_proxies.values():
                node.wait_for_highest_tip_of_node(self.one_normal_node)

            for node in self.nodes.values():
                node.connect(node.outgoing_ips)
            utils.sleep(4 + len(self.all_nodes) * 0.2)

            for node in self.all_bitcoin_nodes.values():
                node.spent_to_address = node.get_new_address()
                node.rpc_connect()

            for node in self.all_public_nodes.values():
                node.add_latency()

            logging.info(config.log_line_sim_start)
            self.event.execute()

            # only use regular nodes since selfish nodes can trail back
            array = False
            while utils.check_equal(array) is False:
                logging.debug('Waiting for blocks to spread...')
                utils.sleep(0.2)
                array = [int(node.get_block_count()) for node in self.nodes.values()]
            logging.info(config.log_line_sim_end)

            bash.check_output(dockercmd.fix_data_dirs_permissions())

            self.post_processing.execute()

            for node in self.all_nodes.values():
                node.grep_log_for_errors()
        finally:
            # remove proxies first. if not proxies could be already stopped when trying to remove
            for node in self.selfish_node_proxies.values():
                node.rm_silent()
            for node in self.all_bitcoin_nodes.values():
                node.rm_silent()
            utils.sleep(3 + len(self.all_nodes) * 0.2)

            bash.call_silent(dockercmd.rm_network())
