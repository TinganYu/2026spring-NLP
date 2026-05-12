from dataclasses import asdict

from .models import DiaryEntry, AnalysisResult
from .emotion import detect_emotion
from .analysis import build_correlation_discovery, build_doctor_visit_prep
from shared.pii import review_pii
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

    important_entities = [
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

# 這裡的apply_pii_mask是使用者的選項，決定是否要在分析前先遮蔽PII。預設為True，表示會遮蔽。
def process_entry(text: str, meta: dict = None, apply_pii_mask: bool = True) -> AnalysisResult:
    """Orchestrator: receives a diary text and returns structured analysis.

    It first checks whether the text contains PII. If `apply_pii_mask` is True,
    the text will be masked before emotion and symptom analysis.
    """
    pii_review = review_pii(text)
    processed_text = (
        pii_review.redacted_text if apply_pii_mask and pii_review.needs_masking else text
    )

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
            "pii_review": {
                "needs_masking": pii_review.needs_masking,
                "entities": [
                    {
                        "text": entity.text,
                        "category": entity.category,
                        "start": entity.start,
                        "end": entity.end,
                        "confidence_score": entity.confidence_score,
                    }
                    for entity in pii_review.entities
                ],
            },
            "pii_applied": apply_pii_mask and pii_review.needs_masking,
            "phi": phi_summary,
            "analysis": {
                "correlation_discovery": build_correlation_discovery(phi_summary, emotion_label=emotion.label),
                "doctor_visit_prep": build_doctor_visit_prep(phi_summary),
            },
        },
    )

