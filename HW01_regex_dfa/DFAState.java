public final class DFAState {
    public final int id;
    public final int[] transitions = new int[NFA.ASCII_SIZE];
    public String acceptingToken;
    public boolean trap;

    public DFAState(int id) {
        this.id = id;
        java.util.Arrays.fill(transitions, -1);
    }
}
