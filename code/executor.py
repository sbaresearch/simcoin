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


class Executor:
    def __init__(self, args, nodes, selfish_nodes):
        self.count = 0
        if args.dry_run:
            self.execution_function = execute_dry_run
        else:
            self.execution_function = execute_print

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
            self.exec('rm -rf ' + config.root_dir + '*')

            self.exec(dockercmd.create_network(config.ip_range))
            self.exec('sleep 1')

            [self.exec(node.run()) for node in self.all_bitcoind_nodes.values()]
            for index, node in enumerate(self.all_bitcoind_nodes.values()):
                [self.exec(cmd) for cmd
                 in node.connect([str(node.ip) for node in list(self.all_bitcoind_nodes.values())[index+1:index+5]])]

            self.exec('sleep 5')  # wait before generating otherwise "Error -28" (still warming up)
            self.warmup_block_generation()

            [self.exec('; '.join([node.delete_peers_file(), node.rm()])) for node in self.all_bitcoind_nodes.values()]

            [self.exec(node.run()) for node in self.all_bitcoind_nodes.values()]
            [self.exec(node.wait_until_height_reached(config.warmup_blocks + len(self.all_bitcoind_nodes)))
             for node in self.all_bitcoind_nodes.values()]

            [self.exec(node.run()) for node in self.selfish_node_proxies.values()]
            [self.exec(node.wait_for_highest_tip_of_node(self.one_normal_node))
             for node in self.selfish_node_proxies.values()]

            for node in self.nodes.values():
                [self.exec(cmd) for cmd in node.connect(node.outgoing_ips)]

            reader = csv.reader(open(config.tick_csv, "r"), delimiter=";")
            for i, line in enumerate(reader):
                for cmd in line:
                    cmd_parts = cmd.split(' ')
                    if cmd_parts[0] == 'block':
                        self.exec(bitcoindcmd.generate_block(cmd_parts[1], 1))
                    elif cmd_parts[0] == 'tx':
                        node = self.all_bitcoind_nodes[cmd_parts[1]]
                        self.exec(node.generate_tx())
                    else:
                        raise Exception("Unknown cmd={} in {}-file".format(cmd_parts[0], config.tick_csv))

            self.exec(self.wait_for_all_blocks_to_spread())

            self.exec(dockercmd.fix_data_dirs_permissions())

            self.exec(self.save_consensus_chain())
            self.exec(self.save_chains())

            # [self.exec(bitcoindcmd.get_chain_tips(node)) for node in self.all_bitcoind_nodes]
            # [for self.exec(cmd) for cmd in logs.aggregate_logs(self.nodes))]

        finally:
            [self.exec(node.rm()) for node in self.all_nodes.values()]
            self.exec('sleep 5')
            self.exec(dockercmd.rm_network())

    def warmup_block_generation(self):
        self.exec('echo Begin of warmup')

        for index, node in enumerate(self.all_bitcoind_nodes.values()):
            self.exec(node.wait_until_height_reached(index))
            self.exec(node.generate_block())

        node = self.all_bitcoind_nodes[config.reference_node]
        self.exec(node.wait_until_height_reached(len(self.all_bitcoind_nodes)))
        self.exec(node.generate_block(config.warmup_blocks))
        [self.exec(node.wait_until_height_reached(config.warmup_blocks + len(self.all_bitcoind_nodes)))
         for node in self.all_bitcoind_nodes.values()]

        self.exec('echo End of warmup')

    def wait_for_all_blocks_to_spread(self):

        # only use regular nodes since selfish nodes can trail back
        block_counts = ['$(' + bitcoindcmd.get_block_count(node.name) + ')' for node in self.nodes.values()]
        return ('while : ; do block_counts=(' + ' '.join(block_counts) + '); '
                'prev=${block_counts[0]}; wait=false; echo Current block_counts=${block_counts[@]}; '
                'for i in "${block_counts[@]}"; do if [ $prev != $i ]; then wait=true; fi; done; '
                'if [ $wait == false ]; then break; fi; '
                'echo Waiting for blocks to spread...; sleep 0.2; done')

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

    def bitcoind_nodes_array(self):
        return 'nodes=(' + ' '.join(node.name for node in self.all_bitcoind_nodes.values()) + ')'

    def first_block_height(self):
        return len(self.all_bitcoind_nodes) + 100 + 1

    def exec(self, cmd):
        self.count += 1
        self.execution_function(cmd, self.count)


def execute_dry_run(cmd, count):
    print('{}: {}'.format(count, cmd))
    return 'ret-{}'.format(count)


def execute_print(cmd, count):
    output = execute(cmd, count).decode("utf-8")
    print(output, end='')


def execute(cmd, count):
    print('{}: {}'.format(count, cmd))
    return subprocess.check_output(cmd, shell=True, executable='/bin/bash')
