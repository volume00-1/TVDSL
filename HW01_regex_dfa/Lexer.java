import java.util.ArrayList;
import java.util.List;

public final class Lexer {
    public static final class Lexeme {
        public final String token;
        public final String text;
        
        public Lexeme(String token, String text) { 
            this.token = token; 
            this.text = text; 
        }
        
        @Override 
        public String toString() { 
            return token + "(" + text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + ")"; 
        }
    }

    private final DFA dfa;
    
    public Lexer(DFA dfa) { 
        this.dfa = dfa; 
    }

    public List<Lexeme> tokenize(String input) {
        List<Lexeme> result = new ArrayList<>();
        int position = 0;

        while (position < input.length()) {
            int state = dfa.startState;
            int cursor = position;
            int lastAcceptPosition = -1;
            String lastToken = null;

            while (cursor < input.length()) {
                int code = input.charAt(cursor);
                int next = code < NFA.ASCII_SIZE ? dfa.states.get(state).transitions[code] : dfa.trapState;
                
                if (next == dfa.trapState) break; 
                
                state = next; 
                cursor++;
                
                String token = dfa.states.get(state).acceptingToken;
                if (token != null) { 
                    lastAcceptPosition = cursor; 
                    lastToken = token; 
                }
            }

            if (lastAcceptPosition < 0) {
                result.add(new Lexeme("ERROR", String.valueOf(input.charAt(position))));
                position++;
                continue;
            }

            String text = input.substring(position, lastAcceptPosition);
            
            if ("INT".equals(lastToken) && "0".equals(text) && lastAcceptPosition < input.length() && Character.isDigit(input.charAt(lastAcceptPosition))) {
                int end = lastAcceptPosition + 1;
                while (end < input.length() && Character.isDigit(input.charAt(end))) {
                    end++;
                }
                result.add(new Lexeme("ERROR", input.substring(position, end)));
                position = end;
                continue;
            }

            if (!isSkipped(lastToken)) {
                result.add(new Lexeme(lastToken, text));
            }
            
            position = lastAcceptPosition;
        }
        return result;
    }

    private boolean isSkipped(String token) {
        for (Token specification : dfa.tokens) {
            if (specification.name.equals(token)) return specification.skip;
        }
        return false;
    }
}