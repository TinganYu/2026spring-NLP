from dataclasses import asdict
from typing import Dict, Any, List

from .models import DiaryEntry, AnalysisResult, DiaryRecord, SymptomRecord, MedicationRecord
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


def process_entry(text: str, meta: dict = None) -> AnalysisResult:
    """Orchestrator: receives a diary text and returns structured analysis."""
    processed_text = text

    entry = DiaryEntry(text=processed_text, meta=meta or {})
    emotion = detect_emotion(processed_text)
    phi_result = analyze_healthcare_entities(processed_text, target_language="en")
    phi_summary = _summarize_phi(phi_result)
    
    symptoms = [
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


def _format_event_text(relation_type: str, roles: Dict[str, str]) -> str:
    """將關聯事件格式化為可讀的中文句子"""
    if relation_type == "TimeOfCondition":
        return f"{roles.get('Condition') or roles.get('Symptom') or '某個症狀'} 發生在 {roles.get('Time') or roles.get('Date') or '某個時間'}"
    if relation_type == "DurationOfCondition":
        return f"{roles.get('Condition') or roles.get('Symptom') or '某個症狀'} 持續 {roles.get('Duration') or '某段時間'}"
    if relation_type == "DosageOfMedication":
        return f"{roles.get('Medication') or roles.get('Drug') or '某個藥物'} 的劑量是 {roles.get('Dosage') or '某個劑量'}"
    if relation_type == "FrequencyOfMedication":
        return f"{roles.get('Medication') or roles.get('Drug') or '某個藥物'} 的服用頻率是 {roles.get('Frequency') or '某個頻率'}"
    if relation_type == "TimeOfMedication":
        return f"在 {roles.get('Time') or '某個時間'} 服用 {roles.get('Medication') or '某個藥物'}"
    if relation_type == "QualifierOfCondition":
        return f"{roles.get('Condition') or roles.get('Symptom') or '某個症狀'} 的程度/狀態是 {roles.get('Qualifier') or '某種狀態'}"
    if relation_type == "BodySiteOfCondition":
        return f"{roles.get('Condition') or roles.get('Symptom') or '某個症狀'} 發生在 {roles.get('BodySite') or '某個部位'}"
    
    return f"{relation_type}: {', '.join(f'{k}={v}' for k, v in roles.items())}"


def to_diary_record(result: AnalysisResult, date: str) -> DiaryRecord:
    """將 AnalysisResult 轉換為前端與圖表直接可用的統一 DiaryRecord 結構"""
    phi = result.extra.get("phi", {})
    entities = phi.get("entities", [])
    relations = phi.get("relations", [])
    
    # 解析 relations 備用
    parsed_relations = []
    for rel in relations:
        roles = {r.get("name") or "Unknown": r.get("entity_text") or "" for r in rel.get("roles", [])}
        parsed_relations.append({
            "type": rel.get("relation_type"),
            "roles": roles
        })

    # 1. 整理 Symptoms
    symptom_records = []
    for ent in entities:
        if ent.get("category") == "SymptomOrSign":
            key = ent.get("normalized_text") or ent.get("text") or ""
            display = ent.get("text") or ""
            
            # 判斷 status
            status = "affirmed"
            assertion = ent.get("assertion")
            if assertion:
                cert = assertion.get("certainty")
                cond = assertion.get("conditionality")
                temp = assertion.get("temporal")
                assoc = assertion.get("association")
                
                if cert in ("negative", "negative_possible"): status = "negated"
                elif cond in ("hypothetical", "conditional"): status = "hypothetical"
                elif temp == "past": status = "historical"
                elif temp == "future": status = "hypothetical"
                elif assoc == "other": status = "other_person"
                elif cert in ("positive_possible", "neutral_possible"): status = "uncertain"

            # 判斷 severity (1-3)
            severity = 1
            for pr in parsed_relations:
                if pr["type"] == "QualifierOfCondition":
                    cond_text = pr["roles"].get("Condition") or pr["roles"].get("Symptom")
                    if cond_text == display:
                        qualifier = pr["roles"].get("Qualifier", "")
                        if any(k in qualifier for k in ["嚴重", "重度", "劇烈", "3"]): severity = 3
                        elif any(k in qualifier for k in ["中度", "2"]): severity = 2
                        elif any(k in qualifier for k in ["輕微", "1"]): severity = 1

            symptom_records.append(SymptomRecord(key=key, display=display, status=status, severity=severity))

    # 2. 整理 Medications
    medication_records = []
    for ent in entities:
        if ent.get("category") == "MedicationName":
            key = ent.get("normalized_text") or ent.get("text") or ""
            display = ent.get("text") or ""
            frequency = ""
            
            for pr in parsed_relations:
                if pr["type"] == "FrequencyOfMedication":
                    med_text = pr["roles"].get("Medication") or pr["roles"].get("Drug")
                    if med_text == display:
                        frequency = pr["roles"].get("Frequency", "")
                        break
            
            medication_records.append(MedicationRecord(
                key=key, display=display, frequency=frequency, inferred=False
            ))

    # 3. 整理 Events
    target_event_types = {
        "QualifierOfCondition", "TimeOfCondition", "DurationOfCondition",
        "DosageOfMedication", "FrequencyOfMedication", "TimeOfMedication", "BodySiteOfCondition"
    }
    events = []
    for pr in parsed_relations:
        if pr["type"] in target_event_types:
            events.append({
                "type": pr["type"],
                "roles": pr["roles"],
                "text": _format_event_text(pr["type"], pr["roles"])
            })

    return DiaryRecord(
        date=date,
        emotion_label=result.emotion.label,
        emotion_score=result.emotion.score,
        symptoms=symptom_records,
        medications=medication_records,
        events=events
    )