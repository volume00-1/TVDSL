import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class DFA {
    public final List<DFAState> states;
    public final int startState;
    public final int trapState;
    public final List<Token> tokens;

    private DFA(List<DFAState> states, int startState, int trapState, List<Token> tokens) {
        this.states = states; 
        this.startState = startState; 
        this.trapState = trapState; 
        this.tokens = tokens;
    }

    public static DFA build(NFA nfa, List<Token> tokens) {
        List<DFAState> result = new ArrayList<>();
        Map<Set<Integer>, Integer> ids = new HashMap<>();
        List<Set<NFAState>> subsets = new ArrayList<>();
        
        Set<NFAState> initialNfa = nfa.epsilonClosure(java.util.Collections.singleton(nfa.start));
        Set<Integer> initial = idsOf(initialNfa);
        
        ids.put(initial, 0); 
        subsets.add(initialNfa); 
        result.add(new DFAState(0));
        
        for (int index = 0; index < subsets.size(); index++) {
            Set<NFAState> subset = subsets.get(index);
            DFAState state = result.get(index);
            state.acceptingToken = acceptingToken(subset);
            
            for (int symbol = 0; symbol < NFA.ASCII_SIZE; symbol++) {
                Set<NFAState> moved = new HashSet<>();
                for (NFAState source : subset) {
                    for (NFAState target : source.transitions.getOrDefault(symbol, java.util.Collections.emptySet())) {
                        moved.add(target);
                    }
                }
                if (moved.isEmpty()) continue;
                
                // Calculate epsilon-closure for the new set of states
                Set<NFAState> closure = nfa.epsilonClosure(moved);
                Set<Integer> key = idsOf(closure);
                Integer target = ids.get(key);
                
                if (target == null) { 
                    target = result.size(); 
                    ids.put(key, target); 
                    subsets.add(closure); 
                    result.add(new DFAState(target)); 
                }
                state.transitions[symbol] = target;
            }
        }
        
        int trap = result.size();
        DFAState trapState = new DFAState(trap); 
        trapState.trap = true;
        Arrays.fill(trapState.transitions, trap); 
        result.add(trapState);
        
        for (DFAState state : result) {
            for (int symbol = 0; symbol < NFA.ASCII_SIZE; symbol++) {
                if (state.transitions[symbol] < 0) state.transitions[symbol] = trap;
            }
        }
        
        return new DFA(result, 0, trap, tokens);
    }

    private static Set<Integer> idsOf(Set<NFAState> states) {
        Set<Integer> result = new HashSet<>(); 
        for (NFAState state : states) result.add(state.id); 
        return result;
    }

    private static String acceptingToken(Set<NFAState> states) {
        String token = null; 
        int priority = Integer.MAX_VALUE;
        for (NFAState state : states) {
            if (state.acceptingToken != null && state.acceptingPriority < priority) { 
                token = state.acceptingToken; 
                priority = state.acceptingPriority; 
            }
        }
        return token;
    }

    public DFA minimizeHopcroft() {
        List<Set<Integer>> partitions = new ArrayList<>();
        Map<String, Set<Integer>> acceptingGroups = new HashMap<>();
        Set<Integer> nonAccepting = new HashSet<>();
        
        for (DFAState state : states) {
            if (state.acceptingToken == null) nonAccepting.add(state.id);
            else acceptingGroups.computeIfAbsent(state.acceptingToken, ignored -> new HashSet<>()).add(state.id);
        }
        
        if (!nonAccepting.isEmpty()) partitions.add(nonAccepting);
        partitions.addAll(acceptingGroups.values());
        
        ArrayDeque<Set<Integer>> work = new ArrayDeque<>(partitions);
        
        while (!work.isEmpty()) {
            Set<Integer> splitter = work.removeFirst();
            for (int symbol = 0; symbol < NFA.ASCII_SIZE; symbol++) {
                Set<Integer> predecessors = new HashSet<>();
                for (DFAState state : states) {
                    if (splitter.contains(state.transitions[symbol])) predecessors.add(state.id);
                }
                
                for (int i = 0; i < partitions.size(); i++) {
                    Set<Integer> part = partitions.get(i);
                    Set<Integer> inside = new HashSet<>(part); 
                    inside.retainAll(predecessors);
                    
                    if (inside.isEmpty() || inside.size() == part.size()) continue;
                    
                    Set<Integer> outside = new HashSet<>(part); 
                    outside.removeAll(predecessors);
                    
                    partitions.set(i, inside); 
                    partitions.add(outside);
                    
                    if (work.remove(part)) { 
                        work.addLast(inside); 
                        work.addLast(outside); 
                    } else if (inside.size() <= outside.size()) {
                        work.addLast(inside); 
                    } else {
                        work.addLast(outside);
                    }
                    i++;
                }
            }
        }
        
        Map<Integer, Integer> blockByState = new HashMap<>();
        for (int block = 0; block < partitions.size(); block++) {
            for (int state : partitions.get(block)) blockByState.put(state, block);
        }
        
        List<DFAState> minimized = new ArrayList<>();
        for (int block = 0; block < partitions.size(); block++) {
            DFAState representative = states.get(partitions.get(block).iterator().next());
            DFAState state = new DFAState(block); 
            state.acceptingToken = representative.acceptingToken; 
            state.trap = representative.trap;
            
            for (int symbol = 0; symbol < NFA.ASCII_SIZE; symbol++) {
                state.transitions[symbol] = blockByState.get(representative.transitions[symbol]);
            }
            minimized.add(state);
        }
        
        return new DFA(minimized, blockByState.get(startState), blockByState.get(trapState), tokens);
    }

    public String toJson() {
        StringBuilder out = new StringBuilder();
        out.append("{\n  \"alphabetSize\": 128,\n  \"start\": ").append(startState).append(",\n  \"trap\": ").append(trapState).append(",\n  \"accepting\": {");
        boolean first = true;
        for (DFAState state : states) {
            if (state.acceptingToken != null) { 
                if (!first) out.append(", "); 
                first = false; 
                out.append("\"").append(state.id).append("\": \"").append(state.acceptingToken).append("\""); 
            }
        }
        out.append("},\n  \"transitions\": [\n");
        for (int i = 0; i < states.size(); i++) { 
            out.append("    ").append(Arrays.toString(states.get(i).transitions)); 
            if (i + 1 < states.size()) out.append(','); 
            out.append('\n'); 
        }
        return out.append("  ]\n}\n").toString();
    }
}