"""Helpers for constructing reusable Canvas API resources."""

from dataclasses import dataclass

from canvasapi import Canvas
from canvasapi.course import Course

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
    token = settings.canvas.token.get_secret_value()
    api_client = canvas or Canvas(str(settings.canvas.api_url), token)
    course = api_client.get_course(settings.canvas.course_id)
    return CanvasResources(canvas=api_client, course=course, settings=settings)
