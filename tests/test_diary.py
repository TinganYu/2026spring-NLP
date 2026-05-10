import sys
import os
import pytest

from diary import process_entry


def test_process_entry_basic():
    text = "今天感覺頭暈，有點難過"
    res = process_entry(text, meta={"user_id": "u1"})
    assert res.entry.text == text
    assert res.entry.meta.get("user_id") == "u1"
    assert hasattr(res, "emotion")
    assert hasattr(res, "symptoms")
    assert any(s.name == "頭暈" for s in res.symptoms)
