#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

# os.system("git clone https://github.com/bitcoin/bitcoin src/bitcoin")

## check system for dependencies
# git
os.system('docker version') # sudo gpasswd -a ${USER} docker; sudo service docker restart; newgrp docker

# etc

# docker network create --driver bridge isolated_nw

python
import os
os.system(      # p2p bootstrap node
    'docker run '
    '    --rm=true '   # remove container
    '    --net=isolated_nw '
    '    --name="fst" '   # conatiner name
    '    btn/base:v1 '      # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
    '    bitcoind ' ## run bitcoind
    '       -regtest '
    '       -datadir=/data ' # change datadir
    '       -debug '         # log all events
    '       -printtoconsole ' # print the log to stdout instead of a file
    '       -logips '        # include IPs
    '       -connect=0.0.0.0 ' # do not connect to anyone
    '       -listen '        # but still listen for incomming
    '       -listenonion=0 ' # disable tor
    '       -onlynet=ipv4 '  # omits ipv6 and tor addresses
    ## wallet options
    '       -disablewallet=1 '
    ) 



os.system(      # first normal node
    'docker run '
    '    --rm=true '   # remove container
    '    --name="snd" '   # conatiner name
    '    --net=isolated_nw '
    '    --link fst:fst ' #sourcecontainername:alias
    '    btn/base:v1 '      # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
    '    bitcoind ' ## run bitcoind
    '       -datadir=/data ' # change datadir
    '       -debug '         # log all events
    '       -printtoconsole ' # print the log to stdout instead of a file
    '       -logips '        # include IPs
    '       -dns=1'
    '       -dnsseed=0 '     # disable dns seed lookups, otherwise this gets seeds even with docker --internal network
    '       -addnode=fst ' # only connect to ourself introductionary node
    '       -listen '        # but still listen for incomming
    '       -listenonion=0 ' # disable tor
    '       -onlynet=ipv4 '  # omits ipv6 and tor addresses
        ## wallet options
    '       -keypool=0 '
    )

os.system(      # snd normal node
    'docker run '
    '    --rm=true '   # remove container
    '    --name="trd" '   # conatiner name
    '    --net=isolated_nw '
    '    --link fst:fst ' #sourcecontainername:alias
    '    btn/base:v1 '      # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
    '    bitcoind ' ## run bitcoind
    '       -gen=1000'
    '       -datadir=/data ' # change datadir
    '       -debug '         # log all events
    '       -printtoconsole ' # print the log to stdout instead of a file
    '       -logips '        # include IPs
    '       -dns=1 '    
    '       -dnsseed=0 '     # disable dns seed lookups, otherwise this gets seeds even with docker --internal network
    '       -addnode=fst ' # start with bootstrap node
    '       -listenonion=0 ' # disable tor
    '       -onlynet=ipv4 '  # omits ipv6 and tor addresses
        ## wallet options
    '       -keypool=100 '
    '       -regtest '
    )

os.system('docker exec -it trd bitcoin-cli -regtest -datadir=/data generate 100')

os.system('docker stop snd')
os.system('docker rm snd')

os.system('docker exec fst bitcoin-cli getbalance')
