import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public final class Main {
    private static final class TestCase {
        final String input; final String expected;
        TestCase(String input, String expected) { this.input = input; this.expected = expected; }
    }

    public static void main(String[] args) throws IOException {
        List<Token> tokens = Token.specification();
        NFA nfa = new NFA();
        for (int i = 0; i < tokens.size(); i++) nfa.addToken(tokens.get(i), i);
        DFA dfa = DFA.build(nfa, tokens);
        DFA minimized = dfa.minimizeHopcroft();
        Lexer lexer = new Lexer(minimized);

        Files.writeString(Path.of("dfa.json"), minimized.toJson(), StandardCharsets.UTF_8);
        List<String> reportTests = runTests(lexer);
        Files.write(Path.of("Report.md"), report(tokens, nfa, dfa, minimized, reportTests), StandardCharsets.UTF_8);
        System.out.println("NFA states: " + nfa.states.size());
        System.out.println("DFA states: " + dfa.states.size());
        System.out.println("Minimized DFA states: " + minimized.states.size());
        System.out.println("Tests: " + reportTests.stream().filter(line -> line.contains("| PASS |")).count() + "/" + reportTests.size() + " PASS");
        System.out.println("Generated: dfa.json, Report.md");
    }

    private static List<String> runTests(Lexer lexer) {
        List<TestCase> tests = Arrays.asList(
            new TestCase("", ""), new TestCase(" \t\r\n", ""),
            new TestCase("0", "INT(0)"), new TestCase("00", "ERROR(00)"), new TestCase("01", "ERROR(01)"),
            new TestCase("_name value_2", "IDENT(_name) IDENT(value_2)"),
            new TestCase("function returns while if else assert assume invariant length", "FUNCTION(function) RETURNS(returns) WHILE(while) IF(if) ELSE(else) ASSERT(assert) ASSUME(assume) INVARIANT(invariant) LENGTH(length)"),
            new TestCase("()[]{},; + - * / == != <= >= < > =", "LPAREN(() RPAREN()) LBRACKET([) RBRACKET(]) LBRACE({) RBRACE(}) COMMA(,) SEMICOLON(;) PLUS(+) MINUS(-) STAR(*) SLASH(/) EQEQ(==) NE(!=) LE(<=) GE(>=) LT(<) GT(>) ASSIGN(=)"),
            new TestCase("// comment to end\nfunction", "FUNCTION(function)"),
            new TestCase("a\u00E9", "IDENT(a) ERROR(\u00E9)"), new TestCase("abc123", "IDENT(abc123)")
        );
        List<String> lines = new ArrayList<>();
        for (TestCase test : tests) {
            String actual = join(lexer.tokenize(test.input));
            lines.add("| `" + printable(test.input) + "` | `" + test.expected + "` | `" + actual + "` | " + (test.expected.equals(actual) ? "PASS" : "FAIL") + " |");
        }
        boolean asciiSmokePassed = true;
        for (int code = 0; code < NFA.ASCII_SIZE; code++) {
            try { lexer.tokenize(String.valueOf((char) code)); }
            catch (RuntimeException exception) { asciiSmokePassed = false; break; }
        }
        lines.add("| `ASCII 0..127 smoke` | every character processed | no runtime error | " + (asciiSmokePassed ? "PASS" : "FAIL") + " |");
        return lines;
    }

    private static String join(List<Lexer.Lexeme> lexemes) {
        StringBuilder result = new StringBuilder();
        for (Lexer.Lexeme lexeme : lexemes) { if (result.length() > 0) result.append(' '); result.append(lexeme); }
        return result.toString();
    }

    private static String printable(String value) { return value.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t"); }

    private static List<String> report(List<Token> tokens, NFA nfa, DFA dfa, DFA minimized, List<String> tests) {
        List<String> lines = new ArrayList<>();
        lines.add("# HW1: Lexer, Regex to DFA, Minimization"); lines.add("");
        lines.add("## Regular expressions"); lines.add(""); lines.add("| Token | Regex | Mode |"); lines.add("|---|---|---|");
        for (Token token : tokens) lines.add("| " + token.name + " | `" + token.regex + "` | " + (token.skip ? "skip" : "accept") + " |");
        lines.add(""); lines.add("## Statistics"); lines.add("");
        lines.add("NFA states: " + nfa.states.size() + ". DFA states: " + dfa.states.size() + ". Minimized DFA states: " + minimized.states.size() + ".");
        lines.add(""); lines.add("## Trap"); lines.add("");
        lines.add("State " + minimized.trapState + " is the trap state; all undefined ASCII transitions lead to it. Non-ASCII input is also routed to the trap.");
        lines.add(""); lines.add("## Tests"); lines.add(""); lines.add("| Input | Expected token | Actual result | Status |"); lines.add("|---|---|---|---|"); lines.addAll(tests);
        lines.add(""); lines.add("The transition table is serialized to `dfa.json` (ASCII alphabet, 128 columns per state).");
        return lines;
    }
}
