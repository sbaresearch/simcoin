package tree;

public class ResultPurge<P extends Identifyable & Printable> {
	
	public ResultPurge(int nodesRemoved, Node<P> firstSplitNode) {
		this.nodesRemoved = nodesRemoved;
		this.firstSplitNode = firstSplitNode;
	}
	
	public int nodesRemoved;
	public Node<P> firstSplitNode;
}