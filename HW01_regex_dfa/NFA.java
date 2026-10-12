import java.util.*;

public final class NFA {
    public static final int ASCII_SIZE = 128;
    public final List<NFAState> states = new ArrayList<>();
    public final NFAState start;

    public NFA() {
        this.start = newState();
    }

    public NFAState newState() {
        NFAState state = new NFAState(states.size());
        states.add(state);
        return state;
    }

    public void addToken(Token token, int priority) {
        Fragment fragment = new RegexParser(token.regex, this).parse();
        start.epsilon.add(fragment.start);
        fragment.end.acceptingToken = token.name;
        fragment.end.acceptingPriority = priority;
    }

    public Set<NFAState> epsilonClosure(Set<NFAState> input) {
        Set<NFAState> result = new HashSet<>(input);
        Deque<NFAState> work = new ArrayDeque<>(input);
        while (!work.isEmpty()) {
            NFAState state = work.removeFirst();
            for (NFAState target : state.epsilon) {
                if (result.add(target)) work.addLast(target); 
            }
        }
        return result;
    }

    private static final class Fragment {
        final NFAState start, end;
        Fragment(NFAState start, NFAState end) { this.start = start; this.end = end; }
    }

    private static final class RegexParser {
        final String regex;
        final NFA nfa;
        int pos = 0;

        RegexParser(String regex, NFA nfa) { this.regex = regex; this.nfa = nfa; }

        Fragment parse() {
            Fragment result = parseExpression();
            if (pos != regex.length()) throw new RuntimeException("Ошибка в regex: " + regex.substring(pos));
            return result;
        }

        private Fragment parseExpression() {
            Fragment left = parseConcatenation();
            while (peek('|')) {
                pos++;
                Fragment right = parseConcatenation();
                NFAState start = nfa.newState();
                NFAState end = nfa.newState();
                start.epsilon.add(left.start); start.epsilon.add(right.start);
                left.end.epsilon.add(end); right.end.epsilon.add(end);
                left = new Fragment(start, end);
            }
            return left;
        }

        private Fragment parseConcatenation() {
            Fragment result = null;
            while (pos < regex.length() && !peek(')') && !peek('|')) {
                Fragment next = parseRepetition();
                if (result == null) result = next;
                else { 
                    result.end.epsilon.add(next.start); 
                    result = new Fragment(result.start, next.end); 
                }
            }
            return result != null ? result : new Fragment(nfa.newState(), nfa.newState());
        }

        private Fragment parseRepetition() {
            Fragment result = parseAtom();
            while (pos < regex.length()) {
                if (peek('*')) {
                    pos++;
                    NFAState start = nfa.newState(), end = nfa.newState();
                    start.epsilon.add(result.start); start.epsilon.add(end);
                    result.end.epsilon.add(result.start); result.end.epsilon.add(end);
                    result = new Fragment(start, end);
                } else if (peek('+')) {
                    pos++;
                    NFAState start = nfa.newState(), end = nfa.newState();
                    start.epsilon.add(result.start); 
                    result.end.epsilon.add(result.start); result.end.epsilon.add(end);
                    result = new Fragment(start, end);
                } else {
                    break;
                }
            }
            return result;
        }

        private Fragment parseAtom() {
            if (peek('(')) { pos++; Fragment res = parseExpression(); expect(')'); return res; }
            
            Set<Integer> symbols = new HashSet<>();
            if (peek('[')) {
                symbols = parseCharacterClass();
            } else {
                symbols.add(readEscaped());
            }
            
            NFAState start = nfa.newState(), end = nfa.newState();
            for (int symbol : symbols) start.addTransition(symbol, end);
            return new Fragment(start, end);
        }

        private Set<Integer> parseCharacterClass() {
            expect('[');
            boolean negated = peek('^');
            if (negated) pos++;
            
            Set<Integer> symbols = new HashSet<>();
            while (pos < regex.length() && !peek(']')) {
                int first = readEscaped();
                if (peek('-') && pos + 1 < regex.length() && regex.charAt(pos + 1) != ']') {
                    pos++;
                    int last = readEscaped();
                    for (int c = first; c <= last; c++) symbols.add(c);
                } else {
                    symbols.add(first);
                }
            }
            expect(']');
            
            if (negated) {
                Set<Integer> all = new HashSet<>();
                for (int c = 0; c < ASCII_SIZE; c++) all.add(c);
                all.removeAll(symbols);
                return all;
            }
            return symbols;
        }

        private int readEscaped() {
            if (pos >= regex.length()) throw new RuntimeException("Неожиданный конец regex");
            char ch = regex.charAt(pos++);
            if (ch != '\\') return ch;
            char esc = regex.charAt(pos++);
            return switch (esc) {
                case 'n' -> '\n'; case 'r' -> '\r'; case 't' -> '\t';
                case 's' -> ' '; case '\\' -> '\\';
                default -> esc;
            };
        }

        private boolean peek(char expected) { return pos < regex.length() && regex.charAt(pos) == expected; }
        private void expect(char expected) { 
            if (!peek(expected)) throw new RuntimeException("Ожидалось '" + expected + "'"); 
            pos++; 
        }
    }
}