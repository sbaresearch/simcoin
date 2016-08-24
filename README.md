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

generate node image `docker build --tag btn/base:v1 - < docker/baseimage` build

run infrastructure

1. checkout this projects sourcode from `github`
4. run `docker build --tag btn/base:v2 - < docker/baseimage` to build the docker image 
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

# Analyzing

When the simulation finishes the data of each node is stored in './datadirs'.
Each node has its own folder named after the hostname.
The folders contain the 'data' directory of the bitcoind.
This not only includes the blockchain which _should_ be identical for each node but also the `debug.log`.
Parsing, storing and viewing the logfiles and can be done with the ELK stack.
ELK stands for Elastic, Logstash, Kibana.

## Setting up ELK

'''
docker pull elasticsearch:2.3.5
docker pull logstash:2.3.4-1
docker pull kibana:4.5.4

docker run --name elastic --detach elasticsearch:2.3.5
docker run --name kibana --detach --link elastic:elasticsearch --publish 5601:5601 kibana:4.5.4
docker run --name logstash --rm --link elastic:elastic -v "$PWD":/data logstash:2.3.4-1 logstash -f /data/docker/logstash.conf
# ^^^^ will not terminate, wait for until the ouput stops and all entries are parsed and exit manually (ctrl+c)

# open http://localhost:5601
# beware of the timeframe (upper right corner) if no data is shown

docker rm --force elastic
docker rm --force kibana
'''

## Logfile Events

This sections tries to account for all log messages that can be found in the debug.log

Startup log entries

```
2016-08-18 09:55:10 Bitcoin version v0.12.1.0-g9779e1e (Mon, 11 Apr 2016 13:01:43 +0200)
2016-08-18 09:55:10 InitParameterInteraction: parameter interaction: -whitelistforcerelay=1 -> setting -whitelistrelay=1
2016-08-18 09:55:10 Using BerkeleyDB version Berkeley DB 4.8.30: (April  9, 2010)
2016-08-18 09:55:10 Default data directory /root/.bitcoin
2016-08-18 09:55:10 Using data directory /data/regtest
2016-08-18 09:55:10 Using config file /data/bitcoin.conf
2016-08-18 09:55:10 Using at most 125 connections (1048576 file descriptors available)
2016-08-18 09:55:10 Using 2 threads for script verification
2016-08-18 09:55:10 scheduler thread start
2016-08-18 09:55:10 Allowing HTTP connections from: 127.0.0.0/8 ::1/128 
2016-08-18 09:55:10 Binding RPC on address ::1 port 18332
2016-08-18 09:55:10 Binding RPC on address 127.0.0.1 port 18332
2016-08-18 09:55:10 Initialized HTTP server
2016-08-18 09:55:10 HTTP: creating work queue of depth 16
2016-08-18 09:55:10 Starting RPC
2016-08-18 09:55:10 Starting HTTP RPC server
2016-08-18 09:55:10 No rpcpassword set - using random cookie authentication
2016-08-18 09:55:10 Generated RPC authentication cookie /data/regtest/.cookie
2016-08-18 09:55:10 Registering HTTP handler for / (exactmatch 1)
2016-08-18 09:55:10 Starting HTTP server
2016-08-18 09:55:10 HTTP: starting 4 worker threads
2016-08-18 09:55:10 Entering http event loop
2016-08-18 09:55:10 Using wallet wallet.dat
2016-08-18 09:55:10 init message: Verifying wallet...
2016-08-18 09:55:10 CDBEnv::Open: LogDir=/data/regtest/database ErrorFile=/data/regtest/db.log
2016-08-18 09:55:10 Bound to [::]:18444
2016-08-18 09:55:10 Bound to 0.0.0.0:18444
2016-08-18 09:55:10 Cache configuration:
2016-08-18 09:55:10 * Using 2.0MiB for block index database
2016-08-18 09:55:10 * Using 32.5MiB for chain state database
2016-08-18 09:55:10 * Using 65.5MiB for in-memory UTXO set
2016-08-18 09:55:10 init message: Loading block index...
2016-08-18 09:55:10 Opening LevelDB in /data/regtest/blocks/index
2016-08-18 09:55:10 Opened LevelDB successfully
2016-08-18 09:55:10 Using obfuscation key for /data/regtest/blocks/index: 0000000000000000
2016-08-18 09:55:10 Opening LevelDB in /data/regtest/chainstate
2016-08-18 09:55:10 Opened LevelDB successfully
2016-08-18 09:55:10 Using obfuscation key for /data/regtest/chainstate: e72d96f202c6fcfa
2016-08-18 09:55:10 LoadBlockIndexDB: last block file = 0
2016-08-18 09:55:10 LoadBlockIndexDB: last block file info: CBlockFileInfo(blocks=121, size=22837, heights=0...120, time=2011-02-02...2016-08-18)
2016-08-18 09:55:10 Checking all blk files are present...
2016-08-18 09:55:10 LoadBlockIndexDB: transaction index disabled
2016-08-18 09:55:10 LoadBlockIndexDB: hashBestChain=4cebb1a704caa887d1c9d40358903093d88a43cac3ceee2450080770611e249f height=120 date=2016-08-18 09:53:37 progress=1.000000
2016-08-18 09:55:10 init message: Verifying blocks...
2016-08-18 09:55:10 Verifying last 120 blocks at level 3
2016-08-18 09:55:10 No coin database inconsistencies in last 120 blocks (120 transactions)
2016-08-18 09:55:10  block index             273ms
2016-08-18 09:55:10 Reading estimates: 98 FeeRate buckets counting confirms up to 25 blocks
2016-08-18 09:55:10 Reading estimates: 29 Priority buckets counting confirms up to 25 blocks
2016-08-18 09:55:10 init message: Loading wallet...
2016-08-18 09:55:10 nFileVersion = 120100
2016-08-18 09:55:10 Keys: 2 plaintext, 0 encrypted, 2 w/ metadata, 2 total
2016-08-18 09:55:10  wallet                   52ms
2016-08-18 09:55:10 init message: Activating best chain...
2016-08-18 09:55:10 mapBlockIndex.size() = 121
2016-08-18 09:55:10 nBestHeight = 120
2016-08-18 09:55:10 setKeyPool.size() = 1
2016-08-18 09:55:10 mapWallet.size() = 0
2016-08-18 09:55:10 mapAddressBook.size() = 1
2016-08-18 09:55:10 init message: Loading addresses...
2016-08-18 09:55:10 ERROR: Read: Failed to open file /data/regtest/banlist.dat
2016-08-18 09:55:10 Invalid or missing banlist.dat; recreating
2016-08-18 09:55:10 Loaded 2 addresses from peers.dat  1ms
2016-08-18 09:55:10 Added connection to 127.0.0.1:0 peer=0
2016-08-18 09:55:10 AddLocal(240.0.0.6:18444,1)
2016-08-18 09:55:10 Discover: IPv4 eth0: 240.0.0.6
2016-08-18 09:55:10 DNS seeding disabled
2016-08-18 09:55:10 net thread start
2016-08-18 09:55:10 init message: Done loading
2016-08-18 09:55:10 msghand thread start
2016-08-18 09:55:10 opencon thread start
```

Connecting to an already seen node
```
2016-08-18 09:55:10 trying connection 240.0.0.3 lastseen=0.0hrs
2016-08-18 09:55:10 Added connection to 240.0.0.3 peer=1
2016-08-18 09:55:10 send version message: version 70012, blocks=120, us=240.0.0.6:18444, them=240.0.0.3:18444, peer=1
2016-08-18 09:55:10 sending: version (102 bytes) peer=1
2016-08-18 09:55:10 addcon thread start
2016-08-18 09:55:10 received: version (102 bytes) peer=1
2016-08-18 09:55:10 sending: verack (0 bytes) peer=1
2016-08-18 09:55:10 ProcessMessages: advertizing address 240.0.0.6:18444
2016-08-18 09:55:10 sending: getaddr (0 bytes) peer=1
2016-08-18 09:55:10 Moving 240.0.0.3:18444 to tried
2016-08-18 09:55:10 receive version message: /Satoshi:0.12.1/: version 70012, blocks=120, us=240.0.0.6:54178, peer=1, peeraddr=240.0.0.3:18444
2016-08-18 09:55:10 added time data, samples 2, offset +0 (+0 minutes)
2016-08-18 09:55:10 sending: ping (8 bytes) peer=1
2016-08-18 09:55:10 AdvertizeLocal: advertizing address 240.0.0.6:18444
2016-08-18 09:55:10 sending: addr (31 bytes) peer=1
2016-08-18 09:55:10 initial getheaders (119) to peer=1 (startheight:120)
2016-08-18 09:55:10 sending: getheaders (613 bytes) peer=1
2016-08-18 09:55:10 received: verack (0 bytes) peer=1
2016-08-18 09:55:10 sending: sendheaders (0 bytes) peer=1
2016-08-18 09:55:10 received: ping (8 bytes) peer=1
2016-08-18 09:55:10 sending: pong (8 bytes) peer=1
2016-08-18 09:55:10 received: addr (31 bytes) peer=1
2016-08-18 09:55:10 disconnecting peer=1
```


Here are the logentries that belong to a single interaction between two nodes.

Receiving headers, then requesting and receiving the block 

```
2016-08-18 09:55:15 received: headers (82 bytes) peer=2

2016-08-18 09:53:16 Requesting block 304a4e71eb7ea2b2349e02029f82c6ae69429771fc6ac9fa052de4d29bbb0b9e (1) peer=2
2016-08-18 09:53:16 sending: getdata (577 bytes) peer=2

2016-08-18 09:53:16 received: block (179 bytes) peer=2
2016-08-18 09:53:16 received block 304a4e71eb7ea2b2349e02029f82c6ae69429771fc6ac9fa052de4d29bbb0b9e peer=2
2016-08-18 09:53:16   - Load block from disk: 0.00ms [0.00s]
2016-08-18 09:53:16     - Sanity checks: 0.01ms [0.00s]
2016-08-18 09:53:16     - Fork checks: 0.06ms [0.00s]
2016-08-18 09:53:16       - Connect 1 transactions: 0.05ms (0.049ms/tx, 0.000ms/txin) [0.00s]
2016-08-18 09:53:16     - Verify 0 txins: 0.10ms (0.000ms/txin) [0.00s]
2016-08-18 09:53:16 Pre-allocating up to position 0x100000 in rev00000.dat
2016-08-18 09:53:16     - Index writing: 4.75ms [0.00s]
2016-08-18 09:53:16     - Callbacks: 0.08ms [0.00s]
2016-08-18 09:53:16   - Connect total: 5.09ms [0.01s]
2016-08-18 09:53:16   - Flush: 0.04ms [0.00s]
2016-08-18 09:53:16   - Writing chainstate: 0.04ms [0.00s]
2016-08-18 09:53:16 Blockpolicy recalculating dynamic cutoffs:
2016-08-18 09:53:16   2: For conf success > 0.95 need Priority >:           -1 from buckets  2.1e+24 -  2.1e+24  Cur Bucket stats   -nan%       0.0/(0.0+0 mempool)
2016-08-18 09:53:16   2: For conf success > 0.95 need FeeRate >:           -1 from buckets  2.1e+15 -  2.1e+15  Cur Bucket stats   -nan%       0.0/(0.0+0 mempool)
2016-08-18 09:53:16  10: For conf success < 0.50 need Priority <:           -1 from buckets 5.76e+07 - 5.76e+07  Cur Bucket stats   -nan%       0.0/(0.0+0 mempool)
2016-08-18 09:53:16  10: For conf success < 0.50 need FeeRate <:           -1 from buckets     1000 -     1000  Cur Bucket stats   -nan%       0.0/(0.0+0 mempool)
2016-08-18 09:53:16 Blockpolicy after updating estimates for 0 confirmed entries, new mempool map size 0
2016-08-18 09:53:16 UpdateTip: new best=304a4e71eb7ea2b2349e02029f82c6ae69429771fc6ac9fa052de4d29bbb0b9e  height=1  log2_work=2  tx=2  date=2016-08-18 08:18:04 progress=1.000000  cache=0.0MiB(1tx)
2016-08-18 09:53:16   - Connect postprocess: 0.45ms [0.00s]
2016-08-18 09:53:16 - Connect block: 5.62ms [0.01s]
2016-08-18 09:53:16 Checking mempool with 0 transactions and 0 inputs
```
## Missing log entries

transactions
