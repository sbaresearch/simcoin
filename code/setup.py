#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
from scheduler import Scheduler
import dockercmd
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


def bitcoind_cmd(strategy='default'):
    daemon = ' bitcoind '
    default = {
          'regtest': ' -regtest ',             # activate regtest mode
          'datadir': ' -datadir=' + guest_dir + ' ',       # change the datadir
          'debug': ' -debug ',                 # log all events
          # 'printblocktree': ' -printblocktree', # removed (would print tree on startup)
          # 'printtoconsole': ' -printtoconsole ', # print the log to stdout instead of a file
          'logips': ' -logips ',               # enable ip loging
          'logtimemicros': ' -logtimemicros',  # add microseconds to logging flag: DEFAULT_LOGTIMEMICROS
          'listen' : ' -listen ',              # ensure listening even if 'connect' is given
          'listenonion' : ' -listenonion=0 ',  # disable tor
          'onlynet': ' -onlynet=ipv4 ',        # disable ipv6
    }
    configs = {
        'default': {},
        'bootstrap' : {
            'disablewallet': ' -disablewallet=1 ' # disable wallet
        },
        'user': {
            'dnsseed' : ' -dnsseed=0 ',  # disable dns seed lookups, otherwise this gets seeds even with docker --internal network
            'addnode' : ' -addnode=' + ip_bootstrap + ' ', # only connect ourself introductionary node
            'seednode': ' -seednode=240.0.0.3 ',
            'keypool' : ' -keypool=1 '
        },
        'miner-solo' : {
            'addnode' : ' -addnode=fst ', # only connect to ourself introductionary node
            'keypool' : ' -keypool=1 '
        }
    }
    default.update(configs[strategy])
    return daemon + (' '.join(default.values()))


def node_info(node):
    commands = [
        #        'getconnectioncount',
        #        'getblockcount',
        #        'getinfo',
        #        'getmininginfo',
                'getpeerinfo'
    ]
    return ';'.join([dockercmd.exec_bash(node, cmd) for cmd in commands])


def slow_network(latency):
    # needed for this cmd: apt install iproute2 and --cap-add=NET_ADMIN
    return "tc qdisc replace dev eth0 root netem delay " + str(latency) + "ms; "


class Execution:
    def __init__(self, number_of_nodes):
        self.ids = [container_prefix + str(element) for element in range(number_of_nodes)]

        self.plan = []

    def create(self, latency, number_of_blocks, block_time):
        plan = []

        try:
            plan.append(dockercmd.create_network(ip_range))
            plan.append(dockercmd.run_bootstrap_node(slow_network(latency) + bitcoind_cmd('user')))
            plan.extend([dockercmd.run_node(_id, slow_network(latency) + bitcoind_cmd('user')) for _id in self.ids])
            plan.append('sleep 2') # wait before generating otherwise "Error -28" (still warming up)

            plan.extend(self.warmup_block_generation())

            scheduler = Scheduler()
            scheduler.add_blocks(number_of_blocks, block_time, [self.random_block_command() for _ in range(1000)])
            scheduler.add_transactions(10, [self.random_transaction_command() for _ in range(10)], transactions_per_second=10)
            plan.extend(scheduler.bash_commands().split('\n'))

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
