import sys
import os
import pytest
# tests/conftest.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from diary.processor import process_entry


def test_process_entry_basic():
    text = "昨晚因為腰痛睡得不好，整晚翻來覆去，導致今天精神很差且心情煩躁。中午去藥局買了布洛芬服用，藥效發揮後疼痛減輕到了 2 分，整個人才稍微放鬆下來。"
    res = process_entry(text, meta={"user_id": "u1"})
    print(res)
    # assert res.entry.text == text
    assert res.entry.meta.get("user_id") == "u1"
    assert hasattr(res, "emotion")
    assert hasattr(res, "symptoms")
