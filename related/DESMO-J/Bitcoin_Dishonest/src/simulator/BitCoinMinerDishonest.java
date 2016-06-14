package simulator;

import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;

import desmoj.core.dist.BoolDistBernoulli;
import desmoj.core.dist.DiscreteDistUniform;
import desmoj.core.simulator.ExternalEvent;
import desmoj.core.simulator.Model;
import desmoj.core.simulator.TimeInstant;
import desmoj.core.simulator.TimeOperations;
import desmoj.core.simulator.TimeSpan;
import desmoj.core.statistic.Accumulate;
import desmoj.core.statistic.BoolStatistic;
import tree.ResultAdd;
import tree.ResultPurge;

public class BitCoinMinerDishonest extends BitCoinMiner {
	
	public static class InternelCommunicationEvent extends ExternalEvent {
		BitCoinMinerDishonest m; BitCoinBlock b;
		public InternelCommunicationEvent(Model owner, String name, 
				BitCoinMinerDishonest m, BitCoinBlock b, boolean showInTrace) {
			super(owner, name, showInTrace);
			this.m = m; this.b = b;
		}
		public void eventRoutine() {m.updateMinedSelfReachtingCenter(b);}
	}
	
	public List<BitCoinBlock> myBlockChainSecretExtension;
	List<BitCoinBlock> myBlocksPublishedUnderRaceCondition;
	BoolStatistic racesWon;
	boolean race;
	boolean publishNextInstantlyDueToPotentialsilentRace;
	BoolDistBernoulli distReachOtherNodesWithPriority;
	DiscreteDistUniform distMinerChoice;
	DiscreteDistUniform distFractionChoice;
	boolean useInternalDelays;
	TimeInstant[] internalMinerActiveAgain;
	double[] subminer_loc_x;
	double[] subminer_loc_y;
	
	public Accumulate myBlockChainSecretExtensionLength;
		
	public BitCoinMinerDishonest(BitCoinModel owner, BitCoinBlock firstBlock, int capacity, long id, double blockInterarrivalPerMiner, double gamma, double avg_transmission_delay_standard, double avg_transmission_delay_internal, boolean showInTrace) {
		super(owner, firstBlock, capacity, id, blockInterarrivalPerMiner, avg_transmission_delay_standard, avg_transmission_delay_internal, BitCoinMiner.Minertype.POOL_DISHONEST, showInTrace);
		//System.out.println("Using Cust with " + param2_publishOnLead2);
		myBlockChainSecretExtension = new LinkedList<BitCoinBlock>();
		myBlockChainSecretExtensionLength = new Accumulate(owner, "BlockChainSecretExtensionLength of " + this, true, false);
		myBlocksPublishedUnderRaceCondition = new LinkedList<BitCoinBlock>();
		race = false;
		publishNextInstantlyDueToPotentialsilentRace = false;
		this.useInternalDelays = (avg_transmission_delay_internal > 0);
		this.distMinerChoice = new DiscreteDistUniform(owner, "Miner choice of "+this.getIdentNumber(), 0, capacity-1, true, false);
		this.distFractionChoice = new DiscreteDistUniform(owner, "Fraction choice of "+this.getIdentNumber(), 1, 10, true, false);
		this.internalMinerActiveAgain = new TimeInstant[capacity];
		this.subminer_loc_x = new double[capacity];
		this.subminer_loc_y = new double[capacity];
		for (int i = 0; i < capacity; i++) {
			this.internalMinerActiveAgain[i] = this.presentTime();
			this.subminer_loc_x[i] = owner.distNodeLocations.sample();
			this.subminer_loc_y[i] = owner.distNodeLocations.sample();
		}
		this.racesWon = new BoolStatistic(owner, "Races won of " + id, true, false);
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
		
		// ignore. miner mined on the wrong leaf
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
		
		if (model.trace) this.sendTraceNote("<b>Dishonest " + this + "</b> found block " + b.printShort());
		myBlockChainSecretExtension.add(b);
		this.myBlockChainSecretExtensionLength.update(myBlockChainSecretExtension.size());

		// no race: keep secret for now and just start over mining on the new block
		if (!race && !publishNextInstantlyDueToPotentialsilentRace && (
		        myBlockChainSecretExtension.size()) < 10) {  // avoid rare case of a really long secret extension
			if (model.trace) this.sendTraceNote("Block is kept secret");
			if (model.trace) this.sendTraceNote("Local block chain:<br/>" + this.myBlockChain.getTreePrintout(true));
			if (model.trace) this.sendTraceNote("Local secret extension: " + this.myBlockChainSecretExtension);
	        
	    // a) race or silent race to end or b) upper bound bound hit: publishing one block     
		} else {
			
			if (model.trace) this.sendTraceNote(race ? "Block is published to end " + (publishNextInstantlyDueToPotentialsilentRace ? "silent " : "") + "race" : "A block is published since lead big enough");
			publishBlocks(1, true, false, -1l, null);
		}
		
		this.currentlyMiningOn = b;
        this.schedule(new EventMiningCompleted(model, 0), this.sampleMiningDuration());
        model.updateSynchronizationStatus(this.currentlyMiningOn.getID());
	}
	
	// return type indicates chain update
	public void updateMinedReceived(BitCoinBlock b, TimeInstant[] senderActiveAgain, boolean racePublication) {
		
		if (model.trace) this.sendTraceNote("<b>Dishonest " + this + "</b> received block " + b.printShort());
		
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
		if (model.trace) this.sendTraceNote("Local secret extension: " + this.myBlockChainSecretExtension);
		
		// Case 1: Fallen behind: Private blocks available but outdated
		// or no private blocks available. 
		// Check for need to switch and a potential race being lost.
		if (this.myBlockChainSecretExtension.isEmpty() || this.currentlyMiningOn.getBlocknumber() < b.getBlocknumber()) {
			
			if (model.trace) this.sendTraceNote("Secret mining has fallen behind");
			
			if (b.getBlocknumber() > this.currentlyMiningOn.getBlocknumber()) {
				
				if (race) {
					this.race = false;		
					this.racesWon.update(false);
				}
				this.publishNextInstantlyDueToPotentialsilentRace = false;
				List<BitCoinBlock> candidates = this.myBlockChain.getDataOnDeepestLeaves();
				
				if (!candidates.contains(this.currentlyMiningOn)) {
					BitCoinBlock nBlock = candidates.get(this.distBlockChoice.sample().intValue() % candidates.size());
					
					// Assume now mining on the new found block
					if (model.trace) this.sendTraceNote("Start over mining");
					this.currentlyMiningOn = nBlock;
			        model.updateSynchronizationStatus(this.currentlyMiningOn.getID());
			        if (!this.isScheduled() && this.distBlockInterarrival != null) 
			        	this.schedule(new EventMiningCompleted(model, 0), this.sampleMiningDuration());
 
				}
			}
		
		// Case 2: Only a single private block which is at the same level as the received one: 
		// Race starts!
		// Publish immediately and hope for the best! Do not change mining.
		} else if (myBlockChainSecretExtension.size() == 1 && 
				myBlockChainSecretExtension.get(0).getBlocknumber() == b.getBlocknumber()){
			
			if (model.trace) this.sendTraceNote("Public and private chains are equal.");
			
				
			if (model.trace) this.sendTraceNote("Publish a local block and race.");
			publishBlocks(1, false, true, b.getMinedByID(), senderActiveAgain);
			race = true;
						
	    // Case 3: Only two private blocks of which the first is at the same level as the received one: 
		// Publish immediately and take over! Do not change mining.
		} else if (myBlockChainSecretExtension.size() == 2 && 
				myBlockChainSecretExtension.get(0).getBlocknumber() == b.getBlocknumber()){
			
			if (model.trace) this.sendTraceNote("Only one block ahead of public chain. Publishing the remaing two blocks.");
			publishBlocks(2, false, false, -1l, null);

		
	    // Case 4: more than two private blocks of which the first is at the same level as the received one: 
		// Only one block needs be published! Do not change mining.
		} else if (myBlockChainSecretExtension.size() == 3 && 
				myBlockChainSecretExtension.get(0).getBlocknumber() == b.getBlocknumber()){
			
			if (model.trace) this.sendTraceNote("Public chain is two blocks behind. Publish 1 block.");
			publishBlocks(1, false, false, -1l, null);
			
	    // Case 4: more than two private blocks of which the first is at the same level as the received one: 
		// Only one block needs be published! Do not change mining.
		} else if (myBlockChainSecretExtension.size() > 3 && 
				myBlockChainSecretExtension.get(0).getBlocknumber() == b.getBlocknumber()){
			
			if (model.trace) this.sendTraceNote("Public chain is more than two blocks behind. Publish 1 block.");
			publishBlocks(1, false, false, -1l, null);
			
		// Other cases: received an outdated block.	
		} else {
			
			// Ignore.
			if (model.trace) this.sendTraceNote("No case appliciable, e.g. block was outdated.");
			
		}
		
		// Race statistics
		if (racePublication) {
			
			//...now mining on the race-published block?
			model.statgamma.update(this.currentlyMiningOn.getID() == b.getID());
		}
	}
	
	private void publishBlocks(int n, boolean justfound, boolean raceBegins, long raceOpponentId, TimeInstant[] raceBeginsSenderActiveAgain) {
		
		// Officially store blocks
		// notes: * no need to update local block count as this is
		//          done in the block's constructor
		//        * no need to check for pending blocks to be added 
		//          since others can't have mined on this new block
		LinkedList<BitCoinBlock> blocks2publish = new LinkedList<BitCoinBlock>();
		for (int i = 0; i < n; i++) {
			if (myBlockChainSecretExtension.isEmpty()) break;
			BitCoinBlock b = myBlockChainSecretExtension.remove(0);
			myBlockChainSecretExtensionLength.update(myBlockChainSecretExtension.size());
			blocks2publish.add(b);
			if (raceBegins) this.myBlocksPublishedUnderRaceCondition.add(b);
			this.updateSplitStats(myBlockChain.add(b, b.getBasedOnID()));
		}		
				
		// Race end?
		if (race && !blocks2publish.isEmpty()) {
			this.race = false;
			this.racesWon.update(true);
		} else if (this.publishNextInstantlyDueToPotentialsilentRace && !blocks2publish.isEmpty()) {
			this.publishNextInstantlyDueToPotentialsilentRace = false;
		}
		
				
		// Purge
		ResultPurge<BitCoinBlock> p = myBlockChain.purge(model.param_model_blockchain_depthdiff_to_cut - 1);
		this.statCountBlockesPurged.update(p.nodesRemoved);
		
		// Send update to others
		for (BitCoinBlock b : blocks2publish) {
			if (model.trace) this.sendTraceNote("Publishing block " + b);
			for (BitCoinMiner m : model.allMiners) {
				if (m.id != this.id) {
					int priority = this.distReachOtherNodesWithPriority.sample() ? 1 : 0;
					TimeSpan transmissionDuration = this.sampleTransmissionDelayStandard(m.loc_x, m.loc_y);
					new EventBlockReceived(model, m, b, Arrays.copyOf(internalMinerActiveAgain, internalMinerActiveAgain.length), priority, raceBegins).schedule(transmissionDuration);
					
//					if (raceBegins && m.id == raceOpponentId) {
//					    TimeInstant arrival = TimeOperations.add(this.presentTime(), transmissionDuration);
//					    for (TimeInstant i : raceBeginsSenderActiveAgain) {
//					        model.statGamma.update(TimeInstant.isBefore(arrival, i));
//					    }
//					}
				}
			}
		}
 	}
}
