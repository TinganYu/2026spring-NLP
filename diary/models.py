"""Data model definitions used across diary processing.

包含 dataclass 與 TypedDict，用於統一各模組間交換的資料結構。
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, TypedDict


class SymptomRecord(TypedDict):
    key: str
    display: str
    status: str
    severity: int


class MedicationRecord(TypedDict):
    key: str
    display: str
    frequency: str
    inferred: bool # 透過assertion推斷是否正在服用


class DiaryRecord(TypedDict):  # 用來讀取DB內的值，並改成前端需要的格式
    date: str
    emotion_label: str
    emotion_score: float
    symptoms: List[SymptomRecord]
    medications: List[MedicationRecord]
    events: List[Dict[str, Any]]


@dataclass
class DiaryEntry:  
    text: str
    meta: Dict[str, Any]


@dataclass
class SentenceResult:
    text: str
    label: str
    score: float


@dataclass
class EmotionResult:
    label: str
    score: float
    sentences: Optional[List[Dict[str, Any]]] = None


@dataclass
class AnalysisResult:  # 基本上就是所有的azure回傳資料，很多巢狀，但是我覺得資料越多越好
    entry: DiaryEntry
    emotion: EmotionResult
    symptoms: List[Dict[str, Any]]
    extra: Dict[str, Any] = None