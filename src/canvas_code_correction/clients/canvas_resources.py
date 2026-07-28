"""Helpers for constructing reusable Canvas API resources."""

from dataclasses import dataclass

from canvasapi import Canvas
from canvasapi.assignment import Assignment
from canvasapi.course import Course
from canvasapi.exceptions import ResourceDoesNotExist
from canvasapi.submission import Submission

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


def resolve_submission_for_assignment(
    assignment: Assignment,
    submission_id: int,
    *,
    include: list[str] | None = None,
) -> Submission:
    """Resolve a Canvas submission by its record ID.

    Canvas keys assignment submission endpoints by *user* ID, so the direct lookup
    can silently return a different student's submission when a user ID happens to
    equal the requested submission ID. Verify the record ID we got back, and fall
    back to scanning the assignment's submissions when it does not match.
    """
    kwargs = {"include": include} if include else {}
    try:
        submission = assignment.get_submission(submission_id, **kwargs)
    except ResourceDoesNotExist:
        submission = None
    else:
        if submission.id == submission_id:
            return submission

    for candidate in assignment.get_submissions():
        if candidate.id == submission_id:
            return assignment.get_submission(candidate.user_id, **kwargs)

    if submission is not None:
        return submission
    msg = f"no submission with id {submission_id} on assignment {assignment.id}"
    raise ResourceDoesNotExist(msg)


def get_assignment_submission(
    course: Course,
    assignment_id: int,
    submission_id: int,
    *,
    include: list[str] | None = None,
) -> tuple[Assignment, Submission]:
    """Return the assignment and resolved submission for the provided identifiers."""
    assignment = course.get_assignment(assignment_id)
    return assignment, resolve_submission_for_assignment(
        assignment,
        submission_id,
        include=include,
    )
