package tree;

public class _TestData implements Identifyable, Printable {
	
	long content;
	
	public _TestData(long content) {
		this.content = content;
	}

	@Override
	public String print() {
		return content + "";
	}

	@Override
	public String printShort() {
		return print();
	}

	@Override
	public long getID() {
		return content;
	}
	
	@Override
	public String toString() {
		return print();
	}

}
