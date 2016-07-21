% Bachelor Thesis
% Andreas Kern e0727972@student.tuwien.ac.at
% July 2016

# Introduction

Bitcoin Testing Netowrk (BTN)

build for reproducability
others can build up on this framework and don't have to replicate complicated setups

technologies involved
* docker images
* TODO docker compose/machine/swarm (kubernetes)
* netfilter/iptables 

steps to run a standard simulation

## setup on ubuntu 16.06 LTS

generate node image `docker build --tag btn/base:v1 - < files/docker/baseimage` build

run infrastructure

1. checkout this projects sourcode from `github`
4. run `docker build --tag btn/base:v1 - < files/docker/baseimage` to build the docker image 
5. run `setup.py` to run the simulation

## standard usage

bitcoind is the server that is run
bitcoin-cli getblockcount for interaction


# changing the standard simulation

## bitcoin sourcode

`cd src/bitcoin; git pull`
TODO github.com/kernoelpanic/bitcoinbuilder

## node behavior

strategy: miner, user, relay ,... ,byzantine, malicious // TODO rename to type
reachability: {always, mostly, seldom}, 

## physical network

nat, latency, bandwith, tc
TODO different subnets selection

## network composition

of which nodes the network consist

## metrics to collect

TODO which information how

# simple networks

*two miners*: 
2 nodes, 1 node type, both mine, both send transactions to themselves

# suggested node types

node = image + instance + connectivity + strategy

assumptions: all have the same sourcecode and the same version

Primary nodes:

* pooled mining (splits every blockreward to a lot addresses, payout threshold, very few nodes), always online
* common user (receives transactions from exchange and other common users, sends to payment providers and other common users, simple payment verification node, does not sync blockchain)

Secondary nodes:

* exchange, receives lots of (big) transactions, sends out a lot of small transactions, does not mine, always online
* solo mining (sends every mined blockreward to exchange, very few nodes), always online
* hodler (only receives transactions, never spends them, sporadically online, syncs blockchain)
* satoshi dice (game of chance, receives a lot of small transactions, returns a lot of them)
* relay (no transactions, always online, syncs blockchain)
* scanner (no transactions, connects to all nodes simultaneously)
* scammer (double spends every transactions)

# optimizations

* deduplicating filesystem for blockchain
* single machine setups
* docker ...

## recomendations 

source: https://bitcoin.org/en/full-node#minimum-requirements

* 80 gigabytes of free disk space
* 2 gigabytes of memory (RAM)
* broadband Internet connection with upload speeds of at least 400 kilobits (50 kilobytes) per second
* 200 gigabytes upload or more a month. 
* Download 20 gigabytes a month, plus around an additional 60 gigabytes the first time you start your node.
* 6 hours a day that your full node can be left running. More hours would be better, and best of all would be if you can run your node continuously.

# Outlook

* different clients (e.g. bitcoinj, hascoin)
* different version numbers
* evolving clients (clients with older version numbers fade out, newer version numbers appear)
* leveldb fail
* fee pressure
* mining strategies (e.g. selfish mining)

# caveats

* first difficulty change was in block #32256 (from 1.00 to 1.18) on 2009-12-30 06:11:04 (~1 year after launch)
  src: https://bitcoinchain.com/block_explorer/block/32256
  blkhas: 000000004f2886a170adb7204cb0c7a824217dd24d11a74423d564c4e0904967/