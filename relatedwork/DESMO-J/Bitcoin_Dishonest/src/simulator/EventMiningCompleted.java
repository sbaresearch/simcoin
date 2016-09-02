package simulator;

public class EventMiningCompleted extends desmoj.core.simulator.Event<BitCoinMiner> {
	
	public EventMiningCompleted(BitCoinModel owner, int priority) {
		super(owner, "MiningCompleted", true);
		this.setSchedulingPriority(priority);
	}

	@Override
	public void eventRoutine(BitCoinMiner who) {
		
		//System.out.println("MC@"+this.presentTime());
		
		// Create Block 
		BitCoinBlock b = new BitCoinBlock((BitCoinModel) this.getModel(), who, who.currentlyMiningOn.getBlocknumber()+1, who.currentlyMiningOn);		
		
		// Update local chain
		who.updateMinedSelf(b);
	}
}

