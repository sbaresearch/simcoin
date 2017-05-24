#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import random
import sys
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


def host(container_id):
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
    return ';'.join([dockercmd.cli(node, cmd) for cmd in commands])


def slow_network(cmd, latency):
    traffic_control = "tc qdisc replace dev eth0 root netem delay " + str(latency) + "ms"
    return traffic_control + "; " + cmd
    # apt install iproute2
    # --cap-add=NET_ADMIN


class NodeManager:
    def __init__(self, plan, number_of_containers, latency):
        self.ids = [container_prefix + str(element) for element in range(number_of_containers)]
        self.nodes = [dockercmd.docker_node(id, slow_network(bitcoind_cmd('user'), latency)) for id in self.ids]
        self.plan = plan
        self.latency = latency

    def __enter__(self):
        self.plan.append(dockercmd.docker_bootstrap(slow_network(bitcoind_cmd('user'), self.latency)))
        self.plan.extend(self.nodes)
        self.plan.append('sleep 2') # wait before generating otherwise "Error -28" (still warming up)
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.plan.extend([dockercmd.docker_stp(id) for id in self.ids])
        self.plan.append(dockercmd.docker_stp('bootstrap'))
        self.plan.append('sleep 5')

    def random_node(self):
        return random.choice(self.ids)

    def every_node_p(self, cmd):
        return [dockercmd.cli(_id, cmd) for _id in self.ids]

    def warmup_block_generation(self):
        # one block for each node ## This forks the chain from the beginning TODO remove
        # plus 100 blocks to enable spending
        return ['echo Begin of warmup'] + self.every_node_p('generate 1') + [self.random_block_command(100)] + ['sleep 5']

    def random_block_command(self, number=1):
        return dockercmd.cli(self.random_node(), 'generate ' + str(number))

    def random_transaction_command(self):
        node = self.random_node()
        return dockercmd.cli(node, 'sendtoaddress $(bitcoin-cli -regtest -datadir=' + guest_dir + ' getnewaddress) 10.0')

    def log_chain_tips(self):
        return self.every_node_p('getchaintips > ' + guest_dir + '/chaintips.json')


def execution_plan(nodes, number_of_blocks, block_time, latency):
    plan = []
    try:
        plan.append('docker network create --subnet=' + ip_range + ' --driver bridge isolated_network ; sleep 1')
        with NodeManager(plan, nodes, latency) as node_manager:
            os.system("rm -rf " + host('*'))

            plan.extend(node_manager.warmup_block_generation())

            sys.path.append('./btn/src')
            s = Scheduler()
            s.add_blocks(number_of_blocks, block_time, [node_manager.random_block_command() for _ in range(1000)])
            s.add_transactions(10, [node_manager.random_transaction_command() for _ in range(10)], transactions_per_second=10)
            plan.extend(s.bash_commands().split('\n'))

            plan.append('sleep 3')  # wait for blocks to spread

            plan.extend(node_manager.log_chain_tips())

            plan.append('docker run --rm --volume ' + root_dir + ':/mnt' + ' ' + image + ' chmod a+rwx --recursive /mnt') # fix permissions on datadirs

            plan.extend(logs.aggregate_logs(node_manager.ids))
    finally:
        plan.append('docker network rm isolated_network')

    return plan
