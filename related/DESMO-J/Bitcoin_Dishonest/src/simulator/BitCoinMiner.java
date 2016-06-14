package simulator;

import java.util.*;

import tree.DataCondition;
import tree.ResultAdd;
import tree.Tree;
import desmoj.core.dist.ContDist;
import desmoj.core.dist.ContDistConstant;
import desmoj.core.dist.ContDistExponential;
import desmoj.core.dist.ContDistNormal;
import desmoj.core.dist.DiscreteDistUniform;
import desmoj.core.simulator.TimeInstant;
import desmoj.core.simulator.TimeSpan;
import desmoj.core.statistic.Count;
import desmoj.core.statistic.Tally;

public abstract class BitCoinMiner extends desmoj.core.simulator.Entity {
	
	public enum Minertype {SINGLE_DEFAULT, POOL_HONEST, POOL_DISHONEST};
	
	long id;
	int capacity;
	Minertype type;
	ContDist distBlockInterarrival;
	ContDist distTransmissionDelayStandard;
	ContDist distTransmissionDelayStandardInternal;
	DiscreteDistUniform distBlockChoice;
	
	double loc_x;
	double loc_y;
	
	BitCoinModel model;
	
	public Tree<BitCoinBlock> myBlockChain;
	List<BitCoinBlock> myPendingBlocks;
	
	BitCoinBlock currentlyMiningOn;	
	
    /** Local blocks mined. */
    public Count statCountBlockesMined;
    public Count statCountBlockesReceived;
    public Count statCountBlockesPurged;
    public Count statCountSplitsAll;
    public Count statCountSplitsComplex;
    
    public Tally statTallyTransmissionTime;
    public Tally statTallyTransmissionTimeInternal;
    
    /**
     * A reporter about this BitCoinMiner.
     */
    class BitCoinMinerReporter extends desmoj.core.report.Reporter {
        
        public BitCoinMinerReporter(desmoj.core.simulator.Reportable informationSource) {
            super(informationSource); // make a Reporter
            this.groupHeading = "Miner data"; this.groupID = 3100; 
            this.numColumns  = 11;
            this.columns = new String[this.numColumns];
            this.entries = new String[this.numColumns];
            this.columns[0]  = "Id";
            this.columns[1]  = "Type";
            this.columns[2]  = "Capacity";
            this.columns[3]  = "Blocks mined";
            this.columns[4]  = "...credited locally";
            this.columns[5]  = "Received blocks used";
            this.columns[6]  = "Received blocks pending";
            this.columns[7]  = "Blocks purged";
            this.columns[8]  = "Races / won";
            this.columns[9]  = "Splits / complex";
            this.columns[10]  = "TT ex / int";
            
         }
        
        /* (non-Javadoc)
         * @see desmoj.core.report.Reporter#getEntries()
         */
        public String[] getEntries() {
        	
        	BitCoinMiner m = BitCoinMiner.this;
        	BitCoinMinerDishonest
        	            dm = (m instanceof BitCoinMinerDishonest) ? (BitCoinMinerDishonest) m : null;
        	            
            this.entries[0] // Id
                    = m.id + "";
            this.entries[1] // Type
                    = m.type.toString();     
            this.entries[2] // Capacity
                    = m.capacity + ""; 
            this.entries[3] // Blocks mined
                    = m.getNumberBlocksMined() + "";   
            this.entries[4] // Blocks mined + credited
            		= m.getNumberBlocksMinedCredited() + "";   
            this.entries[5] // Blocks received that were used
                    =Math.max(0, m.statCountBlockesReceived.getValue() - m.myPendingBlocks.size()) + "";   
            this.entries[6] // Blocks received that are pending
                    = m.myPendingBlocks.size() + "";             
            this.entries[7] // Blocks purged
                    = m.statCountBlockesPurged.getValue() + ""; 
            this.entries[8] // "Races / won"
                    = (dm != null) ? 
                    		dm.racesWon.getObservations() + " / " + dm.racesWon.getTrueObs() :
                    			"n/a";   
            this.entries[9] // "Splits / complex"
                    = m.statCountSplitsAll.getValue() + " / " + m.statCountSplitsComplex.getValue();   
            this.entries[10] // "Races / won"
            		= (dm != null) ?
            		  m.statTallyTransmissionTime.getMean() + " / "
                       + ((statTallyTransmissionTimeInternal.getObservations() > 0) ? 
                    		dm.statTallyTransmissionTimeInternal.getMean() 
                    		: "n/a")
                    		:	"n/a";   
                                    		
//            System.out.println("\nBlockchain of " + BitCoinMiner.this.id + " is\n" + BitCoinMiner.this.myBlockChain.getTreePrintout());
//            System.out.println("First spilt: " + BitCoinMiner.this.myBlockChain.firstSplit.data.printShort());
//            System.out.println("Subs: " + BitCoinMiner.this.myBlockChain.firstSplit.subtree.size());
          
            return this.entries;
        }
    }

    /**
     * Helper object to be able to report about this BitCoinMiner (=Schedulable).
     */
    class BitCoinMinerReportable extends desmoj.core.simulator.Reportable {

        public BitCoinMinerReportable() {
            super(BitCoinMiner.this.model, "Reporter of " + BitCoinMiner.this, true, false);
        }
        
        /* (non-Javadoc)
         * @see desmoj.core.simulator.Reportable#createReporter()
         */
        public desmoj.core.report.Reporter createReporter() {
            return new BitCoinMinerReporter(this);
        }
    }

	public BitCoinMiner(BitCoinModel owner, BitCoinBlock firstBlock, int capacity, long id, double blockInterarrivalPerMiner, double avg_transmission_delay_standard, double avg_transmission_delay_internal, Minertype type, boolean showInTrace) {
		super(owner, "Miner"+id, showInTrace);
		this.model = owner;
		this.capacity = capacity;
		this.type = type;
		this.id = id;
		this.loc_x = owner.distNodeLocations.sample();
		this.loc_y = owner.distNodeLocations.sample();
		//System.out.println("Loc of " + this + " is " + loc_x + "/" + loc_y);
		//System.out.println("Arr of " + this + " is " + blockInterarrivalPerMiner);
		this.statTallyTransmissionTimeInternal = new Tally(owner, "Internal Trans.Time at " + this.getIdentNumber(), false, false);
		this.statTallyTransmissionTime = new Tally(owner, "Trans.Time at " + this.getIdentNumber(), false, false);
		myPendingBlocks = new LinkedList<BitCoinBlock>();
		myBlockChain = new Tree<BitCoinBlock>(firstBlock);
        this.statCountBlockesMined = new Count(this.model, "Blockes mined at "+this.getIdentNumber(), true, false);
        this.statCountBlockesReceived = new Count(this.model, "Blockes received at "+this.getIdentNumber(), true, false);
        this.statCountBlockesPurged = new Count(this.model, "Blockes purged at "+this.getIdentNumber(), true, false);
        this.statCountSplitsAll = new Count(this.model, "Splits (all) at "+this.getIdentNumber(), true, false);
        this.statCountSplitsComplex = new Count(this.model, "splits (compex) at "+this.getIdentNumber(), true, false);
        currentlyMiningOn = firstBlock;
        if (blockInterarrivalPerMiner > 0) {
        	this.distBlockInterarrival = new ContDistExponential(owner, "BlockArrivalsOf"+this.getIdentNumber(), blockInterarrivalPerMiner, false, false);
        }
		if (model.param_model_transmissiondelay.equals("fixed")) {
              this.distTransmissionDelayStandard = new ContDistConstant(owner, "TransmissionDelayStandardOf"+this.getIdentNumber(), avg_transmission_delay_standard, false, false);
              this.distTransmissionDelayStandardInternal = new ContDistConstant(owner, "TransmissionDelayInternalOf"+this.getIdentNumber(), avg_transmission_delay_internal, false, false);
	    } else {
		      this.distTransmissionDelayStandard = new ContDistNormal(owner, "TransmissionDelayStandardOf"+this.getIdentNumber(), avg_transmission_delay_standard, avg_transmission_delay_standard / model.param_model_avg_transmission_delay_cv, false, false);
    	      this.distTransmissionDelayStandardInternal = new ContDistNormal(owner, "TransmissionDelayInternalOf"+this.getIdentNumber(), avg_transmission_delay_internal, avg_transmission_delay_internal / model.param_model_avg_transmission_delay_cv, false, false);
		}
		this.distBlockChoice = new DiscreteDistUniform(owner, "BlockChoiceOf"+this.getIdentNumber(), 0, Integer.MAX_VALUE, false, false);
		new BitCoinMinerReportable();
	}
	
	public TimeSpan sampleMiningDuration() {
		TimeSpan sample = new TimeSpan(this.distBlockInterarrival.sample() / this.capacity);
		//System.out.println(sample);
		return sample;
	}
	
	public TimeSpan sampleTransmissionDelayStandard(double to_x, double to_y) {
		double relative_dist = Math.sqrt((to_x - this.loc_x) * (to_x - this.loc_x) + 
				(to_y - this.loc_y) * (to_y - this.loc_y)) 
				/  0.521405; // av. distance of two points in a 1x1 square 
		TimeSpan sample =  new TimeSpan(relative_dist*this.distTransmissionDelayStandard.sample());
		this.statTallyTransmissionTime.update(sample);
		return sample;
	}
	
    public TimeSpan sampleTransmissionDelayInternal(double to_x, double to_y) {
		double relative_dist = Math.sqrt((to_x - this.loc_x) * (to_x - this.loc_x) + 
				(to_y - this.loc_y) * (to_y - this.loc_y)) 
				/  0.521405; // av. distance of two points in a 1x1 square 
        TimeSpan sample =  new TimeSpan(relative_dist*this.distTransmissionDelayStandardInternal.sample());
        this.statTallyTransmissionTimeInternal.update(sample);
        return sample;
    }
	
    public long getNumberBlocksMined() {
    	return this.statCountBlockesMined.getValue();
    }
    
    public long getNumberBlocksMinedCredited() {
    	return this.myBlockChain.countNodes(new DataCondition<BitCoinBlock>() {
			@Override
			public boolean check(BitCoinBlock candidate) {
				return candidate.getMinedByID() == BitCoinMiner.this.id;
			}
		});
    }

	// what to do after a block was mined myself
	public abstract void updateMinedSelf(BitCoinBlock b);
	
	// what to do after a block was received from others
	public abstract void updateMinedReceived(BitCoinBlock b, TimeInstant[] senderActiveAgain, boolean race);
	
	public String toString(){
		return "Miner"+this.id;
	}
	
	public String getTypeAsString(){
		switch (this.type) {
		case POOL_HONEST:
			return "HonestPool";
		case POOL_DISHONEST:
			return "Dishonest";
		case SINGLE_DEFAULT:
			return "Honest";
		default:
				return "Unknown";
		}
	}
	
	public void checkAndAppendPendingBlocks() {
		BitCoinBlock found = null;
		boolean change;
		do {
			change = false;
			int heuristicUpperBound = 100;
			int i = 0;
			for (BitCoinBlock b : myPendingBlocks) {
				boolean success = this.updateSplitStats(myBlockChain.add(b, b.getBasedOnID())).success;
				if (success) {
					found = b;
					break;
				}
				i++;
				if (i >= heuristicUpperBound) break;
			}
			if (found != null) {
				myPendingBlocks.remove(found);
				change = true;
				found = null;
			}
		} while (change);
	}
		
	public ResultAdd<BitCoinBlock> updateSplitStats(ResultAdd<BitCoinBlock> r) {
		
		if (r.split) {
			this.statCountSplitsAll.update();
			model.statCountSplitsAll.update();
			if (r.complexSplit) {
				this.statCountSplitsComplex.update();
				model.statCountSplitsComplex.update();
			}
		}
		
		return r; // used as "builder" on adding 
	}
	
	public long getID() {
		return id;
	}
}
