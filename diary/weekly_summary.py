"""Weekly aggregation and analysis of diary entries.

Combines multiple diary records (typically 7 days) into a single weekly summary.
Provides emotion trends, symptom patterns, medication usage, and structured data for Groq summarization.
"""

from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional
from .models import AnalysisResult
from .visualization import (
    build_emotion_line_chart,
    build_symptom_frequency_chart,
    build_medication_frequency_chart,
    build_emotion_symptom_cooccurrence,
)


def aggregate_weekly_records(records: List[AnalysisResult]) -> Dict[str, Any]:
    """Aggregate 7 days of diary records into weekly analysis.
    
    Args:
        records: List of AnalysisResult objects from process_entry()
        
    Returns:
        Dictionary containing:
        - emotion_trend: emotion label and score per date
        - symptom_trend: symptoms per date
        - medication_trend: medications per date
        - emotion_line_chart: visualization payload for line chart
        - symptom_frequency_chart: visualization payload for symptom bar chart
        - medication_frequency_chart: visualization payload for medication bar chart
        - cooccurrence_chart: visualization payload for emotion-symptom correlations
        - emotion_statistics: average emotion, trend direction
        - symptom_statistics: most common symptoms
        - medication_statistics: most common medications
        - phi_relations: important entity relationships from the week
    """
    
    if not records:
        return _empty_weekly_summary()
    
    # Prepare records as dictionaries with dates for visualization
    records_with_dates = [
        {
            "date": record.entry.meta.get("date", datetime.now().strftime("%Y-%m-%d")),
            "sentiment_label": record.emotion.label,
            "sentiment_score": record.emotion.score,
            "phi": record.extra.get("phi", {}),
            "emotion_sentences": record.emotion.sentences or [],
        }
        for record in records
    ]
    
    # Build visualization payloads
    emotion_line = build_emotion_line_chart(records_with_dates)
    symptom_freq = build_symptom_frequency_chart(records_with_dates)
    medication_freq = build_medication_frequency_chart(records_with_dates)
    cooccurrence = build_emotion_symptom_cooccurrence(records_with_dates)
    
    # Extract raw trends
    emotion_trend = [
        {
            "date": r["date"],
            "emotion_label": r["sentiment_label"],
            "emotion_score": r["sentiment_score"],
        }
        for r in records_with_dates
    ]
    
    symptom_trend = _extract_symptom_trend(records_with_dates)
    medication_trend = _extract_medication_trend(records_with_dates)
    
    # Calculate statistics
    emotion_stats = _calculate_emotion_statistics(records_with_dates)
    symptom_stats = _calculate_symptom_statistics(symptom_trend)
    medication_stats = _calculate_medication_statistics(medication_trend)
    
    # Extract PHI relations across the week
    phi_relations = _aggregate_phi_relations(records)
    
    return {
        "week_start": records_with_dates[0]["date"] if records_with_dates else None,
        "week_end": records_with_dates[-1]["date"] if records_with_dates else None,
        "record_count": len(records),
        
        # Trend data
        "emotion_trend": emotion_trend,
        "symptom_trend": symptom_trend,
        "medication_trend": medication_trend,
        
        # Visualization payloads
        "emotion_line_chart": emotion_line,
        "symptom_frequency_chart": symptom_freq,
        "medication_frequency_chart": medication_freq,
        "cooccurrence_chart": cooccurrence,
        
        # Statistics
        "emotion_statistics": emotion_stats,
        "symptom_statistics": symptom_stats,
        "medication_statistics": medication_stats,
        
        # Relations for natural language generation
        "phi_relations": phi_relations,
    }


def _extract_symptom_trend(records_with_dates: List[Dict]) -> List[Dict]:
    """Extract symptoms per date."""
    trend = []
    for record in records_with_dates:
        phi = record.get("phi", {})
        symptoms = [
            entity.get("text") or entity.get("normalized_text") or ""
            for entity in phi.get("symptom_or_sign", [])
        ]
        trend.append({
            "date": record["date"],
            "symptoms": symptoms,
        })
    return trend


def _extract_medication_trend(records_with_dates: List[Dict]) -> List[Dict]:
    """Extract medications per date."""
    trend = []
    for record in records_with_dates:
        phi = record.get("phi", {})
        medications = []
        for category in ["MedicationName", "Dosage", "Frequency"]:
            medications.extend([
                entity.get("text") or entity.get("normalized_text") or ""
                for entity in phi.get("entities_by_category", {}).get(category, [])
            ])
        trend.append({
            "date": record["date"],
            "medications": list(set(medications)),  # Remove duplicates
        })
    return trend


def _calculate_emotion_statistics(records_with_dates: List[Dict]) -> Dict[str, Any]:
    """Calculate emotion statistics for the week."""
    if not records_with_dates:
        return {}
    
    scores = [r["sentiment_score"] for r in records_with_dates]
    labels = [r["sentiment_label"] for r in records_with_dates]
    
    avg_score = sum(scores) / len(scores) if scores else 0
    label_counts = Counter(labels)
    most_common_label = label_counts.most_common(1)[0][0] if label_counts else None
    
    # Trend direction: is it improving?
    trend_direction = "stable"
    if len(scores) >= 2:
        trend_value = scores[-1] - scores[0]
        if trend_value > 0.1:
            trend_direction = "improving"
        elif trend_value < -0.1:
            trend_direction = "declining"
    
    return {
        "average_score": round(avg_score, 3),
        "most_common_label": most_common_label,
        "label_distribution": dict(label_counts),
        "trend_direction": trend_direction,
    }


def _calculate_symptom_statistics(symptom_trend: List[Dict]) -> Dict[str, Any]:
    """Calculate symptom statistics for the week."""
    all_symptoms = []
    for day in symptom_trend:
        all_symptoms.extend(day.get("symptoms", []))
    
    if not all_symptoms:
        return {"total_unique_symptoms": 0, "most_common": []}
    
    symptom_counts = Counter(all_symptoms)
    return {
        "total_unique_symptoms": len(symptom_counts),
        "most_common": [
            {"symptom": symptom, "count": count}
            for symptom, count in symptom_counts.most_common(5)
        ],
    }


def _calculate_medication_statistics(medication_trend: List[Dict]) -> Dict[str, Any]:
    """Calculate medication statistics for the week."""
    all_medications = []
    for day in medication_trend:
        all_medications.extend(day.get("medications", []))
    
    if not all_medications:
        return {"total_unique_medications": 0, "most_common": []}
    
    med_counts = Counter(all_medications)
    return {
        "total_unique_medications": len(med_counts),
        "most_common": [
            {"medication": med, "count": count}
            for med, count in med_counts.most_common(5)
        ],
    }


def _aggregate_phi_relations(records: List[AnalysisResult]) -> List[Dict[str, Any]]:
    """Extract important PHI relations across all records."""
    all_relations = []
    
    for record in records:
        phi_summary = record.extra.get("phi", {})
        relations = phi_summary.get("relations", [])
        
        for relation in relations:
            all_relations.append({
                "relation_type": relation.get("relation_type"),
                "roles": relation.get("roles", []),
                "date": record.entry.meta.get("date"),
            })
    
    # Group by relation type for easier summarization
    relations_by_type = defaultdict(list)
    for rel in all_relations:
        rel_type = rel.get("relation_type", "Unknown")
        relations_by_type[rel_type].append(rel)
    
    # Return top relations
    return [
        {
            "relation_type": rel_type,
            "occurrences": len(rels),
            "examples": rels[:2],  # First 2 examples
        }
        for rel_type, rels in sorted(
            relations_by_type.items(),
            key=lambda x: len(x[1]),
            reverse=True,
        )[:5]  # Top 5 relation types
    ]


def _empty_weekly_summary() -> Dict[str, Any]:
    """Return empty summary structure when no records provided."""
    return {
        "week_start": None,
        "week_end": None,
        "record_count": 0,
        "emotion_trend": [],
        "symptom_trend": [],
        "medication_trend": [],
        "emotion_line_chart": {},
        "symptom_frequency_chart": {},
        "medication_frequency_chart": {},
        "cooccurrence_chart": {},
        "emotion_statistics": {},
        "symptom_statistics": {},
        "medication_statistics": {},
        "phi_relations": [],
    }
