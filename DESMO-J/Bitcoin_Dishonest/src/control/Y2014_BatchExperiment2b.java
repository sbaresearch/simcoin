package control;

import java.io.*;
import java.util.LinkedHashMap;

public class Y2014_BatchExperiment2b {

	public static String makecall(int e, int avg_delay) {
		String call = "-b 10 -r -! -o none -m 10;0;0 -t " + Math.max(0, avg_delay) + " -e " + e + " -d 6000000";
		if (avg_delay < 0) call += " -g 100";
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

		BufferedWriter writer = null;

		try {
			writer = new BufferedWriter(new OutputStreamWriter(
					new FileOutputStream("batch_out2b.csv")));

			//java.text.DecimalFormat noAfterDecPoint = new java.text.DecimalFormat("#0");
			//java.text.DecimalFormat oneAfterDecPoint = new java.text.DecimalFormat("#0.0");
			java.text.DecimalFormat threeAfterDecPoint = new java.text.DecimalFormat("#0.000");

			String o =    "delay, m0, ma0, s0, ms0, sc0, dt0, dtc0, dts0, " + 
					             "m1, ma1, s1, ms1, sc1, dt1, dtc1, dts1, " +
				                 "m2, ma2, s2, ms2, sc2, dt2, dtc2, dts2, " +
				               	 "m3, ma3, s3, ms3, sc3, dt3, dtc3, dts3, " +
				                 "time(min)\r\n";
			System.out.print(o);
			writer.write(o); writer.flush();

			for (int delay_set = 0; delay_set <= 58; delay_set++) {
			//for (int delay_set = 58; delay_set >= 0; delay_set--) {
						
				int delay = 0;
				switch (delay_set / 8) {
				case 0: delay = 1; break;
				case 1: delay = 10; break;
				case 2: delay = 100; break;
				case 3: delay = 1000; break;
				case 4: delay = 10000; break;
				case 5: delay = 100000; break;
				}
				delay *= (delay_set % 8)+1;
								
				switch (delay_set) {
				case 48: delay = 12; break;
				case 49: delay = 15; break;
				case 50: delay = 120; break;
				case 51: delay = 150; break;
				case 52: delay = 1200; break;
				case 53: delay = 1500; break;
				case 54: delay = 12000; break;
				case 55: delay = 15000; break;
				case 56: delay = 120000; break;
				case 57: delay = 150000; break;
				case 58: delay = 0; break;
				}				

				String out = delay + ", ";
				long start = System.currentTimeMillis();

				for (int e = 1; e <= 4; e++) {

					String call = makecall(e, delay);
					Runner r = new Runner();

					LinkedHashMap<String, Double> result = r.execute(call.split(" ")); 
					double split = get(result,"s");

					out +=  threeAfterDecPoint.format(get(result,"m")).replace(',','.') + ", " + 	
							threeAfterDecPoint.format(get(result,"ma")).replace(',','.') + ", " + 
							threeAfterDecPoint.format(split).replace(',','.') + ", " + 
							(split < 0.00001 ? " " : threeAfterDecPoint.format(get(result,"ma") / split).replace(',','.'))+ ", " + 
							threeAfterDecPoint.format(get(result,"sc")).replace(',','.') + ", " + 
							threeAfterDecPoint.format(get(result,"dt")).replace(',','.') + ", " +
					        threeAfterDecPoint.format(get(result,"dtc")).replace(',','.') + ", " + 
							threeAfterDecPoint.format(get(result,"dts")).replace(',','.') + ", " ; 
				}
				double minutes = (System.currentTimeMillis() - start) / 1000.0 / 60.0;
				out += threeAfterDecPoint.format(minutes).replace(',','.') + "\r\n";
				System.out.print(out);
				writer.write(out); writer.flush();
			}
		} catch (IOException ex) {
			// report
		} finally {
			try {writer.close();} catch (Exception ex) {}
		}
	}
}
