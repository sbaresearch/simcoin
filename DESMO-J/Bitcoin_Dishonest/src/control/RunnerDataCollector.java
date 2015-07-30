package control;

/**
 * A data collector to report the mean and confidence intervals of one of the models random variables 
 * determined from multiple batch runs. Confidence interval calculation assumes the random variables 
 * are approximately normally distributed with their means and variances unknown.
 */
public class RunnerDataCollector {
    
    // ****** local attributes ******

    /** The sum of all values so far. */
    private double sum;

    /** The sum of all squared values so far. */
    private double sumSquare;
    
    /** The numer of observations. */
    int observations;
    
    /** The numerical precision of the mean. */
    int precisionMean;

    /** The numerical precision of the confidence intervals. */
    int precisionCI;
    
    /** The confidence level. */
    double confidenceLevel;
    
    /** Unique reference to this data collector */
    String id;

    /** Instantiates a new data collector. */
    public RunnerDataCollector(double confidenceLevel, RunnerDataCollectorGroup mygroup, String id, int precisionM, int precisionCI) {
        
        this.sum = this.sumSquare = 0.0;
        this.observations = 0;
        this.confidenceLevel = confidenceLevel;
        this.precisionMean = precisionM;
        this.precisionCI = precisionCI;
        this.id = id;
        
        mygroup.add(this);
    }

    // ****** methods ******

    /**
     * Returns the mean value of all the values observed so far.
     * 
     * @return double : The mean value of all the values observed so far.
     */
    public double getMean() {
        return sum / this.observations;
    }
    
    public String getId() {
        return id;
    }

    /**
     * Returns the standard deviation of all the values observed so far.
     * 
     * @return double : The standard deviation of all the values observed so
     *         far.
     */
    public double getStdDev() {
        long n = this.observations;

        if (n < 2) {
            return Double.NaN;
        }

        // calculate the standard deviation
        return Math.sqrt(Math.abs(n * sumSquare - sum * sum) / (n * (n - 1)));
    }
    
    
    public double getCIHalfwidth() {
    	
    	org.apache.commons.math.distribution.TDistributionImpl tdis = new org.apache.commons.math.distribution.TDistributionImpl(10);
                    
        long n = this.observations;
        double s_dev = getStdDev();
        double alpha = 1 - confidenceLevel;
        
        double conf_int_half_width = -1;
               
        try {
            tdis.setDegreesOfFreedom(n - 1);
            double t = tdis.inverseCumulativeProbability(1-alpha/2);
            conf_int_half_width = s_dev / Math.sqrt(n) * t;
        } catch (org.apache.commons.math.MathException e) {
        } catch (java.lang.IllegalArgumentException e) {
        }
        
        return conf_int_half_width;
    }
    

    /**
     * Discards all observations.
     */
    public void reset() {

        this.sum = this.sumSquare = 0.0;
        this.observations = 0;
    }

    /**
     * Supplies an observation.
     */
    public void update(double val) {
        this.sum += val;
        this.sumSquare += val * val;
        this.observations++;
    }
}
