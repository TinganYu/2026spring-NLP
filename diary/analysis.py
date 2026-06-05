"""PHI 相關的分析與輸出格式。

提供 PHI 摘要功能。將 PHI 的原始輸出整理成適合前端顯示和圖表使用的格式。
"""
from collections import Counter
from typing import Any, Dict, List
from .models import DiaryRecord, SymptomRecord, MedicationRecord, AnalysisResult
from collections import defaultdict

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
        """從一組 roles 中找出有指定 role_names 的 entity_text。"""
        target_names = set(role_names)
        for role in roles:
            if role.get("name") in target_names:
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

    # 預處理：建立關係索引表 (defaultdict(lambda: 會自動建立預設值的字典)
    # symptom_idx: { display_name: { "times": [], "body": [], "frequencies": [], "max_severity": 1 } }
    symptom_idx = defaultdict(lambda: {"times": [], "body": [], "frequencies": [], "max_severity": 1})
    # med_idx: { display_name: { "dosages": [], "frequencies": [] } }
    med_idx = defaultdict(lambda: {"dosages": [], "frequencies": []})

    for rel in relations:
        roles = rel.get("roles", []) # 通常是兩個兩個一組 (i.e. condition qualifier)
        rtype = rel.get("relation_type") # QualifierOfCondition
        
        # 處理 Symptoms 關係
        cond_text = _get_role_text(roles, "Condition", "Symptom")  # 找出關係中是這種類型的entity
        if cond_text:
            target = symptom_idx[cond_text] # 索引標籤
            if rtype == "QualifierOfCondition":
                q = _get_role_text(roles, "Qualifier")
                if q and q.lower() in SEVERITY_MAP:
                    target["max_severity"] = max(target["max_severity"], SEVERITY_MAP[q.lower()]) # 找對應的嚴重等級，沒有就用預設1
            elif rtype == "TimeOfCondition":
                val = _get_role_text(roles, "Time", "Date")
                if val: target["times"].append(val) # 紀錄時間資訊(可以有多個)
            elif rtype == "BodySiteOfCondition":
                val = _get_role_text(roles, "BodySite")
                if val: target["body"].append(val)
            elif rtype == "FrequencyOfCondition":
                val = _get_role_text(roles, "Frequency")
                if val: target["frequencies"].append(val)

        # 處理 Medications 關係
        med_text = _get_role_text(roles, "Medication") # 找出關係中是這種類型的entity
        if med_text:
            target = med_idx[med_text]
            if rtype == "DosageOfMedication":
                val = _get_role_text(roles, "Dosage")
                if val: target["dosages"].append(val)
            elif rtype == "FrequencyOfMedication":
                val = _get_role_text(roles, "Frequency")
                if val: target["frequencies"].append(val)

    # 2. 組裝資料(查詢dict) 
    symptom_records = []
    medication_records = []

    for ent in entities:
        category = ent.get("category")
        text = ent.get("text", "")
        
        if category == "SymptomOrSign":
            data = symptom_idx[text] # 從剛才的索引表拿出這個症狀對應的時間、頻率、嚴重程度等資訊，如果沒有就是預設值
            symptom_records.append(SymptomRecord(
                key=ent.get("normalized_text") or text,
                display=text,
                status=_infer_entity_status(ent),
                severity=data["max_severity"],
                times=data["times"],
                frequencies=data["frequencies"]
            ))
        elif category == "MedicationName":
            data = med_idx[text]
            med_status = _infer_entity_status(ent)
            medication_records.append(MedicationRecord(
                key=ent.get("normalized_text") or text,
                display=text,
                dosages=data["dosages"],
                frequencies=data["frequencies"],
                taken=(med_status == "affirmed") and bool(ent.get("assertion"))
            ))
    

    return DiaryRecord(
        date=date,
        emotion_label=result["emotion"]["label"],
        emotion_score=result["emotion"]["score"],
        symptoms=symptom_records,
        medications=medication_records,
    )
