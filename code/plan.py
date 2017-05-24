#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
from scheduler import Scheduler
import dockercmd
import bitcoindcmd
import logs

# IP range from RFC6890 - IP range for future use
# it does not conflict with https://github.com/bitcoin/bitcoin/blob/master/src/netbase.h
ip_range = "240.0.0.0/4"
ip_bootstrap = "240.0.0.2"

root_dir = '$PWD/../data'
guest_dir = '/data'
log_file = '$PWD/../data/log'

image = 'btn/base:v3'
container_prefix = 'btn-'


def host_dir(container_id):
    return root_dir + '/' + container_id


class Plan:
    def __init__(self, number_of_nodes):
        self.ids = [container_prefix + str(element) for element in range(number_of_nodes)]

    def create(self, latency, number_of_blocks, block_interval):
        plan = []

        try:
            plan.append(dockercmd.create_network(ip_range))
            plan.append(dockercmd.run_bootstrap_node(slow_network(latency) + bitcoindcmd.start('user')))
            plan.extend([dockercmd.run_node(_id, slow_network(latency) + bitcoindcmd.start('user')) for _id in self.ids])
            plan.append('sleep 2') # wait before generating otherwise "Error -28" (still warming up)

            plan.extend(self.warmup_block_generation())

            scheduler = Scheduler(0)
            scheduler.add_blocks(number_of_blocks, block_interval, [self.random_block_command() for _ in range(1000)])
            scheduler.add_tx(number_of_blocks * block_interval, [self.random_transaction_command() for _ in range(10)])
            plan.extend(scheduler.bash_commands())

            plan.append('sleep 3')  # wait for blocks to spread

            plan.extend(self.log_chain_tips())

            plan.append(dockercmd.fix_data_dirs_permissions())

            plan.extend(logs.aggregate_logs(self.ids))

        finally:
            plan.extend([dockercmd.rm_node(_id) for _id in self.ids])
            plan.append(dockercmd.rm_node('bootstrap'))
            plan.append('sleep 5')
            plan.append(dockercmd.rm_network())

        return plan

    def random_node(self):
        return random.choice(self.ids)

    def every_node_p(self, cmd):
        return [dockercmd.exec_bash(_id, cmd) for _id in self.ids]

    def warmup_block_generation(self):
        # one block for each node ## This forks the chain from the beginning TODO remove
        # plus 100 blocks to enable spending
        return ['echo Begin of warmup'] + self.every_node_p('generate 1') + [self.random_block_command(100)] + ['sleep 5']

    def random_block_command(self, number=1):
        return dockercmd.exec_bash(self.random_node(), 'generate ' + str(number))

    def random_transaction_command(self):
        node = self.random_node()
        return dockercmd.exec_bash(node, 'sendtoaddress $(bitcoin-cli -regtest -datadir=' + guest_dir + ' getnewaddress) 10.0')

    def log_chain_tips(self):
        return self.every_node_p('getchaintips > ' + guest_dir + '/chaintips.json')


def slow_network(latency):
    # needed for this cmd: apt install iproute2 and --cap-add=NET_ADMIN
    return "tc qdisc replace dev eth0 root netem delay " + str(latency) + "ms; "
