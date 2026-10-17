"""Local operator-only T08 reservations; never the public multi-instance ledger.

No network calls or automatic initialization. Every reservation is single-use.
An interruption leaves its full amount charged. Separate calls/retries require a
new reservation. Provider-verified usage can reconcile it once, including after
expiry, but cannot erase attempt counters. Store only in an ignored private path.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import TypeAdapter

from batchbeacon.cloud_policy import (
    ModelProbePolicy,
    OpeningLiabilities,
    ProbeGrant,
    validate_admission,
)
from batchbeacon.contracts import Digest, Nonempty, Record


class AdmissionDenied(ValueError):
    pass


class Reservation(Record):
    attempt_id: Nonempty
    policy_sha256: Digest
    request_sha256: Digest
    reserved_nanos: int


class OperatorLedger:
    def __init__(self, path: Path, policy: ModelProbePolicy, grant: ProbeGrant):
        self.path, self.policy, self.grant = path, policy, grant

    def initialize(self, opening: OpeningLiabilities, *, now: datetime) -> None:
        validate_admission(self.policy, self.grant, now)
        prior = opening.substantiated_total()
        day = now.astimezone(ZoneInfo(self.policy.calendar_timezone)).date()
        if any(entry.day > day for entry in opening.prior_attempt_days):
            raise AdmissionDenied("opening attempts cannot be in the future")
        if prior + self.policy.reserve_nanos > self.grant.allocation_nanos:
            raise AdmissionDenied("allocation cannot cover prior liabilities and one attempt")
        # Exclusive creation: an existing, missing-on-reopen or partial ledger is
        # never silently replaced. Operator must reconcile any failed initialization.
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        with self._connection() as db:
            db.executescript("""
                CREATE TABLE allocation (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    policy_sha256 TEXT NOT NULL,
                    grant_sha256 TEXT NOT NULL,
                    opening_json TEXT NOT NULL,
                    prior_nanos INTEGER NOT NULL,
                    circuit_open INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE attempt (
                    id TEXT PRIMARY KEY,
                    request_sha256 TEXT NOT NULL,
                    calendar_day TEXT NOT NULL,
                    reserved_at TEXT NOT NULL,
                    reserved_nanos INTEGER NOT NULL,
                    charged_nanos INTEGER NOT NULL,
                    usage_sha256 TEXT
                );
            """)
            db.execute("INSERT INTO allocation VALUES (1, ?, ?, ?, ?, 0)", (
                self.policy.digest(), self.grant.digest(), opening.model_dump_json(), prior,
            ))

    @contextmanager
    def _connection(self):
        if self.path.is_symlink() or not self.path.is_file():
            raise AdmissionDenied("private ledger is missing or symlinked")
        if self.path.stat().st_mode & 0o077:
            raise AdmissionDenied("ledger permissions must be owner-only")
        db = sqlite3.connect(
            self.path.resolve().as_uri() + "?mode=rw", uri=True,
            timeout=self.policy.ledger_lock_timeout_ms / 1000,
        )
        try:
            db.execute("PRAGMA synchronous=FULL")
            with db:
                yield db
        finally:
            db.close()

    def _allocation(self, db):
        row = db.execute("SELECT * FROM allocation WHERE singleton=1").fetchone()
        if not row or row[1:3] != (self.policy.digest(), self.grant.digest()):
            raise AdmissionDenied("ledger is incomplete or bound to another policy/allocation")
        return row

    def reserve(self, attempt_id: str, request_sha256: str, *, now: datetime) -> Reservation:
        validate_admission(self.policy, self.grant, now)
        TypeAdapter(Nonempty).validate_python(attempt_id, strict=True)
        TypeAdapter(Digest).validate_python(request_sha256, strict=True)
        day = now.astimezone(ZoneInfo(self.policy.calendar_timezone)).date().isoformat()
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            allocation = self._allocation(db)
            if allocation[5]:
                raise AdmissionDenied("cost circuit is open; reconcile before new work")
            if db.execute("SELECT 1 FROM attempt WHERE id=?", (attempt_id,)).fetchone():
                raise AdmissionDenied("attempt already reserved; reconcile instead of reinvoking")
            total, charged = db.execute(
                "SELECT COUNT(*), COALESCE(SUM(charged_nanos), 0) FROM attempt"
            ).fetchone()
            daily = db.execute(
                "SELECT COUNT(*) FROM attempt WHERE calendar_day=?", (day,)
            ).fetchone()[0]
            opening = OpeningLiabilities.model_validate_json(allocation[3])
            opening.substantiated_total()
            total += sum(entry.attempts for entry in opening.prior_attempt_days)
            daily += sum(entry.attempts for entry in opening.prior_attempt_days
                         if entry.day.isoformat() == day)
            if total >= self.policy.max_total_attempts or daily >= self.policy.max_daily_attempts:
                raise AdmissionDenied("paid attempt allowance exhausted")
            amount = self.policy.reserve_nanos
            if allocation[4] + charged + amount > self.grant.allocation_nanos:
                raise AdmissionDenied("insufficient uncommitted allowance")
            db.execute("INSERT INTO attempt VALUES (?, ?, ?, ?, ?, ?, NULL)", (
                attempt_id, request_sha256, day, now.isoformat(), amount, amount,
            ))
        return Reservation(
            attempt_id=attempt_id, policy_sha256=self.policy.digest(),
            request_sha256=request_sha256, reserved_nanos=amount,
        )

    def reconcile(
        self, attempt_id: str, *, input_tokens: int, output_and_thought_tokens: int,
        usage_sha256: str,
    ) -> None:
        """Only complete verified usage; unknown/error/cancel leaves reserve intact.

        If actual usage exceeds its asserted bound, retain the larger liability and
        open the circuit. A duplicate identical reconciliation is idempotent.
        """
        TypeAdapter(Digest).validate_python(usage_sha256, strict=True)
        cost = self.policy.price.cost_nanos(input_tokens, output_and_thought_tokens)
        if cost > 2**63 - 1:
            with self._connection() as db:
                db.execute("BEGIN IMMEDIATE")
                self._allocation(db)
                if not db.execute("SELECT 1 FROM attempt WHERE id=?", (attempt_id,)).fetchone():
                    raise AdmissionDenied("no reservation exists for this usage")
                db.execute("UPDATE allocation SET circuit_open=1 WHERE singleton=1")
            raise AdmissionDenied("usage exceeds ledger representation; preserve reservation")
        violation = (input_tokens > self.policy.max_input_tokens
                     or output_and_thought_tokens > self.policy.billable_output_token_bound)
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            self._allocation(db)
            row = db.execute("SELECT charged_nanos, usage_sha256 FROM attempt WHERE id=?",
                             (attempt_id,)).fetchone()
            if not row:
                raise AdmissionDenied("no reservation exists for this usage")
            if row[1] is not None:
                if row != (cost, usage_sha256):
                    raise AdmissionDenied("conflicting usage reconciliation")
                return
            db.execute("UPDATE attempt SET charged_nanos=?, usage_sha256=? WHERE id=?",
                       (cost, usage_sha256, attempt_id))
            if violation:
                db.execute("UPDATE allocation SET circuit_open=1 WHERE singleton=1")

    def snapshot(self) -> dict:
        with self._connection() as db:
            allocation = self._allocation(db)
            attempts, charged, unknown = db.execute(
                "SELECT COUNT(*), COALESCE(SUM(charged_nanos), 0), "
                "COUNT(*) - COUNT(usage_sha256) FROM attempt"
            ).fetchone()
        opening = OpeningLiabilities.model_validate_json(allocation[3])
        opening.substantiated_total()
        return {
            "policy_sha256": self.policy.digest(), "grant_sha256": self.grant.digest(),
            "attempts": attempts + sum(e.attempts for e in opening.prior_attempt_days),
            "unknown_attempts": unknown,
            "committed_nanos": allocation[4] + charged,
            "allocation_nanos": self.grant.allocation_nanos,
            "circuit_open": bool(allocation[5]),
        }
