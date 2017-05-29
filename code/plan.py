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
ip_bootstrap = "240.0.0.1"

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
        next(ip_addresses)  # omit first ip address used by bootstrap node

        self.config = config
        self.nodes = [Node(node_prefix + str(i), next(ip_addresses)) for i in range(config.nodes)]
        self.selfish_nodes = [SelfishNode(selfish_node_prefix + str(i), next(ip_addresses), next(ip_addresses),
                                          config.selfish_nodes_args) for i in range(config.selfish_nodes)]
        self.all_nodes = self.nodes + self.selfish_nodes

    def create(self):
        config = self.config
        plan = []

        if len(self.selfish_nodes) > 0:
            self.set_public_ips()

        try:
            plan.append("rm -rf " + host_dir('*'))

            plan.append(dockercmd.create_network(ip_range))
            plan.append('sleep 1')

            plan.append(dockercmd.run_bootstrap_node(slow_network(config.latency) + bitcoindcmd.start_user()))
            plan.extend([dockercmd.run_node(node, slow_network(config.latency)
                                            + bitcoindcmd.start_user()) for node in self.nodes])
            plan.extend([dockercmd.run_selfish_node(
                node, slow_network(config.latency) + bitcoindcmd.start_selfish_mining(node))
                for node in self.selfish_nodes])

            plan.append('sleep 2')  # wait before generating otherwise "Error -28" (still warming up)

            plan.extend(self.warmup_block_generation())

            scheduler = Scheduler(0)
            scheduler.add_blocks(config.blocks, config.block_interval, [self.random_block_command() for _ in range(1000)])
            scheduler.add_tx(config.blocks * config.block_interval, [self.random_tx_command() for _ in range(10)])
            plan.extend(scheduler.bash_commands())
            plan.append('sleep 3')  # wait for blocks to spread

            plan.extend(self.log_chain_tips())

            plan.append(dockercmd.fix_data_dirs_permissions())

            plan.extend(logs.aggregate_logs(self.nodes))

        finally:
            plan.extend([dockercmd.rm_node(node.name) for node in self.nodes])
            plan.append(dockercmd.rm_node(bootstrap_node_name))
            plan.append('sleep 5')
            plan.append(dockercmd.rm_network())

        return plan

    def random_node(self):
        return random.choice(self.nodes)

    def exec_bash_every_node(self, cmd):
        return [dockercmd.exec_bash(node.name, cmd) for node in self.all_nodes]

    def warmup_block_generation(self):
        # one block for each node ## This forks the chain from the beginning TODO remove
        # plus 100 blocks to enable spending
        return ['echo Begin of warmup'] + self.every_node_p('generate 1') + [self.random_block_command(100)] + ['sleep 5']

    def random_block_command(self, number=1):
        return dockercmd.exec_bash(self.random_node().name, 'generate ' + str(number))

    def random_tx_command(self):
        node = self.random_node()
        return dockercmd.exec_bash(node.name, 'sendtoaddress $(bitcoin-cli -regtest -datadir=' + bitcoindcmd.guest_dir + ' getnewaddress) 10.0')

    def log_chain_tips(self):
        return self.exec_bash_every_node('getchaintips > ' + bitcoindcmd.guest_dir + '/chaintips.json')

    def set_public_ips(self):
        all_nodes = self.nodes + self.selfish_nodes
        all_ips = [node.ip for node in all_nodes]
        amount = int((len(all_ips) - 1) * self.config.connectivity)

        for node in self.selfish_nodes:
            all_ips.remove(node.ip)
            ips = random.sample(all_ips, amount)
            node.public_ips = ips
            all_ips.append(node.ip)


def slow_network(latency):
    # needed for this cmd: apt install iproute2 and --cap-add=NET_ADMIN
    return "tc qdisc replace dev eth0 root netem delay " + str(latency) + "ms; "


class Node:
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip


class SelfishNode(Node):
    def __init__(self, name, public_ip, private_ip, selfish_nodes_args):
        super().__init__(name, public_ip)

        self.private_ip = private_ip
        self.args = selfish_nodes_args
