import sys
import json
from pathlib import Path

# Ensure project root is importable when running this file directly.
sys.path.append(str(Path(__file__).resolve().parents[1]))

import app as app_module
def test_diary_process_real_output_and_remove_data_sources():

    client = app_module.app.test_client()
    response = client.post(
        "/diary_process",
        json={"text": "昨晚因為腰痛睡得不好，整晚翻來覆去，導致今天精神很差且心情煩躁。中午去藥局買了布洛芬服用，藥效發揮後疼痛減輕到了 2 分，整個人才稍微放鬆下來。", "meta": {"user_id": "u1"}},
    )

    payload = response.get_json()
    print("\n=== REAL API OUTPUT ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    assert response.status_code == 200, response.get_data(as_text=True)

    # API layer should strip data_sources recursively.
    assert "data_sources" not in str(payload)
    assert "entry" in payload
    assert "symptoms" in payload
