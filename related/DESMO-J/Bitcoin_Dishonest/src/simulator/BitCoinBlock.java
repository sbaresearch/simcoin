package simulator;

import tree.Identifyable;
import tree.Printable;

public class BitCoinBlock implements Identifyable, Printable {
	
	private BitCoinModel model;
	private long uniqueid;
	private BitCoinBlock basedOnBitCoinBlock;
	private long blocknumber;
	private long blocklevel;
	private long minedByMinerId;
	private BitCoinMiner.Minertype minedByMinerType;
	private String minedByString;
	protected int subminer;
	
	public BitCoinBlock(BitCoinModel model, BitCoinMiner minedBy, long blocknumber, BitCoinBlock basedOnBitCoinBlock) {
		
		this.model = model;
		this.blocknumber = blocknumber;
		this.blocklevel = (minedBy == null ? 0 : basedOnBitCoinBlock.blocklevel+1);
		this.minedByMinerId = (minedBy == null ? -1 : minedBy.id);
		this.minedByMinerType = (minedBy == null ? null : minedBy.type);
		this.minedByString = (minedByMinerId == -1 ? "-" : minedByMinerId+"");
		model.statCountBlockesMined.update();
		this.uniqueid = this.model.statCountBlockesMined.getValue();
		//System.out.println("Issuing block uid" + uniqueid + " as mined by " + minedByString);
		this.basedOnBitCoinBlock = basedOnBitCoinBlock;
		if (minedBy != null) {
			minedBy.statCountBlockesMined.update();
		}
	}

	@Override
	public String print() {
		
		return "(By "+minedByString+", No "+blocknumber+", Id "+uniqueid+", Base "+getBasedOnID()+")";
	}
	
	@Override
	public String printShort() {
		return "("+minedByString+","+blocknumber+","+uniqueid+"|"+getBasedOnID()+")";
	}
	
	@Override
	public long getID() {
		return uniqueid;
	}
	
	public long getBasedOnID() {
		return basedOnBitCoinBlock == null ? -1l : basedOnBitCoinBlock.getID();
	}
	
	public BitCoinBlock getBasedOnBlock() {
		return basedOnBitCoinBlock == null ? null : basedOnBitCoinBlock;
	}
	
	
	@Override
	public String toString() {
		return printShort();
	}

	public long getUniqueid() {
		return uniqueid;
	}

	public long getBlocknumber() {
		return blocknumber;
	}
	
	public long getBlocklevel() {
		return blocklevel;
	}

	public long getMinedByID() {
		return minedByMinerId;
	}
	
	public BitCoinMiner.Minertype getMinedByType() {
		return minedByMinerType;
	}
}
