# bandit: disable=B101
"""Tests for the result collector."""

from pathlib import Path

from canvas_code_correction.result_collector import collect_results


def _create_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path
    (workspace / "submission").mkdir(parents=True, exist_ok=True)
    (workspace / "submission" / "artifact.txt").write_text("data", encoding="utf-8")
    (workspace / "points.txt").write_text("5\n3\ninvalid\n", encoding="utf-8")
    (workspace / "comments.txt").write_text("Great job!", encoding="utf-8")
    (workspace / "results.json").write_text('{"status": "ok"}', encoding="utf-8")
    return workspace


def test_collect_results(tmp_path: Path) -> None:
    workspace = _create_workspace(tmp_path)

    payload = collect_results(workspace, {"status": "success"}).as_payload()

    assert payload["points"] == 8  # nosec B101
    assert payload["points_breakdown"] == [5.0, 3.0]  # nosec B101
    assert payload["comment"] == "Great job!"  # nosec B101
    assert payload["feedback_zip"]  # nosec B101
    assert Path(payload["feedback_zip"]).exists()  # nosec B101
    assert payload["metadata"]["results"]["status"] == "ok"  # nosec B101


def test_collect_results_missing_files(tmp_path: Path) -> None:
    workspace = tmp_path
    (workspace / "submission").mkdir(parents=True, exist_ok=True)

    payload = collect_results(workspace, {}).as_payload()

    assert payload["points"] == 0  # nosec B101
    assert payload["comment"] == ""  # nosec B101
    assert payload["feedback_zip"]  # nosec B101
