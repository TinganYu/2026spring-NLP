"""Convert structured weekly health data into a natural-language summary using Groq.

負責將趨勢 JSON 包裝成 prompt 並呼叫 Groq 的 chat/completions API。
"""
import configparser
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import requests

config = configparser.ConfigParser()
config.read("config.ini")

def _get_setting(section: str, key: str, env_name: str, default: str = None) -> str:
    value = config.get(section, key, fallback=os.getenv(env_name, default))
    return value.strip() if isinstance(value, str) else value

_GROQ_API_KEY = _get_setting("Groq", "GROQ_API_KEY", "GROQ_API_KEY")
_GROQ_MODEL = _get_setting("Groq", "MODEL", "GROQ_MODEL", "llama-3.1-70b-versatile")
_GROQ_BASE_URL = _get_setting("Groq", "BASE_URL", "GROQ_BASE_URL", "https://api.groq.com/openai/v1")

@dataclass
class GroqSummaryResult:
    prompt: str
    summary: str
    raw_response: Dict[str, Any]


def _build_messages(trend_json: Dict[str, Any], instruction: str = None) -> List[Dict[str, str]]:
    instruction_text = instruction or (
        "你是一位專業且溫暖的健康教練。請根據使用者過去 7 天的情緒、症狀、用藥與 PHI 資料，"
        "總結情緒趨勢，指出情緒與症狀之間可能的關聯，並用繁體中文輸出條列式重點。"
    )

    return [
        {
            "role": "system",
            "content": instruction_text,
        },
        {
            "role": "user",
            "content": f"以下是資料 JSON：\n{json.dumps(trend_json, ensure_ascii=False, indent=2)}",
        },
    ]


def summarize_health_trend(
    trend_json: Dict[str, Any],
    instruction: str = None,
    model: Optional[str] = None,
) -> GroqSummaryResult:
    """Use Groq to turn structured health data into a natural-language summary."""
    if not _GROQ_API_KEY:
        raise RuntimeError("Groq API Key 未設定，請檢查 config.ini 或環境變數。")

    payload = {
        "model": model or _GROQ_MODEL,
        "messages": _build_messages(trend_json, instruction=instruction),
        "temperature": 0.3,
    }

    headers = {
        "Authorization": f"Bearer {_GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{_GROQ_BASE_URL.rstrip('/')}/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        details = response.text if response is not None else ""
        raise RuntimeError(f"Groq summarize failed: {exc} | details: {details}") from exc

    result = response.json()
    choices = result.get("choices", [])
    summary = ""
    if choices:
        summary = choices[0].get("message", {}).get("content", "") or ""

    return GroqSummaryResult(
        prompt=json.dumps(trend_json, ensure_ascii=False),
        summary=summary,
        raw_response=result,
    )


if __name__ == "__main__":
    sample = {
        "emotion_trend": [
            {"date": "2026-05-01", "emotion_label": "negative", "emotion_score": 0.82},
            {"date": "2026-05-02", "emotion_label": "neutral", "emotion_score": 0.55},
        ],
        "symptom_trend": [
            {"date": "2026-05-01", "symptom_or_sign": ["headache"]},
        ],
    }
    out = summarize_health_trend(sample)
    print(out.summary)