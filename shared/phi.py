import configparser
import os
from typing import Any, List, Optional, TypedDict

from azure.ai.textanalytics import HealthcareEntityRelation, TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

from shared.translate import TranslationResult, translate_text


config = configparser.ConfigParser()
config.read("config.ini")


def _get_setting(section: str, key: str, env_name: str, default: str = None) -> str:
    # 先讀 config.ini，讀不到再看環境變數
    try:
        value = config.get(section, key)
    except (configparser.NoSectionError, configparser.NoOptionError):
        value = os.getenv(env_name, default)
        
    return value.strip() if isinstance(value, str) else value


_AZURE_KEY = _get_setting("AzureLanguage", "AZURE_LANGUAGE_KEY", "AZURE_LANGUAGE_KEY")
_AZURE_ENDPOINT = _get_setting("AzureLanguage", "AZURE_LANGUAGE_ENDPOINT", "AZURE_LANGUAGE_ENDPOINT")


class HealthEntityItem(TypedDict, total=False):
    text: str
    normalized_text: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    offset: Optional[int]
    confidence_score: Optional[float]
    data_sources: List[dict]
    assertion: Optional[dict]

class HealthRelationItem(TypedDict, total=False):
    relation_type: Optional[str]
    roles: List[dict]

class HealthAnalysisResult(TypedDict, total=False):
    original_text: str
    translated_text: str
    entities: List[HealthEntityItem]
    relations: List[HealthRelationItem]
    translation: Optional[TranslationResult]
    detected_language: Optional[str]

_client: Optional[TextAnalyticsClient] = None


def _get_client() -> TextAnalyticsClient:
    global _client
    if _client is not None:
        # client 已建立過就直接重用，避免重複初始化
        return _client

    if not _AZURE_KEY or not _AZURE_ENDPOINT:
        raise RuntimeError("Azure Language 設定未完成，請檢查 config.ini 或環境變數。")

    # 建立 Azure Text Analytics client
    _client = TextAnalyticsClient(
        endpoint=_AZURE_ENDPOINT,
        credential=AzureKeyCredential(_AZURE_KEY),
    )
    return _client

def _to_entity_item(entity: Any) -> HealthEntityItem:
    """將 Azure HealthcareEntity 物件轉換為字典"""
    data_sources = [
        {"entity_id": src.entity_id, "name": src.name}
        for src in (entity.data_sources or [])
    ]
    assertion = None
    if entity.assertion:
        assertion = {
            "conditionality": entity.assertion.conditionality,
            "certainty": entity.assertion.certainty,
            "association": entity.assertion.association,
        }
    return {
        "text": entity.text or "",
        "normalized_text": entity.normalized_text,
        "category": entity.category,
        "subcategory": entity.subcategory,
        "offset": entity.offset,
        "confidence_score": entity.confidence_score,
        "data_sources": data_sources,# 這是各種醫療專屬編號(到時候可能沒用就刪了)
        "assertion": assertion,
    }

def _to_relation_item(relation: Any) -> HealthRelationItem:
    """將 Azure HealthcareRelation 物件轉換為字典"""
    roles = [
        {
            "name": role.name,
            "entity_text": role.entity.text if role.entity else None,
        }
        for role in (relation.roles or [])
    ]
    return {
        "relation_type": str(relation.relation_type) if relation.relation_type else None,
        "roles": roles,
    }


# Azure healthcare analysis 只吃英文，因此要丟翻譯後的文字
def analyze_healthcare_entities(
    text: str,
    target_language: str = "en",
    source_language: Optional[str] = None,
    translated_text: Optional[str] = None,
    include_translation: bool = True,
) -> HealthAnalysisResult:
    """Translate text to English and analyze healthcare entities/relation with Azure.

    Parameters
    ----------
    text:
        Input text in any supported source language.
    target_language:
        Translation target language for the preprocessing step. For Azure healthcare,
        this should usually be "en".
    source_language:
        Optional source language for translation.
    translated_text:
        If you already translated the text upstream, pass it here to avoid another translation call.
    include_translation:
        If True and translated_text is not supplied, this function will translate once.
    """
    if not text:
        # 空字串直接回傳空結果，避免多打 API
        return {
            "original_text": text,
            "translated_text": "",
            "entities": [],
            "relations": [],
            "translation": None,
            "detected_language": None,
        }

    translation_result = None
    final_text = translated_text

    if final_text is None and include_translation:
        # 如果外面沒有先翻譯過，這裡先翻一次
        translation_result = translate_text(
            text,
            target_language=target_language,
            source_language=source_language,
        )
        # translate_text now returns a dict
        translations = translation_result.get("translations", [])
        final_text = translations[0]["text"] if translations else text
    elif final_text is None:
        final_text = text

    client = _get_client()
    #Azure 醫療分析屬於複雜運算，採用的是「長時間執行作業 (Long-Running Operation, LRO)」。程式會先拿到一個 poller（輪詢器），然後用 .result() 等待 Azure 慢慢把結果算完傳回來。

    poller = client.begin_analyze_healthcare_entities([final_text], language=target_language)
    result = poller.result()

    # 過濾錯誤文件，只保留正常分析結果
    docs = [doc for doc in result if not doc.is_error]
    if not docs:
        error_docs = [doc for doc in result if doc.is_error]
        if error_docs:
            raise RuntimeError(f"Azure healthcare analysis failed: {error_docs[0].error.message}")
        return {
            "original_text": text,
            "translated_text": final_text,
            "entities": [],
            "relations": [],
            "translation": translation_result,
        }

    doc = docs[0]
    
    entities = [_to_entity_item(entity) for entity in (getattr(doc, "entities", []) or [])]
    relations = [_to_relation_item(relation) for relation in (getattr(doc, "entity_relations", []) or [])]

    detected_language = None
    if translation_result is not None:
        detected_language = translation_result.get("detected_language", None)

    return {
        "original_text": text,
        "translated_text": final_text,
        "entities": entities,
        "relations": relations,
        "translation": translation_result,
        "detected_language": detected_language,
    }


if __name__ == "__main__":
    sample = "我有頭痛，醫生叫我吃布洛芬，每天三次，每次兩顆，連續吃五天。"
    output = analyze_healthcare_entities(sample, target_language="en")
    print("original:", output["original_text"])
    print("translated:", output["translated_text"])
    print("entities:", [(item["text"], item["category"]) for item in output.get("entities", [])])
    print("relations:", [(item["relation_type"], [(r["name"], r["entity_text"]) for r in item.get("roles", [])]) for item in output.get("relations", [])])
