import sys
import json
from pathlib import Path
import pytest

# Ensure project root is importable when running this file directly.
sys.path.append(str(Path(__file__).resolve().parents[1]))

import website.app as app_module
from shared.pii import PIIItem, PIIReview


def test_diary_pii_review_endpoint(monkeypatch):
    review = {
        "needs_masking": True,
        "entities": [{"text": "0912-345-678", "category": "PhoneNumber", "start": 0, "end": 12, "confidence_score": 0.99}],
        "redacted_text": "聯絡我 ************",
    }
    monkeypatch.setattr(app_module, "review_pii", lambda text: review)

    client = app_module.app.test_client()
    response = client.post("/diary_pii_review", json={"text": "聯絡我 0912-345-678"})

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["needs_masking"] is True
    assert payload["entities"][0]["category"] == "PhoneNumber"
    assert payload["redacted_text"] == "聯絡我 ************"


@pytest.mark.integration  # 標記為整合測試 - 速度較慢
def test_diary_process_real_output_and_remove_data_sources(mock_azure_apis):
    """集成測試：驗證完整 API 流程（使用 conftest.py 的 mock）"""
    client = app_module.app.test_client()
    response = client.post(
        "/diary_process",
        json={"text": "昨晚因為腰痛睡得不好，整晚翻來覆去，導致今天精神很差且心情煩躁。中午去藥局買了布洛芬服用，藥效發揮後疼痛減輕到了 2 分，整個人才稍微放鬆下來。", "meta": {"user_id": "u1"}},
    )

    payload = response.get_json()
    print("\n=== API OUTPUT (mocked Azure) ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    assert response.status_code == 200, response.get_data(as_text=True)

    # API 返回 DiaryRecord 格式（not AnalysisResult）
    assert "data_sources" not in str(payload)
    assert "date" in payload  # DiaryRecord 有 date
    assert "emotion_label" in payload  # DiaryRecord 有 emotion_label
    assert "symptoms" in payload
