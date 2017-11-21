# Simcoin - Blockchain Simulation Software
Simcoin facilitates simulations of realistic bitcoin networks. The network created by the simulation software is virtualised by the simulation software on one single host machine. To be able to spawn multiple peers the CPU-heavy proof-of-work is deactivated. Blocks and transactions are created by sending respective commands over RPC to the nodes according to a pre-configured simulation scenario.

## Getting started
* checkout repostiory
* make install
* make build-image
* make test
* make run

## Stack
* [Python 3](https://www.python.org/)
* [Docker](https://www.docker.com/)
* [R Markdown](http://rmarkdown.rstudio.com/)

## Limits
The actual limits of the simulation software depend on the specs of the used host machine and restrictions imposed by the operating system such as a maximum number of connections over the network interface.

At 12/2017 the simulation software was able to simulate the following scenario:
*
*

on a host machine with the specs:
* QEMU Virtual CPU version 2.5+ with 16 CPUs
* Memory 57.718 GB

The utilisation of the CPU (XY%) and Memory (XY%) stayed during the simulation low. The overview of the tick duration shows some bumps and the log of the simulation alerts about failing RPC-calls which needed to be retried to succeed. It seems that, currently the host-to-peer connections over TCP/IP constrains the performance of the simulation software.

## Determinism/Reproducibility
Since the whole simulation is executed in a virtualised environment relying on indeterministic components and behaviours the outcome of multiple executions of the same simulation scenario can vary. Hence, scenarios should be executed multiple times, and if the variance of the results is satisfying, the median values of the metrics should be determined as results. As an expressive metric to compare simulation runs the stale block rate can be used because many configuration paramateres influence the stale rate [gervais2016security](https://eprint.iacr.org/2016/555.pdf).

At 12/2017 the determinism of the simulation software was assesed with the scenario:
* group-a 20 1 25 [bitcoin-0.15.0.1-image](https://github.com/simonmulser/bitcoin/releases/tag/simcoin) (a group containing twenty nodes sharing 100% of the simulated computational power and a latency of 25ms between the peers)
* blocks-per-tick 0.0333333333333333 (in the median every 30th tick a block will be found by a node)
* amount-of-ticks 60480 (ticks is the central time unit used in the simulation software and contains multiple transaction and block events)
* tick-duration .1 (a tich lasts 0.1 seconds)
* txs-per-tick 0 (no transaction are generated in this scenario)
=> reflects 2 weeks of Bitcoin executed in 100.8 minutes (speed up of 200x)

on a host machine with the specs:
* QEMU Virtual CPU version 2.5+ with 16 CPUs
* Memory 57.718 GB

The outcome after 200 simulation was a standard deviation of XY with median XY for the stale block rate.

## Outlook
* Improving performance and stability by [using Unix domain sockets](https://github.com/bitcoin/bitcoin/pull/9979) for host to peer communication. 
* Sustaining different blockchain projects such as Ethereum or Litecoin.
* Using the [ELK-Stack](https://www.elastic.co/products) to parse, store and analyse the log files.
...

## Credits
Ground idea and initial development by Andreas Kern.

Developed in collaboration with Aljosha Judmayer and [SBA-Research](https://www.sba-research.org/).

Sponsored by [Netidee](https://www.netidee.at/).
