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
				--node-group-a bitcoin 3 1 0 \
				--amount-of-ticks 1 \
				--tx-per-tick 90

install:
	cd code; pip3 install -r requirements.txt

build-image:
	cd ./code/docker/base; \
		docker build --tag simcoin/base:v3 .

remove-image:
	docker rmi simcoin/base:v3

build-image-patched:
	docker load < ./code/docker/base-manual/base-manual.tar; \
	cd ./code/docker/patched; \
	docker build --tag simcoin/patched .

remove-image-patched:
	docker rmi simcoin/patched

build-base-manual:
	cd ./code/docker/base-manual; \
	docker build --tag simcoin-base-manual .

save-base-manual : build-base-manual
	cd ./code/docker/base-manual; \
	docker save --output base-manual.tar simcoin-base-manual

remove-base-manual:
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
