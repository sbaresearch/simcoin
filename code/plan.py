import dockercmd
import bitcoindcmd
import ipaddress
import config
import pandas
import csv
from node import PublicBitcoindNode
from node import SelfishPrivateNode
from node import ProxyNode


class Plan:
    def __init__(self, args, nodes, selfish_nodes):
        ip_addresses = ipaddress.ip_network(config.ip_range).hosts()
        next(ip_addresses)  # skipping first ip address (docker fails with error "is in use")

        self.nodes = {config.node_name.format(str(i)):
                      PublicBitcoindNode(config.node_name.format(str(i)), next(ip_addresses),
                                         args.latency)
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
                          ip_proxy, ip_private_node, args.latency, args.selfish_nodes_args)

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

    def create(self):
        plan = []

        try:
            plan.append("rm -rf " + config.root_dir + '/*')

            plan.append(dockercmd.create_network(config.ip_range))
            plan.append('sleep 1')

            plan.extend([node.run() for node in self.all_bitcoind_nodes.values()])
            for index, node in enumerate(self.all_bitcoind_nodes.values()):
                plan.extend(node.connect(list(self.all_bitcoind_nodes.values())[index:index+5]))

            plan.append('sleep 2')  # wait before generating otherwise "Error -28" (still warming up)
            plan.extend(self.warmup_block_generation())

            plan.extend(['; '.join([node.delete_peers_file(), node.rm()]) for node in self.all_bitcoind_nodes.values()])

            plan.extend([node.run() for node in self.all_bitcoind_nodes.values()])
            plan.extend([node.wait_until_height_reached(config.warmup_blocks + len(self.all_bitcoind_nodes))
                         for node in self.all_bitcoind_nodes.values()])

            plan.extend([node.run() for node in self.selfish_node_proxies.values()])
            plan.extend([node.wait_for_highest_tip_of_node(self.one_normal_node) for node in self.selfish_node_proxies.values()])

            reader = csv.reader(open(config.tick_csv, "r"), delimiter=";")
            for i, line in enumerate(reader):
                for cmd in line:
                    cmd_parts = cmd.split(' ')
                    if cmd_parts[0] == 'block':
                        plan.append(bitcoindcmd.generate_block(cmd_parts[1], 1))
                    elif cmd_parts[0] == 'tx':
                        node = self.all_bitcoind_nodes[cmd_parts[1]]
                        plan.append(node.generate_tx())
                    else:
                        raise Exception("Unknown cmd={} in {}-file".format(cmd_parts[0], config.tick_csv))

            plan.append(self.wait_for_all_blocks_to_spread())

            plan.append(dockercmd.fix_data_dirs_permissions())

            plan.append(self.save_consensus_chain())
            plan.append(self.save_chains())

            # plan.extend([bitcoindcmd.get_chain_tips(node) for node in self.all_bitcoind_nodes])
            # plan.extend(logs.aggregate_logs(self.nodes))

        finally:
            plan.extend([node.rm() for node in self.all_nodes.values()])
            plan.append('sleep 5')
            plan.append(dockercmd.rm_network())

        return plan

    def warmup_block_generation(self):
        cmds = ['echo Begin of warmup']
        iter_nodes = iter(self.all_bitcoind_nodes.values())
        prev_node = next(iter_nodes)
        for node in iter_nodes:
            cmds.append(bitcoindcmd.generate_block(prev_node.name))
            cmds.append(node.wait_for_highest_tip_of_node(prev_node))
            prev_node = node

        cmds.append(bitcoindcmd.generate_block(prev_node.name, config.warmup_blocks + 1))
        cmds.extend([node.wait_for_highest_tip_of_node(prev_node) for node in self.all_bitcoind_nodes.values()])

        cmds.append('echo End of warmup')
        return cmds

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
