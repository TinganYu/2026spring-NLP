"""Per-entry processing: 以單筆日記文本產生標準化的 `AnalysisResult`。

職責：偵測情緒、呼叫 PHI 分析、回傳可存入 DB 的結構化結果。
不要在這裡做昂貴的跨筆聚合或 on-demand 的深度分析。
"""

from dataclasses import asdict
from typing import Dict, Any, List
from .models import DiaryEntry, AnalysisResult
from .emotion import detect_emotion
from shared.phi import analyze_healthcare_entities

PHI_INTERESTING_CATEGORIES = {
    "SymptomOrSign",
    "MedicationName",
    "Dosage",
    "Frequency",
    "RouteOfAdministration",
    "BodyStructure",
    "Diagnosis",
    "ProcedureName",
    "TestName",
    "TreatmentName",
    "Duration",
    "ConditionQualifier",
}
# SCORE_PATTERNS = [
#                 r'疼痛[程度級別指數]*\s*(\d+)\s*[分級]?',   # 疼痛程度4分、疼痛4級
#                 r'痛[到了]?\s*(\d+)\s*[分級]',              # 痛到8分
#                 r'[不舒服難受]*程度\s*(\d+)\s*[分級]?',      # 不舒服程度3分
#                 r'(\d+)\s*/\s*10',                          # 4/10
#             ]
def _summarize_phi(health_result):
    entities = [asdict(entity) for entity in health_result.entities]
    relations = [asdict(relation) for relation in health_result.relations]

    entities_by_category = {}
    for entity in entities:
        category = entity["category"] or "Unknown"
        entities_by_category.setdefault(category, []).append(entity)

    important_entities = [
        entity
        for entity in entities
        if entity["category"] in PHI_INTERESTING_CATEGORIES
    ]

    return {
        "input_text": health_result.original_text,
        "translated_text": health_result.translated_text,
        "translation": health_result.translation,
        "important_entities": important_entities,
        "entities_by_category": entities_by_category,
        "entities": entities,
        "relations": relations,
    }

# 最主要的 function：把單筆日記文本轉成 AnalysisResult
def process_entry(text: str, meta: dict = None) -> AnalysisResult:
    """Orchestrator: receives a diary text and returns structured analysis."""
    processed_text = text

    entry = DiaryEntry(text=processed_text, meta=meta or {})
    emotion = detect_emotion(processed_text)
    phi_result = analyze_healthcare_entities(processed_text, target_language="en")
    phi_summary = _summarize_phi(phi_result)
    
    symptoms = [  # 因為症狀是最重要的一塊，所以額外濾出
        entity for entity in phi_summary.get("entities", []) if entity.get("category") == "SymptomOrSign"
    ]

    return AnalysisResult(
        entry=entry,
        emotion=emotion,
        symptoms=symptoms,
        extra={
            "phi": phi_summary,
        },
    )

# processor.py 現在僅負責單筆日記的 AI 呼叫與簡單整理，
# 將較複雜的 PHI -> 前端格式化邏輯移至 diary.analysis