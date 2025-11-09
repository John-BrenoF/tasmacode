AUTOCOMPLETE_PAIRS = {
    "(": ")",
    "[": "]",
    "{": "}",
    "\"": "\"",
    "'": "'",
    "`": "`"
}

AUTOCOMPLETE_WORDS = {
    ".py": [
        "def", "class", "if", "else", "elif", "for", "while", "return",
        "import", "from", "try", "except", "finally", "with", "as", "lambda",
        "True", "False", "None", "print", "len", "range", "self", "super",
        "__init__", "__str__", "__repr__", "yield", "in", "is", "not", "and", "or",
        "dict", "list", "set", "tuple", "str", "int", "float", "bool"
    ],
    ".html": [
        "div", "p", "a", "img", "span", "h1", "h2", "h3", "ul", "ol", "li",
        "table", "tr", "td", "th", "form", "input", "button", "label",
        "<!DOCTYPE html>", "<html>", "<head>", "<body>", "<title>", "<meta>",
        "<link>", "<script>", "<style>", "header", "footer", "nav", "main",
        "section", "article", "aside", "figure", "figcaption", "video", "audio",
        "textarea", "select", "option", "strong", "em", "blockquote",
        "href", "src", "class", "id", "style", "alt"
    ],
    ".css": [
        "color", "background-color", "font-size", "font-weight", "margin",
        "padding", "border", "display", "position", "width", "height",
        "flex", "grid", "absolute", "relative", "block", "inline-block",
        "font-family", "text-align", "line-height", "border-radius", "box-shadow",
        "background", "background-image", "background-size", "flex-direction",
        "justify-content", "align-items", "grid-template-columns", "gap",
        "transition", "transform", "animation", "cursor", ":hover", ":focus"
    ],
    ".js": [
        "function", "const", "let", "var", "if", "else", "for", "while", "return",
        "import", "export", "class", "extends", "super", "this", "true", "false",
        "null", "console.log", "document", "window", "async", "await", "switch",
        "case", "break", "try", "catch", "finally", "throw", "new", "typeof",
        "Promise", "map", "filter", "reduce", "forEach", "addEventListener"
    ],
    ".java": [
        "public", "private", "protected", "static", "final", "class", "interface",
        "enum", "void", "int", "String", "double", "boolean", "if", "else", "for",
        "while", "return", "import", "new", "this", "super", "true", "false", "null",
        "System.out.println", "ArrayList", "HashMap", "List", "Map", "throws",
        "try", "catch", "finally", "extends", "implements", "package"
    ],
    ".rb": [
        "def", "end", "class", "module", "if", "else", "elsif", "unless", "while",
        "for", "in", "do", "return", "require", "include", "true", "false", "nil",
        "puts", "self", "yield", "attr_reader", "attr_writer", "attr_accessor",
        "each", "map", "select", "new"
    ],
    ".c": [
        "int", "char", "float", "double", "void", "struct", "if", "else", "for",
        "while", "do", "return", "#include", "#define", "printf", "scanf", "malloc",
        "free", "sizeof", "NULL", "typedef", "enum", "const", "static", "extern",
        "FILE", "fopen", "fclose", "fprintf"
    ],
    ".cpp": [
        "int", "char", "float", "double", "void", "class", "struct", "if", "else",
        "for", "while", "do", "return", "#include", "using", "namespace", "std",
        "cout", "cin", "vector", "string", "new", "delete", "nullptr", "true", "false",
        "auto", "const", "static", "virtual", "template", "typename", "map", "set",
        "iostream", "vector", "string"
    ],
    ".cs": [
        "public", "private", "protected", "internal", "static", "class", "interface",
        "struct", "enum", "void", "int", "string", "bool", "double", "if", "else",
        "for", "while", "foreach", "return", "using", "namespace", "new", "this",
        "true", "false", "null", "Console.WriteLine", "var", "const", "readonly",
        "get", "set", "List", "Dictionary", "IEnumerable", "async", "await", "Task",
        "from", "where", "select", "orderby"
    ]
}
HTML_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr"
}