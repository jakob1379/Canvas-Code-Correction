"""Helpers for constructing reusable Canvas API resources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from canvasapi import Canvas
from canvasapi.course import Course

if TYPE_CHECKING:  # pragma: no cover - import for type checkers only
    from canvas_code_correction.config import Settings


@dataclass(frozen=True)
class CanvasResources:
    """Aggregated Canvas API objects shared between Prefect tasks."""

    canvas: Canvas
    course: Course
    settings: Settings


def build_canvas_resources(
    settings: Settings,
    *,
    canvas: Canvas | None = None,
) -> CanvasResources:
    """Construct a :class:`CanvasResources` bundle.

    Parameters
    ----------
    settings:
        Configuration containing Canvas connection details.
    canvas:
        Optional preconfigured :class:`~canvasapi.Canvas` instance for testing.
    """

    api_client = canvas or Canvas(settings.canvas.api_url, settings.canvas.token)
    course = api_client.get_course(settings.canvas.course_id)
    return CanvasResources(canvas=api_client, course=course, settings=settings)
