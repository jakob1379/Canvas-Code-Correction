"""Compatibility wrapper for flow collector utilities."""

from __future__ import annotations

import canvas_code_correction.flows.collector as _impl

ERRORS_LOG_FILENAME = _impl.ERRORS_LOG_FILENAME
CollectionMetadata = _impl.CollectionMetadata
GradingResult = _impl.GradingResult
CollectionResult = _impl.CollectionResult

ResultCollector = _impl.ResultCollector

__all__ = [
    "ERRORS_LOG_FILENAME",
    "CollectionMetadata",
    "CollectionResult",
    "GradingResult",
    "ResultCollector",
]
