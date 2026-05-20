import configparser
import os
from typing import List, Optional, Sequence, Union, TypedDict

from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError


config = configparser.ConfigParser()
config.read("config.ini")


def _get_setting(section: str, key: str, env_name: str, default: str = None) -> str:
    try:
        value = config.get(section, key)
    except (configparser.NoSectionError, configparser.NoOptionError):
        value = os.getenv(env_name, default)
        
    return value.strip() if isinstance(value, str) else value


_AZURE_TRANSLATOR_KEY = _get_setting("AzureTranslator", "Key", "AZURE_TRANSLATOR_KEY")
_AZURE_TRANSLATOR_ENDPOINT = _get_setting("AzureTranslator", "Endpoint", "AZURE_TRANSLATOR_ENDPOINT")
_AZURE_TRANSLATOR_REGION = _get_setting("AzureTranslator", "Region", "AZURE_TRANSLATOR_REGION")


class TranslationItem(TypedDict, total=False):
    text: str
    to: str
    # alignment 已移除，前端/上層負責處理對齊需求


class TranslationResult(TypedDict, total=False):
    source_text: str
    detected_language: Optional[str]
    translations: List[TranslationItem]


_client: Optional[TextTranslationClient] = None


def _get_client() -> TextTranslationClient:
    global _client
    if _client is not None:
        return _client

    if not _AZURE_TRANSLATOR_KEY or not _AZURE_TRANSLATOR_ENDPOINT or not _AZURE_TRANSLATOR_REGION:
        raise RuntimeError("Azure Translator 設定未完成，請檢查 config.ini 或環境變數。")

    _client = TextTranslationClient(
        credential=AzureKeyCredential(_AZURE_TRANSLATOR_KEY),
        endpoint=_AZURE_TRANSLATOR_ENDPOINT,
        region=_AZURE_TRANSLATOR_REGION,
    )
    return _client


TargetLanguage = Union[str, Sequence[str]]


def _infer_source_language(text: str) -> Optional[str]:
    """簡單猜來源語言；目前只針對中文文本回傳 zh-Hant，避免 Azure 自動偵測誤判。"""
    if not text:
        return None

    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            return "zh-Hant"
    return None


def translate_text(
    text: str,
    target_language: TargetLanguage,
    source_language: Optional[str] = None,
) -> TranslationResult:
    """Translate text with Azure Translator.

    Parameters
    ----------
    text:
        Source text to translate.
    target_language:
        A single target language code or a list of codes, e.g. "en", "zh-Hant".
    source_language:
        Optional source language. If omitted, Azure can auto-detect.
    """
    if not text:
        return {"source_text": text, "detected_language": None, "translations": []}

    client = _get_client()
    targets = [target_language] if isinstance(target_language, str) else list(target_language)
    if not targets:
        raise ValueError("target_language 不可為空。")

    # 沒有指定來源語言時，先對中文文本做簡單推斷，避免 Azure 誤判
    inferred_source_language = source_language or _infer_source_language(text)

    body = [text]

    try:
        response = client.translate(
            body=body,
            to_language=targets,
            from_language=inferred_source_language,
        )
    except HttpResponseError as exc:
        raise RuntimeError(f"Azure 翻譯失敗: {exc}") from exc

    if not response:
        return {"source_text": text, "detected_language": None, "translations": []}

    first_item = response[0]
    detected_language = getattr(getattr(first_item, "detected_language", None), "language", None)
    translations = [{"text": translation.text, "to": translation.to} for translation in first_item.translations]

    return {
        "source_text": text,
        "detected_language": detected_language,
        "translations": translations,
    }


# `_get_original_text_from_alignment` 已移除 — 翻譯對齊功能改由前端處理

# ============= Convenience function for common use case =============
# 只回傳第一個翻譯結果的文本，適合大多數只需要單一翻譯的情況。
def translate_to(text: str, target_language: str, source_language: Optional[str] = None) -> str:
    """Translate text and return the first translated string for the requested target language."""
    result = translate_text(text, target_language=target_language, source_language=source_language)
    # result is now a dict
    if not result.get("translations"):
        return text
    return result["translations"][0]["text"]


if __name__ == "__main__":
    sample_text = input("請輸入要翻譯的句子: ")
    target_language = input("請輸入目標語言（例如 en、zh-Hant、vi、id）: ").strip() or "en"
    result = translate_text(sample_text, target_language=target_language)

    # result is now a dict
    print("原文：", result["source_text"])
    print("偵測語言：", result["detected_language"])
    for item in result["translations"]:
        print(f"翻譯 ({item['to']})：{item['text']}")
