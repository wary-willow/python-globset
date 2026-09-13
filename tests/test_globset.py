import unittest

from globset import GlobSet, compile_pattern


class TranslateStarTests(unittest.TestCase):
    def test_single_star_excludes_slash(self):
        regex = compile_pattern("*.py")
        self.assertIsNotNone(regex.match("app.py"))
        self.assertIsNone(regex.match("pkg/app.py"))

    def test_single_star_does_not_extend_extension(self):
        regex = compile_pattern("*.py")
        self.assertIsNone(regex.match("app.pyc"))


class DoubleStarTests(unittest.TestCase):
    def test_leading_double_star_slash_matches_zero_dirs(self):
        regex = compile_pattern("**/*.py")
        self.assertIsNotNone(regex.match("app.py"))
        self.assertIsNotNone(regex.match("a/b/app.py"))

    def test_double_star_slash_matches_zero_or_more_dirs(self):
        regex = compile_pattern("a/**/b")
        self.assertIsNotNone(regex.match("a/b"))
        self.assertIsNotNone(regex.match("a/x/b"))
        self.assertIsNotNone(regex.match("a/x/y/b"))
        self.assertIsNone(regex.match("a/b/c"))

    def test_bare_double_star_matches_across_slashes(self):
        regex = compile_pattern("a/**b")
        self.assertIsNotNone(regex.match("a/foob"))
        self.assertIsNotNone(regex.match("a/x/y/zb"))


class CharacterClassTests(unittest.TestCase):
    def test_class_matches_listed_chars(self):
        regex = compile_pattern("[abc].py")
        self.assertIsNotNone(regex.match("a.py"))
        self.assertIsNone(regex.match("d.py"))

    def test_negated_class(self):
        regex = compile_pattern("[!abc].py")
        self.assertIsNotNone(regex.match("d.py"))
        self.assertIsNone(regex.match("a.py"))

    def test_unclosed_class_is_treated_as_literal(self):
        regex = compile_pattern("[abc")
        self.assertIsNotNone(regex.match("[abc"))


class QuestionMarkTests(unittest.TestCase):
    def test_question_mark_matches_one_char_not_slash(self):
        regex = compile_pattern("?.py")
        self.assertIsNotNone(regex.match("a.py"))
        self.assertIsNone(regex.match("ab.py"))
        self.assertIsNone(regex.match("/.py"))


class BraceExpansionTests(unittest.TestCase):
    def test_single_group(self):
        regex = compile_pattern("*.{py,js}")
        self.assertIsNotNone(regex.match("a.py"))
        self.assertIsNotNone(regex.match("a.js"))
        self.assertIsNone(regex.match("a.txt"))

    def test_sequential_groups(self):
        regex = compile_pattern("{a,b}/{c,d}.py")
        self.assertIsNotNone(regex.match("a/c.py"))
        self.assertIsNotNone(regex.match("b/d.py"))
        self.assertIsNone(regex.match("a/x.py"))

    def test_group_combined_with_double_star(self):
        regex = compile_pattern("src/{a,b}/**.py")
        self.assertIsNotNone(regex.match("src/a/mod.py"))
        self.assertIsNotNone(regex.match("src/b/sub/mod.py"))
        self.assertIsNone(regex.match("src/c/mod.py"))


class GlobSetTests(unittest.TestCase):
    def test_last_match_wins(self):
        gs = GlobSet(["*.py", "!test_*.py", "test_ok.py"])
        self.assertTrue(gs.match("app.py"))
        self.assertFalse(gs.match("test_app.py"))
        self.assertTrue(gs.match("test_ok.py"))

    def test_empty_patterns_are_ignored(self):
        gs = GlobSet(["", "*.py", "!"])
        self.assertTrue(gs.match("app.py"))

    def test_no_patterns_never_matches(self):
        gs = GlobSet([])
        self.assertFalse(gs.match("anything"))

    def test_case_insensitive(self):
        gs = GlobSet(["*.PY"], case_sensitive=False)
        self.assertTrue(gs.match("app.py"))

    def test_backslashes_are_normalized(self):
        gs = GlobSet(["a/b.py"])
        self.assertTrue(gs.match("a\\b.py"))

    def test_filter_preserves_order(self):
        gs = GlobSet(["*.py", "!test_*.py"])
        paths = ["test_a.py", "a.py", "notes.txt", "b.py"]
        self.assertEqual(list(gs.filter(paths)), ["a.py", "b.py"])


if __name__ == "__main__":
    unittest.main()
