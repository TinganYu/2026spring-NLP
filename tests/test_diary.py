import sys
import os
import pytest
# tests/conftest.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from diary.processor import process_entry
from diary.models import EmotionResult


def _build_fake_phi_result(text: str):
    """Build a fake PHI result dict (TypedDict)"""
    return {
        "original_text": text,
        "translated_text": text,
        "translation": None,
        "entities": [{"text": "headache", "category": "SymptomOrSign", "normalized_text": None, "subcategory": None, "offset": None, "confidence_score": None, "data_sources": [], "assertion": None}],
        "relations": [{"relation_type": "TimeOfCondition", "roles": []}],
        "detected_language": None,
    }


def test_process_entry_basic():
    text = "昨晚因為腰痛睡得不好，整晚翻來覆去，導致今天精神很差且心情煩躁。中午去藥局買了布洛芬服用，藥效發揮後疼痛減輕到了 2 分，整個人才稍微放鬆下來。"
    res = process_entry(text, meta={"user_id": "u1"})
    print(res)
    # res is now a dict (AnalysisResult TypedDict)
    assert res["entry"]["meta"].get("user_id") == "u1"
    assert "emotion" in res
    assert "symptoms" in res


def test_process_entry_extra_does_not_include_pii_payload(monkeypatch):
    text = "昨晚因為腰痛睡得不好。"
    from diary import processor as processor_module

    monkeypatch.setattr(processor_module, "detect_emotion", lambda value: {"label": "neutral", "score": 0.5, "sentences": []})
    monkeypatch.setattr(processor_module, "analyze_healthcare_entities", lambda value, target_language="en": _build_fake_phi_result(value))

    res = process_entry(text, meta={"user_id": "u1"})

    # res and res["phi"] are now dicts
    phi_blob = res.get("phi", {})
    assert "pii_review" not in phi_blob
    assert "pii_applied" not in phi_blob
