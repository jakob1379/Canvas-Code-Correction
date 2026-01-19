#!/usr/bin/env python3
"""
Wrapper for uv-secure that retries on transient network errors.
"""

import subprocess
import sys
import time
import os
from typing import List


def run_with_retry(args: List[str], max_retries: int = 3, initial_delay: float = 1.0) -> int:
    """Run command with exponential backoff retry."""
    delay = initial_delay
    result = None

    for attempt in range(max_retries):
        if attempt > 0:
            print(f"Retry attempt {attempt + 1}/{max_retries} after {delay:.1f}s delay...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

        print(f"Running uv-secure (attempt {attempt + 1}/{max_retries}): {' '.join(args)}")
        result = subprocess.run(args, capture_output=True, text=True)

        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        # Check for known transient errors
        if result.returncode == 0:
            return 0

        # Check for DNS resolution errors
        if "Temporary failure in name resolution" in result.stderr:
            print("Detected DNS resolution error, will retry...")
            continue
        if "aiobotocore" in result.stderr and "name resolution" in result.stderr.lower():
            print("Detected aiobotocore DNS error, will retry...")
            continue

        # Check for other network-related errors
        network_errors = [
            "Connection refused",
            "Connection reset",
            "Timeout",
            "Network is unreachable",
            "Name or service not known",
        ]
        if any(error in result.stderr for error in network_errors):
            print(f"Detected network error, will retry...")
            continue

        # For other errors, exit immediately
        print(f"uv-secure failed with non-transient error (exit code {result.returncode})")
        return result.returncode

    print(f"Failed after {max_retries} attempts")
    return result.returncode if result is not None else 1


def main() -> None:
    # Build command arguments
    cmd = ["uv-secure"]
    cmd.extend(sys.argv[1:])  # Pass through any additional args

    # Add default arguments for better caching and reliability
    default_args = [
        "--cache-ttl-seconds",
        "604800",  # 1 week cache
        "--check-uv-tool",
        "false",  # Skip checking uv CLI (reduces network calls)
    ]

    # Only add defaults if not already present
    for i in range(0, len(default_args), 2):
        if default_args[i] not in cmd:
            cmd.append(default_args[i])
            cmd.append(default_args[i + 1])

    exit_code = run_with_retry(cmd, max_retries=3)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
