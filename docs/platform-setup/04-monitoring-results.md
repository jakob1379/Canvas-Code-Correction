# Monitoring Results

> **Audience**: CCC platform operators  
> **Prerequisites**: Corrections running via Prefect

After corrections run, CCC uploads feedback and grades to Canvas. You can monitor the process via Prefect and Canvas.

## Prefect Dashboard

The Prefect UI shows flow run status, logs, and any errors. Check the logs for grader output and debugging.

## Canvas Feedback

CCC uploads a feedback ZIP file to each submission's comments area. The ZIP contains:

- `results.json`: Structured results from grader
- `comments.txt`: Plain text feedback
- `points.txt`: Score(s)

Students can download the ZIP from their submission page.

## Grades

CCC can post grades to Canvas if configured. The grade is extracted from `points.txt` (first line). Ensure your grader outputs a numeric score.

## Troubleshooting

Common issues:

- **Grader container fails**: Check Docker image, dependencies, and entrypoint.
- **Missing submission files**: Verify Canvas token and course ID.
- **S3 asset fetch fails**: Ensure bucket block permissions and prefix.
- **Prefect worker offline**: Verify worker connectivity and pool name.

Use `uv run ccc run-once` with a specific submission for debugging.

## Next Steps

Now you have a fully automated correction pipeline! Iterate on your grader tests and improve feedback quality.

For advanced topics, refer to the Administration and Development sections.