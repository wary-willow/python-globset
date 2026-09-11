"""Match paths against a set of glob patterns, gitignore-style.

The standard library's fnmatch and glob modules only answer "does this
one pattern match this one path". As soon as you have a list of
patterns - some of them exclusions - you end up re-implementing the
precedence rules yourself. This module does that part: patterns are
checked in order, a leading '!' negates one, and whichever rule matched
last wins. That's the same resolution order git uses for .gitignore.
"""

import re
from typing import Iterable, List, Pattern, Tuple

__all__ = ["GlobSet", "translate", "compile_pattern"]


def _expand_braces(pattern: str) -> List[str]:
    """Expand `{a,b,c}` alternation into a list of literal patterns.

    Handles one brace group at a time and recurses on the remainder, so
    sequential groups like "{a,b}/{c,d}" expand correctly. Nested braces
    are not supported and pass through as literal text - that covers the
    patterns people actually write (*.{py,js}, src/{a,b}/**.py) without
    a full brace-expansion grammar.
    """
    start = pattern.find("{")
    if start == -1:
        return [pattern]
    end = pattern.find("}", start)
    if end == -1:
        return [pattern]
    prefix = pattern[:start]
    suffix = pattern[end + 1 :]
    options = pattern[start + 1 : end].split(",")
    tails = _expand_braces(suffix)
    return [prefix + option + tail for option in options for tail in tails]


def translate(pattern: str) -> str:
    """Translate a single glob pattern (no braces) into a regex string.

    Supports '*' (anything but '/'), '**' (anything, including '/', with
    "**/" as a zero-or-more-directories prefix), '?', and '[...]'
    character classes. The result is a fragment meant to be anchored by
    the caller, not a full regex on its own.
    """
    i, n = 0, len(pattern)
    parts: List[str] = []
    while i < n:
        c = pattern[i]
        i += 1
        if c == "*":
            if i < n and pattern[i] == "*":
                i += 1
                if i < n and pattern[i] == "/":
                    i += 1
                    parts.append(r"(?:.*/)?")
                else:
                    parts.append(r".*")
            else:
                parts.append(r"[^/]*")
        elif c == "?":
            parts.append(r"[^/]")
        elif c == "[":
            j = i
            if j < n and pattern[j] in "!^":
                j += 1
            if j < n and pattern[j] == "]":
                j += 1
            while j < n and pattern[j] != "]":
                j += 1
            if j >= n:
                parts.append(r"\[")
            else:
                inner = pattern[i:j]
                if inner.startswith("!"):
                    inner = "^" + inner[1:]
                parts.append("[" + inner + "]")
                i = j + 1
        else:
            parts.append(re.escape(c))
    return "".join(parts)


def compile_pattern(pattern: str, case_sensitive: bool = True) -> Pattern[str]:
    """Compile one glob pattern (braces allowed) into an anchored regex."""
    alternatives = _expand_braces(pattern)
    body = "|".join(f"(?:{translate(alt)})" for alt in alternatives)
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(rf"(?s)\A(?:{body})\Z", flags)


class GlobSet:
    """A compiled set of glob patterns, evaluated together like a .gitignore.

    Patterns are checked in the order given. A pattern prefixed with '!'
    negates the match. The last pattern that matches a given path -
    positive or negative - decides the outcome, mirroring how git
    resolves overlapping ignore rules.

    >>> gs = GlobSet(["*.py", "!test_*.py"])
    >>> gs.match("app.py")
    True
    >>> gs.match("test_app.py")
    False
    """

    def __init__(self, patterns: Iterable[str], case_sensitive: bool = True):
        self._rules: List[Tuple[Pattern[str], bool]] = []
        for raw in patterns:
            negate = raw.startswith("!")
            body = raw[1:] if negate else raw
            if not body:
                continue
            self._rules.append((compile_pattern(body, case_sensitive), negate))

    def match(self, path: str) -> bool:
        path = path.replace("\\", "/")
        matched = False
        for regex, negate in self._rules:
            if regex.match(path):
                matched = not negate
        return matched

    def filter(self, paths: Iterable[str]) -> Iterable[str]:
        """Yield the paths that this set matches, in the given order."""
        for path in paths:
            if self.match(path):
                yield path
