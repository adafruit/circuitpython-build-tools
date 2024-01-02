# The MIT License (MIT)
#
# Copyright (c) 2024 Jeff Epler for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Filter program removes some code patterns introduced by type checking,
# to move towards zero overhead static typing in circuitpython libraries
#
# Recognized:
# from __future__ import ...    -- eliminated
# try: import typing            -- eliminated, but first except: preserved
# try: from typing import ...   -- eliminated, but first except: preserved
# if STATIC_TYPING:             -- transformed to 'if 0:'
# if sys.implementation_name... -- transformed to unconditional if
# __version__ = ...             -- set to library version string
#
# mpy-cross does constant propagation and dead branch elimination of
# 'if 0:' and 'if 1:'
#
# Depends on the file being black-formatted!

import pathlib
import sys
import ast

VERBOSE = 0

# The canonical spelling of this test...
sys_implementation_is_circuitpython = ast.unparse(ast.parse('sys.implementation.name == "circuitpython"'))
sys_implementation_not_circuitpython = ast.unparse(ast.parse('not sys.implementation.name == "circuitpython"'))
sys_implementation_not_circuitpython2 = ast.unparse(ast.parse('sys.implementation.name != "circuitpython"'))

def munge(src: pathlib.Path|str, version_str: str) -> str:
    path = pathlib.Path(src)
    replacements = {}

    def replace(line, new):
        if VERBOSE:
            replacements[line] = f"{new:<40s} ### {lines[line]}"
        else:
            replacements[line] = new

    def blank_range(node):
        for i in range(node.lineno, node.end_lineno+1):
            replace(i, "")

    def unblank_range(node):
        for i in range(node.lineno, node.end_lineno+1):
            replacements.pop(i, None)

    def imports_from_typing(node):
        if isinstance(node, ast.Import) and node.names[0].name == 'typing':
            return True
        if isinstance(node, ast.ImportFrom) and node.module == 'typing':
            return True
        return False

    def process_statement(node):
        # filter out 'from future import...'
        if isinstance(node, ast.ImportFrom):
            if node.module == '__future__':
                blank_range(node)
        # filter out 'try: import typing...'
        # but preserve the first 'except:' or 'except ImportError'
        elif isinstance(node, ast.Try):
            b = node.body[0]
            if imports_from_typing(node.body[0]):
                blank_range(node)
                for h in node.handlers:
                    if h.type is None or ast.unparse(h.type) == 'ImportError' or ast.unparse(h.type) == 'Exception':
                        unblank_range(h)
                        replace(h.lineno, 'if 1:')
                        break
                return
        elif isinstance(node, ast.If):
            node_test = ast.unparse(node.test)
            # return the statements in the 'if' branch of 'if sys.implementation...: ...'
            if node_test == sys_implementation_is_circuitpython:
                replace(node.lineno, 'if 1:')
            # return the statements in the 'else' branch of 'if sys.implementation...: ...'
            elif node_test == sys_implementation_not_circuitpython or node_test == sys_implementation_not_circuitpython2:
                replace(node.lineno, 'if 0:')
            # return the statements in the else branch of 'if TYPE_CHECKING: ...'
            elif node_test == 'TYPE_CHECKING':
                replace(node.lineno, 'if 0:')
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == '__version__':
                replace(node.lineno, f"__version__ = \"{version_str}\"")

    content = pathlib.Path(path).read_text(encoding="utf-8")
    # Insert a blank line 0 because ast line numbers are 1-based
    lines = [''] + content.rstrip().split('\n')
    a = ast.parse(content, path.name)

    for node in a.body: process_statement(node)

    result = []
    for i in range(1, len(lines)):
        result.append(replacements.get(i, lines[i]))

    return "\n".join(result) + "\n"
