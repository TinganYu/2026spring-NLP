"""PHI 相關的分析與輸出格式。

提供 PHI 摘要功能。將 PHI 的原始輸出整理成適合前端顯示和圖表使用的格式。
"""
from collections import Counter
from typing import Any, Dict, List
from .models import DiaryRecord, SymptomRecord, MedicationRecord, AnalysisResult

# severity mapping for qualifiers (copied to keep consistent behavior with processor)
SEVERITY_MAP = {
    # level 3 - very severe
    "severe": 3, "serious": 3, "intense": 3, "extreme": 3, "excruciating": 3,
    "agonizing": 3, "unbearable": 3, "very severe": 3, "terrible": 3, "horrible": 3,
    # level 2 - moderate
    "moderate": 2, "significant": 2, "medium": 2, "fair": 2, "quite painful": 2,
    # level 1 - mild
    "mild": 1, "slight": 1, "minor": 1, "minimal": 1, "mildly": 1, "low": 1,
}

def to_diary_record(result: AnalysisResult, date: str) -> DiaryRecord:
    """將 AnalysisResult 轉換為前端與圖表直接可用的統一 DiaryRecord 結構

    輸出範例:
    {
        date: "2026-05-01",
        emotion_label: "negative",
        emotion_score: 0.8,
        symptoms: [
            {"key": "headache", "display": "headache", "status": "affirmed", "severity": 2, "times": ["yesterday"], "frequencies": ["everyday"], "notes": {"BodySiteOfCondition": ["head"]}},
            ],
        medications: [
            {"key": "ibuprofen", "display": "ibuprofen", "frequency": "twice a day", "inferred": true},
            ],
    } 

    """
    phi = result.get("phi", {}) or {}
    entities = phi.get("entities", [])
    relations = phi.get("relations", [])

    def _get_role_text(roles: List[Dict[str, Any]], *role_names: str) -> str:
        for role_name in role_names:
            for role in roles:
                if role.get("name") == role_name:
                    return role.get("entity_text") or ""
        return ""

    def _infer_entity_status(entity: Dict[str, Any]) -> str:
        # 回傳適用於 symptoms 的 status：affirmed/negated/hypothetical/historical/other_person/uncertain
        assertion = entity.get("assertion")
        if not assertion:
            return "affirmed"
        cert = assertion.get("certainty")
        cond = assertion.get("conditionality")
        temp = assertion.get("temporal")
        assoc = assertion.get("association")

        if cert in ("negative", "negative_possible"): return "negated"
        if cond in ("hypothetical", "conditional"): return "hypothetical"
        if temp == "past": return "historical"
        if temp == "future": return "hypothetical"
        if assoc == "other": return "other_person"
        if cert in ("positive_possible", "neutral_possible"): return "uncertain"

        return "affirmed"

    # 1. 整理 Symptoms
    symptom_records = []
    for ent in entities:
        if ent.get("category") == "SymptomOrSign":
            key = ent.get("normalized_text") or ent.get("text") or ""
            display = ent.get("text") or ""

            status = _infer_entity_status(ent)
            times: List[str] = []       # 特別抓出時間
            body: List[str] = []        # 特別抓出身體部位
            frequencies: List[str] = [] # 特別抓出頻率
            notes: Dict[str, List[str]] = {} # 存放所有與該症狀相關的其他 Relation 屬性
            
            max_severity = 1
            for rel in relations:
                roles = rel.get("roles", [])
                
                cond_text = _get_role_text(roles, "Condition", "Symptom", "Entity")
                if cond_text != display:
                    continue

                rtype = rel.get("relation_type")
                if rtype == "QualifierOfCondition":
                        qualifier = _get_role_text(roles, "Qualifier")
                        if qualifier and qualifier.lower() in SEVERITY_MAP:
                            max_severity = max(max_severity, SEVERITY_MAP[qualifier.lower()])
                # 獨立抓取時間
                elif rtype == "TimeOfCondition": 
                    val = _get_role_text(roles, "Time", "Date")
                    if val:
                        times.append(val)
                # 獨立抓取身體部位
                elif rtype == "BodySiteOfCondition":
                    val = _get_role_text(roles, "BodySite")
                    if val:
                        body.append(val)

                # 獨立抓取頻率
                elif rtype == "FrequencyOfCondition":
                    val = _get_role_text(roles, "Frequency")
                    if val:
                        frequencies.append(val)
                
                # # 其他屬性 (部位、程度等) 丟進 notes
                # elif rtype:                  
                    
                #     if rtype not in notes:
                #         notes[rtype] = []
                    
                #     for role in roles:
                #         role_name = role.get("name")
                #         role_text = role.get("entity_text")
                        
                #         # 排除掉指向症狀本身的 role
                #         if role_name not in ("Condition", "Symptom", "Entity") and role_text:
                #             notes[rtype].append(role_text)

            symptom_records.append(SymptomRecord(
                key=key,
                display=display,
                status=status,
                severity=max_severity,
                times=times,             
                frequencies=frequencies, 
                # notes=notes
            ))

    # 2. 整理 Medications（改為累積劑量/頻率/註記為 list）
    medication_records = []
    for ent in entities:
        if ent.get("category") == "MedicationName":
            key = ent.get("normalized_text") or ent.get("text") or ""
            display = ent.get("text") or ""

            dosages: List[str] = []
            frequencies: List[str] = []
            notes: Dict[str, List[str]] = {} # 改為字典結構存放其他屬性

            for rel in relations:
                roles = rel.get("roles", [])
                med_text = _get_role_text(roles, "Medication", "Drug")
                if med_text != display: # relation裡存的是text不是normalized_text，所以用display來比對
                    continue

                rtype = rel.get("relation_type")
                if rtype == "DosageOfMedication":
                    val = _get_role_text(roles, "Dosage")
                    if val:
                        dosages.append(val)
                elif rtype == "FrequencyOfMedication":
                    val = _get_role_text(roles, "Frequency")
                    if val:
                        frequencies.append(val)
                # elif rtype:
                #     # 其他和藥物有關的 relation 當作註記保留，結構為 Dict[str, List[str]]，範例 {"RouteOfAdministration": ["口服"], "FormOfMedication": ["錠劑"]}
                #     if rtype not in notes:
                #         notes[rtype] = []
                    
                #     # 找出該 relation 中，除了「藥物本身」以外的實體文字並塞進 List
                #     for role in roles:
                #         role_name = role.get("name")
                #         role_text = role.get("entity_text")
                        
                #         # 排除掉指向藥物本身的 role (如 Medication, Drug)，只存屬性值 (如 Route, Form 等)
                #         if role_name not in ("Medication", "Drug") and role_text:
                #             notes[rtype].append(role_text)

            # medication 推論為 True 當且僅當 entity 有 assertion 且 status 為 affirmed
            med_status = _infer_entity_status(ent)
            taken_flag = (med_status == "affirmed") and bool(ent.get("assertion"))
            medication_records.append(MedicationRecord(
                key=key,
                display=display,
                dosages=dosages,
                frequencies=frequencies,
                # notes=notes,
                taken=taken_flag
            ))

    return DiaryRecord(
        date=date,
        emotion_label=result["emotion"]["label"],
        emotion_score=result["emotion"]["score"],
        symptoms=symptom_records,
        medications=medication_records,
    )

## =====下方是針對PHI分析結果的進階整理功能，提供給月底回顧和看診準備使用=======
# def build_correlation_discovery(phi: Dict[str, Any], emotion_label: str = None) -> Dict[str, Any]:
#     """把 PHI 結果整理成可做月底回顧的關聯摘要。

#     這裡會把 Emotion、SymptomOrSign、MedicationName、assertion、relation
#     整理成適合做趨勢觀察的資料。
#     """
#     entities = phi.get("entities", [])
#     relations = phi.get("relations", [])

#     # 統計每種 entity category 出現次數
#     categories = Counter(entity.get("category") for entity in entities if entity.get("category"))

#     medications = [entity for entity in entities if entity.get("category") == "MedicationName"]
#     assertions = [
#         {
#             "text": entity.get("text") or entity.get("normalized_text") or "",
#             "category": entity.get("category"), # category內容可能是 SymptomOrSign、MedicationName 等等
#             "conditionality": entity.get("assertion", {}).get("conditionality"),
#             "certainty": entity.get("assertion", {}).get("certainty"),
#             "association": entity.get("assertion", {}).get("association"),
#         }
#         for entity in entities
#         if entity.get("assertion")
#     ]

#     relation_facts = []
#     for relation in relations:
#         relation_type = relation.get("relation_type") or "Unknown"
#         roles = {role.get("name") or "Unknown": role.get("entity_text") or "" for role in relation.get("roles", [])}
#         relation_facts.append(
#             {
#                 "relation_type": relation_type,
#                 "roles": roles,
#                 "text": _format_relation_text(relation_type, roles),
#             }
#         )

#     return {
#         "emotion_label": emotion_label,
#         "category_counts": dict(categories),
#         "medications": medications,
#         "relation_facts": relation_facts,
#         "assertions": assertions,
#     }


# def build_doctor_visit_prep(phi: Dict[str, Any]) -> Dict[str, Any]:
#     """把 PHI 結果整理成看診前可直接輸出的懶人包。

#     目標是快速列出：症狀、持續時間、嚴重程度、用藥與相關時間線。
#     """
#     entities = phi.get("entities", [])
#     relations = phi.get("relations", [])

#     # 這些欄位是看診時最常需要說明的內容
#     symptom_or_sign = [entity for entity in entities if entity.get("category") == "SymptomOrSign"]
#     durations = [entity for entity in entities if entity.get("category") == "Duration"]
#     qualifiers = [entity for entity in entities if entity.get("category") == "ConditionQualifier"]
#     medications = [entity for entity in entities if entity.get("category") == "MedicationName"]

#     # 這裡只保留和時間、持續時間、頻率有關的 relation
#     timeline_items = []
#     for relation in relations:
#         relation_type = relation.get("relation_type") or "Unknown"
#         roles = {role.get("name") or "Unknown": role.get("entity_text") or "" for role in relation.get("roles", [])}
#         if relation_type in {"TimeOfCondition", "DurationOfCondition", "FrequencyOfMedication"}:
#             timeline_items.append(
#                 {
#                     "relation_type": relation_type,
#                     "roles": roles,
#                     "text": _format_relation_text(relation_type, roles),
#                 }
#             )

#     assertion_flags = [
#         {
#             "text": entity.get("text") or entity.get("normalized_text") or "",
#             "category": entity.get("category"),
#             "conditionality": entity.get("assertion", {}).get("conditionality"),
#             "certainty": entity.get("assertion", {}).get("certainty"),
#             "association": entity.get("assertion", {}).get("association"),
#         }
#         for entity in entities
#         if entity.get("assertion")
#     ]

#     return {
#         # `symptom_or_sign` 在看診懶人包需要完整實體，保留此處輸出（on-demand）
#         "symptom_or_sign": symptom_or_sign,
#         "durations": durations,
#         "qualifiers": qualifiers,
#         "medications": medications,
#         "timeline_items": timeline_items,
#         "assertions": assertion_flags,
#         "suggested_summary": _build_visit_summary(symptom_or_sign, durations, qualifiers, medications, timeline_items),
#     }

# 這個可能沒用可以刪掉，先保留在這裡當作參考
# def _format_relation_text(relation_type: str, roles: Dict[str, str]) -> str:
#     # 把 relation 轉成中文可讀句子，方便前端顯示或報告使用
#     if relation_type == "TimeOfCondition":
#         condition = roles.get("Condition") or roles.get("Symptom") or roles.get("Entity") or "某個症狀"
#         time_value = roles.get("Time") or roles.get("Date") or "某個時間"
#         return f"{condition} 發生在 {time_value}"

#     if relation_type == "DurationOfCondition":
#         condition = roles.get("Condition") or roles.get("Symptom") or "某個症狀"
#         duration = roles.get("Duration") or "某段時間"
#         return f"{condition} 持續 {duration}"

#     if relation_type == "DosageOfMedication":
#         medication = roles.get("Medication") or roles.get("Drug") or "某個藥物"
#         dosage = roles.get("Dosage") or "某個劑量"
#         return f"{medication} 的劑量是 {dosage}"

#     if relation_type == "FrequencyOfMedication":
#         medication = roles.get("Medication") or roles.get("Drug") or "某個藥物"
#         frequency = roles.get("Frequency") or "某個頻率"
#         return f"{medication} 的服用頻率是 {frequency}"

#     return f"{relation_type}: {', '.join(f'{k}={v}' for k, v in roles.items())}"

# def _build_visit_summary(
#     symptom_or_sign: List[Dict[str, Any]],
#     durations: List[Dict[str, Any]],
#     qualifiers: List[Dict[str, Any]],
#     medications: List[Dict[str, Any]],
#     timeline_items: List[Dict[str, Any]],
# ) -> List[str]:
#     # 這裡產生最終的看診前摘要，一行一個重點
#     lines = []

#     if symptom_or_sign:
#         symptom_texts = [entity.get("text") for entity in symptom_or_sign if entity.get("text")]
#         lines.append(f"症狀/徵象：{', '.join(symptom_texts)}")

#     if durations:
#         duration_texts = [entity.get("text") for entity in durations if entity.get("text")]
#         lines.append(f"持續時間：{', '.join(duration_texts)}")

#     if qualifiers:
#         qualifier_texts = [entity.get("text") for entity in qualifiers if entity.get("text")]
#         lines.append(f"程度/狀態：{', '.join(qualifier_texts)}")

#     if medications:
#         medication_texts = [entity.get("text") for entity in medications if entity.get("text")]
#         lines.append(f"藥物：{', '.join(medication_texts)}")

#     for item in timeline_items:
#         if item.get("text"):
#             lines.append(item["text"])

#     return lines
