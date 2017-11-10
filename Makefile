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

demo:
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

multidemo:
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

evaluate:
	cd code; \
		python3 simcoin.py \
			multi-run \
				--repeat 100 \
				--group-a bitcoin 20 1 25 simcoin/patched:v2 \
				--blocks-per-tick 0.0333333333333333 \
				--amount-of-ticks 60480 \
				--txs-per-tick 0 \
				--tick-duration .1 \
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
