#!/usr/bin/env python3
"""Read-only BatchBeacon discovery. Requires verification on the actual machine.

No dependency install, login, network request, cloud command, or Git mutation.
Only Python/Git version and Git read commands are executed. Other tools are
reported as found/missing; presence does not prove compatibility or access.
Read applicable workspace instructions before running this helper.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys


INPUT_HASHES = {
    "HACKATHON_BRIEF.md": "4643b9c2753899d0c4a8f48fa68b547af86ec2a897d38fae19aa8b726e77727e",
    "HACKATHON_CODEX_MASTER_PROMPT.md": "bc3b8ec0a6442b2f5164ed6ffcd986ed7d06329b07e0d5af17dd9f62eff5be72",
}


def git_read(root: Path, args: list[str]) -> dict:
    if not shutil.which("git"):
        return {"status": "MISSING"}
    run_env = os.environ.copy()
    run_env["GIT_OPTIONAL_LOCKS"] = "0"
    run_env["GIT_NO_LAZY_FETCH"] = "1"
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
            capture_output=True, text=True, timeout=8, check=False, env=run_env,
        )
        # Do not include stderr: local Git errors may contain a credentialed URL.
        return {"exit_code": result.returncode, "stdout": result.stdout.strip()[:16000]}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"status": "UNVERIFIED", "error_type": type(error).__name__}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if Path.cwd().resolve() != root:
        print("Run from the intended batchbeacon-ai root; no action taken.", file=sys.stderr)
        return 2
    inputs = {}
    for name, expected in INPUT_HASHES.items():
        path = root / name
        if path.is_file() and not path.is_symlink():
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            inputs[name] = {"sha256": actual, "matches_packaged_input": actual == expected}
        else:
            inputs[name] = {"status": "MISSING_OR_SYMLINK"}
    tools = {name: shutil.which(name) for name in (
        "codex", "git", "python3", "python", "uv", "gcloud", "gh",
        "docker", "node", "npm", "playwright", "firebase",
    )}
    instruction_paths = []
    for parent in reversed((root, *root.parents)):
        path = parent / "AGENTS.md"
        if path.is_file():
            instruction_paths.append(str(path))
    git_root = git_read(root, ["rev-parse", "--show-toplevel"])
    observed_root = git_root.get("stdout") if git_root.get("exit_code") == 0 else None
    report = {
        "purpose": "Local read-only discovery; no successful setup/auth/cloud claim",
        "workspace": str(root), "expected_folder_name": "batchbeacon-ai",
        "folder_name_matches": root.name == "batchbeacon-ai",
        "platform": platform.platform(), "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "shell_hint": Path(os.environ.get("SHELL", "unknown")).name,
        "inputs": inputs, "tool_paths_only": tools,
        "ancestor_AGENTS_paths": instruction_paths,
        "git": {
            "version": git_read(root, ["--version"]), "root": git_root,
            "is_this_root": Path(observed_root).resolve() == root if observed_root else None,
            "branch": git_read(root, ["branch", "--show-current"]),
            "head": git_read(root, ["rev-parse", "--verify", "HEAD"]),
            "status": git_read(root, ["status", "--porcelain=v1", "--untracked-files=normal"]),
            "remote_names_only": git_read(root, ["remote"]),
        },
        "still_unverified": [
            "Global/client and nested instructions; inspect through supported mechanisms",
            "Codex/client versions, supported help, permission and auth status",
            "Dependencies, browser/subagent availability and test discovery",
            "Remote URLs/access; inspect and redact before recording",
            "Google identity, IAM, project, billing, regions, quota and service behavior",
            "Every application, evaluation, deployment and submission result",
        ],
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    input_problem = any(not item.get("matches_packaged_input") for item in inputs.values())
    wrong_git_root = bool(observed_root and Path(observed_root).resolve() != root)
    # A legitimate changed original requires reconciliation, not automatic replacement.
    return 2 if input_problem or wrong_git_root or root.name != "batchbeacon-ai" else 0


if __name__ == "__main__":
    raise SystemExit(main())
