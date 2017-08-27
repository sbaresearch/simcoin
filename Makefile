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
				--verbose

# maxes out notebook and server

demo5:
	cd code; \
		python3 simcoin.py \
			run \
				--node-group-a bitcoin 20 1 0 simcoin/patched:v1 \
				--blocks-per-tick 0.0833333333333333 \
				--amount-of-ticks 75 \
				--txs-per-tick 100 \
				--tick-duration 5 \
				--verbose

install:
	cd code; pip3 install -r requirements.txt
	R -e "install.packages(c('rmarkdown','devtools','jsonlite'), repos='https://cran.wu.ac.at')"

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
