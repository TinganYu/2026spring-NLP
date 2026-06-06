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
    target_language: Union[str, Sequence[str]], # sequence 是 list 或 tuple，允許多個目標語言
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



# ============= Convenience function for common use case =============
def translate_list(
    texts: List[str], 
    target_language: str, 
    source_language: Optional[str] = None
) -> List[str]:
    """直接同時翻譯多個文本，回傳翻譯後的字符串列表。
    """
    if not texts:
        return []
        
    client = _get_client()
    
    try:
        response = client.translate(
            body=texts,
            to_language=[target_language],
            from_language=source_language,
        )
    except HttpResponseError as exc:
        raise RuntimeError(f"Azure 批次翻譯失敗: {exc}") from exc
        
    if not response:
        return texts

    return [item.translations[0].text for item in response]

def translate_to(text: str, target_language: str, source_language: Optional[str] = None) -> str:
    """只回傳第一個翻譯結果的文本，適合大多數只需要單一str翻譯的情況。"""
    if not text:
        return text
    results = translate_list([text], target_language=target_language, source_language=source_language)
    
    return results[0] if results else text




import datetime
if __name__ == "__main__":
    time = datetime.datetime.now()
    sample_text = ["Hello, world!", "How are you?"]#input("請輸入要翻譯的句子: ")
    target_language ="en" #input("請輸入目標語言（例如 en、zh-Hant、vi、id）: ").strip() or "en"
    # result = translate_list(sample_text, target_language=target_language)
    result = [translate_to(k, target_language=target_language) for k in sample_text]
    endtime = datetime.datetime.now()
    print("總時間：", endtime - time)

    # result is now a list of strings
    print("原文：", sample_text)
    print("翻譯：", result[0])
    print(f"翻譯 ({target_language})：{result[0]}")
