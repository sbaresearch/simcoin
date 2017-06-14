import random
import dockercmd
import bitcoindcmd
import proxycmd
import ipaddress
from scheduler import Scheduler
import config


class Plan:
    def __init__(self, args):
        self.args = args

        ip_addresses = ipaddress.ip_network(config.ip_range).hosts()
        next(ip_addresses)  # skipping first ip address (docker fails with error "is in use")

        self.nodes = {config.node_prefix + str(i):
                      NormalNode(config.node_prefix + str(i), next(ip_addresses), args.latency) for i in range(args.nodes)}

        self.selfish_node_private_nodes = {}
        self.selfish_node_proxies = {}
        for i in range(args.selfish_nodes):
            ip_private_node = next(ip_addresses)
            ip_proxy = next(ip_addresses)
            self.selfish_node_private_nodes[config.selfish_node_prefix + str(i)] = \
                SelfishPrivateNode(config.node_prefix + str(i), ip_private_node)

            self.selfish_node_proxies[config.selfish_node_prefix + str(i) + config.selfish_node_proxy_postfix] = \
                ProxyNode(config.selfish_node_prefix + str(i) + config.selfish_node_proxy_postfix,
                          ip_proxy, ip_private_node, args.latency)

        self.all_bitcoind_nodes = dict(self.nodes, **self.selfish_node_private_nodes)
        self.all_public_nodes = dict(self.nodes, **self.selfish_node_proxies)
        self.all_nodes = dict(self.nodes, **self.selfish_node_private_nodes, **self.selfish_node_proxies)

        self.one_normal_node = next(iter(self.nodes.values()))

    def create(self):
        args = self.args
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

            plan.extend([node.run() for node in self.selfish_node_private_nodes.values()])
            plan.extend([node.wait_for_highest_tip_of_node(self.one_normal_node) for node in self.selfish_node_private_nodes.values()])

            plan.extend([node.run() for node in self.selfish_node_proxies.values()])
            plan.extend([node.wait_for_highest_tip_of_node(self.one_normal_node) for node in self.selfish_node_proxies.values()])

            scheduler = Scheduler(0)
            scheduler.add_blocks(args.blocks, args.block_interval,
                                 [bitcoindcmd.generate_block(self.random_node()) for _ in range(1000)])
            scheduler.add_tx(args.blocks * args.block_interval, [self.random_tx_command() for _ in range(10)])
            plan.extend(scheduler.bash_commands())
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

    def random_node(self):
        return random.choice(list(self.all_bitcoind_nodes.values()))

    def warmup_block_generation(self):
        cmds = ['echo Begin of warmup']
        iter_nodes = iter(self.all_bitcoind_nodes.values())
        prev_node = next(iter_nodes)
        for node in iter_nodes:
            cmds.append(bitcoindcmd.generate_block(prev_node))
            cmds.append(node.wait_for_highest_tip_of_node(prev_node))
            prev_node = node

        cmds.append(bitcoindcmd.generate_block(prev_node, config.blocks_to_make_coinbase_spendable + 1))
        cmds.extend([node.wait_for_highest_tip_of_node(prev_node) for node in self.all_bitcoind_nodes.values()])

        cmds.append('echo End of warmup')
        return cmds

    def wait_for_all_blocks_to_spread(self):

        # only use regular nodes since selfish nodes can trail back
        block_counts = ['$(' + bitcoindcmd.get_block_count(node) + ')' for node in self.nodes.values()]
        return ('while : ; do block_counts=(' + ' '.join(block_counts) + '); '
                'prev=${block_counts[0]}; wait=false; echo Current block_counts=${block_counts[@]}; '
                'for i in "${block_counts[@]}"; do if [ $prev != $i ]; then wait=true; fi; done; '
                'if [ $wait == false ]; then break; fi; '
                'echo Waiting for blocks to spread...; sleep 0.2; done')

    def random_tx_command(self):
        node = self.random_node()
        create_address_cmd = 'fresh_address=$(' + bitcoindcmd.get_new_address(node) + ')'
        create_tx_cmd = bitcoindcmd.send_to_address(node, '$fresh_address', 0.1)
        return '; '.join([create_address_cmd, create_tx_cmd])

    def save_consensus_chain(self):
        # idea iterate over chain and check if at some height all hashes are the same.
        mock_node = Node('$node', None, None)

        file = config.root_dir + '/consensus_chain.csv'
        csv_header_cmd = r'echo "height;block_hash" | tee -a ' + file
        iter_cmd = ('for height in `seq ' + str(self.first_block_height()) +
                    ' $(' + bitcoindcmd.get_block_count(self.one_normal_node) + ')`; do'
                    ' hash=$(' + bitcoindcmd.get_block_hash(self.one_normal_node, '$height') + ');'
                    ' all_same=true; for node in "${nodes[@]}"; do' +
                    ' if [[ $hash != $(' + bitcoindcmd.get_block_hash(mock_node, '$height') + ')'
                    ' ]]; then all_same=false; fi; done;'
                    ' if [ "$all_same" = true ]; then echo "$height;$hash" '
                    '| tee -a ' + file + '; fi; done')

        return '; '.join([csv_header_cmd, self.bitcoind_nodes_array(), iter_cmd])

    def save_chains(self):
        mock_node = Node('$node', None, None)

        file = config.root_dir + '/chains.csv'
        csv_header_cmd = r'echo "node;block_hashes" | tee -a ' + file
        iter_cmd = ('for node in ${nodes[@]}; do'
                    ' line=$node; for height in `seq ' + str(self.first_block_height()) +
                    ' $(' + bitcoindcmd.get_block_count(mock_node) + ')`; do'
                    ' line="$line;$(' + bitcoindcmd.get_block_hash(mock_node, '$height') + ')";'
                    ' done; echo $line | tee -a ' + file + '; done')

        return '; '.join([csv_header_cmd, self.bitcoind_nodes_array(), iter_cmd])

    def bitcoind_nodes_array(self):
        return 'nodes=(' + ' '.join(node.name for node in self.all_bitcoind_nodes.values()) + ')'

    def first_block_height(self):
        return len(self.all_bitcoind_nodes) + 100 + 1


class Node:
    def __init__(self, name, ip, latency):
        self.name = name
        self.ip = ip
        self.latency = latency

    def rm(self):
        return dockercmd.rm_container(self.name)


class NormalNode(Node):
    def __init__(self, name, ip, latency):
        super().__init__(name, ip, latency)
        self.name = name
        self.ip = ip
        self.latency = latency

    def run(self):
        return dockercmd.run_node(self, bitcoindcmd.start_user(), self.latency)

    def delete_peers_file(self):
        return bitcoindcmd.rm_peers(self)

    def wait_for_highest_tip_of_node(self, node):
        node_tip = bitcoindcmd.get_best_block_hash(node)
        highest_tip = bitcoindcmd.get_best_block_hash(self)
        return 'while [[ $(' + highest_tip + ') != $(' + node_tip + ') ]]; ' \
               'do echo Waiting for blocks to spread...; sleep 0.2; done'

    def connect(self, nodes):
        return bitcoindcmd.connect(self, nodes)


class SelfishPrivateNode(NormalNode):
    def __init__(self, name, ip):
        super().__init__(name, ip, 0)


class ProxyNode(Node):
    def __init__(self, name, ip, private_ip, latency):
        super().__init__(name, ip, latency)
        self.private_ip = private_ip

    def run(self, ):
        mock_node = Node('node-0', None, None)
        current_best_block_hash_cmd = 'start_hash=$(' + bitcoindcmd.get_best_block_hash(mock_node) + ')'
        run_cmd = dockercmd.run_selfish_proxy(self, proxycmd.run_proxy(self, '$start_hash'), self.latency)
        return '; '.join([current_best_block_hash_cmd, run_cmd])

    def wait_for_highest_tip_of_node(self, node):
        current_best_block_hash_cmd = 'current_best=$(' + bitcoindcmd.get_best_block_hash(node) + ')'
        wait_for_selfish_node_cmd = 'while [[ $current_best != $(' + proxycmd.get_best_public_block_hash(self) + \
                                    ') ]]; do echo Waiting for blocks to spread...; sleep 0.2; done'
        return '; '.join(['sleep 2', current_best_block_hash_cmd, wait_for_selfish_node_cmd])
