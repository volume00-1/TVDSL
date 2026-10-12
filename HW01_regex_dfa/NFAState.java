import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.LinkedHashSet;

public final class NFAState {
    public final int id;
    public final Map<Integer, Set<NFAState>> transitions = new LinkedHashMap<>();
    public final Set<NFAState> epsilon = new LinkedHashSet<>();
    
    public String acceptingToken;
    public int acceptingPriority = Integer.MAX_VALUE;

    public NFAState(int id) {
        this.id = id;
    }

    public void addTransition(int symbol, NFAState target) {
        transitions.computeIfAbsent(symbol, ignored -> new LinkedHashSet<>()).add(target);
    }
}
