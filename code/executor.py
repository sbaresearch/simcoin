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


class Executor:
    def __init__(self, args, nodes, selfish_nodes):
        self.count = 0

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
            self.exec_print('rm -rf ' + config.root_dir + '*')

            self.exec_print(dockercmd.create_network(config.ip_range))
            self.exec_print('sleep 1')

            [self.exec_print(node.run()) for node in self.all_bitcoind_nodes.values()]
            self.exec_print('sleep 5')
            for i, node in enumerate(self.all_bitcoind_nodes.values()):
                [self.exec_print(cmd) for cmd
                 in node.connect([str(node.ip) for node in list(self.all_bitcoind_nodes.values())[i+1:i+5]])]

            self.exec_print('sleep 5')  # wait before generating otherwise "Error -28" (still warming up)
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

            self.exec_print('sleep 5')

            reader = csv.reader(open(config.tick_csv, "r"), delimiter=";")
            for i, line in enumerate(reader):
                for cmd in line:
                    cmd_parts = cmd.split(' ')
                    if cmd_parts[0] == 'block':
                        self.exec_print(bitcoindcmd.generate_block(cmd_parts[1], 1))
                    elif cmd_parts[0] == 'tx':
                        node = self.all_bitcoind_nodes[cmd_parts[1]]
                        self.exec_print(node.generate_tx())
                    else:
                        raise Exception("Unknown cmd={} in {}-file".format(cmd_parts[0], config.tick_csv))

            # only use regular nodes since selfish nodes can trail back
            array = [int(self.exec(node.get_block_count())) for node in self.nodes.values()]
            logging.info(array)
            while check_equal(array) is False:
                logging.debug('Waiting for blocks to spread...')
                time.sleep(0.2)

            self.exec_print(dockercmd.fix_data_dirs_permissions())

            self.exec_print(self.save_consensus_chain())
            self.exec_print(self.save_chains())

            self.consolidate_logs()
        finally:
            # remove proxies first. if not proxies could be already stopped when trying to remove
            [self.call(node.rm()) for node in self.selfish_node_proxies.values()]
            [self.call(node.rm()) for node in self.all_bitcoind_nodes.values()]
            self.call('sleep 5')
            self.call(dockercmd.rm_network())

    def warmup_block_generation(self):
        self.exec_print('echo Begin of warmup')

        for i, node in enumerate(self.all_bitcoind_nodes.values()):
            self.wait_until_height_reached(node, i)
            self.exec_print(node.generate_block())

        node = self.all_bitcoind_nodes[config.reference_node]
        self.wait_until_height_reached(node, len(self.all_bitcoind_nodes))
        self.exec_print(node.generate_block(config.warmup_blocks))
        [self.wait_until_height_reached(node, config.warmup_blocks + len(self.all_bitcoind_nodes))
         for node in self.all_bitcoind_nodes.values()]

        self.exec_print('echo End of warmup')

    def wait_until_height_reached(self, node, height):
        while int(self.exec(node.get_block_count())) < height:
            logging.debug('Waiting until height={} is reached...'.format(str(height)))
            time.sleep(0.2)

    def save_consensus_chain(self):
        # idea iterate over chain and check if at some height all hashes are the same.

        file = config.root_dir + '/consensus_chain.csv'
        csv_header_cmd = r'echo "height;block_hash" | tee -a ' + file
        iter_cmd = ('for height in `seq ' + str(self.first_block_height()) +
                    ' $(' + bitcoindcmd.get_block_count(config.reference_node) + ')`; do'
                    ' hash=$(' + bitcoindcmd.get_block_hash(config.reference_node, '$height') + ');'
                    ' all_same=true; for node in "${nodes[@]}"; do' +
                    ' if [[ $hash != $(' + bitcoindcmd.get_block_hash('$node', '$height') + ')'
                    ' ]]; then all_same=false; fi; done;'
                    ' if [ "$all_same" = true ]; then echo "$height;$hash" '
                    '| tee -a ' + file + '; fi; done')

        return '; '.join([csv_header_cmd, self.bitcoind_nodes_array(), iter_cmd])

    def save_chains(self):
        file = config.root_dir + '/chains.csv'
        csv_header_cmd = r'echo "node;block_hashes" | tee -a ' + file
        iter_cmd = ('for node in ${nodes[@]}; do'
                    ' line=$node; for height in `seq ' + str(self.first_block_height()) +
                    ' $(' + bitcoindcmd.get_block_count('$node') + ')`; do'
                    ' line="$line;$(' + bitcoindcmd.get_block_hash(config.reference_node, '$height') + ')";'
                    ' done; echo $line | tee -a ' + file + '; done')

        return '; '.join([csv_header_cmd, self.bitcoind_nodes_array(), iter_cmd])

    def consolidate_logs(self):
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
                                            , r'\1 {}-{}'.format(node.name, i)
                                            , line)
                        prev_match = match.group(0)
                    else:
                        content[i] = '{} {}-{} {}'.format(prev_match, node.name, i, line)

                with open(config.consolidated_log, mode='a') as file:
                    file.writelines(content)
            self.exec_print('sort {} -o {}'.format(config.consolidated_log, config.consolidated_log))
        finally:
            self.call('rm {}'.format(config.tmp_log))

    def bitcoind_nodes_array(self):
        return 'nodes=(' + ' '.join(node.name for node in self.all_bitcoind_nodes.values()) + ')'

    def first_block_height(self):
        return len(self.all_bitcoind_nodes) + 100 + 1

    def exec(self, cmd):
        self.log_cmd(cmd)
        return subprocess.check_output(cmd, shell=True, executable='/bin/bash')

    def call(self, cmd):
        self.log_cmd(cmd)
        return subprocess.call(cmd, shell=True, executable='/bin/bash')

    def log_cmd(self, cmd):
        self.count += 1
        logging.info('{}: {}'.format(self.count, cmd))

    def exec_print(self, cmd):
        output = self.exec(cmd).decode("utf-8")
        [logging.info(output.strip()) for output in output.splitlines()]


def check_equal(lst):
    return not lst or lst.count(lst[0]) == len(lst)

