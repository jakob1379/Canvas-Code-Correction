"""Flow triggering for webhook-triggered corrections."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from canvas_code_correction.config import Settings, resolve_settings_from_block
from canvas_code_correction.flows import (
    CorrectSubmissionPayload,
    correct_submission_flow,
)

logger = logging.getLogger(__name__)


async def trigger_flow(
    course_block: str,
    assignment_id: int,
    submission_id: int,
    settings: Settings,
) -> str | None:
    """Trigger correction flow for a submission.

    Runs the flow in a separate thread to avoid blocking the webhook response.
    Returns flow run ID if successful, None otherwise.
    """
    try:
        # Create payload
        payload = CorrectSubmissionPayload(
            assignment_id=assignment_id,
            submission_id=submission_id,
        )

        # Run flow in separate thread (since it's synchronous)
        # Note: This runs the flow locally, not via a work pool.
        # For production, consider creating a deployment and using work pools.
        def run_flow() -> dict:
            """Synchronous flow execution."""
            # Use temporary download directory
            import tempfile

            with tempfile.TemporaryDirectory(prefix="ccc-webhook-") as tmpdir:
                artifacts = correct_submission_flow(
                    payload=payload,
                    settings=settings,
                    download_dir=Path(tmpdir),
                    dry_run=False,
                )
                # Return minimal info
                return {
                    "success": True,
                    "submission_metadata_keys": list(artifacts.submission_metadata.keys()),
                }

        # Run in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_flow)

        logger.info(
            "Triggered correction flow for %s: assignment %s, submission %s",
            course_block,
            assignment_id,
            submission_id,
        )

        # Generate a fake flow run ID for now (since we're not using Prefect API)
        # In production, you would use `flow.deploy()` and `run_deployment()`.
        import uuid

        flow_run_id = f"local-{uuid.uuid4().hex[:8]}"
        return flow_run_id

    except Exception as e:
        logger.error(
            "Failed to trigger flow for %s (assignment %s, submission %s): %s",
            course_block,
            assignment_id,
            submission_id,
            e,
            exc_info=True,
        )
        return None


# Alias for backward compatibility
trigger_deployment = trigger_flow
