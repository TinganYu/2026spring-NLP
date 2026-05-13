import sys
import os
import pytest
# tests/conftest.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from dataclasses import dataclass

from diary.processor import process_entry
from diary.models import EmotionResult


@dataclass
class _FakeEntity:
    text: str
    category: str


@dataclass
class _FakeRelation:
    relation_type: str
    roles: list


@dataclass
class _FakePhiResult:
    original_text: str
    translated_text: str
    translation: dict
    entities: list
    relations: list


def _build_fake_phi_result(text: str):
    return _FakePhiResult(
        original_text=text,
        translated_text=text,
        translation={},
        entities=[_FakeEntity(text="headache", category="SymptomOrSign")],
        relations=[_FakeRelation(relation_type="TimeOfCondition", roles=[])],
    )


def test_process_entry_basic():
    text = "昨晚因為腰痛睡得不好，整晚翻來覆去，導致今天精神很差且心情煩躁。中午去藥局買了布洛芬服用，藥效發揮後疼痛減輕到了 2 分，整個人才稍微放鬆下來。"
    res = process_entry(text, meta={"user_id": "u1"})
    print(res)
    # assert res.entry.text == text
    assert res.entry.meta.get("user_id") == "u1"
    assert hasattr(res, "emotion")
    assert hasattr(res, "symptoms")


def test_process_entry_extra_does_not_include_pii_payload(monkeypatch):
    text = "昨晚因為腰痛睡得不好。"
    from diary import processor as processor_module

    monkeypatch.setattr(processor_module, "detect_emotion", lambda value: EmotionResult(label="neutral", score=0.5, sentences=[]))
    monkeypatch.setattr(processor_module, "analyze_healthcare_entities", lambda value, target_language="en": _build_fake_phi_result(value))

    res = process_entry(text, meta={"user_id": "u1"})

    assert "pii_review" not in res.extra
    assert "pii_applied" not in res.extra
