import dockercmd
import bitcoindcmd
import ipaddress
import config
import pandas
import csv
from node import PublicBitcoindNode
from node import SelfishPrivateNode
from node import ProxyNode
import subprocess
import logging
import time
import re
import os
import json


class Executor:
    def __init__(self, args, nodes, selfish_nodes):
        self.count = 0
        self.tick_duration = args.tick_duration

        ip_addresses = ipaddress.ip_network(config.ip_range).hosts()
        next(ip_addresses)  # skipping first ip address (docker fails with error "is in use")

        self.nodes = {config.node_name.format(str(i)):
                      PublicBitcoindNode(config.node_name.format(str(i)), next(ip_addresses))
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

        self.all_bitcoind_nodes = dict(self.nodes, **self.selfish_node_private_nodes)
        self.all_public_nodes = dict(self.nodes, **self.selfish_node_proxies)
        self.all_nodes = dict(self.nodes, **self.selfish_node_private_nodes, **self.selfish_node_proxies)

        self.one_normal_node = next(iter(self.nodes.values()))

        network_config = pandas.read_csv(open(config.network_config), skiprows=2, delimiter=';', index_col=0)
        connections = {}
        for node_row, row in network_config.iterrows():
            if node_row.startswith(config.selfish_node_prefix):
                node_row += config.selfish_node_proxy_postfix
            connections[node_row] = []
            for node_column, latency in row.iteritems():
                # exact latency is so far omitted
                if node_column.startswith(config.selfish_node_prefix):
                    node_column += config.selfish_node_proxy_postfix
                if latency >= 0:
                    connections[node_row].append(node_column)

        for node in self.all_public_nodes.values():
            node.outgoing_ips = [str(self.all_public_nodes[connection].ip) for connection in connections[node.name]]

    def execute(self):
        try:
            self.remove_old_containers_if_exists()
            self.recreate_network()
            create_simulation_dir()
            sleep(4)

            [self.exec_print(node.run()) for node in self.all_bitcoind_nodes.values()]
            sleep(4 + len(self.all_bitcoind_nodes) * 0.2)

            for i, node in enumerate(self.all_bitcoind_nodes.values()):
                [self.exec_print(cmd) for cmd
                 in node.connect([str(node.ip) for node in list(self.all_bitcoind_nodes.values())[i+1:i+5]])]
            sleep(4 + len(self.all_bitcoind_nodes) * 0.2)

            self.warmup_block_generation()

            [self.exec_print('; '.join([node.delete_peers_file(), node.rm()])) for node in self.all_bitcoind_nodes.values()]

            [self.exec_print(node.run()) for node in self.all_bitcoind_nodes.values()]
            [self.wait_until_height_reached(node, config.warmup_blocks + len(self.all_bitcoind_nodes))
             for node in self.all_bitcoind_nodes.values()]

            [self.exec_print(node.run()) for node in self.selfish_node_proxies.values()]
            [self.exec_print(node.wait_for_highest_tip_of_node(self.one_normal_node))
             for node in self.selfish_node_proxies.values()]

            for node in self.nodes.values():
                [self.exec_print(cmd) for cmd in node.connect(node.outgoing_ips)]
            sleep(4 + len(self.all_nodes) * 0.2)

            if self.latency > 0:
                [self.exec_print(node.add_latency(self.latency)) for node in self.all_public_nodes.values()]

            reader = csv.reader(open(config.tick_csv, "r"), delimiter=";")
            start_time = time.time()
            for i, line in enumerate(reader):
                for cmd in line:
                    cmd_parts = cmd.split(' ')
                    if cmd_parts[0] == 'block':
                        self.generate_block_and_save_creator(cmd_parts[1], 1)
                    elif cmd_parts[0] == 'tx':
                        node = self.all_bitcoind_nodes[cmd_parts[1]]
                        self.exec_print(node.generate_tx())
                    else:
                        raise Exception('Unknown cmd={} in {}-file'.format(cmd_parts[0], config.tick_csv))

                next_tick = start_time + (i + 1) * self.tick_duration
                current_time = time.time()
                if current_time < next_tick:
                    difference = next_tick - current_time
                    logging.info('Sleep {} seconds for next tick.'.format(difference))
                    sleep(difference)
                else:
                    raise Exception('Current_time={} is higher then next_tick={}.'
                                    ' Consider to lower the tick_interval={}.'
                                    .format(current_time, next_tick, self.tick_duration))

            # only use regular nodes since selfish nodes can trail back
            array = False
            while check_equal(array) is False:
                logging.debug('Waiting for blocks to spread...')
                sleep(0.2)
                array = [int(check_output(node.get_block_count())) for node in self.nodes.values()]

            self.exec_print(dockercmd.fix_data_dirs_permissions())

            self.save_consensus_chain()
            self.save_chains()

            self.aggregate_logs()
            [self.exec_print(node.grep_log_for_errors()) for node in self.all_nodes.values()]
        finally:
            # remove proxies first. if not proxies could be already stopped when trying to remove
            [call(node.rm()) for node in self.selfish_node_proxies.values()]
            [call(node.rm()) for node in self.all_bitcoind_nodes.values()]
            sleep(3 + len(self.all_nodes) * 0.2)

            call(dockercmd.rm_network())

    def warmup_block_generation(self):
        logging.info('Begin warmup')

        for i, node in enumerate(self.all_bitcoind_nodes.values()):
            self.wait_until_height_reached(node, i)
            self.exec_print(node.generate_block())

        node = self.all_bitcoind_nodes[config.reference_node]
        self.wait_until_height_reached(node, len(self.all_bitcoind_nodes))
        self.exec_print(node.generate_block(config.warmup_blocks))
        [self.wait_until_height_reached(node, config.warmup_blocks + len(self.all_bitcoind_nodes))
         for node in self.all_bitcoind_nodes.values()]

        logging.info('End of warmup')

    def wait_until_height_reached(self, node, height):
        while int(check_output(node.get_block_count())) < height:
            logging.debug('Waiting until height={} is reached...'.format(str(height)))
            sleep(0.2)

    def save_consensus_chain(self):
        with open(config.consensus_chain_csv, 'w') as file:
            file.write("height;block_hash\n")
            height = self.first_block_height()
            while True:
                blocks = []
                for node in self.all_bitcoind_nodes.values():
                    try:
                        blocks.append(check_output(node.get_block_hash(height)))
                    except subprocess.CalledProcessError:
                        break
                if len(blocks) > 0 and check_equal(blocks):
                    file.write('{}; {}\n'.format(height, blocks[0]))
                    height += 1
                else:
                    break

    def save_chains(self):
        with open(config.chains_csv, 'w') as file:
            file.write("node;block_hashes\n")
            start = self.first_block_height()
            for node in self.all_bitcoind_nodes.values():
                height = int(check_output(node.get_block_count()))
                hashes = []
                while start <= height:
                    hashes.append(str(check_output(node.get_block_hash(height))))
                    height -= 1
                file.write('{}; {}\n'.format(node.name, '; '.join(hashes)))

    def aggregate_logs(self):
        try:
            for node in self.all_nodes.values():
                self.exec_print('{} > {}'.format(node.cat_log(), config.tmp_log))

                with open(config.tmp_log) as file:
                    content = file.readlines()

                prev_match = ''
                for i, line in enumerate(content):
                    match = re.match(config.log_timestamp_regex, line)
                    if match:
                        content[i] = re.sub(config.log_timestamp_regex
                                            , r'\1 {}'.format(node.name)
                                            , line)
                        prev_match = match.group(0)
                    else:
                        content[i] = '{} {} {}'.format(prev_match, node.name, line)

                with open(config.aggregated_log, mode='a') as file:
                    file.writelines(content)

            self.exec_print('cat {} >> {}'.format(config.log_file, config.aggregated_log))
            self.exec_print('sort {} -o {}'.format(config.aggregated_log, config.aggregated_log))
        finally:
            call('rm {}'.format(config.tmp_log))

    def remove_old_containers_if_exists(self):
        containers = check_output(dockercmd.ps_containers())
        if len(containers) > 0:
            call(dockercmd.remove_all_containers())

    def recreate_network(self):
        exit_code = call(dockercmd.inspect_network(), True)
        if exit_code == 0:
            check_output(dockercmd.rm_network())
        call(dockercmd.create_network(config.ip_range))

    def first_block_height(self):
        return len(self.all_bitcoind_nodes) + config.warmup_blocks + 1

    def exec_print(self, cmd):
        output = check_output(cmd)
        [logging.info(output.strip()) for output in output.splitlines()]

    def generate_block_and_save_creator(self, node, amount):
        blocks_string = check_output(bitcoindcmd.generate_block(node, amount))
        blocks = json.loads(blocks_string)
        with open(config.blocks_csv, 'a') as file:
            for block in blocks:
                file.write('{}; {}\n'.format(node, block))


def check_output(cmd):
    logging.info(cmd)
    with open(os.devnull, 'w') as devnull:
        return_value = subprocess.check_output(cmd, shell=True, executable='/bin/bash', stderr=devnull)
    return return_value.decode('utf-8').rstrip()


def call(cmd, suppress_output=False):
    logging.info(cmd)
    if suppress_output:
        with open(os.devnull, 'w') as devnull:
            return subprocess.call(cmd, shell=True, executable='/bin/bash', stderr=devnull, stdout=devnull)
    else:
        return subprocess.call(cmd, shell=True, executable='/bin/bash')


def sleep(seconds):
    logging.debug("Sleep for {} seconds".format(seconds))
    time.sleep(seconds)


def check_equal(lst):
    return not lst or lst.count(lst[0]) == len(lst)


def create_simulation_dir():
    if not os.path.exists(config.out_dir):
        os.makedirs(config.out_dir)
    if not os.path.exists(config.sim_dir):
        os.makedirs(config.sim_dir)

