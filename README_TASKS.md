# Tasks

## Andreas 

* [ ] archive in- and outputs
* [x] check if docker image exists


### CMD params
* [ ] select docker image
* [ ] select what to log (e.g. forkiness)
* [ ] name output file


## Aljosha

### ZFS
* [ ] Configure ZFS volums using (fs)block based dedub (this is almost trivial)
* [ ] Patch Bitcoind to align the persistence of (btc)blocks in the .dat files in the .bitcoin folder with the (fs)blocksize use for dedub.
* [ ] Find a sweet spot of dedub (fs)blocksize and test if it works with Bitcoin
* [ ] Patch Bitcoind to use configurable max (btc)blocksize. This should be easy, it is defined in a macro imho.

