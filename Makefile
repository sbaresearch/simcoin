all:
	cd code; python3 ./runall.py --nodes=120 --blocks=10 --latency=100 --blockTime=1

smoke:
	cd code; \
		python3 ./main.py \
			--tick-duration 10
			# dryRun

install:
	cd code; pip install -r requirements.txt


.PHONY : test
test:
	cd code; \
		python3 \
			-m unittest discover \
			-s tests

.PHONY : clean
clean:
	rm -r data/*