package tree;

import java.util.LinkedList;
import java.util.List;

public class Node<P extends Identifyable & Printable> {
	
	public P data;
	public Node<P> parent;
	public List<Node<P>> subtree;
	int level;
	boolean purged;

	public Node(P data, int level, Node<P> parent) {
		this.level = level;
		this.data = data;
		this.subtree = new LinkedList<Node<P>>();
		this.parent = parent;
		this.purged = false;
	}
	
	public int getLevel(){
		return level;
	}
	
	public long getEntryID(){
		return data.getID();
	}
	
	public String getEntryPrint(){
		return data.print();
	}
	
	public String getEntryPrintShort(){
		return data.printShort();
	}
	
	public int getDepthOfSubtree() {
		int depth = 0;
		for (Node<P> s : subtree) {
			int currentDepth = 1 + s.getDepthOfSubtree();
			depth = Math.max(depth, currentDepth);
		}
		return depth;
	}
	
	public void markPurged() {
		this.purged = true;
		Node<P> currentNode = this;
		while (currentNode.subtree.size() == 1) {             // linear move instead of recursion, if possible
			currentNode = currentNode.subtree.get(0);
			currentNode.purged = true;
		}		
		for (Node<P> s : currentNode.subtree) {
			s.markPurged();
		}
	}
	
	public int countNodes() {
		int count = 1;
		Node<P> currentNode = this;
		while (currentNode.subtree.size() == 1) {             // linear move instead of recursion, if possible
			currentNode = currentNode.subtree.get(0);
			count++;
		}		
		for (Node<P> s : currentNode.subtree) {
			count += s.countNodes();
		}
		return count;
	}
	
	public int countNodes(DataCondition<P> c) {
		int count = c.check(this.data) ? 1 : 0;
		Node<P> currentNode = this;
		while (currentNode.subtree.size() == 1) {             // linear move instead of recursion, if possible
			currentNode = currentNode.subtree.get(0);
			count += c.check(currentNode.data) ? 1 : 0;
		}
		for (Node<P> s : currentNode.subtree) {
			count += s.countNodes(c);
		}
		return count;
	}
		
	protected ResultAdd<P> add(P nData, long parentId, boolean trySubtreesRecursively, boolean alreadyHadSplit){
		if (this.getEntryID() == parentId) {
			boolean split = !this.subtree.isEmpty();
			Node<P> newNode = new Node<P>(nData, level+1, this);
			this.subtree.add(newNode);
			return new ResultAdd<P>(true, split, split && alreadyHadSplit, level+1, newNode, null);
		} else if (trySubtreesRecursively) {
			LinkedList<Node<P>> nodes2do = new LinkedList<Node<P>>(this.subtree);
			while (!nodes2do.isEmpty()) {
				Node<P> s = nodes2do.removeFirst();
				if (s.getEntryID() == parentId) {
					boolean split = !s.subtree.isEmpty();
					Node<P> newNode = new Node<P>(nData, s.level+1, s);
					s.subtree.add(newNode);
					return new ResultAdd<P>(true, split, split && alreadyHadSplit, s.level+1, newNode, null);
				}
				nodes2do.addAll(s.subtree);
			}
			return new ResultAdd<P>(false, false, false, -1, null, ResultAdd.ReasonForAddFail.UNKNOWN);
		} else {
			return new ResultAdd<P>(false, false, false, -1, null, ResultAdd.ReasonForAddFail.UNKNOWN);		
		}
	}
	
	public boolean contains(P oData){
		if (this.getEntryID() == oData.getID()) {
			return true;
		} else {
			for (Node<P> s : subtree) {
				if (s.contains(oData)) {
					return true;
				}
			}
			return false;
		}
	}
	
	public ResultPurge<P> purge(int max_tollerated_depthdiff, boolean recursively) {
		
		if (this.subtree.isEmpty()) return new ResultPurge<P>(0, null);
		int numberPurgedNodes = 0;
		Node<P> firstSplit = null;
		
		// 1. Purge here
		if (this.subtree.size() > 1) {
			//System.out.println("Found a subtree of size " + this.subtree.size());
			int max_depth = getDepthOfSubtree();
			//System.out.println("...max_depth is " + max_depth);
			int min_depth_required = max_depth - max_tollerated_depthdiff;	
			//System.out.println("...to not purge, requiring a depth of " + min_depth_required);
			if (min_depth_required > 0) {
				LinkedList<Node<P>> newsubtree = new LinkedList<Node<P>>();
				
				for (int i = 0; i < this.subtree.size(); i++) {
					
					//System.out.println("...considering tree with root " + this.subtree.get(i).data);
					if (this.subtree.get(i).getDepthOfSubtree() + 1 >= min_depth_required) {
						newsubtree.add(this.subtree.get(i));
						//System.out.println(".......retained, depth is " + this.subtree.get(i).getDepthOfSubtree());
					} else {
						this.subtree.get(i).markPurged();
						numberPurgedNodes += this.subtree.get(i).countNodes();
						//System.out.println(".......purged, depth is " + this.subtree.get(i).getDepthOfSubtree());
					}
				}
				
				this.subtree = newsubtree;
			}
		}
		if (this.subtree.size() > 1) firstSplit = this;

		// 2. Purge recursively
		if (recursively) {
			
			LinkedList<Node<P>> nodes2do = new LinkedList<Node<P>>(this.subtree);
			
			while (!nodes2do.isEmpty()) {
				Node<P> s = nodes2do.removeFirst();
				numberPurgedNodes += s.purge(max_tollerated_depthdiff, false).nodesRemoved;
				nodes2do.addAll(s.subtree);
				if (s.subtree.size() > 1 && firstSplit == null) firstSplit = s;
			}
		}
		return new ResultPurge<P>(numberPurgedNodes, firstSplit);
	}
	
	public String getTreePrintout(String indent, boolean printleveldepth, boolean html) {
		StringBuffer out = new StringBuffer(indent + getEntryPrintShort());
		if (printleveldepth) out.append("[" + this.getLevel() + "|"+ this.getDepthOfSubtree() + "]");
		out.append(html ? "<br/>" : "\n");
		String innerIndent = indent + (html ? "&nbsp;&nbsp;": "  ");
		for (Node<P> s : subtree) {
			out.append(s.getTreePrintout(innerIndent, printleveldepth, html));
		}
		return out.toString();
	}

}
