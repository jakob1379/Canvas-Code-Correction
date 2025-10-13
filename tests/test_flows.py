from pathlib import Path

from canvas_code_correction.config import Settings
from canvas_code_correction.flows.correct_submission import correct_submission_flow


def test_correct_submission_flow(tmp_path: Path):
    settings = Settings.model_validate(
        {
            "canvas": {
                "api_url": "https://canvas.example",
                "token": "token",
                "course_id": 123,
            },
            "working_dir": tmp_path,
        }
    )

    result = correct_submission_flow.fn(
        assignment_id=1,
        submission_id=42,
        settings=settings,
    )

    assert result["status"] == "pending"
    assert (tmp_path / "1" / "42").exists()
