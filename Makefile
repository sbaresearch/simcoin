all:
	cd code; python3 ./runall.py --nodes=20 --blocks=10 --latency=100 --blockTime=1

smoke:
	cd code; python3 ./runall.py --dryRun=True --nodes=1 --blocks=1

install:
	cd code; pip install -r requirements.txt
