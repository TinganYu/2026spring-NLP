"""Convert structured weekly health data into a natural-language summary using Groq.

負責將趨勢 JSON 包裝成 prompt 並呼叫 Groq 的 chat/completions API。
"""
import configparser
import json
import os
from typing import Any, Dict, List, Optional
import requests

config = configparser.ConfigParser()
config.read("config.ini")

def _get_setting(section: str, key: str, env_name: str, default: str = None) -> str:
    value = config.get(section, key, fallback=os.getenv(env_name, default))
    return value.strip() if isinstance(value, str) else value

_GROQ_API_KEY = _get_setting("Groq", "GROQ_API_KEY", "GROQ_API_KEY")
_GROQ_MODEL = _get_setting("Groq", "MODEL", "GROQ_MODEL", "llama-3.3-70b-versatile")
_GROQ_BASE_URL = _get_setting("Groq", "BASE_URL", "GROQ_BASE_URL", "https://api.groq.com/openai/v1")



def _build_messages(trend_json: Dict[str, Any], instruction: str = None) -> List[Dict[str, str]]:
    instruction_text = instruction or (
        "## 角色與定位\n"
        "你是一位溫暖、貼心且專業的個人健康AI教練。你的任務是解讀使用者過去一段時間的健康數據，並提供日常關懷與建議。\n\n"
        
        "## 輸出格式嚴格規範（違者重罰）\n"
        "1. 必須完全使用【繁體中文（台灣）】輸出。\n"
        "2. 只能輸出溫暖、口語化的【白話文文字】。這是一封寫給使用者的信，不是工程報告。\n"
        "3. 絕對禁止輸出任何 JSON、Markdown 表格、程式碼區塊（如 ```json, **粗體**）或 API 欄位名稱（例如不要寫出 'emotion_score'、'trend_direction' 等字眼）。\n"
        "4. 採用親切的條列式重點，字數控制在 300-400 字之間，排版要舒適易讀。\n\n"
        "5. 不要輸出【歡迎詢問我】或【如果你有任何問題，請隨時告訴我】等開放問答、對話。\n\n"
        
        "## 內容解讀重點\n"
        "- 【情緒與趨勢】：用白話解釋情緒起伏（例如：倒退、漸入佳境、穩定），並給予情緒上的同理（如：『這週辛苦了』）。\n"
        "- 【症狀觀察】：指出明顯的症狀變化或持續存在的症狀（例如：『我注意到你這週頭痛的頻率增加了』）。\n"
        "- 【症狀與情緒關聯】：如果資料中顯示某些症狀與情緒變化有關聯，請用白話說明（例如：『看起來每當你感到心情不好時，都伴隨著睡眠不足...』、『看起來每當你睡眠品質變差時，就會感到心情不好...』）。\n"
        "- 【症狀與用藥關聯】：觀察數據中症狀與用藥的發生頻率，找出潛在關聯（例如：『我注意到你每次偏頭痛時，似乎都會吃布洛芬...』）。\n"
        "- 【行動指引】：給出 1~2 個溫暖、可行的小建議（例如：多喝水、提早半小時睡覺），盡量要與使用者症狀有關聯，不要給予嚴肅的醫療診斷。\n\n"
        
        "## 語氣範例\n"
        "『嗨！這段時間辛苦囉。看了一下你這幾天的紀錄，我發現前幾天你的心情稍微有點悶悶的，不過到了週末有明顯好轉喔！...』"    )

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
    trend_json: Dict[str, Any], # aggregator.py 裡面的所有資料
    instruction: str = None,
) -> str:
    """Use Groq to turn structured health data into a natural-language summary."""
    if not _GROQ_API_KEY:
        raise RuntimeError("Groq API Key 未設定，請檢查 config.ini 或環境變數。")

    payload = {
        "model": _GROQ_MODEL,
        "messages": _build_messages(trend_json, instruction=instruction),
        "temperature": 0.3, 
    }

    headers = { # Groq API 的認證和內容類型設定
        "Authorization": f"Bearer {_GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post( # 呼叫 Groq 的 chat/completions API
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
    choices = result.get("choices", []) # Groq 的回應格式通常會在 'choices' 欄位裡面
    summary = ""
    if choices:
        summary = choices[0].get("message", {}).get("content", "") or ""

    return summary









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
    print(out)