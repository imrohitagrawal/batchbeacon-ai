"""Explicit owned historical source replay. No fetch, model or registry writes."""

from typing import Annotated

from pydantic import Field

from batchbeacon.contracts import Digest, Nonempty, Record
from batchbeacon.evidence_service import canonical, replace
from batchbeacon.guest_service import GuestDenied, RequestKey
from batchbeacon.source_state import SelectionReceipt, SourceSelection


class SourceCommand(Record):
    catalog_hash: Digest
    choice: Nonempty
    expected_revision: Annotated[int, Field(ge=0)]


class StartSourceReview(Record):
    catalog_hash: Digest
    session_reference: Digest


class SourceService:
    def __init__(self, evidence, stores):
        if stores.evidence is not evidence.store or stores.source_runtime is None:
            raise ValueError("explicit_owned_source_reader_required")
        self.evidence, self.guest, self.stores = evidence, evidence.guest, stores

    @staticmethod
    def _keys(key):
        return (
            canonical({"key": key, "purpose": "source_incident"}),
            canonical({"key": key, "purpose": "original_selection"}),
        )

    def _catalog(self, registry):
        catalog = registry.catalog
        if catalog.update is None:
            raise GuestDenied(503, "source_update_not_configured")
        return catalog

    def _view(self, state, registry, request_key=None):
        catalog = self._catalog(registry)
        selection = state.source_selection
        receipt = (
            next((r for r in selection.receipts if r.key == request_key), None)
            if selection and request_key
            else None
        )
        if request_key is not None and receipt is None:
            raise GuestDenied(404, "source_operation_not_recorded")

        def choice(key):
            env = next(c.environment for c in catalog.choices if c.key == key)
            return {
                "choice": key,
                "notices": [
                    n.model_dump(
                        mode="json",
                        include={
                            "authority",
                            "dependency",
                            "published_at",
                            "jurisdictions",
                            "final_url",
                        },
                    )
                    for n in env.notices
                ],
            }

        return {
            "incident_id": state.incident_id,
            "catalog_hash": catalog.digest(),
            "selection_revision": selection.revision if selection else 0,
            "selected_choice": selection.choice if selection else catalog.default_choice,
            "original": choice(catalog.original_choice),
            "update": choice(catalog.update_choice),
            "added_jurisdictions": catalog.update.added_jurisdictions,
            "removed_jurisdictions": catalog.update.removed_jurisdictions,
            "review_only": True,
            "can_replay": bool(
                self.stores.source_runtime.replay_enabled
                and selection
                and selection.choice == catalog.original_choice
            ),
            "operation_revision": receipt.revision if receipt else None,
            "operation_recorded": receipt is not None,
        }

    def read(self, capability, incident_id, request_key=None):
        self.guest.incident(capability, incident_id)
        key = self.guest._key(capability)

        def read(tx):
            snapshot = self.stores.evidence.snapshot(tx, key, incident_id)
            state = self.evidence._check(snapshot, key, incident_id)
            registry = self.stores.source_registry(tx)
            tx.limit_to(snapshot.guest.scope.expires_at)
            return self._view(state, registry, request_key)

        value = self.guest._storage(lambda: self.stores.run(read))
        self.guest.resolve(capability)
        return value

    def select(self, capability, incident_id, request_key: RequestKey, command: SourceCommand):
        if not self.stores.source_runtime.replay_enabled:
            raise GuestDenied(403, "source_replay_inactive")
        self.guest.incident(capability, incident_id)
        key, now = self.guest._key(capability), self.guest._now()
        payload = canonical(
            {
                "command": command.model_dump(mode="json"),
                "source_runtime_hash": self.stores.source_runtime.digest(),
            }
        )

        def change(tx):
            snapshot = self.stores.evidence.snapshot(tx, key, incident_id)
            state = self.evidence._check(snapshot, key, incident_id)
            catalog = self._catalog(self.stores.source_registry(tx))
            if command.catalog_hash != catalog.digest():
                raise GuestDenied(409, "source_catalog_changed")
            old = state.source_selection
            prior = next((r for r in old.receipts if r.key == request_key), None) if old else None
            if prior:
                if prior.payload_hash != payload:
                    raise GuestDenied(409, "source_request_conflict")
                return state
            if old and len(old.receipts) >= self.stores.source_runtime.max_selection_receipts:
                raise GuestDenied(429, "source_receipt_limit")
            alias = bool(
                old
                and old.choice == command.choice
                and any(
                    r.revision == old.revision and r.payload_hash == payload for r in old.receipts
                )
            )
            revision = old.revision if old else 0
            if not alias:
                if command.expected_revision != revision:
                    raise GuestDenied(409, "source_selection_changed")
                counter = next(i for i in snapshot.usage.incidents if i.incident_id == incident_id)
                fresh = (
                    old is None
                    and not state.extractions
                    and not state.observations
                    and not state.results
                    and counter.acquisitions == 0
                    and not counter.verifications
                )
                forward = old is not None and old.choice == catalog.original_choice
                if not (
                    fresh
                    and command.choice == catalog.original_choice
                    or forward
                    and command.choice == catalog.update_choice
                ):
                    raise GuestDenied(409, "source_forward_replay_only")
                revision += 1
            environment = next(
                (c.environment for c in catalog.choices if c.key == command.choice), None
            )
            if environment is None:
                raise GuestDenied(422, "source_choice_unavailable")
            receipt = SelectionReceipt(key=request_key, payload_hash=payload, revision=revision)
            selection = SourceSelection(
                catalog_hash=catalog.digest(),
                choice=command.choice,
                environment_hash=environment.digest(),
                revision=revision,
                selected_at=old.selected_at if alias else now,
                receipts=(*(old.receipts if old else ()), receipt),
            )
            updated = self.evidence._limits(
                replace(
                    state,
                    source_selection=selection,
                    active_result=state.active_result if alias else None,
                )
            )
            tx.limit_to(snapshot.guest.scope.expires_at)
            tx.write(self.stores.name("evidence", key, incident_id), "evidence", updated)
            return updated

        self.guest._storage(lambda: self.stores.run(change))
        self.guest.resolve(capability)
        return self.read(capability, incident_id, request_key)

    @staticmethod
    def session_reference(session):
        return canonical(
            {
                "session": session.scope.session_id,
                "expires_at": session.scope.expires_at.isoformat(),
            }
        )

    def context(self, capability):
        session = self.guest.resolve(capability)
        catalog = self.guest._storage(
            lambda: self.stores.run(lambda tx: self._catalog(self.stores.source_registry(tx)))
        )
        self.guest.resolve(capability)
        return {
            "catalog_hash": catalog.digest(),
            "session_reference": self.session_reference(session),
            "replay_enabled": self.stores.source_runtime.replay_enabled,
            "retrieval_times_recorded": all(
                n.retrieved_at is not None
                for c in catalog.choices
                if c.key in (catalog.original_choice, catalog.update_choice)
                for n in c.environment.notices
            ),
            "can_start": self.stores.source_runtime.replay_enabled
            and len(session.incidents) < self.guest.policy.retail.max_incidents,
            "original_choice": catalog.original_choice,
            "update_choice": catalog.update_choice,
            "added_jurisdictions": catalog.update.added_jurisdictions,
            "original": catalog.update.original.model_dump(mode="json"),
            "update": catalog.update.update.model_dump(mode="json"),
            "review_only": True,
        }

    def start(self, capability, key: RequestKey, command: StartSourceReview):
        if not self.stores.source_runtime.replay_enabled:
            raise GuestDenied(403, "source_replay_inactive")
        session = self.guest.resolve(capability)
        if command.session_reference != self.session_reference(session):
            raise GuestDenied(409, "source_review_owner_changed")
        catalog = self.guest._storage(
            lambda: self.stores.run(lambda tx: self._catalog(self.stores.source_registry(tx)))
        )
        if command.catalog_hash != catalog.digest():
            raise GuestDenied(409, "source_catalog_changed")
        incident_key, selection_key = self._keys(key)
        incident = self.guest.create_incident(capability, incident_key)
        try:
            return self.select(
                capability,
                incident.id,
                selection_key,
                SourceCommand(
                    catalog_hash=catalog.digest(),
                    choice=catalog.original_choice,
                    expected_revision=0,
                ),
            )
        except GuestDenied as error:
            if error.status == 401:
                raise
            raise GuestDenied(503, "source_selection_unconfirmed") from error

    def reconcile_start(self, capability, key: RequestKey):
        session = self.guest.resolve(capability)
        incident_key, selection_key = self._keys(key)
        incident = next((i for i in session.incidents if i.request_key == incident_key), None)
        if incident is None:
            raise GuestDenied(404, "source_review_not_recorded")
        view = self.read(capability, incident.id)
        try:
            recorded = self.read(capability, incident.id, selection_key)
        except GuestDenied as error:
            if error.status != 404:
                raise
            return view | {"start_state": "INVESTIGATION_CREATED"}
        return recorded | {"start_state": "SOURCE_SELECTED"}
