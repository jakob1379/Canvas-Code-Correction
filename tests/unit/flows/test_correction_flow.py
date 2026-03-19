from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pydantic import HttpUrl, SecretStr

from canvas_code_correction.clients.canvas_resources import CanvasResources
from canvas_code_correction.config import (
    CanvasSettings,
    CourseAssetsSettings,
    GraderSettings,
    Settings,
    WorkspaceSettings,
)
from canvas_code_correction.flows.correction import (
    CollectedResults,
    CorrectionResults,
    CorrectionUploads,
    CorrectSubmissionPayload,
    ExecutionSummary,
    FeedbackUploadResult,
    GraderConfig,
    GradeUploadResult,
    SubmissionMetadata,
    UploadConfig,
    _canvas_object_to_dict,
    _resolve_download_dir,
    _resolve_grader_config,
    _resolve_upload_config,
    collect_results,
    correct_submission_flow,
    download_submission_files,
    execute_grader,
    post_grade,
    prepare_workspace_task,
    upload_feedback,
)
from canvas_code_correction.workspace import WorkspaceConfig, WorkspacePaths


def _make_settings() -> Settings:
    return Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.test"),
            token=SecretStr("token"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="bucket-block", path_prefix="prefix"),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(root=Path("/tmp/workspaces")),
    )


@pytest.mark.local
def test_download_submission_files_uses_resolved_names(tmp_path: Path) -> None:
    assignment = Mock()
    submission = Mock()
    second_attachment = Mock(id=22, filename=None, display_name=None)
    submission.attachments = [
        {"id": 11, "filename": "report.txt"},
        second_attachment,
        {"filename": "missing-id.txt"},
    ]
    assignment.get_submission.return_value = submission

    course = Mock()
    course.get_assignment.return_value = assignment

    first_file = Mock(filename="ignored.txt")
    second_file = Mock(display_name="grader.log")
    canvas = Mock()
    canvas.get_file.side_effect = [first_file, second_file]

    resources = CanvasResources(canvas=canvas, course=course, settings=_make_settings())
    payload = CorrectSubmissionPayload(assignment_id=7, submission_id=8)

    result = download_submission_files.fn(resources, payload, tmp_path)

    assert result == [tmp_path / "report.txt", tmp_path / "grader.log"]
    first_file.download.assert_called_once_with((tmp_path / "report.txt").as_posix())
    second_file.download.assert_called_once_with((tmp_path / "grader.log").as_posix())
    assert canvas.get_file.call_count == 2


@pytest.mark.local
def test_collect_results_returns_serializable_payload(tmp_path: Path) -> None:
    workspace = WorkspacePaths(
        root=tmp_path,
        submission_dir=tmp_path / "submission",
        assets_dir=tmp_path / "assets",
    )
    grading_result = Mock(
        points=95,
        comments="Nice work",
        points_file_content="95",
        artifacts_zip_path=tmp_path / "artifacts.zip",
        errors_log_path=None,
        metadata={"mode": "full"},
    )
    collection_result = Mock(
        grading_result=grading_result,
        discovered_files=[tmp_path / "feedback.txt"],
    )

    with patch("canvas_code_correction.flows.correction.ResultCollector") as mock_collector_cls:
        collector = mock_collector_cls.return_value
        collector.collect.return_value = collection_result
        collector.create_feedback_zip.return_value = tmp_path / "feedback.zip"
        collector.validate_result.return_value = ["warning"]

        result = collect_results.fn(workspace, submission_dir_name="submission")

    assert result == CollectedResults(
        points=95,
        comments="Nice work",
        points_file_content="95",
        feedback_zip_path=tmp_path / "feedback.zip",
        artifacts_zip_path=tmp_path / "artifacts.zip",
        errors_log_path=None,
        discovered_files=[tmp_path / "feedback.txt"],
        validation_issues=["warning"],
        metadata={"mode": "full"},
    )
    collector.collect.assert_called_once_with("submission")


@pytest.mark.local
def test_canvas_object_to_dict_ignores_private_attributes() -> None:
    class CanvasObject:
        def __init__(self) -> None:
            self.id = 10
            self.name = "Submission"
            self._secret = "hidden"

    assert _canvas_object_to_dict(CanvasObject()) == {"id": 10, "name": "Submission"}


@pytest.mark.local
def test_prepare_workspace_task_builds_config_and_prepares_workspace() -> None:
    resources = CanvasResources(canvas=Mock(), course=Mock(), settings=_make_settings())
    payload = CorrectSubmissionPayload(assignment_id=10, submission_id=20)
    submission_files = [Path("submission.py")]
    workspace = Mock()

    with (
        patch(
            "canvas_code_correction.flows.correction.prepare_workspace",
            return_value=workspace,
        ) as mock_prepare_workspace,
    ):
        result = prepare_workspace_task.fn(resources, payload, submission_files)

    assert result is workspace
    mock_prepare_workspace.assert_called_once_with(
        WorkspaceConfig(
            workspace_root=resources.settings.workspace.root,
            bucket_block=resources.settings.assets.bucket_block,
            path_prefix=resources.settings.assets.path_prefix,
            assignment_id=10,
            submission_id=20,
        ),
        submission_files,
    )


@pytest.mark.local
def test_execute_grader_returns_serializable_payload() -> None:
    workspace = WorkspacePaths(
        root=Path("workspace"),
        submission_dir=Path("workspace/submission"),
        assets_dir=Path("workspace/assets"),
    )
    execution_result = Mock(
        exit_code=0,
        timed_out=False,
        duration_seconds=12.5,
        stdout="done",
        stderr="",
        container_id="abc123",
    )

    with patch("canvas_code_correction.flows.correction.GraderExecutor") as mock_executor_cls:
        executor = mock_executor_cls.return_value
        executor.execute_in_workspace.return_value = execution_result

        result = execute_grader.fn(Mock(), workspace)

    assert result == ExecutionSummary(
        exit_code=0,
        timed_out=False,
        duration_seconds=12.5,
        stdout="done",
        stderr="",
        container_id="abc123",
    )


@pytest.mark.local
def test_upload_feedback_returns_failure_without_feedback_zip() -> None:
    resources = CanvasResources(canvas=Mock(), course=Mock(), settings=_make_settings())
    payload = CorrectSubmissionPayload(assignment_id=10, submission_id=20)

    result = upload_feedback.fn(
        resources,
        payload,
        results=CollectedResults(
            points=None,
            comments="",
            points_file_content="",
            feedback_zip_path=None,
            artifacts_zip_path=None,
            errors_log_path=None,
            discovered_files=[],
            validation_issues=[],
            metadata={},
        ),
    )

    assert result == FeedbackUploadResult(
        success=False,
        message="No feedback zip path in results",
        duplicate=False,
        comment_posted=False,
        details=None,
    )


@pytest.mark.local
def test_upload_feedback_uses_canvas_uploader(tmp_path: Path) -> None:
    submission = Mock()
    assignment = Mock()
    assignment.get_submission.return_value = submission
    course = Mock()
    course.get_assignment.return_value = assignment
    resources = CanvasResources(canvas=Mock(), course=course, settings=_make_settings())
    payload = CorrectSubmissionPayload(assignment_id=10, submission_id=20)
    upload_result = Mock(
        success=True,
        message="uploaded",
        duplicate=False,
        comment_posted=True,
        details={"id": 1},
    )

    with patch(
        "canvas_code_correction.flows.correction.create_uploader_from_resources",
    ) as mock_create:
        uploader = mock_create.return_value
        uploader.upload_feedback.return_value = upload_result

        result = upload_feedback.fn(
            resources,
            payload,
            results=CollectedResults(
                points=None,
                comments="",
                points_file_content="",
                feedback_zip_path=tmp_path / "feedback.zip",
                artifacts_zip_path=None,
                errors_log_path=None,
                discovered_files=[],
                validation_issues=[],
                metadata={},
            ),
        )

    assert result == FeedbackUploadResult(
        success=True,
        message="uploaded",
        duplicate=False,
        comment_posted=True,
        details={"id": 1},
    )


@pytest.mark.local
def test_post_grade_returns_failure_without_points() -> None:
    resources = CanvasResources(canvas=Mock(), course=Mock(), settings=_make_settings())
    payload = CorrectSubmissionPayload(assignment_id=10, submission_id=20)

    result = post_grade.fn(
        resources,
        payload,
        results=CollectedResults(
            points=None,
            comments="",
            points_file_content="",
            feedback_zip_path=Path(),
            artifacts_zip_path=None,
            errors_log_path=None,
            discovered_files=[],
            validation_issues=[],
            metadata={},
        ),
    )

    assert result == GradeUploadResult(
        success=False,
        message="No points in results",
        duplicate=False,
        grade_posted=False,
        details=None,
    )


@pytest.mark.local
def test_post_grade_uses_canvas_uploader() -> None:
    submission = Mock()
    assignment = Mock()
    assignment.get_submission.return_value = submission
    course = Mock()
    course.get_assignment.return_value = assignment
    resources = CanvasResources(canvas=Mock(), course=course, settings=_make_settings())
    payload = CorrectSubmissionPayload(assignment_id=10, submission_id=20)
    upload_result = Mock(
        success=True,
        message="posted",
        duplicate=False,
        grade_posted=True,
        details={"grade": "100"},
    )

    with patch(
        "canvas_code_correction.flows.correction.create_uploader_from_resources",
    ) as mock_create:
        uploader = mock_create.return_value
        uploader.upload_grade.return_value = upload_result

        result = post_grade.fn(
            resources,
            payload,
            results=CollectedResults(
                points=100,
                comments="",
                points_file_content="",
                feedback_zip_path=None,
                artifacts_zip_path=None,
                errors_log_path=None,
                discovered_files=[],
                validation_issues=[],
                metadata={},
            ),
        )

    assert result == GradeUploadResult(
        success=True,
        message="posted",
        duplicate=False,
        grade_posted=True,
        details={"grade": "100"},
    )


@pytest.mark.local
def test_resolve_download_dir_creates_temp_directory_when_missing(tmp_path: Path) -> None:
    created_dir = tmp_path / "generated-downloads"

    with patch(
        "canvas_code_correction.flows.correction.tempfile.mkdtemp",
        return_value=str(created_dir),
    ) as mock_mkdtemp:
        result = _resolve_download_dir(None)

    assert result == created_dir
    mock_mkdtemp.assert_called_once_with(prefix="ccc-download-")


@pytest.mark.local
def test_correct_submission_flow_uses_generated_download_directory(tmp_path: Path) -> None:
    payload = CorrectSubmissionPayload(assignment_id=10, submission_id=20)
    settings = _make_settings()
    resources = Mock()
    generated_dir = tmp_path / "generated-downloads"

    with (
        patch(
            "canvas_code_correction.flows.correction.build_canvas_resources",
            return_value=resources,
        ),
        patch(
            "canvas_code_correction.flows.correction.fetch_submission_metadata",
            return_value=SubmissionMetadata(assignment={}, submission={}),
        ),
        patch(
            "canvas_code_correction.flows.correction._resolve_download_dir",
            return_value=generated_dir,
        ) as mock_resolve_download_dir,
        patch(
            "canvas_code_correction.flows.correction.download_submission_files",
            return_value=[],
        ) as mock_download_files,
        patch(
            "canvas_code_correction.flows.correction.prepare_workspace_task",
            return_value=WorkspacePaths(
                root=tmp_path / "workspace",
                submission_dir=tmp_path / "workspace" / "submission",
                assets_dir=tmp_path / "workspace" / "assets",
            ),
        ),
        patch(
            "canvas_code_correction.flows.correction.create_default_grader_config",
            return_value=Mock(),
        ),
        patch(
            "canvas_code_correction.flows.correction.execute_grader",
            return_value=ExecutionSummary(
                exit_code=0,
                timed_out=False,
                duration_seconds=0.0,
                stdout="",
                stderr="",
                container_id=None,
            ),
        ),
        patch(
            "canvas_code_correction.flows.correction.collect_results",
            return_value=CollectedResults(
                points=None,
                comments="",
                points_file_content="",
                feedback_zip_path=None,
                artifacts_zip_path=None,
                errors_log_path=None,
                discovered_files=[],
                validation_issues=[],
                metadata={},
            ),
        ),
        patch(
            "canvas_code_correction.flows.correction.upload_feedback",
            return_value=FeedbackUploadResult(
                success=False,
                message="",
                duplicate=False,
                comment_posted=False,
                details=None,
            ),
        ),
        patch(
            "canvas_code_correction.flows.correction.post_grade",
            return_value=GradeUploadResult(
                success=False,
                message="",
                duplicate=False,
                grade_posted=False,
                details=None,
            ),
        ),
    ):
        correct_submission_flow.fn(payload, settings, download_dir=None)

    mock_resolve_download_dir.assert_called_once_with(None)
    mock_download_files.assert_called_once_with(resources, payload, generated_dir)


@pytest.mark.local
def test_correct_submission_flow_orchestrates_stages(tmp_path: Path) -> None:
    payload = CorrectSubmissionPayload(assignment_id=10, submission_id=20)
    settings = _make_settings()
    resources = Mock()
    metadata = SubmissionMetadata(assignment={"id": 10}, submission={"id": 20})
    downloaded = [tmp_path / "downloaded.txt"]
    workspace = WorkspacePaths(
        root=tmp_path / "workspace",
        submission_dir=tmp_path / "workspace" / "submission",
        assets_dir=tmp_path / "workspace" / "assets",
    )
    grader_config = Mock()
    execution_result = ExecutionSummary(
        exit_code=0,
        timed_out=False,
        duration_seconds=1.0,
        stdout="",
        stderr="",
        container_id=None,
    )
    collection_result = CollectedResults(
        points=100,
        comments="",
        points_file_content="100",
        feedback_zip_path=tmp_path / "feedback.zip",
        artifacts_zip_path=None,
        errors_log_path=None,
        discovered_files=[],
        validation_issues=[],
        metadata={},
    )
    feedback_result = FeedbackUploadResult(
        success=True,
        message="uploaded",
        duplicate=False,
        comment_posted=True,
        details={},
    )
    grade_result = GradeUploadResult(
        success=True,
        message="posted",
        duplicate=False,
        grade_posted=True,
        details={},
    )

    with (
        patch(
            "canvas_code_correction.flows.correction.build_canvas_resources",
            return_value=resources,
        ),
        patch(
            "canvas_code_correction.flows.correction.fetch_submission_metadata",
            return_value=metadata,
        ),
        patch(
            "canvas_code_correction.flows.correction.download_submission_files",
            return_value=downloaded,
        ),
        patch(
            "canvas_code_correction.flows.correction.prepare_workspace_task",
            return_value=workspace,
        ),
        patch(
            "canvas_code_correction.flows.correction.create_default_grader_config",
            return_value=grader_config,
        ) as mock_create_default,
        patch(
            "canvas_code_correction.flows.correction.execute_grader",
            return_value=execution_result,
        ),
        patch(
            "canvas_code_correction.flows.correction.collect_results",
            return_value=collection_result,
        ),
        patch(
            "canvas_code_correction.flows.correction.upload_feedback",
            return_value=feedback_result,
        ) as mock_upload_feedback,
        patch(
            "canvas_code_correction.flows.correction.post_grade",
            return_value=grade_result,
        ) as mock_post_grade,
    ):
        result = correct_submission_flow.fn(
            payload,
            settings,
            download_dir=tmp_path / "downloads",
            dry_run=True,
        )

    assert result.submission_metadata == metadata
    assert result.downloaded_files == downloaded
    assert result.workspace == workspace
    assert result.results == CorrectionResults(
        execution=execution_result,
        collection=collection_result,
        feedback_upload=feedback_result,
        grade_upload=grade_result,
    )
    assert result.uploads == CorrectionUploads(
        feedback=feedback_result,
        grade=grade_result,
    )
    mock_create_default.assert_called_once_with(
        docker_image="jakob1379/canvas-grader:latest",
        command=["sh", "main.sh"],
        timeout_seconds=300,
        memory_mb=512,
    )
    mock_upload_feedback.assert_called_once()
    assert mock_upload_feedback.call_args.args[3] == UploadConfig(
        check_duplicates=True,
        upload_comments=True,
        upload_grades=True,
        dry_run=True,
        verbose=False,
    )
    assert mock_post_grade.call_args.args[3] == UploadConfig(
        check_duplicates=True,
        upload_comments=True,
        upload_grades=True,
        dry_run=True,
        verbose=False,
    )


def test_correct_submission_flow_resolves_policy_configs(tmp_path: Path) -> None:
    payload = CorrectSubmissionPayload(assignment_id=10, submission_id=20)
    settings = _make_settings()
    resources = Mock()
    workspace = WorkspacePaths(
        root=tmp_path / "workspace",
        submission_dir=tmp_path / "workspace" / "submission",
        assets_dir=tmp_path / "workspace" / "assets",
    )
    resolved_grader_config = GraderConfig(
        docker_image="override-image:latest",
        command=["python", "run.py"],
    )
    resolved_upload_config = UploadConfig(
        check_duplicates=False,
        upload_comments=False,
        upload_grades=False,
        dry_run=True,
    )

    with (
        patch(
            "canvas_code_correction.flows.correction.build_canvas_resources",
            return_value=resources,
        ),
        patch(
            "canvas_code_correction.flows.correction.fetch_submission_metadata",
            return_value=SubmissionMetadata(assignment={}, submission={}),
        ),
        patch(
            "canvas_code_correction.flows.correction._resolve_download_dir",
            return_value=tmp_path / "downloads",
        ),
        patch(
            "canvas_code_correction.flows.correction.download_submission_files",
            return_value=[],
        ),
        patch(
            "canvas_code_correction.flows.correction.prepare_workspace_task",
            return_value=workspace,
        ),
        patch(
            "canvas_code_correction.flows.correction._resolve_grader_config",
            return_value=resolved_grader_config,
        ) as mock_resolve_grader_config,
        patch(
            "canvas_code_correction.flows.correction._resolve_upload_config",
            return_value=resolved_upload_config,
        ) as mock_resolve_upload_config,
        patch(
            "canvas_code_correction.flows.correction.execute_grader",
            return_value=ExecutionSummary(
                exit_code=0,
                timed_out=False,
                duration_seconds=0.0,
                stdout="",
                stderr="",
                container_id=None,
            ),
        ) as mock_execute_grader,
        patch(
            "canvas_code_correction.flows.correction.collect_results",
            return_value=CollectedResults(
                points=None,
                comments="",
                points_file_content="",
                feedback_zip_path=None,
                artifacts_zip_path=None,
                errors_log_path=None,
                discovered_files=[],
                validation_issues=[],
                metadata={},
            ),
        ),
        patch(
            "canvas_code_correction.flows.correction.upload_feedback",
            return_value=FeedbackUploadResult(
                success=False,
                message="",
                duplicate=False,
                comment_posted=False,
                details=None,
            ),
        ) as mock_upload_feedback,
        patch(
            "canvas_code_correction.flows.correction.post_grade",
            return_value=GradeUploadResult(
                success=False,
                message="",
                duplicate=False,
                grade_posted=False,
                details=None,
            ),
        ) as mock_post_grade,
    ):
        correct_submission_flow.fn(
            payload,
            settings,
            download_dir=tmp_path / "downloads",
            dry_run=True,
        )

    mock_resolve_grader_config.assert_called_once_with(settings)
    mock_resolve_upload_config.assert_called_once_with(settings, dry_run=True)
    mock_execute_grader.assert_called_once_with(resolved_grader_config, workspace)
    assert mock_upload_feedback.call_args.args[3] == resolved_upload_config
    assert mock_post_grade.call_args.args[3] == resolved_upload_config


def test_resolve_grader_config_uses_settings_defaults() -> None:
    settings = _make_settings()
    settings.grader.docker_image = "custom/image:latest"
    settings.grader.command = ["python", "run.sh"]
    settings.grader.timeout_seconds = 123
    settings.grader.memory_mb = 1024

    config = _resolve_grader_config(settings)

    assert config.docker_image == "custom/image:latest"
    assert config.command == ["python", "run.sh"]
    assert config.resource_limits.timeout_seconds == 123
    assert config.resource_limits.memory_mb == 1024


def test_resolve_grader_config_accepts_override() -> None:
    settings = _make_settings()
    override = GraderConfig(docker_image="override:latest")

    assert _resolve_grader_config(settings, grader_config=override) is override


def test_resolve_upload_config_uses_settings_defaults() -> None:
    settings = _make_settings()
    settings.grader.upload_check_duplicates = False
    settings.grader.upload_comments = False
    settings.grader.upload_grades = True
    settings.grader.upload_verbose = True

    config = _resolve_upload_config(settings, dry_run=False)

    assert config == UploadConfig(
        check_duplicates=False,
        upload_comments=False,
        upload_grades=True,
        dry_run=False,
        verbose=True,
    )


def test_resolve_upload_config_accepts_override() -> None:
    settings = _make_settings()
    override = UploadConfig(check_duplicates=False, upload_comments=False, upload_grades=False)

    assert _resolve_upload_config(settings, dry_run=True, upload_config=override) is override
