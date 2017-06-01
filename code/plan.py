#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
from scheduler import Scheduler
import dockercmd
import bitcoindcmd
import logs
import ipaddress

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
bootstrap_node_name = 'bootstrap'


def host_dir(container_id):
    return root_dir + '/' + container_id


class Plan:
    def __init__(self, config):
        ip_addresses = ipaddress.ip_network(ip_range).hosts()
        next(ip_addresses)  # skipping first ip address (docker fails with error "is in use")
        next(ip_addresses)  # omit first ip address used by bootstrap node

        self.config = config
        self.nodes = [Node(node_prefix + str(i), next(ip_addresses)) for i in range(config.nodes)]
        self.selfish_nodes = [SelfishNode(selfish_node_prefix + str(i), next(ip_addresses), next(ip_addresses),
                                          config.selfish_nodes_args) for i in range(config.selfish_nodes)]
        self.all_nodes = self.nodes + self.selfish_nodes

        self.bootstrap_node = Node(bootstrap_node_name, ip_bootstrap)

    def create(self):
        config = self.config
        plan = []

        if len(self.selfish_nodes) > 0:
            self.set_public_ips()

        try:
            plan.append("rm -rf " + host_dir('*'))

            plan.append(dockercmd.create_network(ip_range))
            plan.append('sleep 1')

            plan.append(dockercmd.run_bootstrap_node(self.bootstrap_node, bitcoindcmd.start_user(), config.latency))
            plan.extend([dockercmd.run_node(node, bitcoindcmd.start_user(), config.latency) for node in self.all_nodes])

            plan.append('sleep 2')  # wait before generating otherwise "Error -28" (still warming up)
            plan.extend(self.warmup_block_generation())

            plan.extend([node.rm_private_node() for node in self.selfish_nodes])
            plan.extend([dockercmd.run_selfish_node(node, bitcoindcmd.start_selfish_mining(node), config.latency)
                         for node in self.selfish_nodes])

            scheduler = Scheduler(0)
            scheduler.add_blocks(config.blocks, config.block_interval, [self.random_block_command() for _ in range(1000)])
            scheduler.add_tx(config.blocks * config.block_interval, [self.random_tx_command() for _ in range(10)])
            plan.extend(scheduler.bash_commands())
            plan.append(self.wait_for_all_blocks_to_spread())

            plan.append(dockercmd.fix_data_dirs_permissions())

            plan.extend([bitcoindcmd.get_chain_tips(node) for node in self.all_nodes])
            plan.extend(logs.aggregate_logs(self.nodes))

        finally:
            plan.extend([node.rm() for node in self.all_nodes])
            plan.append(self.bootstrap_node.rm())
            plan.append('sleep 5')
            plan.append(dockercmd.rm_network())

        return plan

    def random_node(self):
        return random.choice(self.all_nodes)

    def warmup_block_generation(self):
        cmds = ['echo Begin of warmup']
        iter_nodes = iter(self.all_nodes)
        prev_node = next(iter_nodes)
        for node in iter_nodes:
            cmds.append(bitcoindcmd.generate_block(prev_node))
            self.wait_until_nodes_have_same_tip(cmds, prev_node, [node])
            prev_node = node

        cmds.append(bitcoindcmd.generate_block(prev_node, 101))
        self.wait_until_nodes_have_same_tip(cmds, prev_node, self.all_nodes)

        cmds.append('echo End of warmup')
        return cmds

    def wait_until_nodes_have_same_tip(self, cmds, leading_node, nodes):
        highest_tip = bitcoindcmd.get_best_block_hash(leading_node)
        for node in nodes:
            node_tip = bitcoindcmd.get_best_block_hash(node)
            cmds.append('while [[ $(' + highest_tip + ') != $(' + node_tip + ') ]]; ' +
                        'do echo Waiting for blocks to spread...; sleep 0.2; done')

    def wait_for_all_blocks_to_spread(self):

        # only use regular nodes since selfish nodes can trail back
        block_counts = ['$(' + bitcoindcmd.get_block_count(node) + ')' for node in self.nodes]
        return 'while : ; do block_counts=(' + ' '.join(block_counts) + '); '\
               + 'prev=${block_counts[0]}; wait=false; echo Current block_counts=${block_counts[@]}; ' \
                 'for i in "${block_counts[@]}"; do if [ $prev != $i ]; then wait=true; fi; done; ' \
                 'if [ $wait == false ]; then break; fi; ' \
                 'echo Waiting for blocks to spread...; sleep 0.2; done'

    def random_block_command(self, amount=1):
        return bitcoindcmd.generate_block(self.random_node(), amount)

    def random_tx_command(self):
        node = self.random_node()
        create_address_cmd = bitcoindcmd.get_new_address(node)
        create_tx_cmd = bitcoindcmd.send_to_address(node, '$fresh_address', 0.1)
        return 'fresh_address=$(' + create_address_cmd + '); ' + create_tx_cmd

    def set_public_ips(self):
        all_nodes = self.nodes + self.selfish_nodes
        all_ips = [node.ip for node in all_nodes]
        amount = int((len(all_ips) - 1) * self.config.connectivity)

        for node in self.selfish_nodes:
            all_ips.remove(node.ip)
            ips = random.sample(all_ips, amount)
            node.public_ips = ips
            all_ips.append(node.ip)


class Node:
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip

    def rm(self):
        return 'docker rm --force ' + self.name


class SelfishNode(Node):
    def __init__(self, name, public_ip, private_ip, selfish_nodes_args):
        super().__init__(name, public_ip)

        self.private_ip = private_ip
        self.args = selfish_nodes_args

    def rm(self):
        return super(SelfishNode, self).rm() + '; docker rm --force ' + self.name + '_proxy'

    def rm_private_node(self):
        return super(SelfishNode, self).rm()
