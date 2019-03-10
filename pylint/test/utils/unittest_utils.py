# -*- coding: utf-8 -*-
# Copyright (c) 2013-2014 Google, Inc.
# Copyright (c) 2013-2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2014 Arun Persaud <arun@nubati.net>
# Copyright (c) 2015-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2015 Aru Sahni <arusahni@gmail.com>
# Copyright (c) 2015 Ionel Cristian Maries <contact@ionelmc.ro>
# Copyright (c) 2016 Derek Gustafson <degustaf@gmail.com>
# Copyright (c) 2016 Glenn Matthews <glenn@e-dad.net>
# Copyright (c) 2017-2018 Anthony Sottile <asottile@umich.edu>
# Copyright (c) 2017 Pierre Sassoulas <pierre.sassoulas@cea.fr>
# Copyright (c) 2017 ttenhoeve-aa <ttenhoeve@appannie.com>
# Copyright (c) 2017 Łukasz Rogalski <rogalski.91@gmail.com>
# Copyright (c) 2018 Pierre Sassoulas <pierre.sassoulas@wisebim.fr>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import io
import re
import warnings

import astroid

from pylint.checkers.utils import check_messages, get_node_last_lineno
from pylint.utils import ASTWalker, utils


class TestASTWalker(object):
    class MockLinter(object):
        def __init__(self, msgs):
            self._msgs = msgs

        def is_message_enabled(self, msgid):
            return self._msgs.get(msgid, True)

    class Checker(object):
        def __init__(self):
            self.called = set()

        @check_messages("first-message")
        def visit_module(self, module):
            self.called.add("module")

        @check_messages("second-message")
        def visit_call(self, module):
            raise NotImplementedError

        @check_messages("second-message", "third-message")
        def visit_assignname(self, module):
            self.called.add("assignname")

        @check_messages("second-message")
        def leave_assignname(self, module):
            raise NotImplementedError

    def test_check_messages(self):
        linter = self.MockLinter(
            {"first-message": True, "second-message": False, "third-message": True}
        )
        walker = ASTWalker(linter)
        checker = self.Checker()
        walker.add_checker(checker)
        walker.walk(astroid.parse("x = func()"))
        assert {"module", "assignname"} == checker.called

    def test_deprecated_methods(self):
        class Checker(object):
            def __init__(self):
                self.called = False

            @check_messages("first-message")
            def visit_assname(self, node):
                self.called = True

        linter = self.MockLinter({"first-message": True})
        walker = ASTWalker(linter)
        checker = Checker()
        walker.add_checker(checker)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            walker.walk(astroid.parse("x = 1"))

            assert not checker.called


def test__basename_in_blacklist_re_match():
    patterns = [re.compile(".*enchilada.*"), re.compile("unittest_.*")]
    assert utils._basename_in_blacklist_re("unittest_utils.py", patterns)
    assert utils._basename_in_blacklist_re("cheese_enchiladas.xml", patterns)


def test__basename_in_blacklist_re_nomatch():
    patterns = [re.compile(".*enchilada.*"), re.compile("unittest_.*")]
    assert not utils._basename_in_blacklist_re("test_utils.py", patterns)
    assert not utils._basename_in_blacklist_re("enchilad.py", patterns)


def test_decoding_stream_unknown_encoding():
    """decoding_stream should fall back to *some* decoding when given an
    unknown encoding.
    """
    binary_io = io.BytesIO(b"foo\nbar")
    stream = utils.decoding_stream(binary_io, "garbage-encoding")
    # should still act like a StreamReader
    ret = stream.readlines()
    assert ret == ["foo\n", "bar"]


def test_decoding_stream_known_encoding():
    binary_io = io.BytesIO("€".encode("cp1252"))
    stream = utils.decoding_stream(binary_io, "cp1252")
    assert stream.read() == "€"


class TestGetNodeLastLineno:
    def test_get_node_last_lineno_simple(self):
        node = astroid.extract_node(
            """
            pass
        """
        )
        assert get_node_last_lineno(node) == 2

    def test_get_node_last_lineno_if_simple(self):
        node = astroid.extract_node(
            """
            if True:
                print(1)
                pass
            """
        )
        assert get_node_last_lineno(node) == 4

    def test_get_node_last_lineno_if_elseif_else(self):
        node = astroid.extract_node(
            """
            if True:
                print(1)
            elif False:
                print(2)
            else:
                print(3)
            """
        )
        assert get_node_last_lineno(node) == 7

    def test_get_node_last_lineno_while(self):
        node = astroid.extract_node(
            """
            while True:
                print(1)
            """
        )
        assert get_node_last_lineno(node) == 3

    def test_get_node_last_lineno_while_else(self):
        node = astroid.extract_node(
            """
            while True:
                print(1)
            else:
                print(2)
            """
        )
        assert get_node_last_lineno(node) == 5

    def test_get_node_last_lineno_for(self):
        node = astroid.extract_node(
            """
            for x in range(0, 5):
                print(1)
            """
        )
        assert get_node_last_lineno(node) == 3

    def test_get_node_last_lineno_for_else(self):
        node = astroid.extract_node(
            """
            for x in range(0, 5):
                print(1)
            else:
                print(2)
            """
        )
        assert get_node_last_lineno(node) == 5

    def test_get_node_last_lineno_try(self):
        node = astroid.extract_node(
            """
            try:
                print(1)
            except ValueError:
                print(2)
            except Exception:
                print(3)
            """
        )
        assert get_node_last_lineno(node) == 7

    def test_get_node_last_lineno_try_except_else(self):
        node = astroid.extract_node(
            """
            try:
                print(1)
            except Exception:
                print(2)
                print(3)
            else:
                print(4)
            """
        )
        assert get_node_last_lineno(node) == 8

    def test_get_node_last_lineno_try_except_finally(self):
        node = astroid.extract_node(
            """
            try:
                print(1)
            except Exception:
                print(2)
            finally:
                print(4)
            """
        )
        assert get_node_last_lineno(node) == 7

    def test_get_node_last_lineno_try_except_else_finally(self):
        node = astroid.extract_node(
            """
            try:
                print(1)
            except Exception:
                print(2)
            else:
                print(3)
            finally:
                print(4)
            """
        )
        assert get_node_last_lineno(node) == 9

    def test_get_node_last_lineno_with(self):
        node = astroid.extract_node(
            """
            with x as y:
                print(1)
                pass
            """
        )
        assert get_node_last_lineno(node) == 4

    def test_get_node_last_lineno_method(self):
        node = astroid.extract_node(
            """
            def x(a, b):
                print(a, b)
                pass
            """
        )
        assert get_node_last_lineno(node) == 4

    def test_get_node_last_lineno_decorator(self):
        node = astroid.extract_node(
            """
            @decor()
            def x(a, b):
                print(a, b)
                pass
            """
        )
        assert get_node_last_lineno(node) == 5

    def test_get_node_last_lineno_class(self):
        node = astroid.extract_node(
            """
            class C(object):
                CONST = True

                def x(self, b):
                    print(b)

                def y(self):
                    pass
                    pass
            """
        )
        assert get_node_last_lineno(node) == 10

    def test_get_node_last_lineno_combined(self):
        node = astroid.extract_node(
            """
            class C(object):
                CONST = True

                def y(self):
                    try:
                        pass
                    except:
                        pass
                    finally:
                        pass
            """
        )
        assert get_node_last_lineno(node) == 11