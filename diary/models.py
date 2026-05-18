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
    inferred: bool


class DiaryRecord(TypedDict):
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
class AnalysisResult:
    entry: DiaryEntry
    emotion: EmotionResult
    symptoms: List[Dict[str, Any]]
    extra: Dict[str, Any] = None