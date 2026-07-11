import subprocess
from pathlib import Path

import yaml


def _compose() -> dict[str, object]:
    compose_path = Path(__file__).parents[2] / "docker-compose.yml"
    return yaml.safe_load(compose_path.read_text(encoding="utf-8"))


def test_dev_webhook_profile_contains_complete_optional_stack() -> None:
    services = _compose()["services"]

    for service_name in ("dev-init", "prefect-worker", "webhook-listener", "cloudflared"):
        assert services[service_name]["profiles"] == ["dev-webhook"]


def test_dev_services_wait_for_successful_provisioning() -> None:
    services = _compose()["services"]

    for service_name in ("prefect-worker", "webhook-listener"):
        assert services[service_name]["depends_on"]["dev-init"]["condition"] == (
            "service_completed_successfully"
        )
    assert services["cloudflared"]["depends_on"]["webhook-listener"]["condition"] == (
        "service_healthy"
    )


def test_dev_init_fails_closed_and_keeps_token_off_command_line() -> None:
    init = _compose()["services"]["dev-init"]
    command = init["command"][0]

    assert "CCC_WEBHOOK_DRY_RUN" in command
    assert "CCC_ALLOW_LIVE_CANVAS_WRITES" in command
    assert "CCC_WEBHOOK_PUBLIC_URL must be an HTTPS origin" in command
    assert 'printf %s "$$CANVAS_API_TOKEN"' in command
    assert "--token-stdin" in command
    assert "--token " not in command
    assert "--webhook-auth canvas-signed-jwt" in command
    assert "work-pool create --type process --overwrite" in command
    assert "ccc system deploy create" in command


def test_dev_init_rejects_missing_configuration_before_provisioning() -> None:
    command = _compose()["services"]["dev-init"]["command"][0].replace("$$", "$")

    result = subprocess.run(  # noqa: S603
        ["/bin/sh", "-euc", command],
        check=False,
        capture_output=True,
        text=True,
        env={},
    )

    assert result.returncode != 0
    assert "CANVAS_API_URL" in result.stderr


def test_dev_init_rejects_unacknowledged_live_writes() -> None:
    command = _compose()["services"]["dev-init"]["command"][0].replace("$$", "$")
    env = {
        "CANVAS_API_URL": "https://canvas.example.edu",
        "CANVAS_API_TOKEN": "secret",
        "CANVAS_COURSE_ID": "123",
        "CANVAS_TEST_ASSIGNMENT_ID": "456",
        "CCC_COURSE_SLUG": "cs101",
        "CCC_WORKSPACE_ROOT": "/tmp/ccc/workspaces",
        "CCC_WEBHOOK_PUBLIC_URL": "https://ccc-dev.example.com",
        "CCC_WEBHOOK_DRY_RUN": "false",
        "CLOUDFLARE_TUNNEL_TOKEN": "secret",
    }

    result = subprocess.run(  # noqa: S603
        ["/bin/sh", "-euc", command],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode != 0
    assert "CCC_ALLOW_LIVE_CANVAS_WRITES=true" in result.stderr


def test_dev_stack_uses_internal_endpoints_and_safe_tunnel_token() -> None:
    services = _compose()["services"]

    for service_name in ("dev-init", "prefect-worker", "webhook-listener"):
        environment = services[service_name]["environment"]
        assert environment["PREFECT_API_URL"] == "http://prefect-server:4200/api"
        assert environment["RUSTFS_ENDPOINT"] == "http://rustfs:9000"

    tunnel = services["cloudflared"]
    assert "CLOUDFLARE_TUNNEL_TOKEN" in tunnel["environment"]["TUNNEL_TOKEN"]
    assert "CLOUDFLARE_TUNNEL_TOKEN" not in tunnel["command"]


def test_worker_retains_docker_socket_and_identical_workspace_mount() -> None:
    worker = _compose()["services"]["prefect-worker"]
    volumes = worker["volumes"]

    assert "/var/run/docker.sock:/var/run/docker.sock" in volumes
    assert any(
        volume.count("${CCC_WORKSPACE_ROOT:-/tmp/ccc/workspaces}") == 2 for volume in volumes
    )


def test_host_orchestration_script_is_removed() -> None:
    repo_root = Path(__file__).parents[2]

    assert not (repo_root / "scripts" / "dev_stack.py").exists()
