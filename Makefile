all:
	cd code; python3 ./runall.py --nodes=2 --blocks=110

smoke:
	cd code; python3 ./runall.py --dryRun=True --nodes=1 --blocks=1
