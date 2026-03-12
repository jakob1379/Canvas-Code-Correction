"""Integration tests for the setup-course CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from canvas_code_correction.cli import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Return a Typer CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_canvas_course():
    """Return a mock Canvas course."""
    course = MagicMock()
    course.id = 13122436
    course.name = "Test Course"
    course.course_code = "TEST-101"
    return course


@pytest.fixture
def mock_canvas_assignments():
    """Return mock Canvas assignments."""
    assignment1 = MagicMock()
    assignment1.id = 59160606
    assignment1.name = "Assignment 1"
    assignment1.published = True

    assignment2 = MagicMock()
    assignment2.id = 59160607
    assignment2.name = "Assignment 2"
    assignment2.published = False

    return [assignment1, assignment2]


class TestSetupCourseNonInteractive:
    """Tests for setup-course command in non-interactive mode."""

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    @patch("canvas_code_correction.cli.CourseConfigBlock")
    def test_setup_course_non_interactive_success(
        self,
        mock_block_class: MagicMock,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
        mock_canvas_course: MagicMock,
    ) -> None:
        """Test setup-course with all required arguments provided."""
        # Setup Canvas mock
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_course.return_value = mock_canvas_course
        mock_canvas_class.return_value = mock_canvas

        # Setup block mock
        mock_block = MagicMock()
        mock_block_class.return_value = mock_block

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                "test-token",
                "--course-id",
                "13122436",
                "--assets-block",
                "test-bucket",
                "--slug",
                "test-course",
            ],
        )

        assert result.exit_code == 0
        assert "Course configuration saved as block: ccc-course-test-course" in result.output
        mock_canvas_class.assert_called_once_with(
            "https://canvas.instructure.com",
            "test-token",
        )
        mock_block_class.assert_called_once()
        mock_block.save.assert_called_once_with("ccc-course-test-course", overwrite=True)

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    def test_setup_course_missing_token_non_interactive(
        self,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """Test setup-course fails when token is missing in non-interactive mode."""
        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--course-id",
                "13122436",
                "--assets-block",
                "test-bucket",
            ],
        )

        assert result.exit_code == 1
        assert "--token or --token-stdin is required in non-interactive mode" in result.output
        mock_canvas_class.assert_not_called()

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    @patch("canvas_code_correction.cli.CourseConfigBlock")
    def test_setup_course_token_from_stdin_non_interactive(
        self,
        mock_block_class: MagicMock,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
        mock_canvas_course: MagicMock,
    ) -> None:
        """Test setup-course reads token from stdin in non-interactive mode."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_course.return_value = mock_canvas_course
        mock_canvas_class.return_value = mock_canvas

        mock_block = MagicMock()
        mock_block_class.return_value = mock_block

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token-stdin",
                "--course-id",
                "13122436",
                "--assets-block",
                "test-bucket",
                "--slug",
                "test-course",
            ],
            input="stdin-token\n",
        )

        assert result.exit_code == 0
        mock_canvas_class.assert_called_once_with("https://canvas.instructure.com", "stdin-token")

    @pytest.mark.local
    def test_setup_course_token_and_token_stdin_mutually_exclusive(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Test setup-course rejects using --token and --token-stdin together."""
        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                "explicit-token",
                "--token-stdin",
                "--course-id",
                "13122436",
                "--assets-block",
                "test-bucket",
            ],
            input="stdin-token\n",
        )

        assert result.exit_code == 1
        assert "Use either --token or --token-stdin, not both" in result.output

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    def test_setup_course_missing_course_id_non_interactive(
        self,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """Test setup-course fails when course-id is missing in non-interactive mode."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas_class.return_value = mock_canvas

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                "test-token",
                "--assets-block",
                "test-bucket",
            ],
        )

        assert result.exit_code == 1
        assert "--course-id is required in non-interactive mode" in result.output

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    def test_setup_course_missing_assets_block_non_interactive(
        self,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """Test setup-course fails when assets-block is missing in non-interactive mode."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_course.return_value = MagicMock()
        mock_canvas_class.return_value = mock_canvas

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                "test-token",
                "--course-id",
                "13122436",
            ],
        )

        assert result.exit_code == 1
        assert "--assets-block is required in non-interactive mode" in result.output

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    def test_setup_course_invalid_token(
        self,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """Test setup-course fails with invalid token."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.side_effect = Exception("Invalid token")
        mock_canvas_class.return_value = mock_canvas

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                "invalid-token",
                "--course-id",
                "13122436",
                "--assets-block",
                "test-bucket",
            ],
        )

        assert result.exit_code == 1
        assert "Failed to validate Canvas API token" in result.output

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    def test_setup_course_invalid_course_id(
        self,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """Test setup-course fails with invalid course ID."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_course.side_effect = Exception("Course not found")
        mock_canvas_class.return_value = mock_canvas

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                "test-token",
                "--course-id",
                "99999",
                "--assets-block",
                "test-bucket",
            ],
        )

        assert result.exit_code == 1
        assert "Course ID 99999 not found" in result.output

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    @patch("canvas_code_correction.cli.CourseConfigBlock")
    def test_setup_course_with_test_mappings(
        self,
        mock_block_class: MagicMock,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
        mock_canvas_course: MagicMock,
    ) -> None:
        """Test setup-course with test mappings provided."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_course.return_value = mock_canvas_course
        mock_canvas_class.return_value = mock_canvas

        mock_block = MagicMock()
        mock_block_class.return_value = mock_block

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                "test-token",
                "--course-id",
                "13122436",
                "--assets-block",
                "test-bucket",
                "--slug",
                "test-course",
                "--test-map",
                "59160606:/tests/test_assignment1.py",
                "--test-map",
                "59160607:/tests/test_assignment2.py",
            ],
        )

        assert result.exit_code == 0
        # Verify test mappings were passed to block
        call_kwargs = mock_block_class.call_args.kwargs
        assert call_kwargs["grader_env"]["CCC_TEST_MAP_59160606"] == "/tests/test_assignment1.py"
        assert call_kwargs["grader_env"]["CCC_TEST_MAP_59160607"] == "/tests/test_assignment2.py"

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    @patch("canvas_code_correction.cli.CourseConfigBlock")
    def test_setup_course_with_env_vars(
        self,
        mock_block_class: MagicMock,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
        mock_canvas_course: MagicMock,
    ) -> None:
        """Test setup-course with environment variables."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_course.return_value = mock_canvas_course
        mock_canvas_class.return_value = mock_canvas

        mock_block = MagicMock()
        mock_block_class.return_value = mock_block

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                "test-token",
                "--course-id",
                "13122436",
                "--assets-block",
                "test-bucket",
                "--slug",
                "test-course",
                "--env",
                "KEY1=value1",
                "--env",
                "KEY2=value2",
            ],
        )

        assert result.exit_code == 0
        call_kwargs = mock_block_class.call_args.kwargs
        assert call_kwargs["grader_env"]["KEY1"] == "value1"
        assert call_kwargs["grader_env"]["KEY2"] == "value2"

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    @patch("canvas_code_correction.cli.CourseConfigBlock")
    def test_setup_course_with_all_options(
        self,
        mock_block_class: MagicMock,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
        mock_canvas_course: MagicMock,
    ) -> None:
        """Test setup-course with all optional arguments."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_course.return_value = mock_canvas_course
        mock_canvas_class.return_value = mock_canvas

        mock_block = MagicMock()
        mock_block_class.return_value = mock_block

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                "test-token",
                "--api-url",
                "https://canvas.example.com",
                "--course-id",
                "13122436",
                "--assets-block",
                "test-bucket",
                "--assets-prefix",
                "graders/test/",
                "--slug",
                "test-course",
                "--docker-image",
                "custom/grader:latest",
                "--work-pool",
                "test-pool",
            ],
        )

        assert result.exit_code == 0
        mock_canvas_class.assert_called_once_with(
            "https://canvas.example.com",
            "test-token",
        )
        call_kwargs = mock_block_class.call_args.kwargs
        assert str(call_kwargs["canvas_api_url"]) == "https://canvas.example.com/"
        assert call_kwargs["asset_path_prefix"] == "graders/test/"
        assert call_kwargs["grader_image"] == "custom/grader:latest"
        assert call_kwargs["work_pool_name"] == "test-pool"


class TestSetupCourseInteractive:
    """Tests for setup-course command in interactive mode."""

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    @patch("canvas_code_correction.cli.CourseConfigBlock")
    @patch("canvas_code_correction.cli.Prompt.ask")
    @patch("canvas_code_correction.cli.IntPrompt.ask")
    @patch("canvas_code_correction.cli.Confirm.ask")
    def test_setup_course_interactive_success(
        self,
        mock_confirm: MagicMock,
        mock_int_prompt: MagicMock,
        mock_prompt: MagicMock,
        mock_block_class: MagicMock,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
        mock_canvas_course: MagicMock,
        mock_canvas_assignments: list,
    ) -> None:
        """Test interactive setup-course with user inputs."""
        # Setup Canvas mock
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_courses.return_value = [mock_canvas_course]
        mock_canvas.get_course.return_value = mock_canvas_course
        mock_canvas_class.return_value = mock_canvas

        mock_canvas_course.get_assignments.return_value = mock_canvas_assignments

        # Setup block mock
        mock_block = MagicMock()
        mock_block_class.return_value = mock_block

        # Setup prompts
        mock_prompt.side_effect = [
            "test-token",  # API token
            "test-course",  # Course slug
            "test-bucket",  # Assets block
            "graders/test-course/",  # Assets prefix
            "",  # Docker image (empty)
            "",  # Work pool (empty)
        ]
        mock_int_prompt.return_value = 13122436  # Course ID
        mock_confirm.side_effect = [
            False,  # Don't map tests
            True,  # Save configuration
        ]

        result = cli_runner.invoke(app, ["course", "setup"])

        assert result.exit_code == 0
        assert "Course configuration saved as block: ccc-course-test-course" in result.output
        mock_block.save.assert_called_once()

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    @patch("canvas_code_correction.cli.Prompt.ask")
    def test_setup_course_interactive_invalid_token(
        self,
        mock_prompt: MagicMock,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """Test interactive setup-course with invalid token."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.side_effect = Exception("Invalid token")
        mock_canvas_class.return_value = mock_canvas

        mock_prompt.return_value = "invalid-token"

        result = cli_runner.invoke(app, ["course", "setup"])

        assert result.exit_code == 1
        assert "Failed to validate Canvas API token" in result.output


@pytest.mark.integration
@pytest.mark.skipif(
    not Path(".env.dev").exists(),
    reason="No .env.dev file found for live testing",
)
class TestSetupCourseLive:
    """Live integration tests against real Canvas API.

    These tests require a valid .env.dev file with Canvas credentials.
    They will make actual API calls to Canvas.
    """

    def test_setup_course_live_non_interactive(self) -> None:
        """Test setup-course against live Canvas API in non-interactive mode.

        This test uses credentials from .env.dev file.
        """
        import os

        # Load credentials from .env.dev
        token = os.getenv("CANVAS_API_TOKEN")
        course_id = os.getenv("CANVAS_COURSE_ID")
        if not token or not course_id:
            pytest.skip("Canvas credentials not available in environment")

        # This test would run against live Canvas API
        # For safety, we just verify the command structure works
        # Actual live testing should be done manually
        pytest.skip("Live Canvas API testing requires manual verification")


class TestSetupCourseEdgeCases:
    """Edge case tests for setup-course command."""

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    @patch("canvas_code_correction.cli.CourseConfigBlock")
    def test_setup_course_block_save_failure(
        self,
        mock_block_class: MagicMock,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
        mock_canvas_course: MagicMock,
    ) -> None:
        """Test setup-course when block save fails."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_course.return_value = mock_canvas_course
        mock_canvas_class.return_value = mock_canvas

        mock_block = MagicMock()
        mock_block.save.side_effect = RuntimeError("Save failed")
        mock_block_class.return_value = mock_block

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                "test-token",
                "--course-id",
                "13122436",
                "--assets-block",
                "test-bucket",
                "--slug",
                "test-course",
            ],
        )

        assert result.exit_code == 1
        assert "Error saving course block" in result.output

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    @patch("canvas_code_correction.cli.CourseConfigBlock")
    def test_setup_course_invalid_test_mapping_format(
        self,
        mock_block_class: MagicMock,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
        mock_canvas_course: MagicMock,
    ) -> None:
        """Test setup-course with invalid test mapping format."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_course.return_value = mock_canvas_course
        mock_canvas_class.return_value = mock_canvas

        mock_block = MagicMock()
        mock_block_class.return_value = mock_block

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                "test-token",
                "--course-id",
                "13122436",
                "--assets-block",
                "test-bucket",
                "--slug",
                "test-course",
                "--test-map",
                "invalid-mapping-format",
            ],
        )

        assert result.exit_code == 0
        # Should skip invalid mapping but still succeed
        assert "Skipping invalid test mapping" in result.output

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    @patch("canvas_code_correction.cli.CourseConfigBlock")
    def test_setup_course_invalid_env_var_format(
        self,
        mock_block_class: MagicMock,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
        mock_canvas_course: MagicMock,
    ) -> None:
        """Test setup-course with invalid env var format."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_course.return_value = mock_canvas_course
        mock_canvas_class.return_value = mock_canvas

        mock_block = MagicMock()
        mock_block_class.return_value = mock_block

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                "test-token",
                "--course-id",
                "13122436",
                "--assets-block",
                "test-bucket",
                "--slug",
                "test-course",
                "--env",
                "INVALID_ENV_VAR",
            ],
        )

        assert result.exit_code == 0
        assert "Skipping invalid env var" in result.output
