package control;

import java.io.*;
import java.util.LinkedHashMap;

public class Y2014_BatchExperiment1 {
	
	public static String makecall(int dishonest_pool_size, int avg_delay, int e, boolean c) {
		String call = "-b 10 -r -! -e " + e + " -o none -m " + (40-dishonest_pool_size) + ";0;" + dishonest_pool_size + " -t " + Math.max(0, avg_delay) + " -d 12000000";
		if (c) 
		    call += " -u " + Math.max(0, avg_delay);
		else
		    call += " -u 0";
		return call;
    }
	
	public static double get(LinkedHashMap<String, Double> result, String key) {
		double r = result.get(key);
		if (Double.isInfinite(r) || Double.isNaN(r)) 
			return 0;
		else 
			return r;
	}
	
    public static void main(String[] args) {
    	
    	int e = 2;
    	boolean c = false;
    	
		for (int i = 0; i < args.length ; i++) {
			if (args[i].startsWith("e")) {
				int value = Integer.parseInt(args[i].substring(1));
				System.out.println("Found e option: " + value); e = value; args[i] = " ";
			}
			if (args[i].startsWith("c")) {
				System.out.println("Found c option"); c = true;
			}
		}
    	
    	BufferedWriter writer = null;

    	try {
    	    writer = new BufferedWriter(new OutputStreamWriter(
    	          new FileOutputStream("batch_out_e " + e + (c ? "_using_c" :"") + ".csv")));
    	
			java.text.DecimalFormat noAfterDecPoint = new java.text.DecimalFormat("#0");
			//java.text.DecimalFormat oneAfterDecPoint = new java.text.DecimalFormat("#0.0");
	        java.text.DecimalFormat threeAfterDecPoint = new java.text.DecimalFormat("#0.000");
	    	
    		String out = "dishon;delay;; m; ma_c; mr_c;; mhs; mhsa_c; mhsr_c;; mdp; mdpa_c; mdpr_c;; mdpr_c/mr_c;; time\r\n";
        	System.out.print(out);
        	writer.write(out); writer.flush();
	    	
        	for (int delay = 0; delay <= 2000; delay += 100) {
        		for (int dishonest_pool_size = 0; dishonest_pool_size <= 20; dishonest_pool_size +=2) {
        			
        			String call = makecall(dishonest_pool_size, delay, e, c);
	        		Runner r = new Runner();
	        		long start = System.currentTimeMillis();
	        		LinkedHashMap<String, Double> result = r.execute(call.split(" ")); 
	        		double minutes = (System.currentTimeMillis() - start) / 1000.0 / 60.0;
	        		
	        		double edge = get(result,"mdpr_c")/get(result,"mr_c");
	        		if (Double.isNaN(edge)) edge = 0;
	        		
	        		out =   dishonest_pool_size + "; " +
	        	    		delay + ";; " + 
	        	    		noAfterDecPoint.format(get(result,"m")) + "; " + 	
	        	    		noAfterDecPoint.format(get(result,"ma_c")) + "; " + 
	        	    		threeAfterDecPoint.format(get(result,"mr")).replace(',','.') + ";; " + 
	        	    		noAfterDecPoint.format(get(result,"mhs")) + "; " + 	
	        	    		noAfterDecPoint.format(get(result,"mhsa_c")) + "; " + 
	        	    		threeAfterDecPoint.format(get(result,"mhsr_c")).replace(',','.') + ";; " + 
//	        	    		noAfterDecPoint.format(get(result,"mhp")) + "; " + 	
//	        	    		noAfterDecPoint.format(get(result,"mhpa_c")) + "; " + 
//	        	    		threeAfterDecPoint.format(get(result,"mhpr_c")).replace(',','.') + ";; " + 
	        	    		noAfterDecPoint.format(get(result,"mdp")) + "; " + 	
	        	    		noAfterDecPoint.format(get(result,"mdpa_c")) + "; " + 
	        	    		threeAfterDecPoint.format(get(result,"mdpr_c")).replace(',','.') + ";; " + 
	        	    		threeAfterDecPoint.format(edge).replace(',','.') + ";; " +
	        	    		threeAfterDecPoint.format(minutes).replace(',','.') + "\r\n";

	        	  System.out.print(out);
	        	  writer.write(out); writer.flush();
	    		        		
	        	}
	    	}
    	} catch (IOException ex) {
      	  // report
      	} finally {
      	   try {writer.close();} catch (Exception ex) {}
      	}
    }
}
