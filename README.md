##  Simcoin - Blockchain Simulation Software 🏗️
Simcoin facilitates simulations of realistic bitcoin networks. The network created by the simulation software is virtualised by the simulation software on one single host machine. To be able to spawn multiple peers the CPU-heavy proof-of-work is deactivated. Blocks and transactions are created by sending respective commands over RPC to the nodes according to a pre-configured simulation scenario.

## Getting started 🏁
Prerequisites: `python3`, `docker`, `make` and `R`. Check if you have them installed.

* `git clone git@github.com:simonmulser/simcoin.git`
* `cd simcoin`
* `make install`
* `make build-image`
* `make test`
* `make run`

## Stack 📚
* [Python 3](https://www.python.org/)
* [Docker](https://www.docker.com/)
* [R Markdown](http://rmarkdown.rstudio.com/)

## Performance 🚀
When running a simulation, monitor the host machine closely. Check utilisation of RAM, CPU, Disk and Network. Further, control the log created by the host system (`dmesg`) and the log produced by the simulation software (`data/debug.log`) and nodes (`data/last_run/node-X/debug.log`). To improve the performance consider the following:
* Increase the ARP-cache if you encounter a neighbour table (ARP-cache) overflow in the kernel messages (`dmesg`).
* Run the whole simulation in RAM by using tmpfs.
* Use a better host machine! 😉

## Outlook/Possible improvements 🔮
* Improving performance and stability by [using Unix domain sockets](https://github.com/bitcoin/bitcoin/pull/9979) for host to peer communication. 
* Sustaining different blockchain projects such as Ethereum or Litecoin.
* Using the [ELK-Stack](https://www.elastic.co/products) to parse, store and analyse the log files.

## Credits 🙏
Ground idea and initial development by Andreas Kern.

&nbsp;

<img src="https://github.com/simonmulser/simcoin/blob/master/graphics/sba_logo.jpg" alt="Image of SBA-Research logo" style="width: 314px;"/>

Developed in collaboration with Aljosha Judmayer and [SBA-Research](https://www.sba-research.org/) in the context of a thesis.

&nbsp;

<img src="https://github.com/simonmulser/simcoin/blob/master/graphics/netidee_logo_scholarship.jpg" alt="Image of netidee logo scholarship" style="width: 330px;"/>

Additional outcome of a thesis sponsored by [Netidee](https://www.netidee.at/) Scholarship 12th Call, year 2017/2018.
