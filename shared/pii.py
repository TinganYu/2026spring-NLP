import configparser
import os
from typing import Any, Dict, List, Optional, TypedDict
import requests

config = configparser.ConfigParser()
config.read("config.ini")

def _get_setting(env_name: str, default: str = None) -> str:
    value = config.get("AzureLanguage", env_name, fallback=os.getenv(env_name, default))
    return value.strip() if isinstance(value, str) else value

_AZURE_KEY = _get_setting("AZURE_LANGUAGE_KEY")
_AZURE_ENDPOINT = _get_setting("AZURE_LANGUAGE_ENDPOINT")
_AZURE_LANGUAGE = _get_setting("AZURE_LANGUAGE_DEFAULT", "zh-Hant")

class PIIItem(TypedDict, total=False):
    text: str
    category: str
    start: int
    end: int
    confidence_score: Optional[float]

class PIIReview(TypedDict, total=False):
    needs_masking: bool
    entities: List[PIIItem]
    redacted_text: Optional[str]



def review_pii(text: str, language: Optional[str] = None) -> PIIReview:
    """檢查文本中是否包含 PII，並回傳整理好的 review 結果。"""
    if not _AZURE_KEY or not _AZURE_ENDPOINT:
        raise RuntimeError("Azure API Key 或 Endpoint 未設定。")

    endpoint = _AZURE_ENDPOINT.rstrip("/")
    api_url = f"{endpoint}/language/:analyze-text?api-version=2025-11-15-preview" 

    headers = { # Azure PII API 的認證和內容類型設定
        "Ocp-Apim-Subscription-Key": _AZURE_KEY,
        "Content-Type": "application/json",
    }

    body = {
        "kind": "PiiEntityRecognition",
        "parameters": {
            "modelVersion": "latest",
            "piiCategories": [
                "Person",
                "PhoneNumber",
                "Email",
                "Address",
                "IPAddress",
                "CreditCardNumber",
                "Organization",
            ],
            "redactionPolicy": {
                "policyKind": "entityMask", # 使用上課教的實體遮罩會將他替換成類似 [PII_Person] 的標籤
            },
        },
        "analysisInput": {
            "documents": [
                {
                    "id": "1",
                    "language": language or _AZURE_LANGUAGE,
                    "text": text or "",
                }
            ]
        },
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=body, timeout=30)
        response.raise_for_status() # 如果 HTTP 回應狀態碼不是 200，會丟出例外

    # ======這幾段基本上只是做檢查和錯誤處理===================================
    except requests.exceptions.RequestException as exc:
        details = ""
        if hasattr(exc, "response") and exc.response is not None:
            details = f" | details: {exc.response.text}"
        raise RuntimeError(f"Azure PII API request failed: {exc}{details}") from exc

    result = response.json()
    if "results" not in result or "documents" not in result["results"]:
        raise RuntimeError(f"Unexpected Azure PII response format: {result}")

    docs = result["results"]["documents"]
    if not docs:
        parsed_entities: List[Dict[str, Any]] = []
        parsed_redacted_text = text
    # ========================================================================
    else:
        doc = docs[0]
        parsed_entities = doc.get("entities", [])
        parsed_redacted_text = doc.get("redactedText", text)

    # 轉換成自定義 dict 序列
    items: List[PIIItem] = []
    for e in parsed_entities:
        offset = int(e.get("offset", 0) or 0)
        length = int(e.get("length", 0) or 0)
        items.append({
            "text": e.get("text", ""),
            "category": e.get("category", "Unknown"),
            "start": offset,
            "end": offset + length,
            "confidence_score": e.get("confidenceScore"),
        })

    return {
        "needs_masking": len(items) > 0,
        "entities": items,
        "redacted_text": parsed_redacted_text,
    }




if __name__ == "__main__":
    sample = "你好，我是陳大文，手機 0912-345-678，email: test@example.com。"
    review = review_pii(sample)
    print("needs_masking:", review.needs_masking)
    print("entities:", [(e.text, e.category) for e in review.entities])
    print("masked:", review.redacted_text)