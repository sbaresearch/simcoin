# Simulating Bitcoin

## Tasks

* Configure ZFS volums using (fs)block based dedub (this is almost trivial)
* Patch Bitcoind to align the persistence of (btc)blocks in the .dat files in the .bitcoin folder with the (fs)blocksize use for dedub.
* Find a sweet spot of dedub (fs)blocksize and test if it works with Bitcoin
* Patch Bitcoind to use configurable max (btc)blocksize. This should be easy, it is defined in a macro imho.
* Patch Bitcoind to use configurable difficulty values. Here the testnet mode of Bitcoin can be used as a template but I guess this will be more work than the (btc)blocksize
* Patch the Bitcoin regtest feature to make it possibe to set the above mentioned configuration options.
* Instrument the Bitcoin regtest feature and write a management client (ideally in python) to spawn the required instances.
* Run the emulations



## Meeting notes

### 2015-11-11 
* check how much amazon instances we started during scanning ?
    - *about 50* 
* How to include network delay when using `regtest` mode of `bitcoind`
* C programmer required for Bitcoin terminal software project
    - Linux (embedded)
    - PoS (Point of Sales Terminal)
    - Bitcoin REST (coinbase)
* Check for Bitcoin austria meetup @SBA
    - *yes, is possible*
    - *no timeslot yet*
* Check for time required between BSc thesis registration and completion 

#### Links
* https://github.com/bitcoinxt/bitcoinxt/commits/master/qa/rpc-tests/test_framework
* https://github.com/btcsuite?page=1
* http://hashingit.com/
* http://bitcoin.stackexchange.com/search?q=regtest
* http://bitcoin.stackexchange.com/questions/37340/valid-fork-in-regtest-change-blockchain-via-rpc
* http://bitcoin.stackexchange.com/questions/36013/is-it-possible-to-create-bitcoind-regtest-network-on-ubuntu-which-itself-is-on
* http://bitcoin-class.org/syllabus/
* https://piazza.com/princeton/spring2015/btctech/home
* http://www.crypto.edu.pl/Dziembowski/papers
* http://www.sigsac.org/ccs/CCS2015/pro_tutorial.html 
