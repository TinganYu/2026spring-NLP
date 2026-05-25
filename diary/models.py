"""Data model definitions used across diary processing.

統一使用 TypedDict，便於 JSON/dict 序列化與 DB 存取。
"""

from typing import List, Dict, Any, Optional, TypedDict


class SymptomRecord(TypedDict):
    key: str
    display: str
    status: str
    severity: int
    times: List[str]
    body: List[str] 
    frequencies: List[str]
    notes: Dict[str, List[str]]


class MedicationRecord(TypedDict):
    key: str
    display: str
    dosages: List[str]
    frequencies: List[str]
    notes: Dict[str, List[str]]
    taken: bool # 根據日記內容判定是否有服用（True 表示日記中有記錄/推論為有服用）


class DiaryRecord(TypedDict):  # 用來讀取DB內的值，並改成前端需要的格式
    date: str
    emotion_label: str
    emotion_score: float
    symptoms: List[SymptomRecord]
    medications: List[MedicationRecord]
    # events 已移除，相關關係資料請從 PHI 原始 relations 或 aggregator 的 phi_relations 取得


class DiaryEntry(TypedDict, total=False):
    text: str
    meta: Dict[str, Any]


class SentenceResult(TypedDict, total=False):
    text: str
    label: str
    score: float


class EmotionResult(TypedDict, total=False):
    label: str
    score: float
    sentences: Optional[List[Dict[str, Any]]]


class AnalysisResult(TypedDict, total=False):
    entry: DiaryEntry
    emotion: EmotionResult
    symptoms: List[Dict[str, Any]]
    phi: Optional[Dict[str, Any]]