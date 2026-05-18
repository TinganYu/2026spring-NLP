"""Per-entry processing: 以單筆日記文本產生標準化的 `AnalysisResult`。

職責：偵測情緒、呼叫 PHI 分析、回傳可存入 DB 的結構化結果。
不要在這裡做昂貴的跨筆聚合或 on-demand 的深度分析。
"""

from dataclasses import asdict
from typing import Dict, Any, List
import re
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
SEVERITY_MAP = {
                # Azure normalized_text 常見輸出
                "severe": 3, "serious": 3, "intense": 3, "extreme": 3, "excruciating": 3,
                "moderate": 2, "significant": 2,
                "mild": 1, "slight": 1, "minor": 1, "minimal": 1,
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
    for rel in relations:   # 先把 relation 的 roles 轉成 dict，方便後續查詢
        roles = {r.get("name") or "Unknown": r.get("entity_text") or "" for r in rel.get("roles", [])}
        parsed_relations.append({
            "type": rel.get("relation_type"),
            "roles": roles
        })

    # 1. 整理 Symptoms
    symptom_records = []
    for ent in entities:
        if ent.get("category") == "SymptomOrSign":
            key = ent.get("normalized_text") or ent.get("text") or "" # 優先使用 normalized_text 作為 key，確保同一症狀不同表達方式能對應到同一個 key
            display = ent.get("text") or ""
            
            # 判斷 status(我們自己的變數)
            status = "affirmed" # 預設為 affirmed(肯定)，除非後來發現是 negated(消失)、hypothetical(假設)、historical(過去/歷史) 等
            assertion = ent.get("assertion")
            if assertion:
                cert = assertion.get("certainty")       # 確定性 (真假)
                cond = assertion.get("conditionality")  # 條件性 (是不是假設語氣)
                temp = assertion.get("temporal")        # 時間性 (過去、現在、未來)
                assoc = assertion.get("association")    # 關聯性 (是誰的症狀)
                
                if cert in ("negative", "negative_possible"): status = "negated"
                elif cond in ("hypothetical", "conditional"): status = "hypothetical"
                elif temp == "past": status = "historical"
                elif temp == "future": status = "hypothetical"
                elif assoc == "other": status = "other_person"  # 代表這個症狀不是使用者本人的，可能是家人或朋友的狀況
                elif cert in ("positive_possible", "neutral_possible"): status = "uncertain"

            # 判斷 severity 
            max_severity = 1
            for pr in parsed_relations:
                if pr["type"] == "QualifierOfCondition":
                    cond_text = pr["roles"].get("Condition") or pr["roles"].get("Symptom") # 因為azure有時用Condition，有時用Symptom，所以兩個都試著對應看看
                    if cond_text == display:
                        q = pr["roles"].get("Qualifier")
                        if q and q.lower() in SEVERITY_MAP:
                            # 比較取最大值，不使用 break，確保同時有 mild 和 severe 時以 severe 為主
                            max_severity = max(max_severity, SEVERITY_MAP[q.lower()])

            symptom_records.append(SymptomRecord(
                key=key, 
                display=display, 
                status=status, 
                severity=max_severity
            ))

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