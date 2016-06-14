package tree;

public abstract class DataCondition<P extends Identifyable & Printable> {
	
	public abstract boolean check(P candidate);

}
