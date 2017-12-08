all:
	echo "Run the following targets manually install, build-image, test, run"

demo:
	cd code; \
		python3 simcoin.py \
			run \
				--group-a 2 .6 0 simcoin/bitcoin:v2 \
				--group-b 1 .4 0 simcoin/bitcoin:v2 \
				--amount-of-ticks 10 \
				--txs-per-tick 2 \
				--blocks-per-tick 0.7 \
				--system-snapshots-frequency 2 \
				--verbose

multidemo:
	cd code; \
		python3 simcoin.py \
			multi-run \
				--repeat 2 \
				--group-a 2 .6 10 simcoin/bitcoin:v2 \
				--group-b 1 .4 10 simcoin/bitcoin:v2 \
				--blocks-per-tick 0.9 \
				--amount-of-ticks 7 \
				--txs-per-tick 10 \
				--tick-duration 1 \
				--system-snapshots-frequency 1 \
				--verbose

install:
	# for kableExtra
	sudo apt install libmagick++-dev
	sudo apt install pandoc
	cd code; pip3 install -r requirements.txt
	R -e "install.packages(c('rmarkdown','devtools','jsonlite','dplyr','anytime', 'kableExtra', 'lattice', 'reshape2'), repos='https://cran.wu.ac.at')"
	# https://stackoverflow.com/questions/20923209/problems-installing-the-devtools-package

build-image:
	cd ./code/docker; \
	docker build --no-cache --tag simcoin/bitcoin:v2 .

rm-image:
	docker rmi simcoin/bitcoin:v2

cp-run:
	rm -r /tmp/run; \
	mkdir /tmp/run; \
	cp -r data/last_run/* /tmp/run/.

cp-multi:
	rm -r /tmp/run; \
	mkdir /tmp/run; \
	mkdir /tmp/run/postprocessing; \
	cp -r data/last_multi_run/* /tmp/run/postprocessing/.

.PHONY : test
test:
	cd code; \
		python3 \
			-m unittest discover \
			-s tests

.PHONY : clean
clean:
	rm -rf data/*
	docker stop `docker ps --quiet --filter name=simcoin`
