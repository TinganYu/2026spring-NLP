import configparser
import os
from typing import List, Optional, Sequence, Union, TypedDict
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

config = configparser.ConfigParser()
config.read("config.ini")

def _get_setting(section: str, key: str, env_name: str, default: str = None) -> str:
    value = config.get(section, key, fallback=os.getenv(env_name, default))
    return value.strip() if isinstance(value, str) else value

_AZURE_TRANSLATOR_KEY = _get_setting("AzureTranslator", "Key", "AZURE_TRANSLATOR_KEY")
_AZURE_TRANSLATOR_ENDPOINT = _get_setting("AzureTranslator", "Endpoint", "AZURE_TRANSLATOR_ENDPOINT")
_AZURE_TRANSLATOR_REGION = _get_setting("AzureTranslator", "Region", "AZURE_TRANSLATOR_REGION")

class TranslationItem(TypedDict, total=False):
    text: str
    to: str
    # alignment 已移除，沒有用

class TranslationResult(TypedDict, total=False):
    source_text: str
    detected_language: Optional[str]
    translations: List[TranslationItem]

def _get_client() -> TextTranslationClient:
    if not _AZURE_TRANSLATOR_KEY or not _AZURE_TRANSLATOR_ENDPOINT or not _AZURE_TRANSLATOR_REGION:
        raise RuntimeError("Azure Translator 設定未完成，請檢查 config.ini 或環境變數。")

    return TextTranslationClient(
        credential=AzureKeyCredential(_AZURE_TRANSLATOR_KEY),
        endpoint=_AZURE_TRANSLATOR_ENDPOINT,
        region=_AZURE_TRANSLATOR_REGION,
    )


def translate_text(
    text: str,
    target_language: Union[str, Sequence[str]],
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
    targets = [target_language] if isinstance(target_language, str) else list(target_language) # Azure Translator API 需要一個 list，如果輸入是str(單一個)就轉成list，如果已經是list就直接使用。
    if not targets:
        raise ValueError("target_language 不可為空。")

    body = [text]

    try:
        response = client.translate(
            body=body,
            to_language=targets,
            from_language=source_language,
        )
    except HttpResponseError as exc:
        raise RuntimeError(f"Azure 翻譯失敗: {exc}") from exc
    if not response:
        return {"source_text": text, "detected_language": None, "translations": []}

    first_item = response[0] # Azure Translator API 的回應是一個列表，每個元素對應一個輸入文本。因為我們一次只翻譯一段文本，所以取第一個元素即可。
    detected_language = getattr(getattr(first_item, "detected_language", None), "language", None)
    
    translation_list: List[TranslationItem] = [ {"text": translation.text, "to": translation.to} for translation in first_item.translations]
    
    return {
        "source_text": text,
        "detected_language": detected_language,
        "translations": translation_list,
    }





if __name__ == "__main__":
    sample_text = input("請輸入要翻譯的句子: ")
    target_language = input("請輸入目標語言（例如 en、zh-Hant、vi、id）: ").strip() or "en"
    result = translate_text(sample_text, target_language=target_language)

    # result is now a dict
    print("原文：", result["source_text"])
    print("偵測語言：", result["detected_language"])
    for item in result["translations"]:
        print(f"翻譯 ({item['to']})：{item['text']}")
