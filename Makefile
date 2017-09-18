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

demo1:
	cd code; \
		python3 simcoin.py \
			run \
				--node-group-a bitcoin 3 1 0 simcoin/normal:v3\
				--amount-of-ticks 1 \
				--tx-per-tick 90 \
				--verbose

demo2:
	cd code; \
		python3 simcoin.py \
			run \
				--node-group-a bitcoin 50 1 0 simcoin/normal:v3\
				--amount-of-ticks 100 \
				--tx-per-tick 9 \
				--verbose

demo3:
	cd code; \
		python3 simcoin.py \
			run \
				--node-group-a bitcoin 2 1 0 simcoin/normal:v3\
				--amount-of-ticks 100 \
				--tx-per-tick 1 \
				--verbose

demo4:
	cd code; \
		python3 simcoin.py \
			run \
				--node-group-a bitcoin 3 1 0 simcoin/patched:v1\
				--amount-of-ticks 10 \
				--tx-per-tick 2 \
				--blocks-per-tick 0.7 \
				--system-snapshots-frequency 1 \
				--verbose

# maxes out notebook and server
demo5:
	cd code; \
		python3 simcoin.py \
			run \
				--node-group-a bitcoin 500 1 0 simcoin/patched:v1 \
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
				--node-group-a bitcoin 100 1 0 simcoin/patched:v1 \
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
				--node-group-a bitcoin 3 1 10 simcoin/patched:v1 \
				--blocks-per-tick 0.5 \
				--amount-of-ticks 5 \
				--txs-per-tick 10 \
				--tick-duration .3 \
				--system-snapshots-frequency 1 \
				--verbose

install:
	# for kableExtra
	sudo apt install libmagick++-dev
	sudo apt install pandoc
	cd code; pip3 install -r requirements.txt
	R -e "install.packages(c('rmarkdown','devtools','jsonlite','dplyr','anytime', 'kableExtra', 'lattice'), repos='https://cran.wu.ac.at')"
	# https://stackoverflow.com/questions/20923209/problems-installing-the-devtools-package

build-image:
	cd ./code/docker/normal; \
		docker build --tag simcoin/normal:v3 .

rm-image:
	docker rmi simcoin/normal:v3

build-patched-image : build-base-image
	cd ./code/docker/patched; \
	docker build --tag simcoin/patched:v1 .

rm-patched-image:
	docker rmi simcoin/patched:v1

build-base-image:
	cd ./code/docker/base; \
	docker build --tag simcoin/base:v1 .

rm-base-image:
	docker rmi simcoin/base:v1

.PHONY : test
test:
	cd code; \
		python3 \
			-m unittest discover \
			-s tests

.PHONY : clean
clean:
	rm -rf data/*
