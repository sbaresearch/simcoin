#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

# os.system("git clone https://github.com/bitcoin/bitcoin src/bitcoin")

# create execution plan
import array
plan = []

## check system for dependencies
# git
def check_dependencies():
    if (os.system('docker version') != 0):
        # sudo gpasswd -a ${USER} docker; sudo service docker restart; newgrp docker
        exit("docker not found or not accessible")

# check_dependencies()
# etc

# IP range from RFC6890
# it does not conflict with https://github.com/bitcoin/bitcoin/blob/master/src/netbase.h
ip_range = "240.0.0.0/4"
ip_bootstrap = "240.0.0.2"

image = 'btn/base:v1'
conatiner_prefix = 'btn-'
number_of_conatiners = 10
number_of_blocks = '6'

plan.append('docker network create --subnet=' + ip_range + ' --driver bridge isolated_nw ; sleep 1')

# python
# import os

def bitcoindCmd (strategy = 'default'):
    daemon = ' bitcoind '
    default = {
          'regtest': ' -regtest ',       # activate regtest mode
          'datadir': ' -datadir=/data ', # change the datadir
          'debug': ' -debug ',           # log all events
          #'printtoconsole': ' -printtoconsole ', # print the log to stdout instead of a file TODO `docker logs`
          'logips': ' -logips ',         # enable ip loging
          'listen' : ' -listen ',        # ensure listening even if 'connect' is given
          'listenonion' : ' -listenonion=0 ', # disable tor 
          'onlynet': ' -onlynet=ipv4 ',  # disable ipv6
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
    return  daemon + ( ' '.join(default.values()) )

def dockerBootstrapCmd (cmd):
    return (' '
    ' docker run '
    '   --detach=true '
    '   --net=isolated_nw '
    '   --ip=' + ip_bootstrap + ' '
    '   --name=bootstrap'   # conatiner name
    '   ' + image + ' '      # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
    '   ' + cmd + ' '
    ' '
    )

def dockerNodeCmd (name,cmd):
    return (' '
    ' docker run '
    '   --cap-add=NET_ADMIN ' # for `tc`
    '   --detach=true '
    '   --net=isolated_nw '
    '   --name=' + name + ' '   # conatiner name
    '   --hostname=' + name + ' '
    '   --volume $PWD/datadirs/' + name + ':/data '
    '   ' + image + ' '      # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
    '   bash -c "' + cmd + '" '
    ' '
    )

def cli(node,command):
    return (' '
    ' docker exec ' 
    + node + 
    ' bitcoin-cli -regtest -datadir=/data '
    + command +
    ' '
    )

def nodeInfo(node):
    commands = [
#        'getconnectioncount',
#        'getblockcount',
#        'getinfo',
#        'getmininginfo',
        'getpeerinfo'
    ]
    return ';'.join([cli(node,cmd) for cmd in commands])


def dockerStp (name):
    return (' '
    ' docker rm --force ' + name + ' & '
    ' '
    )

def status():
    import subprocess
    batcmd = cli('bootstrap','getpeerinfo')
    result = subprocess.check_output(batcmd, shell=True)

    import json
    import codecs
    pretty = json.loads(str(result))
    return [ node['synced_headers'] for node in pretty]

# src https://github.com/dcm-oss/blockade/blob/master/blockade/net.py
def slow_network(cmd):
    traffic_control = "tc qdisc replace dev eth0 root netem delay 500ms"
    return traffic_control + "; " + cmd
    # apt install iproute2
    # --cap-add=NET_ADMIN

# config

ids = [ conatiner_prefix + str(element) for element in range(number_of_conatiners)]
commands = [ dockerNodeCmd(id,slow_network(bitcoindCmd('user'))) for id in ids ]

# setup
plan.append( dockerBootstrapCmd(bitcoindCmd('user')) )
plan.extend( commands )

plan.append('sleep 2') # wait before generating otherwise "Error -28" (still warming up)

# run
plan.append(cli(ids[1],'generate ' + number_of_blocks))

plan.append('sleep 10') # wait for blocks to spread

# stop
plan.extend( [ dockerStp(id) for id in ids] )
plan.append( dockerStp('bootstrap') )
plan.append('sleep 2')

plan.append('docker network rm isolated_nw')

# fix permissions on datadirs
plan.append('docker run --rm --volume $PWD/datadirs:/data ' + image + ' chmod a+rwx --recursive /data')

# plan.append('cat datadirs/btn-1/regtest/debug.log')

print('\n'.join(plan))


os.system("rm -rf ./datadirs/*")

[os.system(cmd) for cmd in plan] 

os.system(' '
  ' docker run --name elastic --detach elasticsearch:2.3.5 '
  ' ; docker run --name kibana --detach --link elastic:elasticsearch --publish 5601:5601 kibana:4.5.4 '
  ' ; docker run --name logstash --rm --link elastic:elastic -v "$PWD":/data logstash:2.3.4-1 logstash -f /data/docker/logstash.conf '
  ' '
)
# cleanup
# `rm -rf ./datadirs/*`