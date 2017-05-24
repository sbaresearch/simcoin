#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import random
import sys
from scheduler import Scheduler

# IP range from RFC6890 - IP range for future use
# it does not conflict with https://github.com/bitcoin/bitcoin/blob/master/src/netbase.h
ip_range = "240.0.0.0/4"
ip_bootstrap = "240.0.0.2"

image = 'btn/base:v3'
if os.system("docker inspect " + image + " > /dev/null") != 0:
    print("Image " + image + " not found")
    exit()
container_prefix = 'btn-'


class DataDir:

    @staticmethod
    def root_dir():
        return '$PWD/../data'

    @staticmethod
    def host(container_id):
        return DataDir.root_dir() + '/' + container_id

    @staticmethod
    def guest():
        return '/data'

    @staticmethod
    def log_file():
        """return the path to the execution log"""
        return '$PWD/../data/log'


class Docker:

    def __init__(self,plan):
        self.plan = plan

    def __enter__(self):
        self.plan.append('docker network create --subnet=' + ip_range + ' --driver bridge isolated_network ; sleep 1')
        return self

    def __exit__(self, excpetion_type, exception_value, traceback):
        self.plan.append('docker network rm isolated_network')

    @staticmethod
    def docker_bootstrap_cmd(cmd):
        return (' '
                ' docker run '
                '   --detach=true '
                '   --net=isolated_network '
                '   --ip=' + ip_bootstrap + ' '
                '   --name=bootstrap'   # container name
                '   ' + image + ' '      # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
                '   bash -c "' + cmd + '" '
                ' '
                )

    @staticmethod
    def docker_node_cmd(name, cmd):
        return (' '
                ' docker run '
                '   --cap-add=NET_ADMIN ' # for `tc`
                '   --detach=true '
                '   --net=isolated_network '
                '   --name=' + name + ' '   # container name
                '   --hostname=' + name + ' '
                '   --volume ' + DataDir.host(name) + ':' + DataDir.guest() + ' '
                '   ' + image + ' '      # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
                '   bash -c "' + cmd + '" '
                ' ')

    @staticmethod
    def docker_stp(name):
        return (' '
                ' docker rm --force ' + name + ' & '
                ' ')

    @staticmethod
    def cli(node, command):
        return (' '
                ' docker exec '
                + node +
                ' /bin/sh -c \''
                '    bitcoin-cli -regtest -datadir=' + DataDir.guest() + ' ' # -printtoconsole -daemon
                +    command +
                ' \' '
                ' ')


def bitcoind_cmd(strategy='default'):
    daemon = ' bitcoind '
    default = {
          'regtest': ' -regtest ',             # activate regtest mode
          'datadir': ' -datadir=' + DataDir.guest() + ' ',       # change the datadir
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
    return ';'.join([Docker.cli(node, cmd) for cmd in commands])


def slow_network(cmd, latency):
    traffic_control = "tc qdisc replace dev eth0 root netem delay " + str(latency)+ "ms"
    return traffic_control + "; " + cmd
    # apt install iproute2
    # --cap-add=NET_ADMIN


class NodeManager():
    def __init__(self, plan, number_of_containers, latency):
        self.ids = [container_prefix + str(element) for element in range(number_of_containers)]
        self.nodes = [Docker.docker_node_cmd(id, slow_network(bitcoind_cmd('user'), latency)) for id in self.ids ]
        self.plan = plan
        self.latency = latency

    def __enter__(self):
        self.plan.append(Docker.docker_bootstrap_cmd(slow_network(bitcoind_cmd('user'), self.latency)))
        self.plan.extend( self.nodes )
        self.plan.append('sleep 2') # wait before generating otherwise "Error -28" (still warming up)
        return self

    def __exit__(self, excpetion_type, exception_value, traceback):
        self.plan.extend([Docker.docker_stp(id) for id in self.ids])
        self.plan.append(Docker.docker_stp('bootstrap'))
        self.plan.append('sleep 5')

    def random_node(self):
        return random.choice(self.ids)

    def every_node_p(self, cmd):
        return [Docker.cli(_id, cmd) for _id in self.ids]

    def warmup_block_generation(self):
        # one block for each node ## This forks the chain from the beginning TODO remove
        # plus 100 blocks to enable spending
        return ['echo Begin of warmup'] + self.every_node_p('generate 1') + [self.random_block_command(100)] + ['sleep 5']

    def random_block_command(self, number=1):
        return Docker.cli(self.random_node(), 'generate ' + str(number))

    def random_transaction_command(self):
        node = self.random_node()
        return Docker.cli(node, 'sendtoaddress $(bitcoin-cli -regtest -datadir=' + DataDir.guest() + ' getnewaddress) 10.0')

    def log_chain_tips(self):
        return self.every_node_p('getchaintips > ' + DataDir.guest() + '/chaintips.json')


def execution_plan(nodes, number_of_blocks, block_time, latency):
    plan = []
    with Docker(plan):
        with NodeManager(plan, nodes, latency) as nodeManager:
            os.system("rm -rf " + DataDir.host('*'))

            plan.extend(nodeManager.warmup_block_generation())

            sys.path.append('./btn/src')
            s = Scheduler()
            s.add_blocks(number_of_blocks, block_time, [nodeManager.random_block_command() for _ in range(1000)])
            s.add_transactions(10, [nodeManager.random_transaction_command() for _ in range(10)], transactions_per_second=10)
            plan.extend(s.bash_commands().split('\n'))

            plan.append('sleep 3')  # wait for blocks to spread

            plan.extend(nodeManager.log_chain_tips())

            plan.append('docker run --rm --volume ' + DataDir.root_dir() + ':/mnt' + ' ' + image + ' chmod a+rwx --recursive /mnt') # fix permissions on datadirs

            plan.extend(aggregate_logs(nodeManager.ids))

    return plan


def aggregate_logs(ids):
    commands = []
    timestamp_length = str(len('2016-09-22 14:46:41.706605'))
    data_dir = DataDir.root_dir()
    logfile = DataDir.log_file()
    logfile_raw = logfile + '.raw'

    def prefix_lines(prefix):
        return 'sed -e \'s/^/' + prefix + ' /\''

    def remove_empty_lines():
        return 'sed "s/^$//g"'

    def remove_lines_starting_with_whitspace():
        return 'sed "s/^[[:space:]].*$//g"'

    def remove_multiline_error_messages():
        return 'sed "s/^.\{26\}  .*$//g"'

    def sed_command(_id): # insert node id after timestamp
        return 'sed "s/^.\{' + timestamp_length + '\}/& ' + _id + '/g"'

    "remove files from previous run"
    commands.append('rm -rf ' + logfile)
    commands.append('rm -rf ' + logfile_raw)

    "consolidate logfiles from the nodes"
    commands.extend([' cat ' + DataDir.host(_id) + '/regtest/debug.log '
                     ' |   ' + sed_command(_id) +
                     ' >>  ' + logfile_raw + '; '
                    for _id in ids])

    "clean the logfiles"
    commands.append(' cat ' + logfile_raw +
                    ' | ' + remove_empty_lines() +
                    ' | ' + remove_lines_starting_with_whitspace() +
                    ' | ' + remove_multiline_error_messages() +
                    ' > ' + logfile
                    )
    "sort by timestamp"
    commands.append(' sort ' + logfile)

    "aggregate fork information"
    commands.extend([' cat ' + DataDir.host(_id) + '/chaintips.json '
                     ' | jq "length" '
                     ' | ' + prefix_lines(_id) +
                     ' >> ' + data_dir + '/forks; '
                    for _id in ids])

    return commands
