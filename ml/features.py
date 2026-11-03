# features.py
#
# Turns test code into something a model can learn from.
#
# Used in two places, so they always do exactly the same thing:
#   - build_dataset.py, on real tests downloaded from GitHub (for training)
#   - detective.py, on your own tests file (for predicting)

import ast
import io
import re
import tokenize

SETUP_NAMES = {"setUp", "tearDown", "setUpClass", "tearDownClass",
               "setup_method", "teardown_method", "setup_class", "teardown_class"}

FUNCTION_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)


def tests_in_file(source):
    """Find every test in a file's source code.

    Returns a list of (name, code, context):
      name     "test_x", or "TestClass::test_x" for a test inside a class
      code     the test function's own code
      context  the code around it that can affect it: the file's imports,
               the fixtures the test asks for, and setUp/tearDown methods
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    imports = [s for s in tree.body if isinstance(s, (ast.Import, ast.ImportFrom))]
    top_level_functions = {s.name: s for s in tree.body if isinstance(s, FUNCTION_TYPES)}

    # (name, function, setup methods of its class)
    found = []
    for statement in tree.body:
        if isinstance(statement, FUNCTION_TYPES) and statement.name.startswith("test"):
            found.append((statement.name, statement, []))
        elif isinstance(statement, ast.ClassDef):
            methods = [s for s in statement.body if isinstance(s, FUNCTION_TYPES)]
            setups = [m for m in methods if m.name in SETUP_NAMES]
            for method in methods:
                if method.name.startswith("test"):
                    found.append((f"{statement.name}::{method.name}", method, setups))

    tests = []
    for name, function, setups in found:
        asked_for = {arg.arg for arg in function.args.args}
        fixtures = [top_level_functions[a] for a in asked_for if a in top_level_functions]
        context = imports + fixtures + setups
        code = ast.get_source_segment(source, function) or ""
        context_code = "\n".join(ast.get_source_segment(source, c) or "" for c in context)
        tests.append((name, code, context_code))
    return tests


def words(code, prefix=""):
    """Split code into lowercase words. Comments and strings are skipped.

    "self.assertEqual(time_now, x)" -> "self assert equal time now x"
    """
    out = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(code).readline):
            if token.type == tokenize.NAME:
                # split snake_case and camelCase into separate words
                for part in re.split(r"_|(?<=[a-z])(?=[A-Z])", token.string):
                    if part:
                        out.append(prefix + part.lower())
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return " ".join(out)


def to_text(code, context):
    """The single piece of text the model reads for one test.

    Words from the surrounding context get a "ctx_" prefix, so the model can
    tell "the test calls sleep" apart from "the file imports time".
    """
    return words(code) + " " + words(context, prefix="ctx_")
