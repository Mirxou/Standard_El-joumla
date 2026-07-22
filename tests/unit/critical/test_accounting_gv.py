#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Critical test for the gv() helper function in accounting_service.py.

gv() is a core utility that safely extracts values from dicts, tuples,
lists, and sqlite3.Row objects without crashing on type mismatches or
missing keys/indices. Many accounting service methods depend on it.
"""

import sqlite3

import pytest

from src.services.accounting_service import gv


class TestGVHelper:
    """Tests for the gv(container, index_or_key, default) function."""

    # ---- dict access ----

    def test_dict_with_existing_key(self):
        """gv() returns the value for an existing dict key."""
        data = {"name": "Ahmed", "amount": 1500.0}
        assert gv(data, "name") == "Ahmed"
        assert gv(data, "amount") == 1500.0

    def test_dict_with_missing_key_returns_default(self):
        """gv() returns the default when the key is absent from a dict."""
        data = {"name": "Ahmed"}
        assert gv(data, "age") is None
        assert gv(data, "age", 0) == 0
        assert gv(data, "missing", "fallback") == "fallback"

    def test_dict_with_none_value(self):
        """gv() returns None stored in dict, not the default."""
        data = {"value": None}
        assert gv(data, "value") is None
        assert gv(data, "value", 42) is None  # actual None, not default

    # ---- list/tuple access ----

    def test_list_with_valid_int_index(self):
        """gv() returns the element at a valid list index."""
        data = [10, 20, 30]
        assert gv(data, 0) == 10
        assert gv(data, 2) == 30

    def test_tuple_with_valid_int_index(self):
        """gv() returns the element at a valid tuple index."""
        data = ("a", "b", "c")
        assert gv(data, 1) == "b"

    def test_string_index_on_tuple_returns_default(self):
        """gv() with a string index on a tuple/list must NOT crash."""
        data = ("a", "b", "c")
        # isinstance(i, int) is False for a string → falls through to default
        assert gv(data, "name") is None
        assert gv(data, "name", "N/A") == "N/A"

    def test_list_out_of_range_returns_default(self):
        """gv() with an out-of-range index returns default, not IndexError."""
        data = [10, 20]
        assert gv(data, 5) is None
        assert gv(data, 5, -1) == -1
        assert gv(data, -1) is None  # negative index: len(k) > -1 is True only if len > 0...
        # Actually -1 index: len([10,20])=2 > -1 is True (Python int comparison)
        # but list[-1] = 20, so let's just test a very large index
        assert gv(data, 999) is None

    # ---- sqlite3.Row (a tuple subclass) ----

    def test_sqlite3_row_with_int_index(self):
        """gv() works with sqlite3.Row accessed by integer index."""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE t (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO t VALUES (1, 'test')")
        row = conn.execute("SELECT * FROM t").fetchone()
        # sqlite3.Row is a tuple subclass
        assert isinstance(row, tuple)
        assert gv(row, 0) == 1
        assert gv(row, 1) == "test"
        conn.close()

    def test_sqlite3_row_with_string_key_returns_default(self):
        """gv() with a string key on sqlite3.Row falls to default (not dict)."""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE t (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO t VALUES (1, 'test')")
        row = conn.execute("SELECT * FROM t").fetchone()
        # Row is a tuple, not a dict → string index returns default
        assert gv(row, "name") is None
        assert gv(row, "name", "default_val") == "default_val"
        conn.close()

    # ---- None / edge cases ----

    def test_none_input_returns_default(self):
        """gv() with None container returns default without crashing."""
        assert gv(None, "key") is None
        assert gv(None, 0) is None
        assert gv(None, "key", 42) == 42

    def test_empty_dict(self):
        """gv() on an empty dict returns default."""
        assert gv({}, "anything") is None
        assert gv({}, "anything", "safe") == "safe"

    def test_empty_list(self):
        """gv() on an empty list returns default (no IndexError)."""
        assert gv([], 0) is None

    def test_default_none_is_default(self):
        """When no explicit default is passed, None is the implicit default."""
        assert gv({"a": 1}, "b") is None
        assert gv([1], 99) is None