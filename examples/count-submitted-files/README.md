# Count Submitted Files Example

This is the docs example checked into the repo so it is available immediately
for local testing.

## Contents

- `assets/grader.py` counts submitted files and writes CCC output files.
- `assets/main.sh` runs the example with the default CCC container contract.
- `local-workspace/submission/` is a sample student submission.

## Run It Locally

From the repository root:

```bash
cd examples/count-submitted-files
export CCC_WORKSPACE_DIR="$(pwd)/local-workspace"
export CCC_RESULTS_FILE="$CCC_WORKSPACE_DIR/results.json"
export CCC_POINTS_FILE="$CCC_WORKSPACE_DIR/points.txt"
export CCC_COMMENTS_FILE="$CCC_WORKSPACE_DIR/comments.txt"
python3 assets/grader.py
cat local-workspace/results.json
cat local-workspace/comments.txt
```

## Run It In Docker

```bash
cd examples/count-submitted-files
docker run --rm \
  -v "$(pwd)/assets:/workspace/assets:ro" \
  -v "$(pwd)/local-workspace:/workspace" \
  jakob1379/canvas-grader:latest \
  sh /workspace/assets/main.sh
```
