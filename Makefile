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

demo2:
	cd code; \
		python3 simcoin.py \
			run \
				--node-group-a bitcoin 50 1 0 \
				--amount-of-ticks 100 \
				--tx-per-tick 9

install:
	cd code; pip3 install -r requirements.txt

build-image:
	cd ./code/docker/base; \
		docker build --tag btn/base:v3

remove-image:
	docker rmi btn/base:v3

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
