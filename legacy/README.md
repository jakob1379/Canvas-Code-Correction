# Legacy Scripts

This directory houses the original bash- and script-driven implementation of
Canvas Code Correction. Files in `legacy/scripts/` remain source material for
the migration effort and are no longer executed as part of the v2 Prefect
orchestrator.

As functionality is ported into the new Python modules under
`src/canvas_code_correction/`, the corresponding legacy assets should be
deleted. Keeping the remaining scripts grouped here makes it easier to track
what still needs migration and keeps pre-commit checks focused on the v2 code
path.
