##  Simcoin - A Blockchain Simulation Framework 🏗️
Simcoin facilitates realistic simulations of blockchain networks (currently Bitcoin only). The network is virtualised by the simulation software on one single Unix host machine. To be able to spawn multiple peers the CPU-heavy proof-of-work is deactivated. Blocks and transactions are created by sending respective commands over RPC to the nodes according to a pre-configured simulation scenario.

## Getting started 🏁
Prerequisites: `python3`, `pip3`, `docker`, `make` and `R`. Check if you have them installed.

* `git clone https://github.com/simonmulser/simcoin.git`
* `cd simcoin`
* `make install` (if fails check output, you may need to install other dependencies depending on your OS)
* `make build-image` (consider to use multiple threads to build the image - check Dockerfile under `code/docker`)
* `make demo`
* checkout results under `data/last_run` and the generated report `data/last_run/postprocessing/report.pdf`

## Stack 📚
* [Python 3](https://www.python.org/)
* [Docker](https://www.docker.com/)
* [R Markdown](http://rmarkdown.rstudio.com/)

## Performance 🚀
When running a simulation, monitor the host machine closely. Check utilisation of RAM, CPU, Disk and Network. Further, control the log created by the host system (`dmesg`) as well as the log produced by the simulation framework (`data/debug.log`) and nodes (`data/last_run/node-X/debug.log`). To improve the performance consider the following:
* Increase the ARP-cache if you encounter a neighbour table (ARP-cache) overflow in the kernel messages (`dmesg`).
* Run the whole simulation in RAM by using tmpfs.
* Use a better host machine! 😉

## Outlook/Possible improvements 🔮
* Improving performance and stability by [using Unix domain sockets](https://github.com/bitcoin/bitcoin/pull/9979) for host to peer communication. 
* Sustaining different blockchain projects such as Ethereum or Litecoin.
* Using the [ELK-Stack](https://www.elastic.co/products) to parse, store and analyse the log files.
* Using [Kubernetes](https://kubernetes.io/) to orchestrate containers
