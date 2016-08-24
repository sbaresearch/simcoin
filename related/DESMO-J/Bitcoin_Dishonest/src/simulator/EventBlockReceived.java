package simulator;

import desmoj.core.simulator.TimeInstant;

public class EventBlockReceived extends desmoj.core.simulator.ExternalEvent {
	
    BitCoinMiner receiver;
	BitCoinBlock blockNew;
	TimeInstant[] senderActiveAgain;
	boolean race;
	
	public EventBlockReceived(BitCoinModel owner, BitCoinMiner receiver, BitCoinBlock blockNew, TimeInstant[] activeAgain, int priority, boolean race) {
		super(owner, "BlockReceived", true);
		this.receiver = receiver;
		this.blockNew = blockNew;
		this.senderActiveAgain = activeAgain;
		this.setSchedulingPriority(priority);
		this.race = race;
	}

	@Override
	public void eventRoutine() {
		
		//System.out.println("BR@"+this.presentTime());
		receiver.statCountBlockesReceived.update();
		receiver.model.statCountBlockesReceived.update();
				
		// Update locally
		receiver.updateMinedReceived(blockNew, senderActiveAgain, race);
	}
}
