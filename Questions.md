# Questions that arose during the meetings

# Things in the `debug.log`

## What does the `log2_work` mean?

```
// main.cpp@2718
log(chainActive.Tip()->nChainWork.getdouble())/log(2.0)
```

```
// main.cpp@3210    
pindexNew->nChainWork = (pindexNew->pprev ? pindexNew->pprev->nChainWork : 0) + GetBlockProof(*pindexNew);
```

``` src = 
// chain.cpp@115
arith_uint256 GetBlockProof(const CBlockIndex& block)
{
    arith_uint256 bnTarget;
    bool fNegative;
    bool fOverflow;
    bnTarget.SetCompact(block.nBits, &fNegative, &fOverflow);
    if (fNegative || fOverflow || bnTarget == 0)
        return 0;
    // We need to compute 2**256 / (bnTarget+1), but we can't represent 2**256
    // as it's too large for a arith_uint256. However, as 2**256 is at least as large
    // as bnTarget+1, it is equal to ((2**256 - bnTarget - 1) / (bnTarget+1)) + 1,
    // or ~bnTarget / (nTarget+1) + 1.
    return (~bnTarget / (bnTarget + 1)) + 1;
}
```

```
// arith_uint256.h
/** 256-bit unsigned big integer. */
class arith_uint256 : public base_uint<256> {
public:
    arith_uint256() {}
    arith_uint256(const base_uint<256>& b) : base_uint<256>(b) {}
    arith_uint256(uint64_t b) : base_uint<256>(b) {}
    explicit arith_uint256(const std::string& str) : base_uint<256>(str) {}

    /**
     * The "compact" format is a representation of a whole
     * number N using an unsigned 32bit number similar to a
     * floating point format.
     * The most significant 8 bits are the unsigned exponent of base 256.
     * This exponent can be thought of as "number of bytes of N".
     * The lower 23 bits are the mantissa.
     * Bit number 24 (0x800000) represents the sign of N.
     * N = (-1^sign) * mantissa * 256^(exponent-3)
     *
     * Satoshi's original implementation used BN_bn2mpi() and BN_mpi2bn().
     * MPI uses the most significant bit of the first byte as sign.
     * Thus 0x1234560000 is compact (0x05123456)
     * and  0xc0de000000 is compact (0x0600c0de)
     *
     * Bitcoin only uses this "compact" format for encoding difficulty
     * targets, which are unsigned 256bit quantities.  Thus, all the
     * complexities of the sign bit and using base 256 are probably an
     * implementation accident.
     */
    arith_uint256& SetCompact(uint32_t nCompact, bool *pfNegative = NULL, bool *pfOverflow = NULL);
    uint32_t GetCompact(bool fNegative = false) const;

    friend uint256 ArithToUint256(const arith_uint256 &);
    friend arith_uint256 UintToArith256(const uint256 &);
};
```
What are nbits?

`https://bitcoin.org/en/glossary/nbits`


# Is a block always relayed?

e.g. an old block that forks the chain. It is accepted, but is it relayed?

not during initial download

```
// main.cpp@3028
/**
 * Make the best chain active, in multiple steps. The result is either failure
 * or an activated best chain. pblock is either NULL or a pointer to a block
 * that is already loaded (to avoid loading it again from disk).
 */
bool ActivateBestChain(CValidationState &state, const CChainParams& chainparams, const CBlock *pblock)
...
                        // Limit announcements in case of a huge reorganization.
                        // Rely on the peer's synchronization mechanism in that case.
...
                // Relay inventory, but don't relay old inventory during initial block download.
                int nBlockEstimate = 0;
                if (fCheckpointsEnabled)
                    nBlockEstimate = Checkpoints::GetTotalBlocksEstimate(chainparams.Checkpoints());
                {
                    LOCK(cs_vNodes);
                    BOOST_FOREACH(CNode* pnode, vNodes) {
                        if (nNewHeight > (pnode->nStartingHeight != -1 ? pnode->nStartingHeight - 2000 : nBlockEstimate)) {
                            BOOST_REVERSE_FOREACH(const uint256& hash, vHashes) {
                                pnode->PushBlockHash(hash);
                            }
                        }
                    }
                }
```

```
ProcessGetData
main.cpp(4763)
...
                        // To prevent fingerprinting attacks, only send blocks outside of the active
                        // chain if they are valid, and no more than a month older (both in time, and in
                        // best equivalent proof of work) than the best header chain we know about.
...
                            LogPrintf("%s: ignoring request from peer=%i for old block that isn't in the main chain\n", __func__, pfrom->GetId());

...
                // disconnect node in case we have reached the outbound limit for serving historical blocks
                // never disconnect whitelisted nodes
                static const int nOneWeek = 7 * 24 * 60 * 60; // assume > 1 week = historical
```

# How does a fork look like in the log

# Is a warmup phase necessary?

it's implemented but there is still a fork at block1

# What happens to transactions in a competing block?

# How does the heaviest chain rule work?

it sums up the targets (which changes every 2016 blocks).
In a fork a smaller target value than in the main chain could exist.

# is there a confirmation limit?

# How does the mempool behave?

# What are 'old' transactions? Are they treated differently?

```
// main.cpp(4804)
                            // CMerkleBlock just contains hashes, so also push any transactions in the block the client did not see
                            // This avoids hurting performance by pointlessly requiring a round-trip
                            // Note that there is currently no way for a node to request any single transactions we didn't send here -
                            // they must either disconnect and retry or request the full block.
                            // Thus, the protocol spec specified allows for us to provide duplicate txn here,
                            // however we MUST always provide at least what the remote peer ne

```

# What is the lifecycle of a transaction?

inv -> get -> tx -> mempool -> relay -> block -> rm from mempool -> unspent -> 'old'

# Wisdom of the chain.

* `main.cpp(6374)// Only actively request headers from a single peer, unless we're close to today.`

From the byzantine generals meeting (24.01.2017)
================================================

* Can old Transactions be requested?
* Can a merkle root be requested?
* Can a client run without the full blockchain but with only the UTXO set
* how do checkpoints influnce incoming block vaidation?

