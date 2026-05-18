"""PHI 相關的分析與輸出格式。

提供 correlation discovery、看診懶人包等 on-demand 的 PHI 摘要功能。
這些函式通常在使用者請求時被呼叫，而非在每次 process_entry 時執行。
"""

from collections import Counter
from typing import Any, Dict, List

from .models import DiaryRecord, SymptomRecord, MedicationRecord, AnalysisResult

# severity mapping for qualifiers (copied to keep consistent behavior with processor)
SEVERITY_MAP = {
    "severe": 3, "serious": 3, "intense": 3, "extreme": 3, "excruciating": 3,
    "moderate": 2, "significant": 2,
    "mild": 1, "slight": 1, "minor": 1, "minimal": 1,
}


def build_correlation_discovery(phi: Dict[str, Any], emotion_label: str = None) -> Dict[str, Any]:
    """把 PHI 結果整理成可做月底回顧的關聯摘要。

    這裡會把 Emotion、SymptomOrSign、MedicationName、assertion、relation
    整理成適合做趨勢觀察的資料。
    """
    entities = phi.get("entities", [])
    relations = phi.get("relations", [])

    # 統計每種 entity category 出現次數
    categories = Counter(entity.get("category") for entity in entities if entity.get("category"))

    medications = [entity for entity in entities if entity.get("category") == "MedicationName"]
    assertions = [
        {
            "text": entity.get("text") or entity.get("normalized_text") or "",
            "category": entity.get("category"), # category內容可能是 SymptomOrSign、MedicationName 等等
            "conditionality": entity.get("assertion", {}).get("conditionality"),
            "certainty": entity.get("assertion", {}).get("certainty"),
            "association": entity.get("assertion", {}).get("association"),
        }
        for entity in entities
        if entity.get("assertion")
    ]

    relation_facts = []
    for relation in relations:
        relation_type = relation.get("relation_type") or "Unknown"
        roles = {role.get("name") or "Unknown": role.get("entity_text") or "" for role in relation.get("roles", [])}
        relation_facts.append(
            {
                "relation_type": relation_type,
                "roles": roles,
                "text": _format_relation_text(relation_type, roles),
            }
        )

    return {
        "emotion_label": emotion_label,
        "category_counts": dict(categories),
        "medications": medications,
        "relation_facts": relation_facts,
        "assertions": assertions,
    }


def build_doctor_visit_prep(phi: Dict[str, Any]) -> Dict[str, Any]:
    """把 PHI 結果整理成看診前可直接輸出的懶人包。

    目標是快速列出：症狀、持續時間、嚴重程度、用藥與相關時間線。
    """
    entities = phi.get("entities", [])
    relations = phi.get("relations", [])

    # 這些欄位是看診時最常需要說明的內容
    symptom_or_sign = [entity for entity in entities if entity.get("category") == "SymptomOrSign"]
    durations = [entity for entity in entities if entity.get("category") == "Duration"]
    qualifiers = [entity for entity in entities if entity.get("category") == "ConditionQualifier"]
    medications = [entity for entity in entities if entity.get("category") == "MedicationName"]

    # 這裡只保留和時間、持續時間、頻率有關的 relation
    timeline_items = []
    for relation in relations:
        relation_type = relation.get("relation_type") or "Unknown"
        roles = {role.get("name") or "Unknown": role.get("entity_text") or "" for role in relation.get("roles", [])}
        if relation_type in {"TimeOfCondition", "DurationOfCondition", "FrequencyOfMedication"}:
            timeline_items.append(
                {
                    "relation_type": relation_type,
                    "roles": roles,
                    "text": _format_relation_text(relation_type, roles),
                }
            )

    assertion_flags = [
        {
            "text": entity.get("text") or entity.get("normalized_text") or "",
            "category": entity.get("category"),
            "conditionality": entity.get("assertion", {}).get("conditionality"),
            "certainty": entity.get("assertion", {}).get("certainty"),
            "association": entity.get("assertion", {}).get("association"),
        }
        for entity in entities
        if entity.get("assertion")
    ]

    return {
        # `symptom_or_sign` 在看診懶人包需要完整實體，保留此處輸出（on-demand）
        "symptom_or_sign": symptom_or_sign,
        "durations": durations,
        "qualifiers": qualifiers,
        "medications": medications,
        "timeline_items": timeline_items,
        "assertions": assertion_flags,
        "suggested_summary": _build_visit_summary(symptom_or_sign, durations, qualifiers, medications, timeline_items),
    }


def _format_relation_text(relation_type: str, roles: Dict[str, str]) -> str:
    # 把 relation 轉成中文可讀句子，方便前端顯示或報告使用
    if relation_type == "TimeOfCondition":
        condition = roles.get("Condition") or roles.get("Symptom") or roles.get("Entity") or "某個症狀"
        time_value = roles.get("Time") or roles.get("Date") or "某個時間"
        return f"{condition} 發生在 {time_value}"

    if relation_type == "DurationOfCondition":
        condition = roles.get("Condition") or roles.get("Symptom") or "某個症狀"
        duration = roles.get("Duration") or "某段時間"
        return f"{condition} 持續 {duration}"

    if relation_type == "DosageOfMedication":
        medication = roles.get("Medication") or roles.get("Drug") or "某個藥物"
        dosage = roles.get("Dosage") or "某個劑量"
        return f"{medication} 的劑量是 {dosage}"

    if relation_type == "FrequencyOfMedication":
        medication = roles.get("Medication") or roles.get("Drug") or "某個藥物"
        frequency = roles.get("Frequency") or "某個頻率"
        return f"{medication} 的服用頻率是 {frequency}"

    return f"{relation_type}: {', '.join(f'{k}={v}' for k, v in roles.items())}"


def to_diary_record(result: AnalysisResult, date: str) -> DiaryRecord:
    """將 AnalysisResult 轉換為前端與圖表直接可用的統一 DiaryRecord 結構

    這個函式原先放在 `processor.py`，已搬移至此以統一管理 PHI -> 前端格式化邏輯。
    """
    phi = result.get("phi", {}) or {}
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

            status = "affirmed" # 自己的變數，先預設是肯定，後續根據 assertion 的不同屬性調整成 negated(消失)、hypothetical、historical、uncertain、other_person 等等
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

            max_severity = 1
            for pr in parsed_relations:
                if pr["type"] == "QualifierOfCondition":
                    cond_text = pr["roles"].get("Condition") or pr["roles"].get("Symptom") # 有時候 relation 的 role 可能叫 Condition，有時候叫 Symptom，要兩個都檢查
                    if cond_text == display:
                        q = pr["roles"].get("Qualifier")
                        if q and q.lower() in SEVERITY_MAP:
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
                "text": _format_relation_text(pr["type"], pr["roles"])
            })

    return DiaryRecord(
        date=date,
        emotion_label=result["emotion"]["label"],
        emotion_score=result["emotion"]["score"],
        symptoms=symptom_records,
        medications=medication_records,
        events=events
    )


def _build_visit_summary(
    symptom_or_sign: List[Dict[str, Any]],
    durations: List[Dict[str, Any]],
    qualifiers: List[Dict[str, Any]],
    medications: List[Dict[str, Any]],
    timeline_items: List[Dict[str, Any]],
) -> List[str]:
    # 這裡產生最終的看診前摘要，一行一個重點
    lines = []

    if symptom_or_sign:
        symptom_texts = [entity.get("text") for entity in symptom_or_sign if entity.get("text")]
        lines.append(f"症狀/徵象：{', '.join(symptom_texts)}")

    if durations:
        duration_texts = [entity.get("text") for entity in durations if entity.get("text")]
        lines.append(f"持續時間：{', '.join(duration_texts)}")

    if qualifiers:
        qualifier_texts = [entity.get("text") for entity in qualifiers if entity.get("text")]
        lines.append(f"程度/狀態：{', '.join(qualifier_texts)}")

    if medications:
        medication_texts = [entity.get("text") for entity in medications if entity.get("text")]
        lines.append(f"藥物：{', '.join(medication_texts)}")

    for item in timeline_items:
        if item.get("text"):
            lines.append(item["text"])

    return lines
