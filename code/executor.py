import dockercmd
import bitcoincmd
import ipaddress
import config
import pandas
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


class Executor:
    def __init__(self, args):
        self.count = 0
        self.tick_duration = args.tick_duration
        self.stats = None
        self.prepare = None

        nodes = selfish_nodes = 0
        network_config = pandas.read_csv(open(config.network_config), delimiter=';', index_col=0)
        for node_row, row in network_config.iterrows():
            if node_row.startswith(config.node_prefix):
                nodes += 1
            elif node_row.startswith(config.selfish_node_prefix):
                selfish_nodes += 1
            else:
                raise Exception('Unknown node type in {}'.format(config.network_config))
        logging.info('Parsed {} nodes and {} selfish nodes from {}'.format(nodes, selfish_nodes, config.network_config))

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
        self.first_block_height = len(self.all_bitcoin_nodes) + config.warmup_blocks + 1

        self.all_public_nodes = dict(self.nodes, **self.selfish_node_proxies)
        self.all_nodes = dict(self.nodes, **self.selfish_node_private_nodes, **self.selfish_node_proxies)

        self.one_normal_node = next(iter(self.nodes.values()))

        network_config = pandas.read_csv(open(config.network_config), delimiter=';', index_col=0)
        connections = {}
        for node_row, row in network_config.iterrows():
            if node_row.startswith(config.selfish_node_prefix):
                node_row += config.selfish_node_proxy_postfix
            connections[node_row] = []
            for node_column, value in row.iteritems():
                if node_column.startswith(config.selfish_node_prefix):
                    node_column += config.selfish_node_proxy_postfix
                if node_column == node_row:
                    self.all_public_nodes[node_column].latency = value
                elif value == 1:
                    connections[node_row].append(node_column)

        for node in self.all_public_nodes.values():
            node.outgoing_ips = [str(self.all_public_nodes[connection].ip) for connection in connections[node.name]]

    def execute(self):
        try:
            prepare.remove_old_containers_if_exists()
            prepare.recreate_network()
            prepare.prepare_simulation_dir()
            utils.sleep(4)

            [bash.check_output(node.run()) for node in self.all_bitcoin_nodes.values()]
            utils.sleep(4 + len(self.all_bitcoin_nodes) * 0.2)

            for i, node in enumerate(self.all_bitcoin_nodes.values()):
                [bash.check_output(cmd) for cmd
                 in node.connect([str(node.ip) for node in list(self.all_bitcoin_nodes.values())[i + 1:i + 5]])]
            utils.sleep(4 + len(self.all_bitcoin_nodes) * 0.2)

            self.prepare.warmup_block_generation()

            [bash.check_output('; '.join([node.delete_peers_file(), node.rm()])) for node in self.all_bitcoin_nodes.values()]

            [bash.check_output(node.run()) for node in self.all_bitcoin_nodes.values()]
            [prepare.wait_until_height_reached(node, config.warmup_blocks + len(self.all_bitcoin_nodes))
             for node in self.all_bitcoin_nodes.values()]

            start_hash = bash.check_output(bitcoincmd.get_best_block_hash(config.reference_node))
            [bash.check_output(node.run(start_hash)) for node in self.selfish_node_proxies.values()]
            [bash.check_output(node.wait_for_highest_tip_of_node(self.one_normal_node))
             for node in self.selfish_node_proxies.values()]

            for node in self.nodes.values():
                [bash.check_output(cmd) for cmd in node.connect(node.outgoing_ips)]
            utils.sleep(4 + len(self.all_nodes) * 0.2)

            [[bash.check_output(cmd) for cmd in node.add_latency()] for node in self.all_public_nodes.values()]

            reader = csv.reader(open(config.tick_csv, "r"), delimiter=";")
            start_time = time.time()
            for i, line in enumerate(reader):
                for cmd in line:
                    cmd_parts = cmd.split(' ')
                    if cmd_parts[0] == 'block':
                        self.generate_block_and_save_creator(cmd_parts[1], 1)
                    elif cmd_parts[0] == 'tx':
                        node = self.all_bitcoin_nodes[cmd_parts[1]]
                        bash.check_output(node.generate_tx())
                    else:
                        raise Exception('Unknown cmd={} in {}-file'.format(cmd_parts[0], config.tick_csv))

                next_tick = start_time + (i + 1) * self.tick_duration
                current_time = time.time()
                if current_time < next_tick:
                    difference = next_tick - current_time
                    logging.info('Sleep {} seconds for next tick.'.format(difference))
                    utils.sleep(difference)
                else:
                    raise Exception('Current_time={} is higher then next_tick={}.'
                                    ' Consider to lower the tick_interval={}.'
                                    .format(current_time, next_tick, self.tick_duration))

            # only use regular nodes since selfish nodes can trail back
            array = False
            while utils.check_equal(array) is False:
                logging.debug('Waiting for blocks to spread...')
                utils.sleep(0.2)
                array = [int(bash.check_output(node.get_block_count())) for node in self.nodes.values()]

            bash.check_output(dockercmd.fix_data_dirs_permissions())

            self.stats.save_consensus_chain()
            self.stats.update_blocks_csv()
            self.stats.save_chains()
            self.stats.node_stats()
            self.stats.aggregate_logs()

            [bash.check_output(node.grep_log_for_errors()) for node in self.all_nodes.values()]
        finally:
            # remove proxies first. if not proxies could be already stopped when trying to remove
            [bash.call_silent(node.rm()) for node in self.selfish_node_proxies.values()]
            [bash.call_silent(node.rm()) for node in self.all_bitcoin_nodes.values()]
            utils.sleep(3 + len(self.all_nodes) * 0.2)

            bash.call_silent(dockercmd.rm_network())

    def generate_block_and_save_creator(self, node, amount):
        blocks_string = bash.check_output(bitcoincmd.generate_block(node, amount))
        blocks = json.loads(blocks_string)
        with open(config.blocks_csv, 'a') as file:
            for block in blocks:
                file.write('{};{}\n'.format(node, block))
        self.all_bitcoin_nodes[node].mined_blocks += 1
