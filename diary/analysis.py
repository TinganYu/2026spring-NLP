"""PHI 相關的分析與輸出格式。

提供 correlation discovery、看診懶人包等 on-demand 的 PHI 摘要功能。
這些函式通常在使用者請求時被呼叫，而非在每次 process_entry 時執行。
"""

from collections import Counter, defaultdict
from typing import Any, Dict, List


def _entity_label(entity: Dict[str, Any]) -> str:
    # 優先取原始文字，沒有就用標準化後的文字
    return entity.get("text") or entity.get("normalized_text") or ""


def _relation_roles_map(relation: Dict[str, Any]) -> Dict[str, str]:
    # 把 relation 裡的角色整理成 {角色名稱: 實體文字}，方便後面組句子
    roles = {}
    for role in relation.get("roles", []):
        name = role.get("name") or "Unknown"
        roles[name] = role.get("entity_text") or ""
    return roles


def _assertion_summary(entity: Dict[str, Any]) -> Dict[str, Any] | None:
    # assertion 用來表示這個實體是肯定、否定、條件式或不確定
    assertion = entity.get("assertion")
    if not assertion:
        return None

    return {
        "text": _entity_label(entity),
        "category": entity.get("category"),
        "conditionality": assertion.get("conditionality"),
        "certainty": assertion.get("certainty"),
        "association": assertion.get("association"),
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

    # 找出最重要的幾類資訊
    # 不在此回傳完整 symptom_or_sign，避免和 AnalysisResult.symptoms 重複
    medications = [entity for entity in entities if entity.get("category") == "MedicationName"]

    # 把有 assertion 的實體先整理出來，方便判斷是否要納入統計
    assertions = [summary for entity in entities if (summary := _assertion_summary(entity))]

    # relation 可以直接描述實體之間的關係，例如症狀發生時間、用藥頻率等
    relation_facts = []
    for relation in relations:
        relation_type = relation.get("relation_type") or "Unknown"
        roles = _relation_roles_map(relation)
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
        roles = _relation_roles_map(relation)
        if relation_type in {"TimeOfCondition", "DurationOfCondition", "FrequencyOfMedication"}:
            timeline_items.append(
                {
                    "relation_type": relation_type,
                    "roles": roles,
                    "text": _format_relation_text(relation_type, roles),
                }
            )

    assertion_flags = []
    for entity in entities:
        if entity.get("assertion"):
            # 有 assertion 的內容通常代表更需要注意真假或條件
            assertion_flags.append(_assertion_summary(entity))

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
