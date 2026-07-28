from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from canvas_code_correction.storage.rustfs_provisioning import (
    RustfsProvisioningError,
    RustfsStorageConfig,
    build_bucket_name,
    upload_directory_with_credentials,
)


def test_build_bucket_name_truncates_long_values() -> None:
    long_name = "ccc-assets-" + ("abc123" * 20)

    bucket_name = build_bucket_name(long_name)

    assert len(bucket_name) <= 63
    assert bucket_name.startswith("ccc-assets-")


@patch("canvas_code_correction.storage.rustfs_provisioning.S3Bucket")
def test_upload_directory_with_credentials_wraps_prefect_aws_errors(
    mock_s3_bucket: MagicMock,
    tmp_path: Path,
) -> None:
    work_package_root = tmp_path / "pkg"
    work_package_root.mkdir()
    storage = RustfsStorageConfig(
        endpoint_url="http://localhost:9000",
        region_name="us-east-1",
        aws_access_key_id="SHAREDKEY",
        aws_secret_access_key="SHAREDSECRET",  # noqa: S106
    )
    mock_bucket = MagicMock()
    mock_bucket.put_directory.side_effect = RuntimeError("upload failed")
    mock_s3_bucket.return_value = mock_bucket

    with pytest.raises(RustfsProvisioningError, match="failed to upload directory"):
        upload_directory_with_credentials(
            storage,
            bucket_name="ccc-assets-course-123",
            local_path=work_package_root,
            to_path="graders/course-123/assignments/1",
        )
