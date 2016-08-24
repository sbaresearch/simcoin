package simulator;

import java.util.List;

import desmoj.core.simulator.TimeInstant;
import tree.ResultAdd;
import tree.ResultPurge;

public class BitCoinMinerHonestSimpleSingle extends BitCoinMiner {
	
	public BitCoinMinerHonestSimpleSingle(BitCoinModel owner, BitCoinBlock firstBlock, int capacity, long id, double blockInterarrivalPerMiner, double avg_transmission_delay, boolean showInTrace) {
		super(owner, firstBlock, capacity, id, blockInterarrivalPerMiner, avg_transmission_delay, -1, capacity > 1 ? BitCoinMiner.Minertype.POOL_HONEST : BitCoinMiner.Minertype.SINGLE_DEFAULT, showInTrace);
	}
	
	public void updateMinedSelf(BitCoinBlock b) {
		
		if (model.trace) this.sendTraceNote("<b>Honest " + this + "</b> found block " + b.printShort());
		
		// Store block
		// notes: * no need to update local block count as this is
		//          done in the block's constructor
		//        * no need to check for pending blocks to be added 
		//          since others can't have mined on this new block
		this.updateSplitStats(myBlockChain.add(b, b.getBasedOnID()));

		if (model.trace) this.sendTraceNote("Block is published");
		
		// Purge
		ResultPurge<BitCoinBlock> p = myBlockChain.purge(model.param_model_blockchain_depthdiff_to_cut - 1);
		this.statCountBlockesPurged.update(p.nodesRemoved);
		if (model.trace) this.sendTraceNote("Local block chain:<br/>" + this.myBlockChain.getTreePrintout(true));

		// Send update to others
		for (BitCoinMiner m : model.allMiners) {
			if (m.id != this.id) {
				int priority = (m.type == Minertype.POOL_DISHONEST) ? 1 : 0; // these have a better connection
				new EventBlockReceived(model, m, b, new TimeInstant[]{this.presentTime()}, priority, false).schedule(this.sampleTransmissionDelayStandard(m.loc_x, m.loc_y));
			}
		}
				
		// Start over mining on the new found block
		this.currentlyMiningOn = b;
        this.schedule(new EventMiningCompleted(model, 0), this.sampleMiningDuration());
        model.updateSynchronizationStatus(this.currentlyMiningOn.getID());
	}
	
	// return type indicates chain update
	public void updateMinedReceived(BitCoinBlock b, TimeInstant[] senderActiveAgain, boolean racePublication) {
		
		if (model.trace) this.sendTraceNote("<b>Honest " + this + "</b> received block " + b.printShort());
		
		if (myBlockChain.contains_includingPurged(b)) {
			
			if (model.trace) this.sendTraceNote("Ignored since already received");
			
		} else {
		
			// Store block
			ResultAdd<BitCoinBlock> r = this.updateSplitStats(myBlockChain.add(b, b.getBasedOnID()));
			
			// If addition to chain is not successful, save the block for potential future addition	
			if (!r.success) {
				
				if (model.trace) this.sendTraceNote("Could not be appended. Marked as pending.");
				this.myPendingBlocks.add(0, b);
				
				// Tony's trick: immediately pre-fetch missing blocks, if possible
				BitCoinBlock p = b.getBasedOnBlock();
				while (model.param_model_allow_pending_block_prefetching_missing_blocks && p != null && !myBlockChain.contains_includingPurged(p) && !this.myPendingBlocks.contains(p)) {
					this.myPendingBlocks.add(0, p);
					p = p.getBasedOnBlock(); // move up
				}
			}
			
	        // Check pending
	        checkAndAppendPendingBlocks();	        
		}

		// Purge 
		ResultPurge<BitCoinBlock> p = myBlockChain.purge(model.param_model_blockchain_depthdiff_to_cut - 1);
		this.statCountBlockesPurged.update(p.nodesRemoved);
		if (model.trace) this.sendTraceNote("Local block chain:<br/>" + this.myBlockChain.getTreePrintout(true));
				
		// Re-Decide where to mine from now on 
		List<BitCoinBlock> candidates = this.myBlockChain.getDataOnDeepestLeaves();
		
		if (!candidates.contains(this.currentlyMiningOn)) {
			BitCoinBlock nBlock = candidates.get(this.distBlockChoice.sample().intValue() % candidates.size());
			
			// Assume now mining on the new found block
			this.currentlyMiningOn = nBlock;
	        model.updateSynchronizationStatus(this.currentlyMiningOn.getID());
		}
				
		// Race statistics
		if (racePublication) {
			
			//...now mining on the race-published block?
			model.statgamma.update(this.currentlyMiningOn.getID() == b.getID());
		}
	}
}
