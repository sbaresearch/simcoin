package simulator;

import java.util.Arrays;
import java.util.List;

import desmoj.core.dist.BoolDistBernoulli;
import desmoj.core.dist.DiscreteDistUniform;
import desmoj.core.simulator.ExternalEvent;
import desmoj.core.simulator.Model;
import desmoj.core.simulator.TimeInstant;
import desmoj.core.simulator.TimeOperations;
import desmoj.core.simulator.TimeSpan;
import tree.ResultAdd;
import tree.ResultPurge;

public class BitCoinMinerHonest extends BitCoinMiner {
	
	public static class InternelCommunicationEvent extends ExternalEvent {
		BitCoinMinerHonest m; BitCoinBlock b;
		public InternelCommunicationEvent(Model owner, String name, 
				BitCoinMinerHonest m, BitCoinBlock b, boolean showInTrace) {
			super(owner, name, showInTrace);
			this.m = m; this.b = b;
		}
		public void eventRoutine() {m.updateMinedSelfReachtingCenter(b);}
	}
	
	BoolDistBernoulli distReachOtherNodesWithPriority;
	DiscreteDistUniform distMinerChoice;
	boolean useInternalDelays;
	TimeInstant[] internalMinerActiveAgain;
	double[] subminer_loc_x;
	double[] subminer_loc_y;
	
	public BitCoinMinerHonest(BitCoinModel owner, BitCoinBlock firstBlock, int capacity, long id, 
	        double blockInterarrivalPerMiner, double gamma, double avg_transmission_delay_standard, double avg_transmission_delay_internal, boolean showInTrace) {
		super(owner, firstBlock, capacity, id, blockInterarrivalPerMiner, avg_transmission_delay_standard, avg_transmission_delay_internal, capacity > 1 ? BitCoinMiner.Minertype.POOL_HONEST : BitCoinMiner.Minertype.SINGLE_DEFAULT, showInTrace);
		//System.out.println("Using Cust with " + param2_publishOnLead2);
        this.useInternalDelays = (avg_transmission_delay_internal > 0);
		this.distMinerChoice = new DiscreteDistUniform(owner, "Miner choice of "+this.getIdentNumber(), 0, capacity-1, true, false);
		this.internalMinerActiveAgain = new TimeInstant[capacity];
		this.subminer_loc_x = new double[capacity];
		this.subminer_loc_y = new double[capacity];
		for (int i = 0; i < capacity; i++) {
			this.internalMinerActiveAgain[i] = this.presentTime();
			this.subminer_loc_x[i] = owner.distNodeLocations.sample();
			this.subminer_loc_y[i] = owner.distNodeLocations.sample();
		}
		this.distReachOtherNodesWithPriority = new BoolDistBernoulli(owner, "distReachOtherNodesWithPriorityOf"+this.getIdentNumber(), gamma, false, false);
	}
	
	
	public void updateMinedSelf(BitCoinBlock b) {
		
		// No internal delays if deactivated
		if (!this.useInternalDelays) {
			updateMinedSelfReachtingCenter(b); // immediately
			return;
		}

		// No internal delay if mined by central node
		int miner = this.distMinerChoice.sample().intValue();
		b.subminer = miner;
		if (miner == 0)  {
			updateMinedSelfReachtingCenter(b); // again immediately
			return;
		}
		
		// ignore miner that mined on the wrong leaf
		if (TimeInstant.isBefore(this.presentTime(), this.internalMinerActiveAgain[miner])) {
			return; 
		}
		
		// Otherwise schedule arrival at central node
		new InternelCommunicationEvent(this.getModel(), "Internal communication at " + this.getIdentNumber(), this, b, false).schedule(this.sampleTransmissionDelayInternal(subminer_loc_x[miner], subminer_loc_y[miner]));
	}
	
	public void updateMinedSelfReachtingCenter(BitCoinBlock b) {
		
		if (useInternalDelays) {
			
			// valid?
			if (b.getBasedOnID() != this.currentlyMiningOn.getID()) return; // ignore
			
			// if valid, spread the word!
			for (int i = 0; i < capacity; i++) {
				if (i == 0 || i == b.subminer) continue; // self and successful subminer are up to date
				this.internalMinerActiveAgain[i] = TimeOperations.add(this.presentTime(), this.sampleTransmissionDelayInternal(subminer_loc_x[i], subminer_loc_y[i]));
			}
		}
		
        if (model.trace) this.sendTraceNote("<b>Honest " + this + "</b> found block " + b.printShort());
        this.updateSplitStats(myBlockChain.add(b, b.getBasedOnID()));

     	publishBlock(b);
		
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
	
	private void publishBlock(BitCoinBlock b) {
		
    	// Purge
    	ResultPurge<BitCoinBlock> p = myBlockChain.purge(model.param_model_blockchain_depthdiff_to_cut - 1);
    	this.statCountBlockesPurged.update(p.nodesRemoved);
    	
    	// Send update to others
		if (model.trace) this.sendTraceNote("Publishing block " + b);
		for (BitCoinMiner m : model.allMiners) {
			if (m.id != this.id) {
				int priority = this.distReachOtherNodesWithPriority.sample() ? 1 : 0;
				TimeSpan transmissionDuration = this.sampleTransmissionDelayStandard(m.loc_x, m.loc_y);
				new EventBlockReceived(model, m, b, Arrays.copyOf(internalMinerActiveAgain, internalMinerActiveAgain.length), priority, false).schedule(transmissionDuration);
			}
		}
 	}
}
