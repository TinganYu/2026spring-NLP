"""Weekly aggregation and analysis of diary entries.

Combines multiple diary records (typically 7 days) into a single weekly summary.
Provides emotion trends, symptom patterns, medication usage, and structured data for Groq summarization.
"""

"""Legacy thin wrapper that delegates weekly aggregation to `aggregator.py`.

保留此檔以維持原本 import 路徑相容性。
"""

from .aggregator import aggregate_weekly_records

__all__ = ["aggregate_weekly_records"]
