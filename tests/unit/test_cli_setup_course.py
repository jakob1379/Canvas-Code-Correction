"""Integration tests for the setup-course CLI command."""

from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import typer
import yaml
from typer.testing import CliRunner

from canvas_code_correction import cli_course
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


@pytest.fixture
def mock_provision_assets() -> Iterator[MagicMock]:
    """Patch secure course asset provisioning for CLI tests."""
    with patch("canvas_code_correction.cli_course._provision_course_assets") as mock:
        yield mock


class TestSetupCourseNonInteractive:
    """Tests for setup-course command in non-interactive mode."""

    pytestmark = pytest.mark.usefixtures("mock_provision_assets")

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
        mock_block_class.load.side_effect = ValueError("block not found")

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

        assert result.exit_code == 0
        assert "Course configuration saved as block: ccc-course-13122436-test-101" in result.output
        mock_canvas_class.assert_called_once_with(
            "https://canvas.instructure.com",
            "test-token",
        )
        mock_block_class.assert_called_once()
        mock_block.save.assert_called_once_with(
            "ccc-course-13122436-test-101",
            overwrite=False,
        )
        call_kwargs = mock_block_class.call_args.kwargs
        assert call_kwargs["asset_bucket_block"] == "ccc-assets-13122436-test-101"
        assert call_kwargs["asset_path_prefix"] == "graders/13122436-test-101/"
        assert call_kwargs["storage_auth_mode"] == "shared_environment"
        assert call_kwargs["work_pool_name"] == "course-work-pool-13122436-test-101"

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
        mock_block_class.load.side_effect = ValueError("block not found")

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token-stdin",
                "--course-id",
                "13122436",
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
            ],
            input="stdin-token\n",
        )

        assert result.exit_code == 1
        assert "Use either --token or --token-stdin, not both" in result.output

    @pytest.mark.local
    def test_setup_course_reads_stdin_before_switching_to_tty(
        self,
    ) -> None:
        """Interactive token-stdin mode must consume the pipe before TTY prompts begin."""
        events: list[str] = []

        def fake_resolve_canvas_token(*_args: object, **_kwargs: object) -> str:
            events.append("resolve-token")
            return "stdin-token"

        def fake_switch_stdin(_console: object) -> None:
            events.append("switch-tty")

        fake_course = SimpleNamespace(id=13122436, name="Test Course", course_code="TEST-101")
        fake_setup_config = SimpleNamespace(
            block_name="ccc-course-13122436-test-101",
            work_package_plans=(),
        )

        with (
            patch.object(
                cli_course,
                "_resolve_canvas_token",
                side_effect=fake_resolve_canvas_token,
            ),
            patch.object(cli_course, "_build_canvas_client", return_value=MagicMock()),
            patch.object(
                cli_course,
                "_resolve_course_selection",
                return_value=(13122436, fake_course),
            ),
            patch.object(cli_course, "_build_course_setup_config", return_value=fake_setup_config),
            patch.object(cli_course, "_print_course_setup_summary"),
            patch.object(cli_course, "_save_course_block"),
            patch.object(cli_course, "_ensure_course_block_absent"),
            patch.object(cli_course, "_sync_work_package_manifests"),
            patch.object(cli_course, "_provision_course_assets"),
            patch.object(
                cli_course,
                "_switch_stdin_to_tty_for_prompts",
                side_effect=fake_switch_stdin,
            ),
        ):
            cli_course.course_setup_command(
                cli_course.CourseSetupOptions(
                    token_stdin=True,
                    canvas_api_url=None,
                    canvas_token=None,
                    course_id=13122436,
                    docker_image="jakob1379/canvas-grader:latest",
                    work_packages=[],
                    env_var=[],
                    interactive=True,
                ),
                console=MagicMock(),
                Canvas=MagicMock(),
                CourseConfigBlock=MagicMock(),
                Prompt=MagicMock(),
                IntPrompt=MagicMock(),
                Confirm=MagicMock(),
            )

        assert events[:2] == ["resolve-token", "switch-tty"]

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
            ],
        )

        assert result.exit_code == 1
        assert "--course-id is required in non-interactive mode" in result.output

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    def test_setup_course_legacy_override_flags_are_rejected(
        self,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """Test setup-course rejects legacy manual naming overrides."""
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
            ],
        )

        assert result.exit_code == 2
        assert "No such option" in result.output
        mock_canvas_class.assert_not_called()

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
            ],
        )

        assert result.exit_code == 1
        assert "Failed to validate Canvas credentials" in result.output

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
            ],
        )

        assert result.exit_code == 1
        assert "Course ID 99999 not found" in result.output

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    @patch("canvas_code_correction.cli.CourseConfigBlock")
    def test_setup_course_with_work_packages(
        self,
        mock_block_class: MagicMock,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
        mock_canvas_course: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test setup-course with work-package mappings provided."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_course.return_value = mock_canvas_course
        mock_canvas_class.return_value = mock_canvas

        mock_block = MagicMock()
        mock_block_class.return_value = mock_block
        mock_block_class.load.side_effect = ValueError("block not found")
        work_package_1 = tmp_path / "work-package-1"
        (work_package_1 / "assets").mkdir(parents=True)
        (work_package_1 / "assets" / "main.sh").write_text("#!/bin/sh\n")
        work_package_2 = tmp_path / "work-package-2"
        (work_package_2 / "grader").mkdir(parents=True)
        (work_package_2 / "grader" / "main.sh").write_text("#!/bin/sh\n")

        with patch("canvas_code_correction.cli_course._provision_course_assets") as mock_provision:
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
                    "--work-package",
                    f"59160606:{work_package_1}",
                    "--work-package",
                    f"59160607:{work_package_2}",
                ],
            )

        assert result.exit_code == 0
        mock_provision.assert_called_once()
        # Verify work-package mappings were passed to block
        call_kwargs = mock_block_class.call_args.kwargs
        assert call_kwargs["grader_env"] == {}
        assert call_kwargs["assignment_asset_prefixes"] == {
            59160606: "assignments/59160606",
            59160607: "assignments/59160607",
        }
        manifest_1 = yaml.safe_load((work_package_1 / "work-package.yaml").read_text())
        manifest_2 = yaml.safe_load((work_package_2 / "work-package.yaml").read_text())
        assert manifest_1["assignment_ids"] == [59160606]
        assert manifest_2["assignment_ids"] == [59160607]

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
        mock_block_class.load.side_effect = ValueError("block not found")

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
        """Test setup-course with the remaining optional arguments."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_course.return_value = mock_canvas_course
        mock_canvas_class.return_value = mock_canvas

        mock_block = MagicMock()
        mock_block_class.return_value = mock_block
        mock_block_class.load.side_effect = ValueError("block not found")

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
                "--docker-image",
                "custom/grader:latest",
            ],
        )

        assert result.exit_code == 0
        mock_canvas_class.assert_called_once_with(
            "https://canvas.example.com",
            "test-token",
        )
        call_kwargs = mock_block_class.call_args.kwargs
        assert str(call_kwargs["canvas_api_url"]) == "https://canvas.example.com/"
        assert call_kwargs["asset_bucket_block"] == "ccc-assets-13122436-test-101"
        assert call_kwargs["asset_path_prefix"] == "graders/13122436-test-101/"
        assert call_kwargs["grader_image"] == "custom/grader:latest"
        assert call_kwargs["work_pool_name"] == "course-work-pool-13122436-test-101"


class TestSetupCourseInteractive:
    """Tests for setup-course command in interactive mode."""

    pytestmark = pytest.mark.usefixtures("mock_provision_assets")

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
        mock_block_class.load.side_effect = ValueError("block not found")

        # Setup prompts
        mock_prompt.side_effect = [
            "test-token",  # API token
            "",  # Canvas host (accept default)
            "",  # Docker image (empty)
        ]
        mock_int_prompt.return_value = 1  # Select first course from list
        mock_confirm.side_effect = [
            False,  # Don't map work packages
            True,  # Save configuration
        ]

        result = cli_runner.invoke(app, ["course", "setup"])

        assert result.exit_code == 0
        assert "Course configuration saved as block: ccc-course-13122436-test-101" in result.output
        mock_block.save.assert_called_once()
        assert mock_prompt.call_args_list[1].args[0] == "Canvas host (domain or https:// URL)"
        assert mock_int_prompt.call_args_list[0].args[0] == "Select a course [1-1]"

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

        mock_prompt.side_effect = [
            "invalid-token",
            "",
        ]

        result = cli_runner.invoke(app, ["course", "setup"])

        assert result.exit_code == 1
        assert "Failed to validate Canvas credentials" in result.output

    @pytest.mark.local
    def test_request_work_package_mappings_prompt_mentions_empty_enter(
        self,
        mock_canvas_course: MagicMock,
        mock_canvas_assignments: list,
    ) -> None:
        """Test work-package prompt tells the user how to finish input."""
        mock_canvas_course.get_assignments.return_value = mock_canvas_assignments
        mock_canvas_course.get_assignment.return_value = MagicMock()

        confirm = MagicMock()
        confirm.ask.return_value = True

        prompt = MagicMock()
        prompt.ask.side_effect = [
            "/path/to/work-package",  # invalid format first
            "59160606:/path/to/work-package",
            "",
        ]

        cli_course._request_work_package_mappings(
            mock_canvas_course,
            console=MagicMock(),
            Confirm=confirm,
            Prompt=prompt,
        )

        assert prompt.ask.call_args_list[0].args[0] == (
            "Work-package mapping (press Enter on empty input to finish)"
        )

    @pytest.mark.local
    def test_sync_work_package_manifests_leaves_matching_manifest_untouched(
        self,
        tmp_path: Path,
    ) -> None:
        """A manifest that already lists the assignment is not rewritten."""
        root = tmp_path / "my-work-package"
        (root / "assets").mkdir(parents=True)
        manifest_path = root / "work-package.yaml"
        original = yaml.safe_dump(
            {"schema_version": 1, "assignment_ids": [59160606]},
            sort_keys=False,
        )
        manifest_path.write_text(original)

        plans = cli_course._build_work_package_plans(
            {59160606: root},
            console=MagicMock(),
        )
        cli_course._sync_work_package_manifests(plans, console=MagicMock())

        assert manifest_path.read_text() == original

    @pytest.mark.local
    def test_sync_work_package_manifests_merges_new_assignments(self, tmp_path: Path) -> None:
        """A second assignment mapped to the same package is added to its manifest."""
        root = tmp_path / "my-work-package"
        (root / "assets").mkdir(parents=True)
        manifest_path = root / "work-package.yaml"
        manifest_path.write_text(
            yaml.safe_dump({"schema_version": 1, "assignment_ids": [59160606]}, sort_keys=False),
        )

        plans = cli_course._build_work_package_plans(
            {59160606: root, 59160607: root},
            console=MagicMock(),
        )
        cli_course._sync_work_package_manifests(plans, console=MagicMock())

        assert yaml.safe_load(manifest_path.read_text())["assignment_ids"] == [
            59160606,
            59160607,
        ]

    @pytest.mark.local
    def test_sync_work_package_manifests_preserves_unknown_metadata(
        self,
        tmp_path: Path,
    ) -> None:
        """Keys CCC does not understand survive the rewrite."""
        root = tmp_path / "my-work-package"
        (root / "grader").mkdir(parents=True)
        manifest_path = root / "work-package.yaml"
        manifest_path.write_text(
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "name": "my-work-package",
                    "version": "1.0.0",
                    "assignment_ids": [59160606],
                    "assets": {"source_directory": "grader", "entrypoint": "main.sh"},
                },
                sort_keys=False,
            ),
        )

        plans = cli_course._build_work_package_plans(
            {59160606: root, 59160607: root},
            console=MagicMock(),
        )
        cli_course._sync_work_package_manifests(plans, console=MagicMock())
        manifest = yaml.safe_load(manifest_path.read_text())

        assert manifest["name"] == "my-work-package"
        assert manifest["version"] == "1.0.0"
        assert manifest["assets"]["source_directory"] == "grader"
        assert manifest["assignment_ids"] == [59160606, 59160607]

    @pytest.mark.local
    def test_sync_work_package_manifests_creates_missing_manifest(self, tmp_path: Path) -> None:
        root = tmp_path / "my-work-package"
        (root / "assets").mkdir(parents=True)

        plans = cli_course._build_work_package_plans({59160606: root}, console=MagicMock())
        cli_course._sync_work_package_manifests(plans, console=MagicMock())

        manifest = yaml.safe_load((root / "work-package.yaml").read_text())
        assert manifest == {"schema_version": 1, "assignment_ids": [59160606]}

    @pytest.mark.local
    def test_build_work_package_plans_supports_assets_and_grader(self, tmp_path: Path) -> None:
        """Either directory name works, and each package gets its own bucket prefix."""
        assets_root = tmp_path / "assets-package"
        (assets_root / "assets").mkdir(parents=True)
        grader_root = tmp_path / "grader-package"
        (grader_root / "grader").mkdir(parents=True)

        plans = cli_course._build_work_package_plans(
            {59160606: assets_root, 59160607: grader_root},
            console=MagicMock(),
        )

        assert [plan.prefix for plan in plans] == [
            "assignments/59160606",
            "assignments/59160607",
        ]
        assert [plan.asset_source_dir for plan in plans] == [
            assets_root / "assets",
            grader_root / "grader",
        ]

    @pytest.mark.local
    def test_build_work_package_plans_rejects_package_without_asset_dir(
        self,
        tmp_path: Path,
    ) -> None:
        """A root with no grader/ or assets/ is refused rather than uploaded wholesale."""
        root = tmp_path / "loose-package"
        root.mkdir()
        (root / "main.sh").write_text("#!/bin/sh\n")

        with pytest.raises(typer.Exit) as exc_info:
            cli_course._build_work_package_plans({59160606: root}, console=MagicMock())

        assert exc_info.value.exit_code == 1

    @pytest.mark.local
    def test_upload_work_package_prunes_only_after_a_successful_upload(
        self,
        tmp_path: Path,
    ) -> None:
        """Stale objects are removed after the upload, never before it."""
        root = tmp_path / "package"
        (root / "assets").mkdir(parents=True)
        (root / "assets" / "main.sh").write_text("#!/bin/sh\n")
        (root / "assets" / "lib" / "helper.py").parent.mkdir()
        (root / "assets" / "lib" / "helper.py").write_text("x = 1\n")

        plan = cli_course._build_work_package_plans({59160606: root}, console=MagicMock())[0]
        storage = cli_course.RustfsStorageConfig(
            endpoint_url="http://localhost:9000",
            aws_access_key_id="KEY",
            aws_secret_access_key="SECRET",  # noqa: S106
            region_name="us-east-1",
        )
        calls: list[str] = []

        def fake_upload(*_args: object, **_kwargs: object) -> int:
            calls.append("upload")
            return 2

        def fake_delete(*_args: object, keep: set[str], **_kwargs: object) -> int:
            calls.append("prune")
            assert keep == {
                "assignments/59160606/main.sh",
                "assignments/59160606/lib/helper.py",
            }
            return 0

        with (
            patch.object(cli_course, "upload_directory_with_credentials", fake_upload),
            patch.object(cli_course, "delete_stale_objects", fake_delete),
        ):
            cli_course._upload_work_package(storage, "bucket", plan, console=MagicMock())

        assert calls == ["upload", "prune"]


class TestSetupCourseEdgeCases:
    """Edge case tests for setup-course command."""

    pytestmark = pytest.mark.usefixtures("mock_provision_assets")

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
        mock_block_class.load.side_effect = ValueError("block not found")

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
        assert "Error saving course block" in result.output

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    @patch("canvas_code_correction.cli.CourseConfigBlock")
    def test_setup_course_duplicate_generated_block_name_fails(
        self,
        mock_block_class: MagicMock,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
        mock_canvas_course: MagicMock,
    ) -> None:
        """Test setup-course fails when the generated block name already exists."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_course.return_value = mock_canvas_course
        mock_canvas_class.return_value = mock_canvas

        mock_block = MagicMock()
        mock_block.save.side_effect = ValueError("already exists")
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
            ],
        )

        assert result.exit_code == 1
        assert (
            "Course configuration block already exists: ccc-course-13122436-test-101"
            in result.output
        )

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    @patch("canvas_code_correction.cli.CourseConfigBlock")
    def test_setup_course_invalid_work_package_mapping_format(
        self,
        mock_block_class: MagicMock,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
        mock_canvas_course: MagicMock,
    ) -> None:
        """Test setup-course with invalid work-package mapping format."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_course.return_value = mock_canvas_course
        mock_canvas_class.return_value = mock_canvas

        mock_block = MagicMock()
        mock_block_class.return_value = mock_block
        mock_block_class.load.side_effect = ValueError("block not found")

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
                "--work-package",
                "invalid-mapping-format",
            ],
        )

        assert result.exit_code == 0
        # Should skip invalid mapping but still succeed
        assert "Skipping invalid work-package mapping" in result.output

    @pytest.mark.local
    @patch("canvas_code_correction.cli.Canvas")
    @patch("canvas_code_correction.cli.CourseConfigBlock")
    def test_setup_course_rejects_empty_work_package_mapping_path(
        self,
        mock_block_class: MagicMock,
        mock_canvas_class: MagicMock,
        cli_runner: CliRunner,
        mock_canvas_course: MagicMock,
    ) -> None:
        """Test setup-course skips work-package mappings with an empty path."""
        mock_canvas = MagicMock()
        mock_canvas.get_current_user.return_value = MagicMock()
        mock_canvas.get_course.return_value = mock_canvas_course
        mock_canvas_class.return_value = mock_canvas

        mock_block = MagicMock()
        mock_block_class.return_value = mock_block
        mock_block_class.load.side_effect = ValueError("block not found")

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
                "--work-package",
                "59160606:",
            ],
        )

        assert result.exit_code == 0
        assert "Skipping invalid work-package mapping: 59160606:" in result.output
        assert mock_block_class.call_args.kwargs["assignment_asset_prefixes"] == {}

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
        mock_block_class.load.side_effect = ValueError("block not found")

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
                "--env",
                "INVALID_ENV_VAR",
            ],
        )

        assert result.exit_code == 0
        assert "Skipping invalid env var" in result.output
