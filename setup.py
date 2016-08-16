#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

# os.system("git clone https://github.com/bitcoin/bitcoin src/bitcoin")

## check system for dependencies
# git
def check_dependencies():
    if (os.system('docker version') != 0):
        # sudo gpasswd -a ${USER} docker; sudo service docker restart; newgrp docker
        exit("docker not found or not accessible")

check_dependencies()
# etc

# IP range from RFC6890
# it does not conflict with https://github.com/bitcoin/bitcoin/blob/master/src/netbase.h
ip_range = "240.0.0.0/4"
ip_bootstrap = "240.0.0.2"

conatiner_prefix = 'btn-'
number_of_conatiners = 2

os.system('docker network create --subnet=' + ip_range + ' --driver bridge isolated_nw')

# python
# import os

def bitcoindCmd (strategy = 'default'):
    daemon = ' bitcoind '
    default = {
          'regtest': ' -regtest ',       # activate regtest mode
          'datadir': ' -datadir=/data ', # change the datadir
          'debug': ' -debug ',           # log all events
          'printtoconsole': ' -printtoconsole ', # print the log to stdout instead of a file TODO `docker logs`
          'logips': ' -logips ',         # enable ip loging
          'listen' : ' -listen ',        # ensure listening even if 'connect' is given
          'listenonion' : ' -listenonion=0 ', # disable tor 
          'onlynet': ' -onlynet=ipv4 ',  # disable ipv6
    }
    configs = {
        'default': {},
        'bootstrap' : {
     #       'connect': ' -connect=0.0.0.0 ', # don't connect
            'disablewallet': ' -disablewallet=1 ' # disable wallet
        },
        'user': {
 #          'dns' : ' -dns=1 ', # TODO check if necessary
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
    return daemon + ( ' '.join(default.values()) )

def dockerBootstrapCmd ():
    return (' '
    ' docker run '
    '   --detach=true '
    '   --net=isolated_nw '
    '   --ip=' + ip_bootstrap + ' '
    '   --name=bootstrap'   # conatiner name
    '   btn/base:v1 '      # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
    ' '
    )

def dockerNodeCmd (name):
    return (' '
    ' docker run '
    '   --detach=true '
    '   --net=isolated_nw '
    '   --link=fst:fst '
    '   --name=' + name + ' '   # conatiner name
    '   btn/base:v1 '      # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
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
    ' docker stop --time 0 ' + name + ' ; '
    ' docker rm ' + name + ' ; '
    ' '
    )

def user(id):
    return ( dockerNodeCmd(id) + bitcoindCmd('user') )

def status():
    import subprocess
    batcmd = cli('bootstrap','getpeerinfo')
    result = subprocess.check_output(batcmd, shell=True)

    import json
    import codecs
    pretty = json.loads(str(result))
    return [ node['synced_headers'] for node in pretty]


# config

ids = [ conatiner_prefix + str(element) for element in range(number_of_conatiners)]
commands = [ user(e) for e in ids ]

# setup
os.system( dockerBootstrapCmd() + bitcoindCmd('user') )
[os.system(cmd) for cmd in commands]

os.system('sleep 2') # wait before generating otherwise "Error -28" (still warming up)

# run
# input("Press Enter to generate blocks ...")
os.system(cli(ids[1],'generate 5'))

os.system('sleep 2')

print(status());


# input("Press Enter to cleanup ...")

# stop
[os.system(dockerStp(id)) for id in ids]
os.system(dockerStp('bootstrap'))

os.system('docker network rm isolated_nw')
