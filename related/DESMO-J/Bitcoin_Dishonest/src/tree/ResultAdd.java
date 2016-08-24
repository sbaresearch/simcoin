package tree;

public class ResultAdd<P extends Identifyable & Printable> {
	
	enum ReasonForAddFail {ALREADY_PRESENT, PARENT_MISSING, PARENT_PURGED, UNKNOWN};
	
	public ResultAdd(boolean success, boolean split, boolean complexSplit, int level, Node<P> newnode, ReasonForAddFail reason) {
		this.success = success;
		this.split = split;
		this.complexSplit = complexSplit;
		this.level = level;
		this.newnode = newnode;
		this.reason = reason;
	}
	
	public boolean success;
	public boolean split;
	public boolean complexSplit;
	public int level;
	public Node<P> newnode;
	public ReasonForAddFail reason;
}