from dataclasses import asdict

from .models import DiaryEntry, AnalysisResult
from .emotion import detect_emotion
from .analysis import build_correlation_discovery, build_doctor_visit_prep
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

def _summarize_phi(health_result):
    entities = [asdict(entity) for entity in health_result.entities]
    relations = [asdict(relation) for relation in health_result.relations]

    entities_by_category = {}
    for entity in entities:
        category = entity["category"] or "Unknown"
        entities_by_category.setdefault(category, []).append(entity) # 按照 category 分類實體，方便後續分析和視覺化

    important_entities = [ # 這邊是根據預定義的 PHI_INTERESTING_CATEGORIES 來篩選出重要的實體，這樣在後續的分析和視覺化中就可以專注於這些類別的實體，而不會被其他不太相關的實體干擾
        entity
        for entity in entities
        if entity["category"] in PHI_INTERESTING_CATEGORIES
    ]

    symptom_or_sign = [
        entity
        for entity in entities
        if entity["category"] == "SymptomOrSign"
    ]

    return {
        "input_text": health_result.original_text,
        "translated_text": health_result.translated_text,
        "translation": health_result.translation,
        "symptom_or_sign": symptom_or_sign, # 特別把症狀和體徵整理出來，因為這是日記分析中最常關注的資訊之一
        "important_entities": important_entities,
        "entities_by_category": entities_by_category,
        "entities": entities,
        "relations": relations,
    }


# 不再把 Symptom 轉成 dataclass，直接使用 summarize_phi 內的 symptom_or_sign

def process_entry(text: str, meta: dict = None) -> AnalysisResult:
    """Orchestrator: receives a diary text and returns structured analysis.

    The caller is responsible for any PII review or masking before invoking this.
    """
    processed_text = text

    entry = DiaryEntry(text=processed_text, meta=meta or {})
    emotion = detect_emotion(processed_text)
    phi_result = analyze_healthcare_entities(processed_text, target_language="en")
    phi_summary = _summarize_phi(phi_result)
    # 保持 symptoms 為 summarize_phi 的原始清單（list of dict）
    symptoms = phi_summary.get("symptom_or_sign", [])
    
    return AnalysisResult(
        entry=entry,
        emotion=emotion,
        symptoms=symptoms,
        extra={
            "phi": phi_summary,
            "analysis": { #這只是我暫時對phi裡面的資料作處理，但是之後可能會再改
                "correlation_discovery": build_correlation_discovery(phi_summary, emotion_label=emotion.label),
                "doctor_visit_prep": build_doctor_visit_prep(phi_summary),
            },
        },
    )

