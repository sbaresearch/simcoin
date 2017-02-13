package tree;

public class _Test {

	public static void main(String[] args) {
		
		_TestData t1000 = new _TestData(1000);
		_TestData t1100 = new _TestData(1100);
		_TestData t1110 = new _TestData(1110);
		_TestData t1200 = new _TestData(1200);
		_TestData t1210 = new _TestData(1210);
		_TestData t1211 = new _TestData(1211);
		_TestData t1220 = new _TestData(1220);
		_TestData t1300 = new _TestData(1300);
		_TestData t1310 = new _TestData(1310);
		_TestData t1311 = new _TestData(1311);
		_TestData t13111= new _TestData(13111);
		_TestData t13112= new _TestData(13112);
		_TestData t1312 = new _TestData(1312);
		_TestData t1320 = new _TestData(1320);
		_TestData t1400 = new _TestData(1400);
		
		Tree<_TestData> tree = new Tree<_TestData>(t1000);
		
		ResultAdd<_TestData> r;
		
		r = tree.add(t1100, t1000); if (r.split) System.out.println("Split adding 1100");
		r = tree.add(t1110, t1100); if (r.split) System.out.println("Split adding 1110");
		r = tree.add(t1200, t1000); if (r.split) System.out.println("Split adding 1200");
		r = tree.add(t1210, t1200); if (r.split) System.out.println("Split adding 1210");
		r = tree.add(t1211, t1210); if (r.split) System.out.println("Split adding 1211");
		r = tree.add(t1220, t1200); if (r.split) System.out.println("Split adding 1220");
		r = tree.add(t1300, t1000); if (r.split) System.out.println("Split adding 1300");
		r = tree.add(t1310, t1300); if (r.split) System.out.println("Split adding 1310");
		r = tree.add(t1311, t1310); if (r.split) System.out.println("Split adding 1311");
		r = tree.add(t13111,t1311); if (r.split) System.out.println("Split adding 13111");
		r = tree.add(t13112,t1311); if (r.split) System.out.println("Split adding 13112");
		r = tree.add(t1320, t1300); if (r.split) System.out.println("Split adding 1320");
		r = tree.add(t1400, t1000); if (r.split) System.out.println("Split adding 1400");
		r = tree.add(t1312, t1310); if (r.split) System.out.println("Split adding 1312");
		
		System.out.println(tree.getTreePrintout(false));
		System.out.println("Number of nodes? " + tree.countNodes());
		System.out.println("Number of even nodes? " + tree.countNodes(new DataCondition<_TestData>() {
			@Override
			public boolean check(_TestData candidate) {
				return candidate.content % 2 == 0;
			}
		}));
		System.out.println("Is 1110 present? " + tree.contains(t1110));
		
		
		System.out.println("\nPurging...");
		ResultPurge<?> p = tree.purge(0);
		System.out.println("Purged nodes? " + p.nodesRemoved + "\n");
				
		System.out.println(tree.getTreePrintout(false));
		System.out.println("Is 1110 present? " + tree.contains(t1110));
		System.out.println("Number of nodes? " + tree.countNodes());
		System.out.println("Number of even nodes? " + tree.countNodes(new DataCondition<_TestData>() {
			@Override
			public boolean check(_TestData candidate) {
				return candidate.content % 2 == 0;
			}
		}));
		System.out.println("Deepest leaves? " + tree.getDataOnDeepestLeaves());
	}
}
