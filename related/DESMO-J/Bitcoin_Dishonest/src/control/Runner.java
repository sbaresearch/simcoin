package control;

import desmoj.core.simulator.Experiment;
import desmoj.core.simulator.TimeInstant;

import simulator.BitCoinModel;
import tools.CmdLineParser;

import java.io.File;
import java.text.DecimalFormat;
import java.util.LinkedHashMap;
import java.util.concurrent.TimeUnit;

/**
 * Executable convenience class to start a simulation run based on command line switches. 
 * For a list of all command line switches,
 * execute this class with parameter <code>--help</code>.
 */
public class Runner {

    /** The simulation duration. */
    public double simulationDuration = 1000*10*60;  // seconds

    /** The trace duration (starting from 0). */
    public double traceDuration = -1;  // seconds
    
    /** The debug duration (starting from 0). */
    public double debugDuration = -1;  // seconds
    
    /** Batch counter start value. */
    public int batchStart = 1;
    
    /** Batch counter final value. */
    public int batchLast = 1;
    
    /** Replace default see with a new random one each run */
    public boolean randomSeed = false;
       
    /** Output directory. */
    public String outputdir = "experiment_output";
    
    /** Flag to suppress output if desired. */
    public boolean suppressOutput = false;
    
    /** Flag to suppress the progress bar if desired. */
    public boolean suppressProgressbar = true;
    
    /** Flag to suppress trace if desired. */
    public boolean suppressTrace = true;

    /** The main method to start a simulation run. */
    public static void main(String[] args) {
        
        // Just execute the an experiment as specified by the parameters!
        new Runner().execute(args);
    }
    
    /** Executes an experiment */
    public LinkedHashMap<String,Double> execute(String[] args) {
        
        // save start time
        long start = System.currentTimeMillis();
        
        // create model
        BitCoinModel model = getCustomizedModel(args);

        // prepare global data collection
        RunnerDataCollectorGroup dataCollectors = new RunnerDataCollectorGroup();

        new RunnerDataCollector(0.95, dataCollectors, "m", 2, 2); 
        new RunnerDataCollector(0.95, dataCollectors, "ma_c", 2, 2); 
        new RunnerDataCollector(0.95, dataCollectors, "mr_c", 2, 2); 
        new RunnerDataCollector(0.95, dataCollectors, "ma_s", 2, 2); 
        new RunnerDataCollector(0.95, dataCollectors, "mr_s", 2, 2); 
        new RunnerDataCollector(0.95, dataCollectors, "mhs", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "mhsa_c", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "mhsr_c", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "mhsa_s", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "mhsr_s", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "mhp", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "mhpa_c", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "mhpr_c", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "mhpa_s", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "mhpr_s", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "mdp", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "mdpa_c", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "mdpr_c", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "mdpa_s", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "mdpr_s", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "dt", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "dtc", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "dts", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "s", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "sc", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "r", 2, 2); 
        new RunnerDataCollector(0.95, dataCollectors, "rp", 2, 2); 
        new RunnerDataCollector(0.95, dataCollectors, "rc", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "dre", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "dg", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "dsel", 2, 2);
        new RunnerDataCollector(0.95, dataCollectors, "dsem", 2, 2);

                
        if (!model.param_exp_silent) System.out.println("Using " + dataCollectors.size() + " global data collector(s).");

        // batch run
        for (int batchCurrent = batchStart; batchCurrent <= batchLast; batchCurrent++){

            model.param_exp_batch = batchCurrent;
            
            // create experiment
            Experiment experiment = new Experiment(model.getName() + (batchLast > 1 ? "_B"+batchCurrent : ""), 
                    outputdir, TimeUnit.MILLISECONDS, TimeUnit.SECONDS, null,
                    suppressOutput ? null : Experiment.DEFAULT_REPORT_OUTPUT_TYPE, 
                    suppressOutput ? null : Experiment.DEFAULT_TRACE_OUTPUT_TYPE,
                    suppressOutput ? null : Experiment.DEFAULT_ERROR_OUTPUT_TYPE, 
                    suppressOutput ? null : Experiment.DEFAULT_DEBUG_OUTPUT_TYPE);
            
            experiment.setSilent(model.param_exp_silent);
            experiment.setSeedGenerator(randomSeed ? System.currentTimeMillis() * System.nanoTime() :
            	                                     966 + batchCurrent * 13);
            experiment.setShowProgressBar(!suppressProgressbar);

            // link them to each other
            model.connectToExperiment(experiment);
            
            // trace
            if (traceDuration > 0)
                experiment.tracePeriod(new TimeInstant(0.0), new TimeInstant(traceDuration));
            if (debugDuration > 0)
                experiment.debugPeriod(new TimeInstant(0.0), new TimeInstant(debugDuration));
            
            // perform the simulation experiment
            experiment.stop(new TimeInstant(simulationDuration));
            experiment.start();
            
            // report
            model.prepareReport();
            experiment.report();
            
            // read out data 
            for (int i = 0; i < dataCollectors.size(); i++) {
                double statisticValue = -1; 
                
                if(dataCollectors.get(i).getId().equals("m")) statisticValue = model.stat_read_out_minedAll; 
                if(dataCollectors.get(i).getId().equals("mhs")) statisticValue = model.stat_read_out_minedHonestlySingle; 
                if(dataCollectors.get(i).getId().equals("mhp")) statisticValue = model.stat_read_out_minedHonestlyPool; 
                if(dataCollectors.get(i).getId().equals("mdp")) statisticValue = model.stat_read_out_minedDishonestlyPool; 

                if(dataCollectors.get(i).getId().equals("ma_c" ))  statisticValue = model.stat_read_out_minedAllAccepted_common_agreed; 
                if(dataCollectors.get(i).getId().equals("mr_c" ))  statisticValue = model.stat_read_out_minedAllRatio_common_agreed; 	
                if(dataCollectors.get(i).getId().equals("mhsa_c" ))  statisticValue = model.stat_read_out_minedHonestlySingleAccepted_common_agreed; 
                if(dataCollectors.get(i).getId().equals("mhsr_c" ))  statisticValue = model.stat_read_out_minedHonestlySingleRatio_common_agreed; 	 
                if(dataCollectors.get(i).getId().equals("mhpa_c" ))  statisticValue = model.stat_read_out_minedHonestlyPoolAccepted_common_agreed; 
                if(dataCollectors.get(i).getId().equals("mhpr_c" ))  statisticValue = model.stat_read_out_minedHonestlyPoolRatio_common_agreed; 	
                if(dataCollectors.get(i).getId().equals("mdpa_c" ))  statisticValue = model.stat_read_out_minedDishonestlyPoolAccepted_common_agreed; 
                if(dataCollectors.get(i).getId().equals("mdpr_c" ))  statisticValue = model.stat_read_out_minedDishonestlyPoolRatio_common_agreed; 
               
                if(dataCollectors.get(i).getId().equals("ma_s" ))  statisticValue = model.stat_read_out_minedAllAccepted_counting_each_single_appearance; 
                if(dataCollectors.get(i).getId().equals("mr_s" ))  statisticValue = model.stat_read_out_minedAllRatio_counting_each_single_appearance; 	
                if(dataCollectors.get(i).getId().equals("mhsa_s" ))  statisticValue = model.stat_read_out_minedHonestlySingleAccepted_counting_each_single_appearance; 
                if(dataCollectors.get(i).getId().equals("mhsr_s" ))  statisticValue = model.stat_read_out_minedHonestlySingleRatio_counting_each_single_appearance; 	 
                if(dataCollectors.get(i).getId().equals("mhpa_s" ))  statisticValue = model.stat_read_out_minedHonestlyPoolAccepted_counting_each_single_appearance; 
                if(dataCollectors.get(i).getId().equals("mhpr_s" ))  statisticValue = model.stat_read_out_minedHonestlyPoolRatio_counting_each_single_appearance; 	
                if(dataCollectors.get(i).getId().equals("mdpa_s" ))  statisticValue = model.stat_read_out_minedDishonestlyPoolAccepted_counting_each_single_appearance; 
                if(dataCollectors.get(i).getId().equals("mdpr_s" ))  statisticValue = model.stat_read_out_minedDishonestlyPoolRatio_counting_each_single_appearance; 
                                
                if(dataCollectors.get(i).getId().equals("dt" )) statisticValue = model.stat_read_out_dwellTimeAvg; 
                if(dataCollectors.get(i).getId().equals("dtc")) statisticValue = model.stat_read_out_dwellTimeFreq; 
                if(dataCollectors.get(i).getId().equals("dts")) statisticValue = model.stat_read_out_dwellTimeStD; 
                if(dataCollectors.get(i).getId().equals("s"  )) statisticValue = model.stat_read_out_splitsAllAvg; 
                if(dataCollectors.get(i).getId().equals("sc" )) statisticValue = model.stat_read_out_splitsComplAvg; 
                if(dataCollectors.get(i).getId().equals("r"  )) statisticValue = model.stat_read_out_received; 
                if(dataCollectors.get(i).getId().equals("rp" )) statisticValue = model.stat_read_out_receivedPending; 
                if(dataCollectors.get(i).getId().equals("rc" )) statisticValue = model.stat_read_out_receivedConnected;
                if(dataCollectors.get(i).getId().equals("dre" )) statisticValue = model.stat_read_out_dishonestRaceEfficiency;
                if(dataCollectors.get(i).getId().equals("dg" )) statisticValue = model.stat_read_out_dishonestgamma;
                if(dataCollectors.get(i).getId().equals("dsel" )) statisticValue = model.stat_read_out_dishonestSecExtensionAv;
                if(dataCollectors.get(i).getId().equals("dsem" )) statisticValue = model.stat_read_out_dishonestSecExtensionMax;
            
                dataCollectors.get(i).update(statisticValue);
            }
            
            // Finish
            experiment.finish();          
            
            // Create new model for next run
            if (batchCurrent < batchLast) model = getCustomizedModel(args);
        }
        
        // generate LaTeX Table Output
        // dataCollectors.allLaTeXOut();
        
        // get current time
        long end = System.currentTimeMillis();
        long elapsed = (end - start)/1000;
        
        LinkedHashMap<String,Double> results = dataCollectors.getLinkedMapOfMeansAndCIHalfWidths();
        
        if (!model.param_exp_silent) System.out.println("Global data collector results:\n" + results);
        
        if (elapsed > 0) {

            long seconds  = elapsed % 60;
            elapsed /= 60;
            long minutes  = elapsed % 60;
            elapsed /= 60;
            long hours    = elapsed % 60;
            
            DecimalFormat formatter = new DecimalFormat("00");
            if (!model.param_exp_silent) System.out.println("Computation duration (HH:MM:SS) was " + formatter.format(hours) + ":" + formatter.format(minutes) + ":" + formatter.format(seconds));
        }
        
        return results;
    }

    /** Prints out this class' usage. */
    public static String getUsage() {

        return "Parameter Usage: \n"
          + "-b val   or --batch val    set number of batch experiments (default 1)\n"
          + "-d val   or --duration val set simulation duration in seconds (default 600000 = 1000*10*60s)\n"
          + "-e val   or --delthres val set deletion threshold (depth difference that will be purged, default 3)\n"
          + "-f       or --prefetch_forbidden  allow pending block prefetching missing blocks (standard is no prefetch)\n"      	
          + "-g val   or --gamma val    set gamma (likelihood of priority race transmission to a different pool in percent (default 0)\n"
          + "-l val   or --logtrace val set trace log duration in seconds (default disables)\n"
          + "-m s;h;d or --miners s;h;d uses s standard miners and h/d honest/dishonest pools (default 30;10;10)\n"
          + "-n text  or --name tex     set model name (default 'BTCsimexp')\n"
          + "-o text  or --output text  set output directory or 'none' for no output (default 'experiment_output')\n"
          + "-p       or --progress     show progress bar (default not)\n"
          + "-q s;h;d or --penal s;h;d  uses a penalty factor for mininig duration of s/h/d miners (default 1;1;1)\n"
          + "-r       or --random       use random seed based on system time (standard is DESMO-J default seed)\n"
          + "-t val   or --transSt val  set avg standard transmission delay in milliseconds (default 10000ms)\n"
          + "-u val   or --transIn val  set avg inside pool transmission delay in milliseconds (default 10000ms)\n"
          + "-v val   or --transCV val  set coefficient of variaation for transmission as 1/n (default 10)\n"
          + "-y text  or --transDi text set type of transmission delay dist (default 'nor', alternative use 'fixed')\n"
          + "-!       or --silent       supress all output (default output enabled)\n"
          + "-?       or --help         display this list (no simulation execution)\n";
    }

    /** Sets up a customized model as defined by the parameters */
    public BitCoinModel getCustomizedModel(String[] parameters) {
        
        // create the parser
        CmdLineParser parser = new CmdLineParser();
        CmdLineParser.Option batch               = parser.addIntegerOption('b', "batch" );
        CmdLineParser.Option duration            = parser.addDoubleOption ('d', "duration");
        CmdLineParser.Option e                   = parser.addIntegerOption('e', "delthres" );
        CmdLineParser.Option prefetch_forbidden  = parser.addBooleanOption('f', "noprefetch");
        CmdLineParser.Option gamma               = parser.addIntegerOption('g', "gamma" );
        CmdLineParser.Option logtrace            = parser.addDoubleOption ('l', "logtrace");
        CmdLineParser.Option miners              = parser.addStringOption ('m', "miners");
        CmdLineParser.Option name                = parser.addStringOption ('n', "name");
        CmdLineParser.Option output              = parser.addStringOption ('o', "output");
        CmdLineParser.Option progress            = parser.addBooleanOption('p', "progress");
        CmdLineParser.Option penal               = parser.addStringOption ('q', "penal");
        CmdLineParser.Option randomseed          = parser.addBooleanOption('r', "random");
        CmdLineParser.Option silent              = parser.addBooleanOption('!', "silent");
        CmdLineParser.Option transmission_standa = parser.addIntegerOption('t', "transSt" );
        CmdLineParser.Option transmission_inside = parser.addIntegerOption('u', "transIn" );
        CmdLineParser.Option transmission_cv     = parser.addIntegerOption('v', "transCV" );
        CmdLineParser.Option transmission_dist   = parser.addStringOption ('y', "transDi");

        // read the parameters
        try {
          parser.parse(parameters);
        }
        catch (CmdLineParser.OptionException exception) {
          System.err.println("Invalid parameters!");
          System.err.println(exception.getMessage());
          System.err.println();
          System.err.println(getUsage());
          System.exit(0);
        }

        //  store the EXPERIMENT parameters

        simulationDuration = (Double) parser.getOptionValue(duration, simulationDuration);
        traceDuration = (Double) parser.getOptionValue(logtrace, traceDuration);
        batchLast = (Integer) parser.getOptionValue(batch, batchLast);
        if (parser.getOptionValue(progress)  != null)
            suppressProgressbar = false;
        if (parser.getOptionValue(randomseed)  != null)
            randomSeed = true;

        // create and parameterize the MODEL as specified
        
        String name_String = (String) parser.getOptionValue(name, "BTCsimexp");
        
        // put all command line switches into one string to pass to model
        String allComandLineSwitches = "";
        for (int i = 0; i < parameters.length; i++) {
            allComandLineSwitches += parameters[i] + " ";
        }
        BitCoinModel model = new BitCoinModel(name_String, simulationDuration, allComandLineSwitches);
        
        if (parser.getOptionValue(silent)  != null)
            model.param_exp_silent = true;
        model.trace = (traceDuration >= 0);
        model.param_model_gamma = ((Integer) parser.getOptionValue(gamma, 0)) / 100.0;
        model.param_model_blockchain_depthdiff_to_cut
                                = ((Integer) parser.getOptionValue(e, 3));
        model.param_model_avg_transmission_delay_standard   = ((Integer) parser.getOptionValue(transmission_standa, 10000)) / 1000.0;
        model.param_model_avg_transmission_delay_insidepool = ((Integer) parser.getOptionValue(transmission_inside, 10000)) / 1000.0;
        model.param_model_avg_transmission_delay_cv = (Integer) parser.getOptionValue(transmission_cv, 10);
        
        model.param_model_transmissiondelay = (String) parser.getOptionValue(transmission_dist, "nor");
        
        if (parser.getOptionValue(prefetch_forbidden)  != null)
            model.param_model_allow_pending_block_prefetching_missing_blocks = false;
        
        String miners_s = (String) parser.getOptionValue(miners);
        if (miners_s != null) {
        	//System.out.println("Splitting: " + miners_s);
        	String[] miners_parse = miners_s.split(";");
        	model.param_model_number_honest_miners_single         = Integer.parseInt(miners_parse[0]);
        	model.param_model_capaci_honest_miners_honest_pool    = Integer.parseInt(miners_parse[1]);
        	model.param_model_capaci_honest_miners_dishonest_pool = Integer.parseInt(miners_parse[2]);
        	//System.out.println(model.param_model_capaci_honest_miners_dishonest_pool);
        }
        
        String penal_s = (String) parser.getOptionValue(penal);
        if (penal_s != null) {
//        	System.out.println("Splitting: " + penal_s);
        	String[] penal_parse = penal_s.split(";");
        	model.param_model_block_mining_interarrival_duration_factor_honest_sing = Double.parseDouble(penal_parse[0]);
        	model.param_model_block_mining_interarrival_duration_factor_honest      = Double.parseDouble(penal_parse[1]);
        	model.param_model_block_mining_interarrival_duration_factor_dish        = Double.parseDouble(penal_parse[2]);
//        	System.out.println("..result: " + model.param_model_block_mining_interarrival_duration_factor_honest_sing + " / " + 
//        		model.param_model_block_mining_interarrival_duration_factor_honest + " / " + 
//        		model.param_model_block_mining_interarrival_duration_factor_dish);
        	
        }
               
        //  create the output directory, if it does not yet exist
        outputdir = (String) parser.getOptionValue(output, outputdir);
        if (!outputdir.equals("none")) {
            File outputDir = new File(outputdir);
            if (!outputDir.isDirectory()) {
                 outputDir.mkdir();
            }
        } else{
            this.suppressOutput = true;
        }
        
        // return the customized model
        return model;
    }
}