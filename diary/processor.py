from .models import DiaryEntry, AnalysisResult, Symptom
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


def _entity_to_dict(entity):
    return {
        "text": entity.text,
        "normalized_text": entity.normalized_text,
        "category": entity.category,
        "subcategory": entity.subcategory,
        "offset": entity.offset,
        "confidence_score": entity.confidence_score,
        "data_sources": [
            {
                "entity_id": source.entity_id,
                "name": source.name,
            }
            for source in entity.data_sources
        ],
        "assertion": None
        if entity.assertion is None
        else {
            "conditionality": entity.assertion.conditionality,
            "certainty": entity.assertion.certainty,
            "association": entity.assertion.association,
        },
    }


def _relation_to_dict(relation):
    return {
        "relation_type": relation.relation_type,
        "roles": [
            {
                "name": role.name,
                "entity_text": role.entity_text,
            }
            for role in relation.roles
        ],
    }


def _summarize_phi(health_result):
    entities = [_entity_to_dict(entity) for entity in health_result.entities]
    relations = [_relation_to_dict(relation) for relation in health_result.relations]

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
        "detected_language": health_result.detected_language,
        "target_language": health_result.target_language,
        "symptom_or_sign": symptom_or_sign, # 特別把症狀和體徵整理出來，因為這是日記分析中最常關注的資訊之一
        "important_entities": important_entities,
        "entities_by_category": entities_by_category,
        "entities": entities,
        "relations": relations,
    }


def _phi_symptoms_to_model(phi_summary): # 把 PHI 的 SymptomOrSign 實體轉換成我們模型裡的 Symptom 物件列表
    return [
        Symptom(
            name=entity.get("text") or entity.get("normalized_text") or "",
            match=entity.get("category") or "SymptomOrSign",
        )
        for entity in phi_summary.get("symptom_or_sign", [])
    ]

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
    symptoms = _phi_symptoms_to_model(phi_summary)
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
            "original_text": text,
            "phi": phi_summary,
            "analysis": {
                "correlation_discovery": build_correlation_discovery(phi_summary, emotion_label=emotion.label),
                "doctor_visit_prep": build_doctor_visit_prep(phi_summary),
            },
        },
    )


# def to_visualization_record(analysis_result: AnalysisResult, date: str = None) -> dict:
#     """Convert AnalysisResult to visualization-friendly format.
    
#     This helper function prepares data from process_entry() for use with
#     visualization.py functions like build_emotion_line_chart() and 
#     build_emotion_symptom_cooccurrence().
    
#     Args:
#         analysis_result: Output from process_entry()
#         date: Date string (YYYY-MM-DD). If None, uses meta['date'] or current date.
        
#     Returns:
#         Dictionary with keys: date, sentiment_label, sentiment_score, phi, emotion_sentences
#     """
#     from datetime import datetime
    
#     if date is None:
#         date = analysis_result.entry.meta.get("date", datetime.now().strftime("%Y-%m-%d"))
    
#     return {
#         "date": date,
#         "sentiment_label": analysis_result.emotion.label,
#         "sentiment_score": analysis_result.emotion.score,
#         "phi": analysis_result.extra.get("phi", {}),
#         "emotion_sentences": analysis_result.emotion.sentences or [],
#     }
