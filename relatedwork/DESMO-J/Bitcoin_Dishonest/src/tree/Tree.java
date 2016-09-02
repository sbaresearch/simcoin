package tree;

import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;

public class Tree<P extends Identifyable & Printable> {

	Node<P> root;
	public Node<P> firstSplit;
	LinkedList<Node<P>> lastAddedNodes;
	LinkedList<Node<P>> deepestLeaves;
	HashMap<Long,Node<P>> id2node_includingPurged;
	int deepestLeavesLevel;

	int lastAddedNodesCapacity = 5;

	public Tree(P root) {
		this.root = new Node<P>(root, 0, null);
		this.root.parent = this.root; // point to self
		this.id2node_includingPurged = new HashMap<Long,Node<P>>(5000);
		this.id2node_includingPurged.put(root.getID(), this.root);
		this.lastAddedNodes = new LinkedList<Node<P>>();
		this.lastAddedNodes.add(this.root);
		this.deepestLeaves = new LinkedList<Node<P>>();
		this.deepestLeaves.add(this.root);
		this.deepestLeavesLevel = 0;
		this.firstSplit = null;
	}
	
	public int getDepth() {
		return root.getDepthOfSubtree();
	}
	
	public boolean contains_includingPurged(P nData) {
		if (this.id2node_includingPurged.get(nData.getID()) == null)
			return false;
		else
			return true; 
	}
		
	public ResultAdd<P> add(P nData, P parent){
		return this.add(nData, parent.getID());
	}
	
	public ResultAdd<P> add(P nData, long parentId){
		
		long nID = nData.getID();
		Node<P> self_if_already_added = this.id2node_includingPurged.get(nID);
		if (self_if_already_added != null)  
			return new ResultAdd<P>(false, false, false, -1, null, ResultAdd.ReasonForAddFail.ALREADY_PRESENT); 
		Node<P> parent = this.id2node_includingPurged.get(parentId);
		if (parent == null) 
			return new ResultAdd<P>(false, false, false, -1, null, ResultAdd.ReasonForAddFail.PARENT_MISSING);
		if (parent.purged) 
			return new ResultAdd<P>(false, false, false, -1, null, ResultAdd.ReasonForAddFail.PARENT_PURGED);
		ResultAdd<P> result = parent.add(nData, parentId, false, this.hasSplit());		
	
// Old code before map representation existed		
// 		
//		// try direct add to last accessed first
//		if (!result.success) {
//			System.out.println("Strange!");
//			for (Node<P> n : lastAddedNodes) {
//				
//				// No match? Then continue;
//				if (n.getEntryID() != parentId) continue;
//	
//				// Node to add to has been purged -> no need to look at other places, FAIL immediately
//				if (n.purged) return new ResultAdd<P>(false, false, -1, null);
//	
//				// Otherwise, try adding (should be fine)
//				result = n.add(nData, parentId, false);
//				if (result.success) break;
//			}
//		}
//		
//		// try add in the proximity of the last added node
//		if (!result.success) {
//			Node<P> guess = lastAddedNodes.getFirst();
//			for (int moveup = 0; moveup < 10; moveup++) {guess = guess.parent;}
//			result = guess.add(nData, parentId, true);
//		}
//		
//		// if needed, try it the hard tour
//		if (!result.success) {
//			result = root.add(nData, parentId, true);
//		}
			
		// update last added and first split if needed
		if (result.success) {
			this.id2node_includingPurged.put(nData.getID(), result.newnode);
			this.lastAddedNodes.addFirst(result.newnode);
			if (this.lastAddedNodes.size() > lastAddedNodesCapacity) {
				this.lastAddedNodes.removeLast();
			}
			if (result.split) {
				if (this.firstSplit == null || result.newnode.parent.level < this.firstSplit.level) {
					this.firstSplit = result.newnode.parent;
				}
			}
			if (result.level == this.deepestLeavesLevel) {
				this.deepestLeaves.add(result.newnode);
			} else if (result.level > this.deepestLeavesLevel) {
				this.deepestLeaves.clear();
				this.deepestLeaves.add(result.newnode);
				this.deepestLeavesLevel = result.level;
			}
		}
		
		// tell outside world the results
		return result;
	}
	
	public boolean contains(P oData){
		return root.contains(oData);
	}
	
	public ResultPurge<P> purge(int max_tollerated_depthdiff) {
		
		//System.out.println("First split at " + this.firstSplit);
		if (this.firstSplit == null) {
			return new ResultPurge<P>(0, null);
		} else {
			ResultPurge<P> p = firstSplit.purge(max_tollerated_depthdiff, true);
			this.firstSplit = p.firstSplitNode;
			return p;
		}
  	}
	
	public int countNodes() {
		return root.countNodes();
	}
	
	public int countNodes(DataCondition<P> c) {
		return root.countNodes(c);
	}
	
	public String getTreePrintout(boolean html) {
		return root.getTreePrintout("", false, html);
	}
	
	public List<Node<P>> getNodesOfDeepestLeaves(){
		
		List<Node<P>> result = new LinkedList<Node<P>>();
		for (Node<P> n : deepestLeaves) {
			result.add(n);
		} 
		
		return result;
	}
	
	public List<P> getDataOnDeepestLeaves(){
		
		List<P> result = new LinkedList<P>();
		for (Node<P> n : deepestLeaves) {
			result.add(n.data);
		} 
		
		return result;
	}
	
	public List<P> getDataAll(){
		
		List<P> result = new LinkedList<P>();
		List<Node<P>> lastLevel;
		List<Node<P>> currentLevel = new LinkedList<Node<P>>();
		currentLevel.add(root);
		
		do {
			lastLevel = currentLevel;
			currentLevel = new LinkedList<Node<P>>();
			
			for (Node<P> n : lastLevel) {
				result.add(n.data);
				currentLevel.addAll(n.subtree);
			}
		} while (!currentLevel.isEmpty());
		
		return result;
	}
	
	public boolean hasSplit() {
		return this.firstSplit != null;
	}
}
