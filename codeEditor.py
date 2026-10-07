from nicegui import ui
import json

# Note: this file is mostly AI-generated, with code modified by me as needed.

def makeEditor():
    # The HTML element that will contain CodeMirror
    editor = ui.html('''
        <div id="code-editor"></div>
    ''').classes('w-full h-full')
    ui.html("""
        <style>
            #code-editor {
                width: 100%;
                height: 100%;
                border: 1px solid #aaa;
            }

            .my-highlight {
                background: yellow;
            }
        </style>""")
    return editor

initial_text = """# Sample script
select a from 1 to 3
if a == 3
\tpass
fail"""

def addEditorScript():

    ui.add_body_html('''
<script type="module">
import {
    EditorView,
    basicSetup
} from "https://esm.sh/codemirror@6.0.1";

import {
    EditorState
} from "https://esm.sh/@codemirror/state";

import {
    StreamLanguage,
    syntaxHighlighting,
    HighlightStyle
} from "https://esm.sh/@codemirror/language";

import {
    tags
} from "https://esm.sh/@lezer/highlight";

// ---------------------------------------------------------
// Your language's keywords
// ---------------------------------------------------------

const keywords = new Set([
    "select",
    "from",
    "where",
    "for",
    "in",
    "if",
    "else",
    "elif",
    "break",
    "continue",
    "bychance",
    "print",
    "printa",
    "printc",
    "printr",
    "pass",
    "fail",
    "done",
    "return",
    "input",
    "sorted",
]);

// ---------------------------------------------------------
// Very simple syntax highlighter
// ---------------------------------------------------------

const language = StreamLanguage.define({
    token(stream) {

        if (stream.eatSpace())
            return null;

        // Words
        if (stream.match(/^[A-Za-z~][A-Za-z0-9_~]*/)) {
            const word = stream.current();

            if (keywords.has(word))
                return "keyword";

            return null;
        }

        // Strings
        if (stream.match(/^"[^"]*"/))
            return "string";

        // Numbers
        if (stream.match(/^\\d+/))
            return "number";

        // Operators
        if (stream.match(/^[+\\-*\\/=<>]/))
            return "operator";

        stream.next();
        return null;
    }
});


// ---------------------------------------------------------
// Highlight colors
// ---------------------------------------------------------

const highlightStyle = HighlightStyle.define([
    {
        tag: tags.keyword,
        color: "#0000cc",
        fontWeight: "bold"
    },
    {
        tag: tags.string,
        color: "#008000"
    },
    {
        tag: tags.number,
        color: "#800080"
    },
    {
        tag: tags.operator,
        color: "#aa00aa"
    }
]);


// ---------------------------------------------------------
// Create editor
// ---------------------------------------------------------

const startState = EditorState.create({
    doc: ''' + json.dumps(initial_text) + ''',
    extensions: [
        basicSetup,
        language,
        syntaxHighlighting(highlightStyle),

        EditorView.updateListener.of((update) => {
            if (update.docChanged) {
                const text = update.state.doc.toString();
                emitEvent('code_changed', {
                    text: text
                });
            };
        })
    ]
});

window.makeEditor = function() {
    
    

    window.codeEditor = new EditorView({
        state: startState,
        parent: document.getElementById("code-editor")
    });
};

</script>
''')
    return


