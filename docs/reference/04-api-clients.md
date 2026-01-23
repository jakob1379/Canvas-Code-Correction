# API Clients Reference

## Overview

Canvas interactions are handled through several specialized components that
together provide **download**, **upload**, and **grade‑posting** capabilities.
The long‑term plan is to consolidate these into a single `CanvasClient` module;
for now the functionality is distributed across `CanvasResources`,
`CanvasUploader`, and the `download_submission_files` task.

## Current Status

- **`CanvasClient` module**: Not yet implemented – planned for a future release.
- **Existing components**: Fully functional and used in production flows:
  - `CanvasResources` – bundles the Canvas API client, course object, and
    settings.
  - `CanvasUploader` – idempotent upload of feedback files and grades with
    duplicate detection.
  - `download_submission_files` (Prefect task) – downloads submission
    attachments from Canvas.

## Key Features

### Download Submission Attachments

The `download_submission_files` task retrieves all files attached to a Canvas
submission. It uses the `CanvasResources` bundle to obtain the submission
object, extracts attachment IDs, and downloads each file to a local directory.

**Key behaviors**:

- **Retry/backoff** – currently relies on the underlying `canvasapi` library;
  explicit retry logic will be added in the `CanvasClient` module.
- **Filename resolution** – prefers the attachment’s `display_name` if
  available, otherwise falls back to the file’s `filename` attribute.

### Upload Feedback Artefacts

The `CanvasUploader` class uploads feedback files (e.g., zip archives) to a
submission’s comments. It includes **MD5‑based duplicate detection** to avoid
uploading the same file twice.

**Key behaviors**:

- **Checksum verification** – calculates the MD5 hash of the local file and
  compares it with existing comment attachments.
- **Idempotent upload** – if a duplicate is found, the upload is skipped and a
  success result is returned.
- **Dry‑run mode** – can preview what would be uploaded without making API
  calls.

### Post Grades and Comments

`CanvasUploader` also provides an `upload_grade` method that posts a grade to a
submission. The method checks whether the grade is already set and skips the
update if the values match.

**Key behaviors**:

- **Duplicate detection** – compares the new grade with the current
  `submission.grade`.
- **Configurable upload** – can disable grade posting or comment posting via
  `UploadConfig`.

## Integration Points

### Prefect Tasks

Prefect tasks instantiate `CanvasResources` using credentials obtained from the
`Settings` object. The `build_canvas_resources` helper constructs the bundle:

```python
from canvas_code_correction.clients import build_canvas_resources
from canvas_code_correction.config import Settings

settings = Settings(...)
resources = build_canvas_resources(settings)
```

Tasks that need to download or upload data receive the `resources` object as an
argument.

### Settings

Canvas connection details are stored in a `CanvasSettings` nested model inside
the global `Settings`. The values can be supplied via environment variables, a
Prefect `CourseConfigBlock`, or directly in code.

```python
from canvas_code_correction.config import Settings, CanvasSettings
from pydantic import HttpUrl, SecretStr

settings = Settings(
    canvas=CanvasSettings(
        api_url=HttpUrl("https://canvas.instructure.com"),
        token=SecretStr("your-canvas-token"),
        course_id=12345,
    )
)
```

## Example Usage

The following snippet shows how to use the existing components together:

```python
from canvas_code_correction.clients import build_canvas_resources
from canvas_code_correction.config import Settings
from canvas_code_correction.uploader import CanvasUploader, UploadConfig
from pathlib import Path

# 1. Build Canvas resources
settings = Settings.from_course_block("my-course-block")
resources = build_canvas_resources(settings)

# 2. Download submission files (inside a Prefect task)
#    (see the `download_submission_files` task in `flows.correction`)

# 3. Upload feedback and a grade
assignment = resources.course.get_assignment(1001)
submission = assignment.get_submission(5001)
uploader = CanvasUploader(submission)

feedback_file = Path("feedback.zip")
grade = "95"

config = UploadConfig(check_duplicates=True, dry_run=False)
feedback_result, grade_result = uploader.upload_feedback_and_grade(
    feedback_file, grade, config
)

print(feedback_result.message)
print(grade_result.message)
```

## Future Enhancements

The **`CanvasClient` module** will unify the above capabilities and add:

- **Rate‑limit handling** – automatic backoff when Canvas API throttles
  requests.
- **Caching of course metadata** – reduce redundant API calls for assignments,
  rubrics, etc.
- **Batch operations** – download/upload multiple submissions in a single call.
- **Comprehensive error recovery** – configurable retry policies for transient
  failures.

Until `CanvasClient` is implemented, the existing components provide a stable,
production‑ready interface for all essential Canvas operations.
