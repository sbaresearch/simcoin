package tools;

/**
 * Various auxiliary methods.
 */
public class Tools {
       
    /**
     * Rounds a number.
     */
    public static final double round(double value, int digits) {
        
        double shiftedValue = value * Math.pow(10, digits);
        return Math.round(shiftedValue) / Math.pow(10, digits);     
    }
    
    /**
     * Pauses program execution.
     */
    public static final void pause(long millis) {
        try {
            Thread.sleep(millis);
        } catch (Exception e) {}
    }
}
