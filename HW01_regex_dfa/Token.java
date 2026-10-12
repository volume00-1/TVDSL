import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public final class Token {
    public final String name;
    public final String regex;
    public final boolean skip;

    public Token(String name, String regex, boolean skip) {
        this.name = name;
        this.regex = regex;
        this.skip = skip;
    }

    public static List<Token> specification() {
        List<Token> tokens = new ArrayList<>();
        String[] keywords = {"function", "returns", "while", "if", "else", "assert", "assume", "invariant", "length"};
        for (String keyword : keywords) {
            tokens.add(new Token(keyword.toUpperCase(), keyword, false));
        }
        tokens.addAll(Arrays.asList(
            new Token("IDENT", "[A-Za-z_][A-Za-z0-9_]*", false),
            new Token("INT", "(0|[1-9][0-9]*)", false),
            new Token("WS", "[ \\t\\r\\n]+", true),
            new Token("COMMENT", "//[^\\r\\n]*", true),
            new Token("LPAREN", "\\(", false), new Token("RPAREN", "\\)", false),
            new Token("LBRACKET", "\\[", false), new Token("RBRACKET", "\\]", false),
            new Token("LBRACE", "\\{", false), new Token("RBRACE", "\\}", false),
            new Token("COMMA", ",", false), new Token("SEMICOLON", ";", false),
            new Token("PLUS", "\\+", false), new Token("MINUS", "-", false),
            new Token("STAR", "\\*", false), new Token("SLASH", "/", false),
            new Token("EQEQ", "==", false), new Token("NE", "!=", false),
            new Token("LE", "<=", false), new Token("GE", ">=", false),
            new Token("LT", "<", false), new Token("GT", ">", false),
            new Token("ASSIGN", "=", false)
        ));
        return tokens;
    }
}
