import importlib.util
import json
from pathlib import Path

import pytest


def _load_module():
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "generate_coverage_badge.py"
    spec = importlib.util.spec_from_file_location(
        "generate_coverage_badge_script",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.local
@pytest.mark.parametrize(
    ("coverage_percent", "expected_color"),
    [
        (95.0, "brightgreen"),
        (85.0, "green"),
        (75.0, "yellowgreen"),
        (65.0, "yellow"),
        (55.0, "orange"),
        (45.0, "red"),
    ],
)
def test_determine_color_uses_expected_thresholds(
    coverage_percent: float,
    expected_color: str,
) -> None:
    module = _load_module()

    assert module.determine_color(coverage_percent) == expected_color


@pytest.mark.local
def test_main_writes_badge_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    coverage_json = tmp_path / "coverage.json"
    output_json = tmp_path / "badges" / "coverage.json"
    coverage_json.write_text(
        json.dumps({"totals": {"percent_covered": 87.654}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module.sys,
        "argv",
        [
            "generate_coverage_badge.py",
            "--coverage-json",
            str(coverage_json),
            "--output",
            str(output_json),
        ],
    )

    result = module.main()

    assert result == 0
    assert json.loads(output_json.read_text(encoding="utf-8")) == {
        "schemaVersion": 1,
        "label": "coverage",
        "message": "87.65%",
        "color": "green",
        "namedLogo": "python",
    }


@pytest.mark.local
def test_main_exits_when_coverage_file_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_module()
    missing_path = tmp_path / "missing.json"
    monkeypatch.setattr(
        module.sys,
        "argv",
        ["generate_coverage_badge.py", "--coverage-json", str(missing_path)],
    )

    with pytest.raises(SystemExit) as exc_info:
        module.main()

    assert exc_info.value.code == 1
    assert "Coverage file not found" in capsys.readouterr().err
