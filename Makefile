all:
	echo "Run the following targets manually install, build-image, test, run"

run:
	cd code; \
		python3 ./simcoin.py run      ;

smoke:
	cd code; \
		python3 ./simcoin.py nodes    ;\
		python3 ./simcoin.py network  ;\
		python3 ./simcoin.py ticks    ;\

simulate:
	cd code; \
		python3 ./simcoin.py simulate ;
report:
	cd code; \
		cp reporter/report.Rmd ../data/last_run/postprocessing/;cd ../data/last_run/postprocessing/;R -e library\(rmarkdown\)\;rmarkdown::render\(\"report.Rmd\",\"pdf_document\"\)\;q\(\);rm report.Rmd

RSCRPT=library\(rmarkdown\)\;rmarkdown::render\(\"multi_report.Rmd\",\"pdf_document\"\)\;q\(\);

multi-report:
	cd code; \
		cp reporter/multi_report.Rmd ../data/last_multi_run/; \
		cd ../data/last_multi_run/; \
		R -e $(RSCRPT)
		rm multi_report.Rmd

demo1:
	cd code; \
		python3 simcoin.py \
			run \
				--group-a bitcoin 3 1 0 simcoin/normal:v3 \
				--amount-of-ticks 1 \
				--txs-per-tick 90 \
				--verbose

demo2:
	cd code; \
		python3 simcoin.py \
			run \
				--group-a bitcoin 50 1 0 simcoin/normal:v3 \
				--amount-of-ticks 100 \
				--txs-per-tick 9 \
				--verbose

demo3:
	cd code; \
		python3 simcoin.py \
			run \
				--group-a bitcoin 2 1 0 simcoin/normal:v3 \
				--amount-of-ticks 100 \
				--txs-per-tick 1 \
				--verbose

demo4:
	cd code; \
		python3 simcoin.py \
			run \
				--group-a bitcoin 2 .6 0 simcoin/patched:v2 \
				--group-b bitcoin 1 .4 0 simcoin/patched:v2 \
				--amount-of-ticks 10 \
				--txs-per-tick 2 \
				--blocks-per-tick 0.7 \
				--system-snapshots-frequency 2 \
				--verbose

# maxes out notebook and server
demo5:
	cd code; \
		python3 simcoin.py \
			run \
				--group-a bitcoin 500 1 0 simcoin/patched:v2 \
				--blocks-per-tick 0.0833333333333333 \
				--amount-of-ticks 5000 \
				--txs-per-tick 100 \
				--tick-duration 3 \
				--verbose
# check startup
demo6:
	cd code; \
		python3 simcoin.py \
			run \
				--group-a bitcoin 100 1 0 simcoin/patched:v2 \
				--blocks-per-tick 0.01 \
				--amount-of-ticks 10 \
				--txs-per-tick 10 \
				--tick-duration 1 \
				--verbose

multidemo1:
	cd code; \
		python3 simcoin.py \
			multi-run \
				--repeat 2 \
				--group-a bitcoin 2 .6 10 simcoin/patched:v2 \
				--group-b bitcoin 1 .4 10 simcoin/patched:v2 \
				--blocks-per-tick 0.9 \
				--amount-of-ticks 7 \
				--txs-per-tick 10 \
				--tick-duration 1 \
				--system-snapshots-frequency 1 \
				--verbose

multidemo2:
	cd code; \
		python3 simcoin.py \
			multi-run \
				--repeat 2 \
				--group-a bitcoin 5 1 10 simcoin/patched:v2 \
				--blocks-per-tick 0.5 \
				--amount-of-ticks 100 \
				--txs-per-tick 2 \
				--tick-duration .3 \
				--verbose

multidemo3:
	cd code; \
		python3 simcoin.py \
			multi-run \
				--repeat 10 \
				--group-a bitcoin 50 1 10 simcoin/patched:v2 \
				--blocks-per-tick 0.05 \
				--amount-of-ticks 200 \
				--txs-per-tick 2 \
				--tick-duration 2 \
				--verbose

multidemo4:
	cd code; \
		python3 simcoin.py \
			multi-run \
				--repeat 1 \
				--group-a bitcoin 100 1 10 simcoin/patched:v2 \
				--blocks-per-tick 0.05 \
				--amount-of-ticks 5 \
				--txs-per-tick 2 \
				--tick-duration 2 \
				--verbose

multidemo5:
	cd code; \
		python3 simcoin.py \
			multi-run \
				--repeat 5 \
				--group-a bitcoin 150 1 10 simcoin/patched:v2 \
				--blocks-per-tick 0.05 \
				--amount-of-ticks 200 \
				--txs-per-tick 2 \
				--tick-duration 1 \
				--verbose

selfdemo1:
	cd code; \
		python3 simcoin.py \
			run \
				--group-a bitcoin 3 .75 0 simcoin/patched:v2 \
				--group-b selfish 1 .25 0 simcoin/proxy:v1 \
				--amount-of-ticks 10 \
				--txs-per-tick 2 \
				--blocks-per-tick 0.7 \
				--system-snapshots-frequency 1 \
				--verbose

selfdemo2:
	cd code; \
		python3 simcoin.py \
			run \
				--group-a bitcoin 3 .75 0 simcoin/patched:v2 \
				--group-b selfish 1 .25 0 simcoin/proxy:v1 \
				--amount-of-ticks 100 \
				--txs-per-tick 2 \
				--blocks-per-tick 0.7 \
				--verbose

install:
	# for kableExtra
	sudo apt install libmagick++-dev
	sudo apt install pandoc
	cd code; pip3 install -r requirements.txt
	R -e "install.packages(c('rmarkdown','devtools','jsonlite','dplyr','anytime', 'kableExtra', 'lattice', 'reshape2'), repos='https://cran.wu.ac.at')"
	# https://stackoverflow.com/questions/20923209/problems-installing-the-devtools-package

build-image:
	cd ./code/docker/normal; \
		docker build --tag simcoin/normal:v3 .

rm-image:
	docker rmi simcoin/normal:v3

build-patched-image : build-base-image
	cd ./code/docker/patched; \
	docker build --no-cache --tag simcoin/patched:v2 .

rm-patched-image:
	docker rmi simcoin/patched:v2

build-base-image:
	cd ./code/docker/base; \
	docker build --tag simcoin/base:v1 .

rm-base-image:
	docker rmi simcoin/base:v1

cp-run:
	rm -r /tmp/run; \
	mkdir /tmp/run; \
	cp -r data/last_run/* /tmp/run/.

cp-multi:
	rm -r /tmp/multi; \
	mkdir /tmp/multi; \
	cp -r data/last_multi_run/* /tmp/multi/.

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
