package control;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.LinkedList;

import tools.Tools;

/**
 * Stores and maintains a set of data collectors (<code>RunnerDataCollector</code>) to be updated 
 * during a batch run.
 */
public class RunnerDataCollectorGroup implements Iterable<RunnerDataCollector>{
    
    /** All data collectors. */
    ArrayList<RunnerDataCollector> allCollectors;    
    
    /** Instantiates a new runner data collector group. */
    public RunnerDataCollectorGroup() {
        this.allCollectors = new ArrayList<RunnerDataCollector>();
    }

    public void add(RunnerDataCollector d) {
        this.allCollectors.add(d);
    }
    
    public RunnerDataCollector get(int i) {
        return this.allCollectors.get(i);
    }
    
    public double[] getArrayOfMeans() {
        double[] result = new double[this.size()];
        for (int i = 0; i < this.size(); i++) {
            result[i] = this.allCollectors.get(i).getMean();
        }
        return result;
    }
    
    public LinkedList<Double> getLinkedListOfMeans() {
        LinkedList<Double> result = new LinkedList<Double>();
        for (RunnerDataCollector c : this.allCollectors) {
            result.add(c.getMean());
        }
        return result;
    }
    
    public LinkedHashMap<String, Double> getLinkedMapOfMeansAndCIHalfWidths() {
        LinkedHashMap<String, Double> result = new LinkedHashMap<String, Double>();
        for (RunnerDataCollector c : this.allCollectors) {
            result.put(c.getId(), c.getMean());
            result.put(c.getId()+"ERR", c.getCIHalfwidth());
        }
        return result;
    }
    
    public int size() {
        return this.allCollectors.size();
    }
    
    /**
     * Writes a LeTeX table representation of all collectors' means and confidence intervals to the console.
     */
    public void allLaTeXOut() {
        
        String output = "";
        
        for (int i = 0; i < allCollectors.size(); i++) {
            
            double mean  = allCollectors.get(i).getMean();
            int    pr_m  = allCollectors.get(i).precisionMean;
            
            double conf_int_half_width = allCollectors.get(i).getCIHalfwidth();
            int    pr_ci = allCollectors.get(i).precisionCI;
            
            String suboutput = "$" + Tools.round(mean, pr_m);
            suboutput += "\\pm" + Tools.round(conf_int_half_width, pr_ci);
            suboutput += "$                ";
            suboutput = suboutput.substring(0, 16);
            
            output += suboutput + " " + (i < allCollectors.size() - 1 ? "& " : "\\\\");
        }
        
        System.out.println(output);
    }

    /* (non-Javadoc)
     * @see java.lang.Iterable#iterator()
     */
    public Iterator<RunnerDataCollector> iterator() {
        return this.allCollectors.iterator();
    }
}
