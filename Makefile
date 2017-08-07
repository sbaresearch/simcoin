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
				--tx-per-tick 90

install:
	cd code; pip3 install -r requirements.txt

build-image:
	cd ./code/docker/normal; \
		docker build --tag simcoin/normal:v3 .

remove-image:
	docker rmi simcoin/normal:v3

build-image-patched:
	docker load < ./code/docker/base-manual/base-manual.tar; \
	cd ./code/docker/patched; \
	docker build --tag simcoin/patched .

remove-image-patched:
	docker rmi simcoin/patched

build-base:
	cd ./code/docker/base; \
	docker build --tag simcoin-base .

save-base : build-base
	cd ./code/docker/base; \
	docker save --output base.tar simcoin-base

remove-base:
	docker rmi simcoin-base-manual

.PHONY : test
test:
	cd code; \
		python3 \
			-m unittest discover \
			-s tests

.PHONY : clean
clean:
	rm -rf data/*
	#TODO fix Permission denied
