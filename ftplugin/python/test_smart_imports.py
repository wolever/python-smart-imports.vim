import ast

import unittest
from unittest import TestCase

from smart_imports import Import, PythonSmartImporter

class MockBuf(list):
    def __init__(self, name, contents):
        self.name = name
        list.__init__(self, [line.lstrip() for line in contents.splitlines()])


class MockVim(object):
    def __init__(self, buffers):
        self.buffers = buffers

    def eval(self, _):
        return ""


class IndentTest(TestCase):
    import_tests = [
        ("import foo.bar as baz", ("foo.bar", "baz")),
        ("from foo import bar as baz", ("foo.bar", "baz")),
        ("from foo import bar", ("foo.bar", None)),
        ("import foo.bar", ("foo.bar", None)),
        ("from ...foo import bar", ("...foo.bar", None)),
    ]

    def test_from_ast(self):
        for input, expected in self.import_tests:
            tree = ast.parse(input)
            impts = Import.from_ast(tree)
            if len(impts) != 1:
                raise AssertionError("import not found in %r" %(input, ))
            impt = impts[0]
            self.assertEqual((impt.name, impt.alias), expected)


class PythonSmartImporterTest(TestCase):
    def assertImptsMatch(self, impts, expected):
        if not isinstance(impts, list):
            impts = list(impts)
        if len(impts) != len(expected):
            raise AssertionError("unexpected lengths: %s != %s" %(impts, expected))
        for i, e in zip(impts, expected):
            self.assertEqual((i.name, i.alias), e)

    def test_search_for_imports(self):
        buf = MockBuf("foo.py", """
            import foo.bar as baz
            from ham.spam import eggs as green
            from .local import localthing
        """)
        vim = MockVim([buf])
        si = PythonSmartImporter(vim)

        impts = si.search_for_import("green")
        self.assertImptsMatch(impts, [("ham.spam.eggs", "green")])

        impts = si.search_for_import("eggs")
        self.assertImptsMatch(impts, [("ham.spam.eggs", "green")])

        impts = si.search_for_import("foo.bar")
        self.assertImptsMatch(impts, [("foo.bar", "baz")])

        impts = si.search_for_import("localthing")
        self.assertImptsMatch(impts, [(".local.localthing", None)])

if __name__ == "__main__":
    unittest.main()

