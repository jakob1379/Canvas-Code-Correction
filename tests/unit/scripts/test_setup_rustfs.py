from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError


def _load_module():
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "setup_rustfs.py"
    spec = importlib.util.spec_from_file_location("setup_rustfs_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.local
def test_get_rustfs_config_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    monkeypatch.setenv("RUSTFS_ENDPOINT", "https://s3.amazonaws.com")
    monkeypatch.setenv("RUSTFS_ACCESS_KEY", "key")
    monkeypatch.setenv("RUSTFS_SECRET_KEY", "secret")
    monkeypatch.setenv("RUSTFS_BUCKET_NAME", "bucket")
    monkeypatch.setenv("RUSTFS_PREFIX", "course")

    assert module.get_rustfs_config() == {
        "endpoint_url": "https://s3.amazonaws.com",
        "aws_access_key_id": "key",
        "aws_secret_access_key": "secret",
        "bucket_name": "bucket",
        "prefix": "course",
    }


@pytest.mark.local
def test_ensure_bucket_exists_creates_missing_bucket() -> None:
    module = _load_module()
    s3_client = Mock()
    s3_client.head_bucket.side_effect = ClientError(
        {"Error": {"Code": "404"}},
        "HeadBucket",
    )

    with (
        patch.object(
            module,
            "get_rustfs_config",
            return_value={
                "endpoint_url": "http://localhost:9000",
                "aws_access_key_id": "key",
                "aws_secret_access_key": "secret",
                "bucket_name": "bucket",
                "prefix": "dev",
            },
        ),
        patch.object(module.boto3, "client", return_value=s3_client),
    ):
        result = module.ensure_bucket_exists("bucket")

    assert result is True
    s3_client.create_bucket.assert_called_once_with(Bucket="bucket")


@pytest.mark.local
def test_register_prefect_block_creates_block_when_missing() -> None:
    module = _load_module()

    fake_blocks_core = types.ModuleType("prefect.blocks.core")
    fake_blocks_core.Block = object

    class FakeAwsClientParameters:
        def __init__(self, endpoint_url: str) -> None:
            self.endpoint_url = endpoint_url

    class FakeAwsCredentials:
        def __init__(
            self,
            *,
            aws_access_key_id: str,
            aws_secret_access_key,
            region_name: str,
            aws_client_parameters: FakeAwsClientParameters,
        ) -> None:
            self.aws_access_key_id = aws_access_key_id
            self.aws_secret_access_key = aws_secret_access_key
            self.region_name = region_name
            self.aws_client_parameters = aws_client_parameters

    class FakeS3Bucket:
        created: list[FakeS3Bucket] = []
        saved: list[tuple[str, bool]] = []
        load_calls: list[str] = []

        def __init__(self, *, bucket_name: str, credentials: FakeAwsCredentials) -> None:
            self.bucket_name = bucket_name
            self.credentials = credentials
            self.__class__.created.append(self)

        @classmethod
        def load(cls, name: str):
            cls.load_calls.append(name)
            raise ValueError("missing")

        def save(self, name: str, overwrite: bool = False) -> None:
            self.__class__.saved.append((name, overwrite))

    fake_prefect_aws = types.ModuleType("prefect_aws")
    fake_prefect_aws.AwsClientParameters = FakeAwsClientParameters
    fake_prefect_aws.AwsCredentials = FakeAwsCredentials
    fake_prefect_aws.S3Bucket = FakeS3Bucket

    with (
        patch.object(
            module,
            "get_rustfs_config",
            return_value={
                "endpoint_url": "http://localhost:9000",
                "aws_access_key_id": "key",
                "aws_secret_access_key": "secret",
                "bucket_name": "bucket",
                "prefix": "dev",
            },
        ),
        patch.dict(
            sys.modules,
            {
                "prefect.blocks.core": fake_blocks_core,
                "prefect_aws": fake_prefect_aws,
            },
        ),
    ):
        result = module.register_prefect_block()

    assert result is True
    assert FakeS3Bucket.load_calls == ["local-rustfs"]
    assert FakeS3Bucket.saved == [("local-rustfs", True)]
    assert FakeS3Bucket.created[0].bucket_name == "bucket"
    assert (
        FakeS3Bucket.created[0].credentials.aws_client_parameters.endpoint_url
        == "http://localhost:9000"
    )


@pytest.mark.local
def test_main_runs_setup_sequence(capsys: pytest.CaptureFixture[str]) -> None:
    module = _load_module()

    with (
        patch.object(module, "check_rustfs_available", return_value=True) as mock_rustfs,
        patch.object(module, "check_prefect_server", return_value=True) as mock_prefect,
        patch.object(
            module,
            "get_rustfs_config",
            return_value={
                "endpoint_url": "http://localhost:9000",
                "aws_access_key_id": "key",
                "aws_secret_access_key": "secret",
                "bucket_name": "bucket",
                "prefix": "dev",
            },
        ),
        patch.object(module, "ensure_bucket_exists", return_value=True) as mock_bucket,
        patch.object(module, "upload_test_asset") as mock_upload,
        patch.object(module, "register_prefect_block", return_value=True) as mock_register,
    ):
        result = module.main()

    assert result == 0
    mock_rustfs.assert_called_once_with()
    mock_prefect.assert_called_once_with()
    mock_bucket.assert_called_once_with("bucket")
    mock_upload.assert_called_once_with("bucket", prefix="dev")
    mock_register.assert_called_once_with()
    assert "Setup complete!" in capsys.readouterr().out


@pytest.mark.local
def test_main_fails_when_test_asset_upload_fails(
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_module()

    with (
        patch.object(module, "check_rustfs_available", return_value=True),
        patch.object(module, "check_prefect_server", return_value=True),
        patch.object(
            module,
            "get_rustfs_config",
            return_value={
                "endpoint_url": "http://localhost:9000",
                "aws_access_key_id": "key",
                "aws_secret_access_key": "secret",
                "bucket_name": "bucket",
                "prefix": "dev",
            },
        ),
        patch.object(module, "ensure_bucket_exists", return_value=True),
        patch.object(module, "upload_test_asset", return_value=False),
        patch.object(module, "register_prefect_block") as mock_register,
    ):
        result = module.main()

    assert result == 1
    mock_register.assert_not_called()
    assert "failed to upload the integration test asset" in capsys.readouterr().out.lower()
