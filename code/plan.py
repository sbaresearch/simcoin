#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import dockercmd
import bitcoindcmd
import proxycmd
import ipaddress
from scheduler import Scheduler

# IP range from RFC6890 - IP range for future use
# it does not conflict with https://github.com/bitcoin/bitcoin/blob/master/src/netbase.h
ip_range = "240.0.0.0/4"
ip_bootstrap = "240.0.0.2"

root_dir = '$PWD/../data'
log_file = '$PWD/../data/log'

node_image = 'btn/base:v3'
selfish_node_image = 'proxy'
node_prefix = 'node-'
selfish_node_prefix = 'selfish-node-'
selfish_node_proxy_postfix = '-proxy'
bootstrap_node_name = 'bootstrap'


def host_dir(node):
    return root_dir + '/' + node.name


class Plan:
    def __init__(self, config):
        ip_addresses = ipaddress.ip_network(ip_range).hosts()
        next(ip_addresses)  # skipping first ip address (docker fails with error "is in use")
        next(ip_addresses)  # omit first ip address used by bootstrap node

        self.config = config
        self.nodes = [Node(node_prefix + str(i), next(ip_addresses)) for i in range(config.nodes)]
        self.selfish_nodes = [SelfishNode(selfish_node_prefix + str(i), next(ip_addresses), next(ip_addresses),
                                          config.selfish_nodes_args) for i in range(config.selfish_nodes)]

        self.selfish_node_private_nodes = [node.private_node for node in self.selfish_nodes]
        self.selfish_node_proxies = [node.proxy for node in self.selfish_nodes]
        self.all_bitcoind_nodes = self.nodes + self.selfish_node_private_nodes
        self.all_public_nodes = self.nodes + self.selfish_node_proxies
        self.all_nodes = self.nodes + self.selfish_node_private_nodes + self.selfish_node_proxies

        self.bootstrap_node = Node(bootstrap_node_name, ip_bootstrap)

    def create(self):
        config = self.config
        plan = []

        if len(self.selfish_nodes) > 0:
            self.set_public_ips()

        try:
            plan.append("rm -rf " + root_dir + '/*')

            plan.append(dockercmd.create_network(ip_range))
            plan.append('sleep 1')

            plan.append(dockercmd.run_bootstrap_node(self.bootstrap_node, bitcoindcmd.start_user(), config.latency))
            plan.extend([dockercmd.run_node(node, bitcoindcmd.start_user(), config.latency) for node in self.nodes])
            plan.extend([dockercmd.run_node(node, bitcoindcmd.start_user(), config.latency)
                         for node in self.selfish_node_private_nodes])

            plan.append('sleep 2')  # wait before generating otherwise "Error -28" (still warming up)
            plan.extend(self.warmup_block_generation())

            plan.extend([bitcoindcmd.rm_peers(node) for node in self.selfish_node_private_nodes])
            plan.extend([node.rm() for node in self.selfish_node_private_nodes])

            plan.extend([dockercmd.run_selfish_private_node(node.private_node, bitcoindcmd.start_selfish_mining())
                         for node in self.selfish_nodes])
            plan.extend(self.wait_until_nodes_have_same_tip(self.nodes[0], self.selfish_node_private_nodes))

            plan.extend([self.run_selfish_node_proxy(node, config.latency) for node in self.selfish_nodes])
            plan.extend([self.wait_until_selfish_node_proxy_caught_up(node) for node in self.selfish_nodes])

            scheduler = Scheduler(0)
            scheduler.add_blocks(config.blocks, config.block_interval,
                                 [bitcoindcmd.generate_block(self.random_node()) for _ in range(1000)])
            scheduler.add_tx(config.blocks * config.block_interval, [self.random_tx_command() for _ in range(10)])
            plan.extend(scheduler.bash_commands())
            plan.append(self.wait_for_all_blocks_to_spread())

            plan.append(dockercmd.fix_data_dirs_permissions())

            plan.append(self.save_consensus_chain())

            # plan.extend([bitcoindcmd.get_chain_tips(node) for node in self.all_bitcoind_nodes])
            # plan.extend(logs.aggregate_logs(self.nodes))

        finally:
            plan.extend([node.rm() for node in self.all_nodes])
            plan.append(self.bootstrap_node.rm())
            plan.append('sleep 5')
            plan.append(dockercmd.rm_network())

        return plan

    def random_node(self):
        return random.choice(self.all_bitcoind_nodes)

    def warmup_block_generation(self):
        cmds = ['echo Begin of warmup']
        iter_nodes = iter(self.all_bitcoind_nodes)
        prev_node = next(iter_nodes)
        for node in iter_nodes:
            cmds.append(bitcoindcmd.generate_block(prev_node))
            cmds.extend(self.wait_until_nodes_have_same_tip(prev_node, [node]))
            prev_node = node

        cmds.append(bitcoindcmd.generate_block(prev_node, 101))
        cmds.extend(self.wait_until_nodes_have_same_tip(prev_node, self.all_bitcoind_nodes))

        cmds.append('echo End of warmup')
        return cmds

    def wait_until_nodes_have_same_tip(self, leading_node, nodes):
        cmds = []
        highest_tip = bitcoindcmd.get_best_block_hash(leading_node)
        for node in nodes:
            node_tip = bitcoindcmd.get_best_block_hash(node)
            cmds.append('while [[ $(' + highest_tip + ') != $(' + node_tip + ') ]]; ' +
                        'do echo Waiting for blocks to spread...; sleep 0.2; done')
        return cmds

    def wait_until_selfish_node_proxy_caught_up(self, node):
        current_best_block_hash_cmd = 'current_best=$(' + bitcoindcmd.get_best_block_hash(self.nodes[0]) + ')'
        wait_for_selfish_node_cmd = 'while [[ $current_best != $(' + proxycmd.get_best_public_block_hash(node.proxy) + \
                                    ') ]]; do echo Waiting for blocks to spread...; sleep 0.2; done'
        return '; '.join(['sleep 2', current_best_block_hash_cmd, wait_for_selfish_node_cmd])

    def wait_for_all_blocks_to_spread(self):

        # only use regular nodes since selfish nodes can trail back
        block_counts = ['$(' + bitcoindcmd.get_block_count(node) + ')' for node in self.nodes]
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

    def set_public_ips(self):
        all_ips = [node.ip for node in self.all_public_nodes]
        amount = int((len(all_ips) - 1) * self.config.connectivity)

        for node in self.selfish_node_proxies:
            all_ips.remove(node.ip)
            ips = random.sample(all_ips, amount)
            node.public_ips = ips
            all_ips.append(node.ip)

    def run_selfish_node_proxy(self, node, latency):
        current_best_block_hash_cmd = 'start_hash=$(' + bitcoindcmd.get_best_block_hash(self.nodes[0]) + ')'
        run_cmd = dockercmd.run_selfish_proxy(node.proxy, proxycmd.run_proxy(node.proxy, node.private_node.ip,
                                                                             '$start_hash'), latency)
        return '; '.join([current_best_block_hash_cmd, run_cmd])

    def save_consensus_chain(self):
        # idea iterate over chain and check if at some height all hashes are the same.
        mock_node = Node('$node', None)

        iter_cmd = ('for height in `seq ' + str(self.first_block_height()) +
                    ' $(' + bitcoindcmd.get_block_count(self.all_bitcoind_nodes[0]) + ')`; do'
                    ' hash=$(' + bitcoindcmd.get_block_hash(self.all_bitcoind_nodes[0], '$height') + ');'
                    ' all_same=true; for node in "${nodes[@]}"; do' +
                    ' if [[ $hash != $(' + bitcoindcmd.get_block_hash(mock_node, '$height') + ')'
                    ' ]]; then all_same=false; fi; done;'
                    r' if [ "$all_same" = true ]; then echo $height\; $hash '
                    '| tee -a ' + root_dir + '/consensus_chain.csv; fi; done')

        return '; '.join([self.bitcoind_nodes_array(), iter_cmd])

    def bitcoind_nodes_array(self):
        return 'nodes=(' + ' '.join(node.name for node in self.all_bitcoind_nodes) + ')'

    def first_block_height(self):
        return len(self.all_bitcoind_nodes) + 100 + 1


class Node:
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip

    def rm(self):
        return 'docker rm --force ' + self.name


class SelfishNode:
    def __init__(self, name, public_ip, private_ip, selfish_nodes_args):
        self.proxy = Node(name + selfish_node_proxy_postfix, public_ip)
        self.proxy.args = selfish_nodes_args

        self.private_node = Node(name, private_ip)

    def rm(self):
        return self.proxy.rm() + '; ' + self.private_node.rm()
