"""Pytest 配置和全局 fixtures - 所有測試都用 mock Azure API"""
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_azure_apis(monkeypatch):
    """Mock 所有 Azure API - 僅在測試中明確調用時使用"""
    
    # Mock Groq emotion detection
    mock_emotion = {
        "label": "neutral",
        "score": 0.5,
        "sentences": []
    }
    from diary import processor as processor_module
    monkeypatch.setattr(processor_module, "detect_emotion", lambda text: mock_emotion)
    
    # Mock Azure healthcare entities
    mock_phi = {
        "original_text": "",
        "translated_text": "",
        "entities": [],
        "relations": [],
        "translation": None,
        "detected_language": None,
    }
    def mock_analyze(text, **kwargs):
        mock_phi["original_text"] = text
        mock_phi["translated_text"] = text
        return mock_phi
    
    from shared import phi as phi_module
    monkeypatch.setattr(phi_module, "analyze_healthcare_entities", mock_analyze)
    
    # Mock Azure translator
    mock_translate_result = {
        "source_text": "",
        "detected_language": "en",
        "translations": [{"text": "", "to": "en"}]
    }
    def mock_translate(text, **kwargs):
        mock_translate_result["source_text"] = text
        mock_translate_result["translations"][0]["text"] = text
        return mock_translate_result
    
    from shared import translate as translate_module
    monkeypatch.setattr(translate_module, "translate_text", mock_translate)
    
    # Mock Azure PII detection
    mock_pii = {
        "needs_masking": False,
        "entities": [],
        "redacted_text": ""
    }
    from shared import pii as pii_module
    monkeypatch.setattr(pii_module, "review_pii", lambda text: mock_pii)
    
    yield  # 測試在這裡執行
