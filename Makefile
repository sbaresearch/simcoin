all:
	cd code; python3 ./runall.py --nodes=120 --blocks=10 --latency=100 --blockTime=1

smoke:
	cd code; \
		python3 ./simcoin.py nodes

install:
	cd code; pip3 install -r requirements.txt

.PHONY : test
test:
	cd code; \
		python3 \
			-m unittest discover \
			-s tests

.PHONY : clean
clean:
	rm -r data/*
