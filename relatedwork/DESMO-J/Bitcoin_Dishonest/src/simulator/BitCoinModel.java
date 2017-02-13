package simulator;

import desmoj.core.dist.ContDist;
import desmoj.core.dist.ContDistUniform;
import desmoj.core.report.ModelReporter;
import desmoj.core.simulator.*;
import desmoj.core.statistic.*;

import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;

public class BitCoinModel extends Model {
    
    /**
     * A reporter about this NetworkModel (general)
     */
    class NetworkModelReporter extends ModelReporter {
        
        public NetworkModelReporter() { super(BitCoinModel.this); }
        
        /* (non-Javadoc)
         * @see desmoj.core.report.ModelReporter#getEntries()
         */
        public String[] getEntries() {
            this.entries[0] = ((Model) this.source).description()
              + " report issued at " + ((Model) this.source).presentTime()
              + ". Last reset at " + this.source.resetAt().toString() + ".<br />";
            this.entries[0] += "Command line switches: "
                     + BitCoinModel.this.commandLineSwitches + "<br />";
          return this.entries;
        }
    }

    /**
     * A reporter about this NetworkModel (performance).
     */
    class NetworkModelPerformanceReporter extends desmoj.core.report.Reporter {
        
        public NetworkModelPerformanceReporter(desmoj.core.simulator.Reportable informationSource) {
            super(informationSource); // make a Reporter
                        
            this.groupHeading = "Network performace data"; this.groupID = 3200; 
            this.numColumns  = 9; 
            this.columns = new String[this.numColumns];
            this.entries = new String[this.numColumns];
            this.columns[0]  = "";
            this.columns[1]  = "All:<br/>Mined / accepted / ratio";
            this.columns[2]  = "Honest single only:<br/> Mined / accepted / ratio";
            this.columns[3]  = "Honest pools only:<br/> Mined / accepted / ratio";
            this.columns[4]  = "Dishonest pools only:<br/> Mined / accepted / ratio";
            this.columns[5]  = "Avg Dwell time";
            this.columns[6]  = "Avg Splits / Complex";
            this.columns[7]  = "All:<br/>Received / connected";
            this.columns[8]  = "Dishonest:<br/>Race efficiency / gamma";

        }
        
        /* (non-Javadoc)
         * @see desmoj.core.report.Reporter#getEntries()
         */
        public String[] getEntries() {
        	
        	this.entries[0] = "<b>Common<br/>All</b>";
        	
        	this.entries[1] // All: Mined / accepted / ratio
                    = BitCoinModel.this.stat_read_out_minedAll + " / "
                    + BitCoinModel.this.stat_read_out_minedAllAccepted_common_agreed + " / "
                    + (BitCoinModel.this.stat_read_out_minedAllAccepted_common_agreed == 0 ? "n/a" :
                         BitCoinModel.this.format_oneAfterDecPoint.format(
                  		 BitCoinModel.this.stat_read_out_minedAllRatio_common_agreed * 100) + "%") + "<br/>" +
                         
                  		BitCoinModel.this.stat_read_out_minedAll + " / "
                        + BitCoinModel.this.stat_read_out_minedAllAccepted_counting_each_single_appearance + " / "
                        + (BitCoinModel.this.stat_read_out_minedAllAccepted_counting_each_single_appearance == 0 ? "n/a" :
                             BitCoinModel.this.format_oneAfterDecPoint.format(
                      		 BitCoinModel.this.stat_read_out_minedAllRatio_counting_each_single_appearance * 100) + "%")   ;
        	
            this.entries[2] // Honest single only: Mined / mined+credited / ratio
                    = BitCoinModel.this.stat_read_out_minedHonestlySingle + " / "
                    + BitCoinModel.this.stat_read_out_minedHonestlySingleAccepted_common_agreed + " / "
                    + (BitCoinModel.this.stat_read_out_minedHonestlySingle == 0 ? "n/a" :
                         BitCoinModel.this.format_oneAfterDecPoint.format(
                  		 BitCoinModel.this.stat_read_out_minedHonestlySingleRatio_common_agreed * 100) + "%") + "<br/>" +
                  		
                  		 BitCoinModel.this.stat_read_out_minedHonestlySingle + " / "
                        + BitCoinModel.this.stat_read_out_minedHonestlySingleAccepted_counting_each_single_appearance + " / "
                        + (BitCoinModel.this.stat_read_out_minedHonestlySingle == 0 ? "n/a" :
                             BitCoinModel.this.format_oneAfterDecPoint.format(
                      		 BitCoinModel.this.stat_read_out_minedHonestlySingleRatio_counting_each_single_appearance * 100) + "%")  ;
            
            this.entries[3] // Honest pools only: Mined / mined+credited / ratio
                    = BitCoinModel.this.stat_read_out_minedHonestlyPool + " / "
                    + BitCoinModel.this.stat_read_out_minedHonestlyPoolAccepted_common_agreed + " / "
                    + (BitCoinModel.this.stat_read_out_minedHonestlyPool == 0 ? "n/a" :
                         BitCoinModel.this.format_oneAfterDecPoint.format(
                  		 BitCoinModel.this.stat_read_out_minedHonestlyPoolRatio_common_agreed * 100) + "%") + "<br/>" +
                         
                  		BitCoinModel.this.stat_read_out_minedHonestlyPool + " / "
                        + BitCoinModel.this.stat_read_out_minedHonestlyPoolAccepted_counting_each_single_appearance + " / "
                        + (BitCoinModel.this.stat_read_out_minedHonestlyPool == 0 ? "n/a" :
                             BitCoinModel.this.format_oneAfterDecPoint.format(
                      		 BitCoinModel.this.stat_read_out_minedHonestlyPoolRatio_counting_each_single_appearance * 100) + "%") ;
            
            this.entries[4] // Dishonest pools only: Mined / mined+credited / ratio
                    = BitCoinModel.this.stat_read_out_minedDishonestlyPool + " / "
                    + BitCoinModel.this.stat_read_out_minedDishonestlyPoolAccepted_common_agreed + " / "
                    + (BitCoinModel.this.stat_read_out_minedDishonestlyPool == 0 ? "n/a" :                    
                         BitCoinModel.this.format_oneAfterDecPoint.format(
                   		 BitCoinModel.this.stat_read_out_minedDishonestlyPoolRatio_common_agreed * 100) + "%") + "<br/>" +
                         
                      BitCoinModel.this.stat_read_out_minedDishonestlyPool + " / "
                              + BitCoinModel.this.stat_read_out_minedDishonestlyPoolAccepted_counting_each_single_appearance + " / "
                              + (BitCoinModel.this.stat_read_out_minedDishonestlyPool == 0 ? "n/a" :                    
                                   BitCoinModel.this.format_oneAfterDecPoint.format(
                             		 BitCoinModel.this.stat_read_out_minedDishonestlyPoolRatio_counting_each_single_appearance * 100) + "%") + "<br/>"            ;

            this.entries[5] = BitCoinModel.this.format_threeAfterDecPoint.format(
            		BitCoinModel.this.stat_read_out_dwellTimeAvg);
        	this.entries[6] // Avg Splits / Complex
                    = BitCoinModel.this.format_threeAfterDecPoint.format(
                     		 BitCoinModel.this.stat_read_out_splitsAllAvg) + " / " +
                         BitCoinModel.this.format_threeAfterDecPoint.format(
                  		 BitCoinModel.this.stat_read_out_splitsComplAvg);
            this.entries[7] = BitCoinModel.this.stat_read_out_received + " / " + BitCoinModel.this.stat_read_out_receivedConnected;
            this.entries[8] = BitCoinModel.this.format_threeAfterDecPoint.format(BitCoinModel.this.stat_read_out_dishonestRaceEfficiency * 100) + "% / "
                            + BitCoinModel.this.format_threeAfterDecPoint.format(BitCoinModel.this.stat_read_out_dishonestgamma * 100)  + "%";
            return this.entries;
        }
    }
    
    /**
     * Helper object to be able to report about the performance of this Model (already a "normal" ModelReporter).
     */
    class NetworkModelPerformanceReportable extends desmoj.core.simulator.Reportable {
        
        public NetworkModelPerformanceReportable() {
            super(BitCoinModel.this, "Performance reporter of " + BitCoinModel.this, true, false);
        }
        
        /* (non-Javadoc)
         * @see desmoj.core.simulator.Reportable#createReporter()
         */
        public desmoj.core.report.Reporter createReporter() {
            return new NetworkModelPerformanceReporter(this);
        }
    }    
    
    /** The command line switches. */
    public String commandLineSwitches;
    
    /** Flag to suppress console output */
    public boolean param_exp_silent = false;
           
    /** Flag to suppress trace generation */
    public boolean trace = false;
    
    /** Current Batch ID */
    public int param_exp_batch = 1;
    
    /** The simulation duration. */
    public double param_exp_simulationDuration;
    
    public int     param_model_number_honest_miners_single = 30;
    public int     param_model_capaci_honest_miners_honest_pool = 10;
    public int     param_model_capaci_honest_miners_dishonest_pool = 10;
    public String  param_model_transmissiondelay = "norw";
    public double  param_model_gamma = 0.0;
    public double  param_model_block_mining_interarrival_duration_standard = 10*60; // seconds
    public double  param_model_block_mining_interarrival_duration_factor_dish        = 1; // seconds
    public double  param_model_block_mining_interarrival_duration_factor_honest      = 1; // seconds
    public double  param_model_block_mining_interarrival_duration_factor_honest_sing = 1; // seconds  
    public int     param_model_blockchain_depthdiff_to_cut = 3;
    public double  param_model_avg_transmission_delay_standard = 10; // seconds
    public double  param_model_avg_transmission_delay_insidepool = 10; // seconds
    public double  param_model_avg_transmission_delay_cv = 10; // in 1/n, i.e. this represents cv = 0.1 
    
    public boolean param_model_allow_pending_block_prefetching_missing_blocks = true; 

    
    /** All minders. */
    public ArrayList<BitCoinMiner> allMiners;
    
    /** Overall blocks mined. */
    public Count statCountBlockesMined;
    public Count statCountBlockesReceived;
    public Count statCountSplitsAll;
    public Count statCountSplitsComplex;
    
    /** OVerall dwell time record */
    public Tally statDwellTime;
    public BoolStatistic statgamma;
    
    /** Format helpers */
    public DecimalFormat format_threeAfterDecPoint;
    public DecimalFormat format_oneAfterDecPoint;
    public DecimalFormat format_nothingAfterDecPoint;
    
    /** Stat read out */
    public long   stat_read_out_minedAll = 0;
    public long   stat_read_out_minedHonestlySingle = 0;
	public long   stat_read_out_minedHonestlyPool = 0;
	public long   stat_read_out_minedDishonestlyPool = 0;
	
	public long   stat_read_out_minedAllAccepted_common_agreed = 0;
    public double stat_read_out_minedAllRatio_common_agreed = 0;
	public long   stat_read_out_minedHonestlySingleAccepted_common_agreed = 0;
	public double stat_read_out_minedHonestlySingleRatio_common_agreed = 0;
	public long   stat_read_out_minedHonestlyPoolAccepted_common_agreed = 0;
	public double stat_read_out_minedHonestlyPoolRatio_common_agreed = 0;
	public long   stat_read_out_minedDishonestlyPoolAccepted_common_agreed = 0;
	public double stat_read_out_minedDishonestlyPoolRatio_common_agreed = 0;
	
    public long   stat_read_out_minedAllAccepted_counting_each_single_appearance = 0;
    public double stat_read_out_minedAllRatio_counting_each_single_appearance = 0;
	public long   stat_read_out_minedHonestlySingleAccepted_counting_each_single_appearance = 0;
	public double stat_read_out_minedHonestlySingleRatio_counting_each_single_appearance = 0;
	public long   stat_read_out_minedHonestlyPoolAccepted_counting_each_single_appearance = 0;
	public double stat_read_out_minedHonestlyPoolRatio_counting_each_single_appearance = 0;
	public long   stat_read_out_minedDishonestlyPoolAccepted_counting_each_single_appearance = 0;
	public double stat_read_out_minedDishonestlyPoolRatio_counting_each_single_appearance = 0;
	
    public long   stat_read_out_received = 0;
    public long   stat_read_out_receivedPending = 0;
    public long   stat_read_out_receivedConnected = 0;
	public double stat_read_out_dwellTimeAvg = 0;
	public long   stat_read_out_dwellTimeFreq = 0;
	public double stat_read_out_dwellTimeStD = 0;
	public double stat_read_out_splitsAllAvg = 0;
	public double stat_read_out_splitsComplAvg = 0;
	public double stat_read_out_dishonestRaceEfficiency = 0;
	public double stat_read_out_dishonestgamma = 0;
	public double stat_read_out_dishonestSecExtensionAv = 0;
	public double stat_read_out_dishonestSecExtensionMax = 0;

	
	/** State */
	boolean stat_synchronizationStatus;
	long stat_synchronizationCommonIdMinedOn;
	TimeInstant stat_synchronizationLastStart;
	
	/** Dists */
	ContDist distNodeLocations;

		
    /**
     * Instantiates a new model.
     */
    public BitCoinModel(String name, double duration, String commandLineSwitches) {
        super(null, name, true, true); 
        this.param_exp_simulationDuration = duration;
        this.commandLineSwitches = commandLineSwitches;
        
        DecimalFormatSymbols mySymbols;
        format_threeAfterDecPoint = new DecimalFormat("#0.000");
        mySymbols  =  format_threeAfterDecPoint.getDecimalFormatSymbols();
        mySymbols.setDecimalSeparator('.');
        format_threeAfterDecPoint.setDecimalFormatSymbols(mySymbols);
        format_oneAfterDecPoint = new DecimalFormat("#0.0");
        mySymbols  =  format_oneAfterDecPoint.getDecimalFormatSymbols();
        mySymbols.setDecimalSeparator('.');
        format_oneAfterDecPoint.setDecimalFormatSymbols(mySymbols);
        format_nothingAfterDecPoint = new DecimalFormat("#0");
    }
    
    /* (non-Javadoc)
     * @see desmoj.core.simulator.Model#init()
     */
    public void init() {
        
    	// Dists
    	this.distNodeLocations = new ContDistUniform(this, "Node locations", 0, 1, false, false);
    	
    	// Model structure
        this.allMiners = new ArrayList<BitCoinMiner>();
        int minerstotal = this.param_model_number_honest_miners_single + 
        		          this.param_model_capaci_honest_miners_honest_pool + 
        		          this.param_model_capaci_honest_miners_dishonest_pool;
                
        // Global data collectors
        this.statCountBlockesMined = new Count(this, "Blocked mined total", true, false, true);
        this.statCountBlockesReceived = new Count(this, "Blocked received total", true, false, true);
        this.statDwellTime = new Tally (this, "Dwell time", true, false);
        this.statCountSplitsAll = new Count(this, "Splits (all)", true, false);
        this.statCountSplitsComplex = new Count(this, "splits (compex)", true, false);
        this.statgamma = new BoolStatistic(this, "gamma", true, false);
          
        // Create first block
        BitCoinBlock firstBlock = new BitCoinBlock(this, null, 0, null);
        
        // Create miners
        double singleMinersBlockInterarrivalDuration_honSing = this.param_model_block_mining_interarrival_duration_factor_honest_sing * this.param_model_block_mining_interarrival_duration_standard * minerstotal;
        double singleMinersBlockInterarrivalDuration_hon     = this.param_model_block_mining_interarrival_duration_factor_honest * this.param_model_block_mining_interarrival_duration_standard * minerstotal;
        double singleMinersBlockInterarrivalDuration_dis     = this.param_model_block_mining_interarrival_duration_factor_dish * this.param_model_block_mining_interarrival_duration_standard * minerstotal;
        
        
        for (long i=0; i<param_model_number_honest_miners_single; i++) {
        	BitCoinMiner m = new BitCoinMinerHonest(this, firstBlock, 1, i, 
        	        singleMinersBlockInterarrivalDuration_honSing, this.param_model_gamma, this.param_model_avg_transmission_delay_standard, -1, true);
        	this.allMiners.add(m);
        }
        
        if (param_model_capaci_honest_miners_honest_pool > 0) {
	    	BitCoinMiner pseudo_dish = new BitCoinMinerHonest(this, firstBlock, param_model_capaci_honest_miners_honest_pool, 42, 
	    	        singleMinersBlockInterarrivalDuration_hon, this.param_model_gamma, this.param_model_avg_transmission_delay_standard, param_model_avg_transmission_delay_insidepool, true);
	    	this.allMiners.add(pseudo_dish);
        }
        
        if (param_model_capaci_honest_miners_dishonest_pool > 0) {
	    	BitCoinMiner dish = new BitCoinMinerDishonest(this, firstBlock, param_model_capaci_honest_miners_dishonest_pool, 541, 
	    	        singleMinersBlockInterarrivalDuration_dis, this.param_model_gamma, this.param_model_avg_transmission_delay_standard, param_model_avg_transmission_delay_insidepool, true);
	    	this.allMiners.add(dish);
        }
        
        // Model reporter
        new NetworkModelPerformanceReportable();
        
        // Synchronization status
    	stat_synchronizationStatus = true;
    	stat_synchronizationLastStart = this.presentTime();
    	stat_synchronizationCommonIdMinedOn = firstBlock.getID();
    }
    
    public void updateSynchronizationStatus(long nowMiningOnBlockId) {
    	
    	// currently sync --> check for end
    	if (this.stat_synchronizationStatus) {
    		if (nowMiningOnBlockId != this.stat_synchronizationCommonIdMinedOn) {
    			this.stat_synchronizationStatus = false;
    			this.statDwellTime.update(this.presentTime().getTimeAsDouble() - this.stat_synchronizationLastStart.getTimeAsDouble());
    			this.stat_synchronizationCommonIdMinedOn = -1;
//    			System.out.println("...at " + this.presentTime() + " syn ends ");
    		}
    		
        // currently off-sync --> check for start
    	} else {
    		
    		boolean sync = true;
    		for (BitCoinMiner b : this.allMiners) {
    			if (b.currentlyMiningOn.getUniqueid()!= nowMiningOnBlockId) {
    				sync = false;
    				break;
    			}
    		}
    		
    		if (sync) {
    	    	stat_synchronizationStatus = true;
    	    	stat_synchronizationLastStart = this.presentTime();
    	    	stat_synchronizationCommonIdMinedOn = nowMiningOnBlockId;
    			//System.out.println("At " + this.presentTime() + " syn starts, all nodes mining on " + nowMiningOnBlockId);
     		}
    	}
    }
    

    /* (non-Javadoc)
     * @see desmoj.core.simulator.Model#doInitialSchedules()
     */
    public void doInitialSchedules() {
        
        for (BitCoinMiner m : this.allMiners) {
        	if (m.distBlockInterarrival != null)
        		m.schedule(new EventMiningCompleted(this, 0), m.sampleMiningDuration());
        }
    }
    
    /* (non-Javadoc)
     * @see desmoj.core.simulator.Model#createDefaultReporter()
     */
    public ModelReporter createDefaultReporter() {
        return new NetworkModelReporter();
    }

    /* (non-Javadoc)
     * @see desmoj.core.simulator.Model#description()
     */
    public String description() {
        return "A discrete event simulation model of bitcoin mining.";
    }
    
    
    public static boolean warningsent = false;

	public void prepareReport() {
		
		Set<BitCoinBlock> blocks_all = new HashSet<BitCoinBlock>();
		Set<BitCoinBlock> blocks_common = new HashSet<BitCoinBlock>();
		Set<BitCoinBlock> racePublishedBlocks = new HashSet<BitCoinBlock>();
		Set<Long> leavesCovered = new HashSet<Long>();
		
		for (int i = 0; i < this.allMiners.size(); i++) {
			BitCoinMiner m =  this.allMiners.get(i);
			if (i == 0) {
				blocks_all.addAll(m.myBlockChain.getDataAll());
				blocks_common.addAll(m.myBlockChain.getDataAll());
				leavesCovered.add(m.currentlyMiningOn.getID());
				//System.out.println("Starting with " + blocks_all.size() + " from node 0");
			} else {
				if (!leavesCovered.contains(m.currentlyMiningOn.getID())) {
					//System.out.println("After node " + i);					
					blocks_all.addAll(m.myBlockChain.getDataAll());
					//System.out.println("- all containes " + blocks_all.size());
					blocks_common.retainAll(m.myBlockChain.getDataAll());
					//System.out.println("- common containes " + blocks_common.size());
					leavesCovered.add(m.currentlyMiningOn.getID());
				}
			}
			switch (m.type) {
			case SINGLE_DEFAULT:
				this.stat_read_out_minedHonestlySingle += m.getNumberBlocksMined();
				break;
			case POOL_HONEST:	
				this.stat_read_out_minedHonestlyPool += m.getNumberBlocksMined();
				break;
			case POOL_DISHONEST:	
				this.stat_read_out_minedDishonestlyPool += m.getNumberBlocksMined();
				racePublishedBlocks.addAll(((BitCoinMinerDishonest) m).myBlocksPublishedUnderRaceCondition);
				
				stat_read_out_dishonestSecExtensionAv += ((BitCoinMinerDishonest) m).myBlockChainSecretExtensionLength.getMean();
				double max = ((BitCoinMinerDishonest) m).myBlockChainSecretExtensionLength.getMaximum();
				if (max > stat_read_out_dishonestSecExtensionMax) stat_read_out_dishonestSecExtensionMax = max; 
				
				break;
			}
			this.stat_read_out_receivedPending += m.myPendingBlocks.size();
		}
	    stat_read_out_received = this.statCountBlockesReceived.getValue();
	    stat_read_out_receivedConnected = stat_read_out_received - stat_read_out_receivedPending;
	
		int raceBlockCountPublished = racePublishedBlocks.size();
		racePublishedBlocks.retainAll(blocks_common);
		int raceBlockCountKept = racePublishedBlocks.size();
		//System.out.println(raceBlockCountKept + " / " + raceBlockCountPublished);
		stat_read_out_dishonestRaceEfficiency = (raceBlockCountPublished == 0 ? 0 : 1.0 * raceBlockCountKept / raceBlockCountPublished);
		stat_read_out_dishonestgamma = this.statgamma.getTrueRatio();
	    
		this.stat_read_out_minedAll = this.statCountBlockesMined.getValue() - 1; // minus one to exclude block 0
		this.stat_read_out_minedAllAccepted_common_agreed = blocks_common.size() - 1; // minus one to exclude block 0
		this.stat_read_out_minedAllAccepted_counting_each_single_appearance = blocks_all.size() - 1; // minus one to exclude block 0
		for (BitCoinBlock b : blocks_common) {
			if (b.getMinedByType() != null) switch (b.getMinedByType()) {
			case SINGLE_DEFAULT:
				this.stat_read_out_minedHonestlySingleAccepted_common_agreed++;
				break;
			case POOL_HONEST:	
				this.stat_read_out_minedHonestlyPoolAccepted_common_agreed++;
				break;
			case POOL_DISHONEST:	
				this.stat_read_out_minedDishonestlyPoolAccepted_common_agreed++;        			
				break;
			}
		}
		for (BitCoinBlock b : blocks_all) {
			if (b.getMinedByType() != null) switch (b.getMinedByType()) {
			case SINGLE_DEFAULT:
				this.stat_read_out_minedHonestlySingleAccepted_counting_each_single_appearance++;
				break;
			case POOL_HONEST:	
				this.stat_read_out_minedHonestlyPoolAccepted_counting_each_single_appearance++;
				break;
			case POOL_DISHONEST:	
				this.stat_read_out_minedDishonestlyPoolAccepted_counting_each_single_appearance++;        			
				break;
			}
		}
	
		this.stat_read_out_minedAllRatio_common_agreed
	  	  = 1.0 * this.stat_read_out_minedAllAccepted_common_agreed / 
	  			  this.stat_read_out_minedAll;
		this.stat_read_out_minedHonestlySingleRatio_common_agreed
		  = 1.0 * this.stat_read_out_minedHonestlySingleAccepted_common_agreed / 
				  this.stat_read_out_minedHonestlySingle;
		this.stat_read_out_minedHonestlyPoolRatio_common_agreed
	      = 1.0 * this.stat_read_out_minedHonestlyPoolAccepted_common_agreed / 
			  this.stat_read_out_minedHonestlyPool;
		this.stat_read_out_minedDishonestlyPoolRatio_common_agreed
	 	  = 1.0 * this.stat_read_out_minedDishonestlyPoolAccepted_common_agreed / 
		    	  this.stat_read_out_minedDishonestlyPool;
		
		this.stat_read_out_minedAllRatio_counting_each_single_appearance
	  	  = 1.0 * this.stat_read_out_minedAllAccepted_counting_each_single_appearance / 
	  			  this.stat_read_out_minedAll;
		this.stat_read_out_minedHonestlySingleRatio_counting_each_single_appearance
		  = 1.0 * this.stat_read_out_minedHonestlySingleAccepted_counting_each_single_appearance / 
				  this.stat_read_out_minedHonestlySingle;
		this.stat_read_out_minedHonestlyPoolRatio_counting_each_single_appearance
	      = 1.0 * this.stat_read_out_minedHonestlyPoolAccepted_counting_each_single_appearance / 
			  this.stat_read_out_minedHonestlyPool;
		this.stat_read_out_minedDishonestlyPoolRatio_counting_each_single_appearance
	 	  = 1.0 * this.stat_read_out_minedDishonestlyPoolAccepted_counting_each_single_appearance / 
		    	  this.stat_read_out_minedDishonestlyPool;
		
		this.stat_read_out_dwellTimeAvg = this.statDwellTime.getMean();
		this.stat_read_out_dwellTimeFreq = this.statDwellTime.getObservations();
		this.stat_read_out_dwellTimeStD = this.statDwellTime.getStdDev();
		
	    int minerstotal = this.param_model_number_honest_miners_single + 
		          this.param_model_capaci_honest_miners_honest_pool + 
		          this.param_model_capaci_honest_miners_dishonest_pool;    	
		this.stat_read_out_splitsAllAvg = 1.0 * this.statCountSplitsAll.getValue() / minerstotal;
		this.stat_read_out_splitsComplAvg = 1.0 * this.statCountSplitsComplex.getValue() / minerstotal;
		
		
	}
}