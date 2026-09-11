# globset

`fnmatch` and `glob` only answer one question: does *this* pattern match
*this* path. Real filtering usually needs a *list* of patterns, some of
which are exclusions - "match every `.py` file except the ones under
`vendor/` and except test files" - and the standard library gives you no
help resolving overlaps between them. This library does that part: it
compiles a list of glob patterns into one matcher, with `.gitignore`
semantics (a later pattern overrides an earlier one, and `!pattern`
negates).

## Install

No package is published yet - vendor `src/globset` directly, or add it
as a path dependency once this settles.

## Usage

```python
from globset import GlobSet

rules = GlobSet([
    "*.py",
    "!test_*.py",
    "src/**/*.py",
])

rules.match("app.py")            # True
rules.match("test_app.py")       # False - excluded
rules.match("src/pkg/mod.py")    # True

paths = ["app.py", "test_app.py", "notes.txt", "src/pkg/mod.py"]
list(rules.filter(paths))
# ['app.py', 'src/pkg/mod.py']
```

Patterns support the glob syntax you'd expect:

- `*` matches anything except `/`
- `**/` matches zero or more directories
- `**` alone matches anything, including `/`
- `?` matches a single character except `/`
- `[abc]`, `[a-z]`, `[!abc]` character classes
- `{py,js}` brace alternation, e.g. `*.{py,js}`

Matching is case-sensitive by default; pass `case_sensitive=False` to
`GlobSet(...)` for case-insensitive filesystems.

If you only need a single pattern compiled to a regex, `compile_pattern`
is exposed directly:

```python
from globset import compile_pattern

regex = compile_pattern("src/**/*.py")
regex.match("src/a/b/mod.py") is not None  # True
```

## Status

Early. The matching engine works and is covered by the examples above;
error messages for malformed patterns, a proper test suite, and
performance work on large pattern lists are still to come.

## License

MIT, see `LICENSE`.
