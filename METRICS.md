Metrics collected from the Web

#BitcoinStats from https://blockchain.info/stats
* Blocks Mined	162
* Time Between Blocks	8.3 (minutes)
* Bitcoins Mined	2,025.00000000 BTC
* Total Transaction Fees	130.21430667 BTC
* No. of Transactions	331832
* Total Output Volume	1,979,489.65657051 BTC
* Trade Volume	27,913.53901521 BTC
* earned from transaction fees	6.04 %
* Hash Rate
* Difficulty	392,963,262,344

#BitcoinCharts
* Total number of bitcoins that have already been mined
* Block details; Total size of all block headers and transactions. Not including database indexes.
* Blockchain Size; The total size of all block headers and transactions. Not including database indexes.
* Average block size in MB.
* Orphaned Blocks; The total number of blocks mined but ultimately not attached to the main Bitcoin blockchain.
* The average number of transactions per block.
* Median Transaction Confirmation Time (With Fee Only) for a transaction to be accepted into the public ledger.
* Mining Hash Rate; 
*   The estimated number of tera hashes per second (trillions of hashes per second) the Bitcoin network is performing.
*   A relative measure of how difficult it is to find a new block. The difficulty is adjusted periodically as a function of how much hashing power has been deployed by the network of miners.
* Total value of coinbase block rewards and transaction fees paid to miners.
* Mining Revenue - Total value of coinbase block rewards and transaction fees paid to miners.
* Total Transaction Fees - The total value of all transaction fees paid to miners (not including the coinbase value of block rewards).
* Cost % of Transaction Volume -  A chart showing miners revenue as percentage of the transaction volume.
* Cost per Transaction - A chart showing miners revenue divided by the number of transactions.

#Network activity

* The total number of unique addresses used on the Bitcoin blockchain.
* The number of daily confirmed Bitcoin transactions.
* Total Number of transactions
* The number of Bitcoin transactions added to the mempool per second.
* The number of transactions waiting to be confirmed.
* The rate at which the mempool is growing per second.
* The aggregate size of transactions waiting to be confirmed.
* The number of unspent Bitcoin transactions outputs, also known as the UTXO set size.
* The total number of Bitcoin transactions per day excluding those part of long transaction chains.
  * There are many legitimate reasons to create long transaction chains; however, they may also be cau sed by coin mixing or possible attempts to manipulate transaction volume.
* Number of Transactions Excluding Chains Longer Than 10
* Number of Transactions Excluding Chains Longer Than 100
* Number of Transactions Excluding Chains Longer Than 1000
* Number of Transactions Excluding Chains Longer Than 10,000
* The total value of all transaction outputs per day (includes coins returned to the sender as change).

#Lightning Bitcoin Paper - (2) - Bitcoin scalability Today: Reality Check

* Key Metrics
* Maximum throughput. The maximum throughput is the maximum rate at
   which the blockchain can confirm transactions. Today, Bitcoin’s maximum throughput
   is 3.3–7 transactions/sec [1]. This number is constrained by the maximum
   block size and the inter-block time.
* Latency. Time for a transaction to confirm. A transaction is considered con-
   firmed when it is included in a block, roughly 10 minutes in expectation.1
* Bootstrap time. The time it takes a new node to download and process the
   history necessary to validate the current system state. Presently in Bitcoin, the
   bootstrap time is linear in the size of the blockchain history, and is roughly four
   days (averaged over five fresh t2.medium Amazon EC2 nodes that we connected
   to the network running the most recent master software).
* Cost per Confirmed Transaction (CPCT). The cost in USD of resources
  consumed by the entire Bitcoin system to confirm a single transaction. The
  CPCT encompasses several distinct resources, all of which can be further decomposed
  into operational costs (mainly electricity) and capital equipment costs:
  1. Mining: Expended by miners in generating the proof of work for each block.
  2. Transaction validation: The cost of computation necessary to validate that
     a transaction can spend the outputs referenced by its inputs, dominated by
     cryptographic verifications.
  3. Bandwidth: The cost of network resources required to receive and transmit
     transactions, blocks, and metadata.
  4. Storage: The cost (1) of storing all currently spendable transactions, which is
     necessary for miners and full nodes to perform transaction validation, and (2)
     of storing the blockchain’s (much larger) historical data, which is necessary
     to bootstrap new nodes that join the network.
