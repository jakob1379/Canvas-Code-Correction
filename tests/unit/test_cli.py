"""Unit tests for the CLI module."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from canvas_code_correction.bootstrap import load_settings_from_course_block
from canvas_code_correction.cli import app
from canvas_code_correction.config import Settings
from canvas_code_correction.flows.correction import (
    CollectedResults,
    CorrectionResults,
    CorrectionUploads,
    ExecutionSummary,
    FeedbackUploadResult,
    FlowArtifacts,
    GradeUploadResult,
    SubmissionMetadata,
)
from canvas_code_correction.prefect_blocks.canvas import CourseConfigBlock
from canvas_code_correction.webhooks.deployments import DeploymentEnsureResult


@pytest.fixture
def cli_runner() -> CliRunner:
    """Return a Typer CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_course_block() -> MagicMock:
    """Return a mock CourseConfigBlock."""
    from pydantic import HttpUrl, SecretStr

    mock = MagicMock(spec=CourseConfigBlock)
    mock.canvas_api_url = HttpUrl("https://canvas.example.com")
    mock.canvas_token = SecretStr("secret-token")
    mock.canvas_course_id = 123
    mock.asset_bucket_block = "test-bucket"
    mock.asset_path_prefix = "prefix"
    mock.workspace_root = None
    mock.grader_image = "test/image:latest"
    mock.work_pool_name = "test-pool"
    mock.grader_env = {}
    mock.grader_command = ["sh", "/workspace/assets/main.sh"]
    mock.grader_timeout_seconds = 300
    mock.grader_memory_mb = 512
    mock.grader_upload_check_duplicates = True
    mock.grader_upload_comments = True
    mock.grader_upload_grades = True
    mock.grader_upload_verbose = False
    mock.webhook_secret = None
    mock.deployment_name = None
    mock.webhook_enabled = True
    mock.webhook_require_jwt = False
    mock.webhook_rate_limit = "10/minute"
    return mock


@pytest.fixture
def mock_settings(mock_course_block: MagicMock) -> Settings:
    """Return a Settings object from a mock course block."""
    # Mock the load method to return our mock block
    with patch.object(CourseConfigBlock, "load", return_value=mock_course_block):
        return load_settings_from_course_block("dummy-block")


@pytest.fixture
def mock_flow_artifacts(tmp_path: Path) -> FlowArtifacts:
    """Return mock FlowArtifacts for testing."""
    return FlowArtifacts(
        submission_metadata=SubmissionMetadata(assignment={}, submission={}),
        downloaded_files=[tmp_path / "file1.txt"],
        workspace=None,
        results=CorrectionResults(
            execution=ExecutionSummary(
                exit_code=0,
                timed_out=False,
                duration_seconds=0.0,
                stdout="",
                stderr="",
                container_id=None,
            ),
            collection=CollectedResults(
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
            feedback_upload=FeedbackUploadResult(
                success=False,
                message="",
                duplicate=False,
                comment_posted=False,
                details=None,
            ),
            grade_upload=GradeUploadResult(
                success=False,
                message="",
                duplicate=False,
                grade_posted=False,
                details=None,
            ),
        ),
        uploads=CorrectionUploads(
            feedback=FeedbackUploadResult(
                success=False,
                message="",
                duplicate=False,
                comment_posted=False,
                details=None,
            ),
            grade=GradeUploadResult(
                success=False,
                message="",
                duplicate=False,
                grade_posted=False,
                details=None,
            ),
        ),
    )


# ----- run_once command tests -----


@pytest.mark.local
@patch("canvas_code_correction.cli.load_settings_from_course_block")
@patch("canvas_code_correction.cli.correct_submission_flow")
def test_run_once_single_submission_success(
    mock_flow: MagicMock,
    mock_resolve_settings: MagicMock,
    cli_runner: CliRunner,
    mock_settings: Settings,
    mock_flow_artifacts: FlowArtifacts,
    tmp_path: Path,
) -> None:
    """Test run_once command with single submission success."""
    # Setup mocks
    mock_resolve_settings.return_value = mock_settings
    mock_flow.return_value = mock_flow_artifacts

    result = cli_runner.invoke(
        app,
        ["course", "run", "123", "--submission-id", "456", "--course", "test-course"],
    )

    assert result.exit_code == 0
    assert "Correction flow completed successfully" in result.output
    mock_resolve_settings.assert_called_once_with("test-course")
    mock_flow.assert_called_once()


@pytest.mark.local
@patch("canvas_code_correction.cli.load_settings_from_course_block")
@patch("canvas_code_correction.cli.correct_submission_flow")
def test_run_once_submission_id_zero_still_uses_single_submission_mode(
    mock_flow: MagicMock,
    mock_resolve_settings: MagicMock,
    cli_runner: CliRunner,
    mock_settings: Settings,
    mock_flow_artifacts: FlowArtifacts,
) -> None:
    mock_resolve_settings.return_value = mock_settings
    mock_flow.return_value = mock_flow_artifacts

    result = cli_runner.invoke(
        app,
        ["course", "run", "123", "--submission-id", "0", "--course", "test-course"],
    )

    assert result.exit_code == 0
    assert "submission 0" in result.output
    mock_flow.assert_called_once()


@pytest.mark.local
@patch("canvas_code_correction.cli.load_settings_from_course_block")
@patch("canvas_code_correction.cli.build_canvas_resources")
@patch("canvas_code_correction.cli.correct_submission_flow")
def test_run_once_batch_mode_success(
    mock_flow: MagicMock,
    mock_build_canvas_resources: MagicMock,
    mock_resolve_settings: MagicMock,
    cli_runner: CliRunner,
    mock_settings: Settings,
    tmp_path: Path,
) -> None:
    """Test run_once command in batch mode (no submission-id)."""
    # Setup mocks
    mock_resolve_settings.return_value = mock_settings

    # Mock Canvas resources and assignment submissions
    mock_resources = MagicMock()
    mock_assignment = MagicMock()
    mock_submission1 = MagicMock()
    mock_submission1.id = 100
    mock_submission2 = MagicMock()
    mock_submission2.id = 101
    mock_assignment.get_submissions.return_value = [mock_submission1, mock_submission2]
    mock_resources.course.get_assignment.return_value = mock_assignment
    mock_build_canvas_resources.return_value = mock_resources

    # Mock flow to return something (won't be used due to batch mode loop)
    mock_flow.return_value = None

    result = cli_runner.invoke(
        app,
        ["course", "run", "123", "--course", "test-course"],
    )

    assert result.exit_code == 0
    assert "Batch mode: processing all submissions" in result.output
    assert "Batch processing completed" in result.output
    mock_resolve_settings.assert_called_once_with("test-course")
    mock_build_canvas_resources.assert_called_once_with(mock_settings)
    # Should call correct_submission_flow for each submission
    assert mock_flow.call_count == 2


@pytest.mark.local
@patch("canvas_code_correction.cli.load_settings_from_course_block")
@patch("canvas_code_correction.cli.build_canvas_resources")
@patch("canvas_code_correction.cli.correct_submission_flow")
def test_run_once_batch_mode_submission_error(
    mock_flow: MagicMock,
    mock_build_canvas_resources: MagicMock,
    mock_resolve_settings: MagicMock,
    cli_runner: CliRunner,
    mock_settings: Settings,
    mock_flow_artifacts: FlowArtifacts,
    tmp_path: Path,
) -> None:
    """Test batch mode when a submission raises exception but loop continues."""
    mock_resolve_settings.return_value = mock_settings

    # Mock Canvas resources and assignment submissions
    mock_resources = MagicMock()
    mock_assignment = MagicMock()
    mock_submission1 = MagicMock()
    mock_submission1.id = 100
    mock_submission2 = MagicMock()
    mock_submission2.id = 101
    mock_assignment.get_submissions.return_value = [mock_submission1, mock_submission2]
    mock_resources.course.get_assignment.return_value = mock_assignment
    mock_build_canvas_resources.return_value = mock_resources

    # First submission fails, second succeeds
    mock_flow.side_effect = [RuntimeError("Flow error"), mock_flow_artifacts]

    result = cli_runner.invoke(
        app,
        ["course", "run", "123", "--course", "test-course"],
    )

    assert result.exit_code == 1
    assert "Batch mode: processing all submissions" in result.output
    assert "Error processing submission 100" in result.output
    assert "Submission 101 processed successfully" in result.output
    assert "Batch processing completed with failures: 100" in result.output
    mock_resolve_settings.assert_called_once_with("test-course")
    mock_build_canvas_resources.assert_called_once_with(mock_settings)
    assert mock_flow.call_count == 2


@pytest.mark.local
@patch("canvas_code_correction.cli.load_settings_from_course_block")
@patch("canvas_code_correction.cli.correct_submission_flow")
def test_run_once_dry_run_flag(
    mock_flow: MagicMock,
    mock_resolve_settings: MagicMock,
    cli_runner: CliRunner,
    mock_settings: Settings,
    mock_flow_artifacts: FlowArtifacts,
) -> None:
    """Test run_once command with dry-run flag."""
    mock_resolve_settings.return_value = mock_settings
    mock_flow.return_value = mock_flow_artifacts

    result = cli_runner.invoke(
        app,
        [
            "course",
            "run",
            "123",
            "--submission-id",
            "456",
            "--course",
            "test-course",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "Dry run enabled" in result.output
    mock_flow.assert_called_once()
    # Ensure dry_run parameter is passed
    call_kwargs = mock_flow.call_args.kwargs
    assert call_kwargs.get("dry_run") is True


@pytest.mark.local
@patch("canvas_code_correction.cli.load_settings_from_course_block")
@patch("canvas_code_correction.cli.correct_submission_flow")
def test_run_once_custom_download_dir(
    mock_flow: MagicMock,
    mock_resolve_settings: MagicMock,
    cli_runner: CliRunner,
    mock_settings: Settings,
    mock_flow_artifacts: FlowArtifacts,
    tmp_path: Path,
) -> None:
    """Test run_once command with custom download directory."""
    mock_resolve_settings.return_value = mock_settings
    mock_flow.return_value = mock_flow_artifacts

    custom_dir = tmp_path / "custom"
    custom_dir.mkdir()

    result = cli_runner.invoke(
        app,
        [
            "course",
            "run",
            "123",
            "--submission-id",
            "456",
            "--course",
            "test-course",
            "--download-dir",
            str(custom_dir),
        ],
    )

    assert result.exit_code == 0
    # Should not show temporary directory warning
    assert "Using temporary download directory" not in result.output
    mock_flow.assert_called_once()
    call_kwargs = mock_flow.call_args.kwargs
    assert call_kwargs.get("download_dir") == custom_dir


@pytest.mark.local
@patch("canvas_code_correction.cli.load_settings_from_course_block")
def test_run_once_course_block_not_found(
    mock_resolve_settings: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Test run_once command when course block not found."""
    mock_resolve_settings.side_effect = ValueError("Block not found")

    result = cli_runner.invoke(
        app,
        ["course", "run", "123", "--submission-id", "456", "--course", "test-course"],
    )

    assert result.exit_code == 1
    assert "Error loading course block" in result.output
    mock_resolve_settings.assert_called_once_with("test-course")


@pytest.mark.local
@patch("canvas_code_correction.cli.load_settings_from_course_block")
@patch("canvas_code_correction.cli.correct_submission_flow")
def test_run_once_flow_raises_exception(
    mock_flow: MagicMock,
    mock_resolve_settings: MagicMock,
    cli_runner: CliRunner,
    mock_settings: Settings,
) -> None:
    """Test run_once command when correct_submission_flow raises exception."""
    mock_resolve_settings.return_value = mock_settings
    mock_flow.side_effect = RuntimeError("Flow failed")

    result = cli_runner.invoke(
        app,
        ["course", "run", "123", "--submission-id", "456", "--course", "test-course"],
    )

    assert result.exit_code == 1
    assert "Error running correction flow" in result.output
    mock_flow.assert_called_once()


@pytest.mark.local
@patch("canvas_code_correction.cli.load_settings_from_course_block")
@patch("canvas_code_correction.cli.build_canvas_resources")
def test_run_once_batch_mode_canvas_api_error(
    mock_build_canvas_resources: MagicMock,
    mock_resolve_settings: MagicMock,
    cli_runner: CliRunner,
    mock_settings: Settings,
) -> None:
    """Test batch mode when Canvas API get_assignment raises exception."""
    mock_resolve_settings.return_value = mock_settings
    mock_resources = MagicMock()
    mock_resources.course.get_assignment.side_effect = ConnectionError("API error")
    mock_build_canvas_resources.return_value = mock_resources

    result = cli_runner.invoke(
        app,
        ["course", "run", "123", "--course", "test-course"],
    )

    # The exception is not caught in the CLI, so it propagates and Typer will exit with error.
    assert result.exit_code == 1
    # The exception should be present in result.exception or traceback in output
    assert result.exception is not None
    assert isinstance(result.exception, ConnectionError)
    # The output may contain the error message
    assert "API error" in str(result.exception)
    mock_resolve_settings.assert_called_once_with("test-course")


# ----- course command structure tests -----


@pytest.mark.local
def test_course_help_hides_configure(cli_runner: CliRunner) -> None:
    """Test course help only advertises setup, run, and list."""
    result = cli_runner.invoke(app, ["course", "--help"])

    assert result.exit_code == 0
    assert "setup" in result.output
    assert "run" in result.output
    assert "list" in result.output
    assert "│ configure" not in result.output


@pytest.mark.local
def test_course_configure_command_unavailable(cli_runner: CliRunner) -> None:
    """Test configure command is no longer available."""
    result = cli_runner.invoke(app, ["course", "configure", "--help"])

    assert result.exit_code != 0


# ----- list_courses command tests -----


@pytest.mark.local
@patch("canvas_code_correction.cli.load_course_block")
@patch("canvas_code_correction.cli.find_course_block_names")
def test_list_courses_success_with_blocks(
    mock_find_course_blocks: MagicMock,
    mock_load_course_block: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Test list_courses command when blocks exist."""
    mock_find_course_blocks.return_value = ["ccc-course-cs101", "ccc-course-cs102"]

    # Mock load for each block
    mock_block1 = MagicMock()
    mock_block1.canvas_course_id = 101
    mock_block1.grader_image = "image1:latest"
    mock_block1.asset_bucket_block = "bucket1"
    mock_block2 = MagicMock()
    mock_block2.canvas_course_id = 102
    mock_block2.grader_image = None
    mock_block2.asset_bucket_block = "bucket2"

    mock_load_course_block.side_effect = [mock_block1, mock_block2]

    result = cli_runner.invoke(app, ["course", "list"])

    assert result.exit_code == 0
    assert "Configured Courses" in result.output
    assert "ccc-course-cs101" in result.output
    assert "ccc-course-cs102" in result.output
    mock_find_course_blocks.assert_called_once()
    assert mock_load_course_block.call_count == 2


@pytest.mark.local
@patch("canvas_code_correction.cli.find_course_block_names")
def test_list_courses_empty_result(
    mock_find_course_blocks: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Test list_courses command when no blocks found."""
    mock_find_course_blocks.return_value = []

    result = cli_runner.invoke(app, ["course", "list"])

    assert result.exit_code == 0
    assert "No course configuration blocks found" in result.output
    mock_find_course_blocks.assert_called_once()


@pytest.mark.local
@patch("canvas_code_correction.cli.find_course_block_names")
def test_list_courses_find_raises_exception(
    mock_find_course_blocks: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Test list_courses when find raises exception."""
    mock_find_course_blocks.side_effect = RuntimeError("Find failed")

    result = cli_runner.invoke(app, ["course", "list"])

    assert result.exit_code == 1
    assert "Error listing courses" in result.output
    mock_find_course_blocks.assert_called_once()


@pytest.mark.local
@patch("canvas_code_correction.cli.load_course_block")
@patch("canvas_code_correction.cli.find_course_block_names")
def test_list_courses_load_raises_exception(
    mock_find_course_blocks: MagicMock,
    mock_load_course_block: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Test list_courses when load raises exception for a block."""
    mock_find_course_blocks.return_value = ["ccc-course-cs101", "ccc-course-cs102"]
    mock_load_course_block.side_effect = RuntimeError("Load failed")

    result = cli_runner.invoke(app, ["course", "list"])

    # Should still exit with 0 and show error in table
    assert result.exit_code == 0
    assert "Error: Load failed" in result.output
    mock_find_course_blocks.assert_called_once()
    assert mock_load_course_block.call_count == 2


# ----- webhook serve command tests -----


@pytest.mark.local
@patch("canvas_code_correction.cli.uvicorn.run")
def test_webhook_serve_success_default_host_port(
    mock_uvicorn_run: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Test webhook serve command with default host/port."""
    # Mock uvicorn.run to raise SystemExit to stop infinite loop
    mock_uvicorn_run.side_effect = SystemExit(0)

    result = cli_runner.invoke(app, ["system", "webhook", "serve"])

    # Since we raise SystemExit, the CLI will exit with that code
    # CliRunner will catch SystemExit and treat as exit code 0
    assert result.exit_code == 0
    assert "Starting webhook server on 127.0.0.1:8080" in result.output
    mock_uvicorn_run.assert_called_once_with(
        mock_uvicorn_run.call_args[0][0],  # webhook_fastapi_app
        host="127.0.0.1",
        port=8080,
    )


@pytest.mark.local
@patch("canvas_code_correction.cli.uvicorn.run")
def test_webhook_serve_success_custom_host_port(
    mock_uvicorn_run: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Test webhook serve command with custom host/port."""
    mock_uvicorn_run.side_effect = SystemExit(0)

    result = cli_runner.invoke(
        app,
        ["system", "webhook", "serve", "--host", "127.0.0.1", "--port", "9090"],
    )

    assert result.exit_code == 0
    assert "Starting webhook server on 127.0.0.1:9090" in result.output
    mock_uvicorn_run.assert_called_once_with(
        mock_uvicorn_run.call_args[0][0],
        host="127.0.0.1",
        port=9090,
    )


@pytest.mark.local
@patch("canvas_code_correction.cli.uvicorn.run")
def test_webhook_serve_uvicorn_raises_exception(
    mock_uvicorn_run: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Test webhook serve when uvicorn.run raises exception."""
    mock_uvicorn_run.side_effect = RuntimeError("Uvicorn error")

    _ = cli_runner.invoke(app, ["system", "webhook", "serve"])

    # The exception will propagate and CLI will exit with non-zero
    # We'll just check that uvicorn.run was called.
    mock_uvicorn_run.assert_called_once()


# ----- deploy create command tests -----


@pytest.mark.local
@patch("canvas_code_correction.cli.load_settings_from_course_block")
@patch("canvas_code_correction.cli.ensure_deployment", new_callable=AsyncMock)
def test_deploy_create_success(
    mock_ensure_deployment: AsyncMock,
    mock_resolve_settings: MagicMock,
    cli_runner: CliRunner,
    mock_settings: Settings,
) -> None:
    """Test deploy create command success."""
    mock_resolve_settings.return_value = mock_settings
    mock_ensure_deployment.return_value = DeploymentEnsureResult(
        deployment_name="ccc-course-test-deployment",
        work_pool_name="local-pool",
        ensured=True,
        deployment_id="deployment-id-123",
    )

    result = cli_runner.invoke(app, ["system", "deploy", "create", "test-course"])

    assert result.exit_code == 0
    assert "Deployment 'ccc-course-test-deployment' created/updated successfully" in result.output
    mock_resolve_settings.assert_called_once_with("test-course")
    mock_ensure_deployment.assert_called_once_with(mock_settings, "test-course")


@pytest.mark.local
@patch("canvas_code_correction.cli.load_settings_from_course_block")
def test_deploy_create_block_not_found(
    mock_resolve_settings: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Test deploy create when course block not found."""
    mock_resolve_settings.side_effect = ValueError("Block not found")

    result = cli_runner.invoke(app, ["system", "deploy", "create", "missing-course"])

    assert result.exit_code == 1
    assert "Error loading course block" in result.output
    mock_resolve_settings.assert_called_once_with("missing-course")


@pytest.mark.local
@patch("canvas_code_correction.cli.load_settings_from_course_block")
@patch("canvas_code_correction.cli.ensure_deployment", new_callable=AsyncMock)
def test_deploy_create_ensure_deployment_raises_exception(
    mock_ensure_deployment: AsyncMock,
    mock_resolve_settings: MagicMock,
    cli_runner: CliRunner,
    mock_settings: Settings,
) -> None:
    """Test deploy create when ensure_deployment raises exception."""
    mock_resolve_settings.return_value = mock_settings
    mock_ensure_deployment.side_effect = RuntimeError("Deployment failed")

    result = cli_runner.invoke(app, ["system", "deploy", "create", "test-course"])

    assert result.exit_code == 1
    assert "Error creating deployment" in result.output
    mock_ensure_deployment.assert_called_once_with(mock_settings, "test-course")


# ----- version command tests -----


@pytest.mark.local
@patch("canvas_code_correction.cli.importlib.metadata.version")
def test_version_success(
    mock_version: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Test version command with package found."""
    mock_version.return_value = "2.0.0"

    result = cli_runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "Canvas Code Correction 2.0.0" in result.output
    mock_version.assert_called_once_with("canvas-code-correction")


@pytest.mark.local
@patch("canvas_code_correction.cli.importlib.metadata.version")
def test_version_package_not_found(
    mock_version: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Test version command when package not found."""
    from importlib.metadata import PackageNotFoundError

    mock_version.side_effect = PackageNotFoundError

    result = cli_runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "Canvas Code Correction v2.0.0a0" in result.output
    mock_version.assert_called_once_with("canvas-code-correction")
