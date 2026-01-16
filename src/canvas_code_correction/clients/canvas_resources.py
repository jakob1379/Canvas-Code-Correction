"""Helpers for constructing reusable Canvas API resources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from canvasapi import Canvas

from canvas_code_correction.config import Settings

if TYPE_CHECKING:
    from canvasapi.course import Course


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


def build_canvas_resources_from_course_block(
    block_name: str,
    *,
    canvas: Canvas | None = None,
) -> CanvasResources:
    """Construct CanvasResources from a Prefect course configuration block.

    Parameters
    ----------
    block_name:
        Name of the Prefect course configuration block.
    canvas:
        Optional preconfigured :class:`~canvasapi.Canvas` instance for testing.

    Returns
    -------
    CanvasResources
        Configured Canvas API resources.

    """
    settings = Settings.from_course_block(block_name)
    return build_canvas_resources(settings, canvas=canvas)
