"""Integration tests for CLI command structure.

These tests verify the CLI command structure works correctly without requiring
the full dev stack (RustFS, Prefect server, Canvas API).
"""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from canvas_code_correction.cli import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Return a Typer CLI runner for testing."""
    return CliRunner()


class TestCLICommandStructure:
    """Test that CLI commands are properly structured and accessible."""

    def test_main_help_shows_command_groups(self, cli_runner: CliRunner) -> None:
        """Test that main help shows course and system command groups."""
        result = cli_runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "course" in result.output
        assert "system" in result.output
        assert "📚 Course Administration" in result.output
        assert "🔧 Platform Administration" in result.output

    def test_course_help_shows_subcommands(self, cli_runner: CliRunner) -> None:
        """Test that course group shows setup, run, and list."""
        result = cli_runner.invoke(app, ["course", "--help"])

        assert result.exit_code == 0
        assert "setup" in result.output
        assert "run" in result.output
        assert "list" in result.output
        assert "configure" not in result.output

    def test_system_help_shows_subcommands(self, cli_runner: CliRunner) -> None:
        """Test that system group shows all subcommands."""
        result = cli_runner.invoke(app, ["system", "--help"])

        assert result.exit_code == 0
        assert "webhook" in result.output
        assert "deploy" in result.output
        assert "status" in result.output

    def test_webhook_help_shows_serve(self, cli_runner: CliRunner) -> None:
        """Test that webhook subcommand shows serve."""
        result = cli_runner.invoke(app, ["system", "webhook", "--help"])

        assert result.exit_code == 0
        assert "serve" in result.output

    def test_deploy_help_shows_create(self, cli_runner: CliRunner) -> None:
        """Test that deploy subcommand shows create."""
        result = cli_runner.invoke(app, ["system", "deploy", "--help"])

        assert result.exit_code == 0
        assert "create" in result.output

    def test_version_flag_works(self, cli_runner: CliRunner) -> None:
        """Test that --version flag works."""
        result = cli_runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "Canvas Code Correction" in result.output


class TestCLINoDevStackRequired:
    """Test CLI commands that don't require dev stack."""

    @pytest.mark.local
    def test_course_list_no_courses(self, cli_runner: CliRunner) -> None:
        """Test course list when no courses configured.

        This test doesn't require Prefect server or any external services.
        """
        with patch("canvas_code_correction.cli.find_course_block_names") as mock_find_course_blocks:
            mock_find_course_blocks.return_value = []

            result = cli_runner.invoke(app, ["course", "list"])

            assert result.exit_code == 0
            assert "No course configuration blocks found" in result.output

    @pytest.mark.local
    def test_system_status_shows_checks(self, cli_runner: CliRunner) -> None:
        """Test system status command shows platform checks.

        This test verifies the command runs and shows status checks,
        even if services are not available.
        """
        result = cli_runner.invoke(app, ["system", "status"])

        assert result.exit_code == 0
        assert "Platform Status" in result.output
        assert "Prefect server" in result.output
        assert "RustFS (S3)" in result.output
        assert "ccc system --help" in result.output

    @pytest.mark.local
    def test_system_list_command_removed(self, cli_runner: CliRunner) -> None:
        """Test system list is not an available command."""
        result = cli_runner.invoke(app, ["system", "list"])

        assert result.exit_code != 0
        assert "No such command 'list'" in result.output


class TestCLILegacyCommandMapping:
    """Verify old command mappings work correctly."""

    @pytest.mark.local
    @patch("canvas_code_correction.cli.load_settings_from_course_block")
    @patch("canvas_code_correction.cli.correct_submission_flow")
    def test_old_run_once_now_course_run(
        self,
        mock_flow: MagicMock,
        mock_resolve: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """Test that old 'run-once' is now 'course run'."""
        from pydantic import HttpUrl, SecretStr

        from canvas_code_correction.config import (
            CanvasSettings,
            CourseAssetsSettings,
            GraderSettings,
            Settings,
            WorkspaceSettings,
        )

        # Create mock settings directly without loading from block
        mock_settings = Settings(
            canvas=CanvasSettings(
                api_url=HttpUrl("https://canvas.example.com"),
                token=SecretStr("secret"),
                course_id=123,
            ),
            assets=CourseAssetsSettings(
                bucket_block="test-bucket",
                path_prefix="",
            ),
            grader=GraderSettings(
                docker_image=None,
                work_pool_name=None,
                env={},
            ),
            workspace=WorkspaceSettings(),
        )

        mock_resolve.return_value = mock_settings
        mock_flow.return_value = MagicMock(
            submission_metadata={},
            downloaded_files=[],
            workspace=None,
            results={},
            uploads={},
        )

        # Use new command structure
        result = cli_runner.invoke(
            app,
            ["course", "run", "12345", "--submission-id", "67890", "--course", "test-course"],
        )

        # Should work with new structure
        assert result.exit_code == 0
        mock_resolve.assert_called_once_with("test-course")

    @pytest.mark.local
    def test_configure_command_removed(self, cli_runner: CliRunner) -> None:
        """Test configure command has been removed in favor of setup."""
        result = cli_runner.invoke(app, ["course", "configure", "--help"])

        assert result.exit_code != 0
