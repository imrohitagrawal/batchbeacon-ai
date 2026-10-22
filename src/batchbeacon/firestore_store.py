"""Explicit Firestore SDK adapters; construction performs no I/O or provisioning.

One generated-client transaction reads all participating domains. No fallback,
credential discovery, provider call or real budget initialization occurs here.
The configured environment is a server-owned first-slice selection; T16 must
provide source selection/refresh orchestration before mixed-market integration.
"""

import time
from datetime import UTC, datetime
from typing import Annotated, Literal, Self

from google.api_core import exceptions as cloud_errors
from google.cloud.firestore_v1.services.firestore import FirestoreClient
from google.cloud.firestore_v1.types import (
    BatchGetDocumentsRequest,
    BeginTransactionRequest,
    CommitRequest,
    Document,
    Precondition,
    RollbackRequest,
    TransactionOptions,
    Value,
    Write,
)
from pydantic import Field, TypeAdapter, model_validator

from batchbeacon.acquisition import AcquisitionCompletion, StoredCompletion
from batchbeacon.action_service import ActionPolicy, ActionSnapshot, ActionState
from batchbeacon.cloud_policy import ProjectId
from batchbeacon.contracts import Digest, Record
from batchbeacon.evidence_service import (
    EvidenceEnvironment,
    EvidencePolicy,
    EvidenceSnapshot,
    EvidenceState,
    replace,
)
from batchbeacon.guest_admission import GuestAdmissionState, reserve_guest
from batchbeacon.guest_service import GuestPolicy, GuestSession, OpaqueId
from batchbeacon.shared_admission import Attempt, Budget, IncidentUsage, SessionUsage, Snapshot

Segment = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")]
PositiveSeconds = Annotated[float, Field(gt=0, allow_inf_nan=False)]


class FirestorePolicy(Record):
    project_id: ProjectId
    database_id: Annotated[str, Field(pattern=r"^(\(default\)|[a-z][a-z0-9-]{0,62})$")]
    namespace: Segment
    environment_id: Segment
    mode: Literal["production", "emulator", "offline_test"]
    api_endpoint: Annotated[str, Field(min_length=1, max_length=253)]
    operation_seconds: PositiveSeconds = 15.0
    rpc_seconds: PositiveSeconds = 5.0
    # A separately declared cleanup ceiling; never an extension for a commit/retry.
    cleanup_seconds: PositiveSeconds = 1.0
    max_transaction_attempts: Annotated[int, Field(gt=0)] = 3
    max_documents: Annotated[int, Field(gt=0)] = 64
    max_document_bytes: Annotated[int, Field(gt=0, le=1048576)] = 786432
    max_request_bytes: Annotated[int, Field(gt=0, le=10485760)] = 8388608
    max_read_bytes: Annotated[int, Field(gt=0)] = 8388608

    @model_validator(mode="after")
    def coherent(self) -> Self:
        import re
        if self.rpc_seconds > self.operation_seconds or self.cleanup_seconds > self.rpc_seconds:
            raise ValueError("RPC and cleanup deadlines must fit the operation policy")
        if self.max_document_bytes >= min(self.max_request_bytes, self.max_read_bytes):
            raise ValueError("document must fit request/read bounds")
        if self.mode == "production":
            valid = re.fullmatch(r"(?:[a-z0-9-]+\.)*firestore\.googleapis\.com(?::443)?",
                                 self.api_endpoint)
        else:
            valid = re.fullmatch(r"(?:localhost|127\.0\.0\.1):([0-9]{1,5})", self.api_endpoint)
            if valid and not 1 <= int(valid.group(1)) <= 65535:
                valid = None
        if not valid:
            raise ValueError("endpoint must match the explicitly selected mode")
        return self

    @property
    def database(self):
        return f"projects/{self.project_id}/databases/{self.database_id}"


def _unavailable():
    return OSError("persistent evidence unavailable")


class _Transaction:
    def __init__(self, owner, transaction_id, deadline):
        self.owner, self.id, self.deadline = owner, transaction_id, deadline
        self.reads, self.writes = {}, {}
        self.staged = {}
        self.addresses = {}
        self.timestamps = {}
        self.read_bytes = 0
        self.not_after = None

    def limit_to(self, value):
        if value is not None:
            if value.tzinfo is None:
                raise _unavailable()
            self.not_after = min(self.not_after, value) if self.not_after else value

    def read(self, specifications):
        if self.writes:
            raise _unavailable()  # Firestore requires all reads before writes.
        return self._read_originals(specifications)

    def _read_originals(self, specifications):
        # Used by the finalizer after local staging, before the sole Commit RPC.
        # Staged values never masquerade as database read results.
        pending = {name: kind for name, kind in specifications.items() if name not in self.reads}
        if len(self.reads) + len(pending) > self.owner.policy.max_documents:
            raise _unavailable()
        if pending:
            request = BatchGetDocumentsRequest(database=self.owner.policy.database,
                documents=list(pending), transaction=self.id)
            responses = self.owner._call("batch_get_documents", request, self.deadline,
                                         self.not_after)
            seen = set()
            for response in responses:
                self.owner._remaining(self.deadline, self.not_after)
                kind = type(response).pb(response).WhichOneof("result")
                if kind not in {"found", "missing"}:
                    raise _unavailable()
                name = response.found.name if kind == "found" else response.missing
                if name not in pending or name in seen:
                    raise _unavailable()
                seen.add(name)
                self.read_bytes += len(type(response).serialize(response))
                if self.read_bytes > self.owner.policy.max_read_bytes:
                    raise _unavailable()
                self.reads[name] = self.owner._decode(response.found, pending[name]) \
                    if kind == "found" else None
                if kind == "found":
                    document = type(response.found).pb(response.found)
                    self.timestamps[name] = (
                        response.found.create_time if document.HasField("create_time") else None,
                        response.found.update_time if document.HasField("update_time") else None)
            if seen != set(pending):
                raise _unavailable()
        return {name: self.reads[name] for name in specifications}

    def write(self, name, kind, record, *, create=False):
        if name not in self.reads or (self.reads[name] is None) != create:
            raise _unavailable()
        # Unchanged reads commit no domain writes and retain their writer receipt.
        if record == self.reads[name]:
            return
        document = self.owner._encode(name, kind, record)
        self.writes[name] = Write(update=document, current_document=Precondition(exists=not create))
        self.staged[name] = (kind, self.owner._decode(document, kind))


_MODELS = {"guest": GuestSession, "usage": SessionUsage, "evidence": EvidenceState,
           "actions": ActionState, "environment": EvidenceEnvironment,
           "budget": Budget, "attempt": Attempt, "completion": AcquisitionCompletion,
           "guest_admission": GuestAdmissionState}


class FirestoreStores:
    def __init__(self, client: FirestoreClient, policy: FirestorePolicy,
                 guest_policy: GuestPolicy, evidence_policy: EvidencePolicy,
                 action_policy: ActionPolicy, *, clock=lambda: datetime.now(UTC),
                 monotonic=time.monotonic, guest_admission=None):
        if not isinstance(client, FirestoreClient) or client.api_endpoint != policy.api_endpoint:
            raise ValueError("explicit generated client and matching endpoint required")
        self.client, self.policy = client, policy
        self.guest_policy, self.evidence_policy, self.action_policy = (
            guest_policy, evidence_policy, action_policy)
        self.clock, self.monotonic = clock, monotonic
        self.guest_admission = guest_admission
        self.guests, self.shared = _Guests(self), _Shared(self)
        self.evidence, self.actions = _Evidence(self), _Actions(self)
        self.retail = None
        self.learning = None

    def enable_learning(self, evidence, shared_policy, evaluator, policy=None, *, capability=None):
        from batchbeacon.learning_service import LearningPolicy, LearningService
        if self.learning is not None:
            raise ValueError("learning persistence is already configured")
        self.learning = LearningService(self, evidence, shared_policy, evaluator,
            policy or LearningPolicy(), capability=capability)
        return self.learning

    def enable_retail(self, projector):
        from batchbeacon.retail_store import RetailPersistence
        if self.retail is not None:
            raise ValueError("retail persistence is already configured")
        self.retail = RetailPersistence(self, projector)
        return self.retail

    def name(self, kind, key=None, incident=None):
        if kind not in _MODELS and kind not in {"retail", "refresh", "learning"}:
            raise ValueError("unknown persistence kind")
        if kind in {"guest", "usage", "evidence", "actions", "retail", "refresh", "learning"}:
            TypeAdapter(Digest).validate_python(key)
        elif kind in {"attempt", "completion"}:
            TypeAdapter(OpaqueId).validate_python(key)
        elif kind == "environment":
            key = self.policy.environment_id
        if kind in {"evidence", "actions", "retail"}:
            TypeAdapter(OpaqueId).validate_python(incident)
        elif incident is not None:
            raise ValueError("unexpected incident address")
        suffix = kind + ("-" + key if key else "") + ("-" + incident if incident else "")
        return f"{self.policy.database}/documents/{self.policy.namespace}/{suffix}"

    def _size(self, document):
        # Conservative Firestore stored-size accounting for this fixed envelope:
        # full resource name overcounts the provider's relative document name.
        size = len(document.name.encode()) + 16 + 32
        for key, value in document.fields.items():
            size += len(key.encode()) + 1
            variant = type(value).pb(value).WhichOneof("value_type")
            if variant == "string_value":
                size += len(value.string_value.encode()) + 1
            elif variant == "integer_value":
                size += 8
            else:
                raise _unavailable()
        if size > self.policy.max_document_bytes:
            raise _unavailable()

    def _encode(self, name, kind, record):
        # Validate model_copy results as well as data returned by storage.
        try:
            record = self._model(kind).model_validate_json(record.model_dump_json(
                exclude_computed_fields=kind == "learning"))
        except ValueError:
            record = None
        if record is None:
            raise _unavailable()
        document = Document(name=name, fields={
            "schema": Value(integer_value=1), "kind": Value(string_value=kind),
            "writer_config_hash": Value(string_value=self.policy.digest()),
            "payload": Value(string_value=record.model_dump_json(
                exclude_computed_fields=kind == "learning"))})
        if kind == "guest" and self.retail is not None:
            document.fields["retail_policy_hash"] = Value(
                string_value=self.retail.projector.configuration_hash)
        if kind == "guest" and self.learning is not None:
            document.fields["learning_policy_hash"] = Value(
                string_value=self.learning.configuration_hash)
        self._size(document)
        return document

    def _decode(self, document, kind):
        self._size(document)
        fields = document.fields
        expected = {"schema", "kind", "writer_config_hash", "payload"}
        if kind == "guest" and self.learning is not None:
            expected.add("learning_policy_hash")
            if fields.get("learning_policy_hash", Value()).string_value != \
                    self.learning.configuration_hash:
                raise _unavailable()
        if kind == "guest" and self.retail is not None:
            expected.add("retail_policy_hash")
            if fields.get("retail_policy_hash", Value()).string_value != \
                    self.retail.projector.configuration_hash:
                raise _unavailable()
        if set(fields) != expected \
                or fields["schema"].integer_value != 1 or fields["kind"].string_value != kind:
            raise _unavailable()
        TypeAdapter(Digest).validate_python(fields["writer_config_hash"].string_value)
        # Operational configuration may change without making old evidence vanish.
        # The original writer hash is retained; domain policy hashes still apply.
        try:
            return self._model(kind).model_validate_json(fields["payload"].string_value)
        except ValueError:
            pass
        raise _unavailable()  # Keep private payloads out of validation exception chains.

    @staticmethod
    def _model(kind):
        if kind == "learning":
            from batchbeacon.learning_service import LearningState
            return LearningState
        if kind == "retail":
            from batchbeacon.retail_store import StoredProjection
            return StoredProjection
        if kind == "refresh":
            from batchbeacon.retail_refresh import RefreshState
            return RefreshState
        return _MODELS[kind]

    def _remaining(self, deadline, not_after=None):
        remaining = deadline - self.monotonic()
        if not_after is not None:
            now = self.clock()
            if now.tzinfo is None:
                raise _unavailable()
            remaining = min(remaining, (not_after - now).total_seconds())
        if remaining <= 0:
            raise _unavailable()
        return min(remaining, self.policy.rpc_seconds)

    def _call(self, method, request, deadline, not_after=None):
        if len(type(request).serialize(request)) > self.policy.max_request_bytes:
            raise _unavailable()
        return getattr(self.client, method)(request=request, retry=None,
            timeout=self._remaining(deadline, not_after))

    def _cleanup(self, transaction_id):
        if transaction_id:
            try:
                self._call("rollback", RollbackRequest(database=self.policy.database,
                    transaction=transaction_id), self.monotonic() + self.policy.cleanup_seconds)
            except Exception:
                pass  # Cleanup cannot replace an original denial or unknown outcome.

    def run(self, operation, *, not_after=None):
        deadline, retry_id = self.monotonic() + self.policy.operation_seconds, b""
        for _ in range(self.policy.max_transaction_attempts):
            transaction_id = b""
            try:
                response = self._call("begin_transaction", BeginTransactionRequest(
                    database=self.policy.database, options=TransactionOptions(read_write=
                        TransactionOptions.ReadWrite(retry_transaction=retry_id))), deadline,
                    not_after)
                transaction_id = response.transaction
                if not transaction_id:
                    raise _unavailable()
                transaction = _Transaction(self, transaction_id, deadline)
                transaction.limit_to(not_after)
                result = operation(transaction)
                if self.retail is not None:
                    self.retail.finalize(transaction)
                self._call("commit", CommitRequest(database=self.policy.database,
                    transaction=transaction_id, writes=list(transaction.writes.values())),
                    deadline, transaction.not_after)
                transaction_id = b""  # Commit acknowledged; never roll it back.
                self._remaining(deadline, not_after)
                return result
            except cloud_errors.Aborted:
                retry_id = transaction_id
                self._cleanup(transaction_id)
                self._remaining(deadline, not_after)
            except cloud_errors.GoogleAPICallError as exc:
                self._cleanup(transaction_id)
                raise _unavailable() from exc
            except BaseException:
                self._cleanup(transaction_id)
                raise
        raise _unavailable()

    def _guest(self, transaction, key):
        transaction.addresses[key] = None
        names = {self.name("guest", key): "guest", self.name("usage", key): "usage"}
        records = transaction.read(names)
        guest, usage = records[self.name("guest", key)], records[self.name("usage", key)]
        if guest is None:
            if usage is not None:
                raise _unavailable()
            return None, None
        if guest.capability_hash != key or guest.policy_hash != self.guest_policy.digest():
            raise _unavailable()
        self._usage(guest, usage)
        return guest, usage

    @staticmethod
    def _usage(guest, usage):
        ids = [i.id for i in guest.incidents]
        if usage is None or usage.session_id != guest.scope.session_id \
                or len(ids) != len(set(ids)) \
                or len({i.request_key for i in guest.incidents}) != len(ids) \
                or sorted(i.incident_id for i in usage.incidents) != sorted(ids) \
                or len({r.id for r in usage.runs}) != len(usage.runs) \
                or len({r.request_key for r in usage.runs}) != len(usage.runs):
            raise _unavailable()
        for counter in usage.incidents:
            acquired = sum(r.incident_id == counter.incident_id for r in usage.runs)
            if counter.acquisitions != acquired \
                    or len({v.request_key for v in counter.verifications}) != len(
                        counter.verifications):
                raise _unavailable()
        if any(r.incident_id not in ids or r.calls != len(r.call_operation_keys)
               or r.calls != len(r.attempt_ids) or len(set(r.attempt_ids)) != len(r.attempt_ids)
               for r in usage.runs):
            raise _unavailable()

    def _child(self, record, guest, incident, kind):
        policy = self.evidence_policy if kind == "evidence" else self.action_policy
        if record is None or guest is None or record.session_id != guest.scope.session_id \
                or record.incident_id != incident or record.policy_hash != policy.digest() \
                or not any(i.id == incident for i in guest.incidents):
            raise _unavailable()
        return record


class _Guests:
    def __init__(self, store):
        self.store = store

    def create(self, session):
        s = self.store
        if session.incidents or session.policy_hash != s.guest_policy.digest():
            raise _unavailable()
        def create(tx):
            guest, usage = s._guest(tx, session.capability_hash)
            if guest is not None or usage is not None:
                raise _unavailable()
            learning_name = None
            if s.learning is not None:
                learning_name = s.name("learning", session.capability_hash)
                if tx.read({learning_name: "learning"})[learning_name] is not None:
                    raise _unavailable()
            admission_name, admitted = None, None
            if s.guest_admission is not None:
                admission_name = s.name("guest_admission")
                stored = tx.read({admission_name: "guest_admission"})[admission_name]
                admitted = reserve_guest(s.guest_admission, stored, s.clock())
                tx.limit_to(s.guest_admission.expires_at)
            elif s.policy.mode == "production":
                raise _unavailable()
            tx.limit_to(session.scope.expires_at)
            if admission_name is not None:
                tx.write(admission_name, "guest_admission", admitted)
            tx.write(s.name("guest", session.capability_hash), "guest", session, create=True)
            tx.write(s.name("usage", session.capability_hash), "usage",
                     SessionUsage(session_id=session.scope.session_id), create=True)
            if learning_name is not None:
                tx.write(learning_name, "learning", s.learning.baseline(session), create=True)
        s.run(create, not_after=s.guest_admission.expires_at if s.guest_admission else None)

    def get(self, key):
        return self.store.run(lambda tx: self.store._guest(tx, key)[0])

    def transact(self, key, change):
        s = self.store
        def operate(tx):
            guest, usage = s._guest(tx, key)
            result = GuestSession.model_validate_json(change(guest).model_dump_json())
            if guest is None or result.model_dump(exclude={"incidents"}) != guest.model_dump(
                    exclude={"incidents"}):
                raise _unavailable()
            existing = {i.id: i for i in guest.incidents}
            updated = {i.id: i for i in result.incidents}
            if not set(existing) <= set(updated) or len(updated) != len(result.incidents) \
                    or len({i.request_key for i in result.incidents}) != len(result.incidents) \
                    or any(updated[k].request_key != old.request_key
                           for k, old in existing.items()):
                raise _unavailable()
            added = [i for i in result.incidents if i.id not in existing]
            if len(added) > 1 or any(i.batches for i in added):
                raise _unavailable()
            children = {s.name(kind, key, i.id): kind for i in added
                        for kind in ("evidence", "actions")}
            if any(value is not None for value in tx.read(children).values()):
                raise _unavailable()
            usage = replace(usage, incidents=(*usage.incidents,
                *(IncidentUsage(incident_id=i.id) for i in added)))
            s._usage(result, usage)
            tx.limit_to(guest.scope.expires_at)
            tx.write(s.name("guest", key), "guest", result)
            tx.write(s.name("usage", key), "usage", usage)
            for incident in added:
                for kind, cls, policy in (("evidence", EvidenceState, s.evidence_policy),
                                          ("actions", ActionState, s.action_policy)):
                    tx.write(s.name(kind, key, incident.id), kind,
                        cls(session_id=guest.scope.session_id, incident_id=incident.id,
                            policy_hash=policy.digest()), create=True)
            return result
        return s.run(operate)


class _Shared:
    def __init__(self, store):
        self.store = store

    def create_budget(self, budget):
        s = self.store
        def create(tx):
            name = s.name("budget")
            if tx.read({name: "budget"})[name] is not None:
                raise _unavailable()
            tx.write(name, "budget", budget, create=True)
        s.run(create)

    def transact(self, address, change):
        s = self.store
        def operate(tx):
            guest, usage = s._guest(tx, address.guest_key) if address.guest_key else (None, None)
            names = {s.name("budget"): "budget"}
            if address.attempt_id:
                names[s.name("attempt", address.attempt_id)] = "attempt"
            if address.inspect_session_attempts:
                if guest is None or usage is None:
                    raise _unavailable()
                names.update({s.name("attempt", aid): "attempt"
                              for run in usage.runs for aid in run.attempt_ids})
            records = tx.read(names)
            budget = records[s.name("budget")]
            attempt = records.get(s.name("attempt", address.attempt_id)) \
                if address.attempt_id else None
            if attempt and (attempt.id != address.attempt_id or budget is None
                or attempt.grant_hash != budget.grant_hash
                or attempt.policy_hash != budget.policy_hash
                or (guest and attempt.session_id != guest.scope.session_id)):
                raise _unavailable()
            history = None
            if address.inspect_session_attempts:
                history = tuple(records[s.name("attempt", aid)]
                                for run in usage.runs for aid in run.attempt_ids)
                if any(a is None for a in history):
                    raise _unavailable()
            result = change(Snapshot(budget, guest, usage, attempt, history))
            tx.limit_to(result.not_after)
            if guest:
                tx.limit_to(guest.scope.expires_at)
            if result.budget is not None:
                if budget is None:
                    raise _unavailable()
                tx.write(s.name("budget"), "budget", result.budget)
            if result.usage is not None:
                if guest is None:
                    raise _unavailable()
                s._usage(guest, result.usage)
                tx.write(s.name("usage", address.guest_key), "usage", result.usage)
            if result.attempt is not None:
                if not address.attempt_id or result.attempt.id != address.attempt_id:
                    raise _unavailable()
                tx.write(s.name("attempt", address.attempt_id), "attempt", result.attempt,
                         create=attempt is None)
            return result
        return s.run(operate)


class _Evidence:
    def __init__(self, store):
        self.store = store

    def snapshot(self, tx, key, incident):
        s = self.store
        guest, usage = s._guest(tx, key)
        names = {s.name("evidence", key, incident): "evidence",
                 s.name("environment"): "environment"}
        records = tx.read(names)
        state = s._child(records[s.name("evidence", key, incident)], guest, incident, "evidence")
        environment = records[s.name("environment")]
        if environment is None:
            raise _unavailable()
        latest = next((r for r in reversed(usage.runs) if r.incident_id == incident), None)
        proof = None
        if latest is not None:
            name = s.name("completion", latest.id)
            record = tx.read({name: "completion"})[name]
            if record is not None:
                created, updated = tx.timestamps[name]
                if created is None or updated is None or (record.run_id, record.session_id,
                    record.incident_id) != (latest.id, guest.scope.session_id, incident):
                    raise _unavailable()
                proof = StoredCompletion(record, created, updated)
        return EvidenceSnapshot(guest, state, environment, usage, proof)

    def transact(self, key, incident, change):
        s = self.store
        def operate(tx):
            snapshot = self.snapshot(tx, key, incident)
            result = change(snapshot)
            s._child(result, snapshot.guest, incident, "evidence")
            tx.limit_to(snapshot.guest.scope.expires_at)
            # Candidate/history writes can complete late, but only immutable
            # completion server metadata can make their results eligible.
            tx.write(s.name("evidence", key, incident), "evidence", result)
            return result
        return s.run(operate)

    def complete(self, key, incident, run_id, change):
        s = self.store
        def operate(tx):
            snapshot = self.snapshot(tx, key, incident)
            name = s.name("completion", run_id)
            if name not in tx.reads:
                raise _unavailable()
            receipt = change(snapshot)
            if (receipt.run_id, receipt.session_id, receipt.incident_id) != (
                    run_id, snapshot.guest.scope.session_id, incident):
                raise _unavailable()
            prior = tx.reads[name]
            if prior is not None and prior != receipt:
                raise _unavailable()
            run = next(r for r in snapshot.usage.runs if r.id == run_id)
            if (prior is None and run.completion_hash is not None) or (
                    prior is not None and run.completion_hash != receipt.digest()):
                raise _unavailable()
            tx.limit_to(snapshot.guest.scope.expires_at)
            if prior is None:
                tx.limit_to(receipt.deadline)
                tx.write(name, "completion", receipt, create=True)
                usage = replace(snapshot.usage, runs=tuple(
                    replace(r, completion_hash=receipt.digest()) if r.id == run_id else r
                    for r in snapshot.usage.runs))
                tx.write(s.name("usage", key), "usage", usage)
        s.run(operate)


class _Actions:
    def __init__(self, store):
        self.store = store

    def transact(self, key, incident, change):
        s = self.store
        def operate(tx):
            snapshot = s.evidence.snapshot(tx, key, incident)
            guest, evidence, environment = snapshot.guest, snapshot.state, snapshot.environment
            names = {s.name("actions", key, incident): "actions"}
            records = tx.read(names)
            actions = s._child(records[s.name("actions", key, incident)], guest,
                               incident, "actions")
            result = change(ActionSnapshot(guest, evidence, environment, actions,
                                          snapshot.usage, snapshot.completion))
            s._child(result, guest, incident, "actions")
            tx.limit_to(guest.scope.expires_at)
            tx.write(s.name("actions", key, incident), "actions", result)
            return result
        return s.run(operate)
