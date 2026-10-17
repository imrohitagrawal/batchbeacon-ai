#!/usr/bin/env python3
"""Collect non-secret local settings; verify on the actual owner machine.

No installation, authentication, network/cloud operation, or approval grant.
Creates an ignored .batchbeacon/local-settings.json only after local inspection.
Never overwrites an existing settings file. --check validates without changes.
Any existing permissions or authority must be recorded separately in STATE.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


DEADLINE = "2026-10-18T18:29:00Z"
IGNORE_LINE = "/.batchbeacon/"


def aware_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps require an explicit timezone")
    return parsed.astimezone(timezone.utc)


def positive_amount(value: object, field: str) -> Decimal:
    try:
        amount = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError(f"{field} must be numeric") from error
    if not amount.is_finite() or amount <= 0:
        raise ValueError(f"{field} must be finite and greater than zero")
    return amount


def validate(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError("settings must be a JSON object")
    required = {
        "schema_version", "project_id", "cloud_run_region", "firestore_database",
        "firestore_location", "model_endpoint_kind", "model_location", "model_id",
        "private_image_bucket", "resource_owner", "currency", "total_allowance",
        "evaluation_allowance", "demo_and_service_reserve", "verified_deadline",
        "service_retention_review_at", "settings_are_not_authorization",
    }
    if required - data.keys():
        raise ValueError("missing fields: " + ", ".join(sorted(required - data.keys())))
    if data["schema_version"] != 1 or data["settings_are_not_authorization"] is not True:
        raise ValueError("unsupported schema or missing no-authorization marker")
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", str(data["project_id"])):
        raise ValueError("project_id must be an actual Google project ID, not a number or placeholder")
    if not re.fullmatch(r"[a-z]+-[a-z]+[0-9]+", str(data["cloud_run_region"])):
        raise ValueError("cloud_run_region format is invalid; verify real regional availability separately")
    for field in ("firestore_database", "firestore_location", "model_location", "model_id"):
        if not re.fullmatch(r"[A-Za-z0-9_.()/-]{1,120}", str(data[field])):
            raise ValueError(f"{field} has an invalid local value")
    if data["model_endpoint_kind"] != "vertex_ai":
        raise ValueError("this local configuration expects the recommended Google Cloud endpoint; record a decision before adapting")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]", str(data["private_image_bucket"])):
        raise ValueError("private_image_bucket must be a candidate or verified bucket name, not a URL")
    if not str(data["resource_owner"]).strip() or len(str(data["resource_owner"])) > 160:
        raise ValueError("name the actual resource/spend owner")
    if not re.fullmatch(r"[A-Z]{3}", str(data["currency"])):
        raise ValueError("currency must be a three-letter uppercase code")
    total = positive_amount(data["total_allowance"], "total_allowance")
    evaluation = positive_amount(data["evaluation_allowance"], "evaluation_allowance")
    reserve = positive_amount(data["demo_and_service_reserve"], "demo_and_service_reserve")
    if evaluation + reserve >= total:
        raise ValueError("eval allowance plus demo/service reserve must leave a positive build/other-cloud allowance")
    deadline = aware_time(str(data["verified_deadline"]))
    if aware_time(str(data["service_retention_review_at"])) <= deadline:
        raise ValueError("retention review must follow the deadline; retain service through actual judging obligations")


def ask(label: str, default: str | None = None) -> str:
    value = input(f"{label}" + (f" [{default}]" if default else "") + ": ").strip()
    value = value or default or ""
    if not value:
        raise ValueError(f"{label} is required; use discovery rather than a placeholder")
    return value


def inspect_root(root: Path) -> None:
    if Path.cwd().resolve() != root or root.name != "batchbeacon-ai":
        raise ValueError("run from the intended batchbeacon-ai root after workspace inspection")
    if shutil.which("git"):
        check = subprocess.run(["git", "--no-optional-locks", "-C", str(root), "rev-parse", "--show-toplevel"],
                               capture_output=True, text=True, timeout=8, check=False)
        if check.returncode == 0 and Path(check.stdout.strip()).resolve() != root:
            raise ValueError("this folder is inside a different repository; resolve the intended project boundary first")
    for path in (root / ".gitignore", root / ".batchbeacon", root / ".batchbeacon/local-settings.json"):
        if path.is_symlink():
            raise ValueError("refusing symlinked configuration targets")


def ensure_ignore(root: Path) -> None:
    ignore = root / ".gitignore"
    existing = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
    # Last matching pattern wins. Appending the exact directory rule is conservative.
    if not existing.rstrip().endswith(IGNORE_LINE):
        separator = "" if not existing or existing.endswith("\n") else "\n"
        with ignore.open("a", encoding="utf-8") as handle:
            handle.write(separator + IGNORE_LINE + "\n")
    check_ignored(root)


def check_ignored(root: Path) -> None:
    ignore = root / ".gitignore"
    if not ignore.is_file() or IGNORE_LINE not in ignore.read_text(encoding="utf-8").splitlines():
        raise ValueError("the explicit local settings ignore rule is missing")
    if shutil.which("git") and (root / ".git").exists():
        check = subprocess.run(["git", "--no-optional-locks", "-C", str(root), "check-ignore", "-q", ".batchbeacon/local-settings.json"],
                               capture_output=True, text=True, timeout=8, check=False)
        if check.returncode != 0:
            raise ValueError("local settings are not ignored or were already tracked; no settings written")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate existing settings without modifying any file")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        inspect_root(root)
        target = root / ".batchbeacon/local-settings.json"
        if target.exists():
            validate(json.loads(target.read_text(encoding="utf-8")))
            check_ignored(root)
            print("Existing local settings are structurally valid; unchanged. Availability, authority and values still require verification.")
            return 0
        if args.check:
            raise ValueError("local settings do not exist; no files changed")
        print("Non-secret values only. Do not enter credentials. This does not approve spending or create resources.")
        data = {
            "schema_version": 1,
            "project_id": ask("Actual Google project ID"),
            "cloud_run_region": ask("Verified Cloud Run region"),
            "firestore_database": ask("Verified/authorized Firestore database ID", "(default)"),
            "firestore_location": ask("Verified/authorized Firestore location"),
            "model_endpoint_kind": "vertex_ai",
            "model_location": ask("Verified Gemini endpoint location"),
            "model_id": ask("Verified model ID", "gemini-3.8-flash"),
            "private_image_bucket": ask("Verified or explicitly proposed private image bucket name"),
            "resource_owner": ask("Actual resource and spend owner"),
            "currency": ask("Budget currency, three-letter code").upper(),
            "total_allowance": ask("Total proposed/approved allowance"),
            "evaluation_allowance": ask("Evaluation allowance within total"),
            "demo_and_service_reserve": ask("Demo and retained-service reserve within total"),
            "verified_deadline": ask("Current verified deadline ISO timestamp with timezone", DEADLINE),
            "service_retention_review_at": ask("Review service retention after all judging obligations, ISO timestamp with timezone"),
            "settings_are_not_authorization": True,
        }
        validate(data)
        ensure_ignore(root)
        target.parent.mkdir(mode=0o700, exist_ok=True)
        # Exclusive creation prevents accidental overwrite; no secret values are collected.
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        print("Created ignored local settings. Record actual approvals separately; verify all account/configuration values before external work.")
        return 0
    except (ValueError, OSError, EOFError, KeyboardInterrupt, subprocess.TimeoutExpired) as error:
        print(f"Configuration incomplete: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
