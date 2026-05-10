import configparser
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

config = configparser.ConfigParser()
config.read("config.ini")


def _get_setting(env_name: str, default: str = None) -> str:
    try:
        return config.get("AzureLanguage", env_name).strip()
    except Exception:
        value = os.getenv(env_name, default)
        return value.strip() if isinstance(value, str) else value


_AZURE_KEY = _get_setting("AZURE_LANGUAGE_KEY")
_AZURE_ENDPOINT = _get_setting("AZURE_LANGUAGE_ENDPOINT")
_AZURE_LANGUAGE = _get_setting("AZURE_LANGUAGE_DEFAULT", "zh-Hant")


@dataclass
class PIIItem:
    text: str
    category: str
    start: int
    end: int
    confidence_score: Optional[float] = None


@dataclass
class PIIReview:
    needs_masking: bool
    entities: List[PIIItem]
    redacted_text: Optional[str] = None


def _call_pii_api(text: str, language: Optional[str] = None) -> Dict[str, Any]:
    '''
    調用 Azure PII API 進行分析
    
    輸出:
    entities列表
    redacted_text: 已經過遮蔽處理的文本
    '''
    if not _AZURE_KEY or not _AZURE_ENDPOINT:
        raise RuntimeError("Azure API Key 或 Endpoint 未設定。")

    endpoint = _AZURE_ENDPOINT.rstrip("/")
    api_url = f"{endpoint}/language/:analyze-text?api-version=2025-11-15-preview"
    
    headers = {
        "Ocp-Apim-Subscription-Key": _AZURE_KEY,
        "Content-Type": "application/json",
    }
    
    # 直接在此定義 request body，乾淨俐落
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
                "policyKind": "entityMask",
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
        response.raise_for_status()
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
        return {"entities": [], "redacted_text": text}

    doc = docs[0]
    entities = doc.get("entities", [])
    redacted_text = doc.get("redactedText", text)

    return {
        "entities": entities,
        "redacted_text": redacted_text,
    }


def review_pii(text: str, language: Optional[str] = None) -> PIIReview:
    '''
    檢查文本中是否包含PII（Personally Identifiable Information）

    輸出格式:
        {
        "needs_masking": true,
        "entities": [
            {
            "text": "0912-345-678",
            "category": "PhoneNumber",
            "start": 5,
            "end": 17,
            "confidence_score": 0.99
            }...
        ],
        "redacted_text": "聯絡我 *********** 或 ****************"
        }
    '''
    parsed = _call_pii_api(text, language=language)

    items: List[PIIItem] = []
    for e in parsed["entities"]:
        offset = int(e.get("offset", 0) or 0)  #這裡保留字的位置，說不定前端可以加入顏色、螢光筆顯示?
        length = int(e.get("length", 0) or 0)
        items.append(
            PIIItem(
                text=e.get("text", ""),
                category=e.get("category", "Unknown"),
                start=offset,
                end=offset + length,
                confidence_score=e.get("confidenceScore"),
            )
        )

    return PIIReview(
        needs_masking=len(items) > 0,
        entities=items,
        redacted_text=parsed["redacted_text"],
    )

# ============= Helper functions for common use cases =============
# 這些函數提供更簡單的接口，讓使用者可以直接獲取PII實體列表、是否需要遮蔽，以及遮蔽後的文本。
# 但要先呼叫review_pii來避免重複調用API

def detect_pii(text: str, language: Optional[str] = None) -> List[PIIItem]:
    '''只回傳PII實體列表，不包含redacted_text等額外資訊'''
    return review_pii(text, language=language).entities


def has_pii(text: str, language: Optional[str] = None) -> bool:
    '''只回傳是否需要遮蔽，不包含實體列表或redacted_text等額外資訊'''
    return review_pii(text, language=language).needs_masking


def mask_pii(
    text: str,
    language: Optional[str] = None,
    review: Optional[PIIReview] = None,
) -> str:
    """只回傳 Azure redaction result.
    Pass `review` when you already called `review_pii` to avoid an extra API call.
    """
    pii_review = review or review_pii(text, language=language)
    return pii_review.redacted_text or text


if __name__ == "__main__":
    sample = "你好，我是陳大文，手機 0912-345-678，email: test@example.com。"
    review = review_pii(sample)
    print("needs_masking:", review.needs_masking)
    print("entities:", [(e.text, e.category) for e in review.entities])
    print("masked:", review.redacted_text)