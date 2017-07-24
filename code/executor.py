import dockercmd
import bitcoincmd
import ipaddress
import config
import csv
from node import PublicBitcoinNode
from node import SelfishPrivateNode
from node import ProxyNode
import logging
import time
import json
import bash
import prepare
import utils
import networktopology
import subprocess


class Executor:
    def __init__(self, args):
        self.count = 0
        self.stats = None
        self.event = None

        nodes, selfish_nodes = networktopology.read_amount_of_nodes()
        ip_addresses = ipaddress.ip_network(config.ip_range).hosts()
        next(ip_addresses)  # skipping first ip address (docker fails with error "is in use")

        self.nodes = {config.node_name.format(str(i)):
                      PublicBitcoinNode(config.node_name.format(str(i)), next(ip_addresses))
                      for i in range(nodes)}

        self.selfish_node_private_nodes = {}
        self.selfish_node_proxies = {}
        for i in range(selfish_nodes):
            ip_private_node = next(ip_addresses)
            ip_proxy = next(ip_addresses)
            self.selfish_node_private_nodes[config.selfish_node_name.format(str(i))] = \
                SelfishPrivateNode(config.selfish_node_name.format(str(i)), ip_private_node)

            self.selfish_node_proxies[config.selfish_node_proxy_name.format(str(i))] = \
                ProxyNode(config.selfish_node_proxy_name.format(str(i)),
                          ip_proxy, ip_private_node, args.selfish_nodes_args)

        self.all_bitcoin_nodes = dict(self.nodes, **self.selfish_node_private_nodes)

        self.all_public_nodes = dict(self.nodes, **self.selfish_node_proxies)
        self.all_nodes = dict(self.nodes, **self.selfish_node_private_nodes, **self.selfish_node_proxies)

        self.one_normal_node = next(iter(self.nodes.values()))

        connections = networktopology.read_connections()
        for node in self.all_public_nodes.values():
            node.outgoing_ips = [str(self.all_public_nodes[connection].ip) for connection in connections[node.name]]

        latencies = networktopology.read_latencies()
        for node in latencies.keys():
            self.all_public_nodes[node].latency = latencies[node]

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

            for node in self.all_public_nodes.values():
                node.add_latency()

            for node in self.all_bitcoin_nodes.values():
                node.spent_to_address = node.get_new_address()

            self.event.execute()

            # only use regular nodes since selfish nodes can trail back
            array = False
            while utils.check_equal(array) is False:
                logging.debug('Waiting for blocks to spread...')
                utils.sleep(0.2)
                array = [int(node.get_block_count()) for node in self.nodes.values()]

            bash.check_output(dockercmd.fix_data_dirs_permissions())

            self.stats.save_consensus_chain()
            self.stats.update_blocks_csv()
            self.stats.update_tx_csv()
            self.stats.save_chains()
            self.stats.node_stats()
            self.stats.aggregate_logs()

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

    def generate_block_and_save_creator(self, node, amount):
        blocks_string = bash.check_output(bitcoincmd.generate_block(node, amount))
        blocks = json.loads(blocks_string)
        with open(config.blocks_csv, 'a') as file:
            for block in blocks:
                file.write('{};{}\n'.format(node, block))
        self.all_bitcoin_nodes[node].mined_blocks += 1


def generate_tx_and_save_creator(node, address):
    try:
        tx_hash = node.generate_tx(address)
        with open(config.tx_csv, 'a') as file:
            file.write('{};{}\n'.format(node.name, tx_hash))
    except subprocess.CalledProcessError:
        logging.info('Could not generate tx for node {}'.format(node.name))
