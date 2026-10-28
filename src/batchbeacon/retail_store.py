"""Atomic summary production and coherent, history-free Firestore queue reads.

Only the injected server service graph can enroll a new shop. Its guest envelope
binds the projection policy, so a legacy/unconfigured writer fails closed.
"""

from datetime import timedelta
from typing import Literal

from batchbeacon.acquisition import AcquisitionCompletion, StoredCompletion
from batchbeacon.action_service import ActionSnapshot
from batchbeacon.contracts import Record
from batchbeacon.evidence_service import replace
from batchbeacon.guest_service import GuestDenied
from batchbeacon.retail_projection import (
    CapabilityObservation,
    CapabilityReason,
    CapabilityState,
    CompletionWitness,
    IncidentProjection,
    MaterialUpdate,
    QueueFilter,
    material_state_hash,
    usage_basis,
)


def unavailable():
    return GuestDenied(503, "retail_snapshot_unavailable")


class StoredProjection(Record):
    version: Literal["stored-retail-1"] = "stored-retail-1"
    projection: IncidentProjection
    completion: AcquisitionCompletion | None


class RetailPersistence:
    def __init__(self, store, projector):
        if (projector.guest.repository is not store.guests
                or projector.evidence.store is not store.evidence
                or projector.actions.store is not store.actions
                or projector.guest.policy != store.guest_policy
                or projector.evidence.policy != store.evidence_policy
                or projector.actions.policy != store.action_policy):
            raise ValueError("retail requires the same owned persistence service graph")
        self.store, self.projector = store, projector

    def _check(self, stored, guest, usage, incident):
        p = self.projector
        if stored is None:
            raise unavailable()
        p._bound(stored, p.policy.projection_bytes)
        row = stored.projection
        if (row.session_id != guest.scope.session_id or row.incident_id != incident
                or row.policy_hash != p.configuration_hash
                or row.usage_basis_hash != usage_basis(usage, incident)
                or row.acquisition.completion is not None):
            raise unavailable()
        receipt = stored.completion
        if (receipt is None) != (row.run is None or row.run.completion_hash is None):
            raise unavailable()
        if receipt is not None and (
                (receipt.run_id, receipt.session_id, receipt.incident_id,
                 receipt.binding_hash, receipt.deadline, receipt.digest()) !=
                (row.run.id, row.session_id, row.incident_id, row.run.binding_hash,
                 row.run.deadline, row.run.completion_hash)):
            raise unavailable()
        return row

    def finalize(self, tx):
        """Validate complete domain overlays before appending derived writes.

        All reads are performed before the sole network Commit. Callback reads
        remain prohibited after local staging; only this finalizer reads originals.
        """
        if not tx.staged:
            return
        s, p = self.store, self.projector
        summaries = []

        def effective(name):
            return tx.staged[name][1] if name in tx.staged else tx.reads[name]

        for key in tx.addresses:
            gn, un = s.name("guest", key), s.name("usage", key)
            guest, usage = effective(gn), effective(un)
            old_guest, old_usage = tx.reads[gn], tx.reads[un]
            p.guest._live(guest, key)
            s._usage(guest, usage)
            tx.limit_to(guest.scope.expires_at)
            prior_incidents = {i.id: i for i in old_guest.incidents} if old_guest else {}
            affected = tuple(i.id for i in guest.incidents if (
                prior_incidents.get(i.id) != i
                or old_usage is None
                or i.id not in prior_incidents
                or usage_basis(old_usage, i.id) != usage_basis(usage, i.id)
                or s.name("evidence", key, i.id) in tx.staged
                or s.name("actions", key, i.id) in tx.staged))
            if not affected:
                continue
            names = {s.name("environment"): "environment"}
            for incident in affected:
                for kind in ("retail", "evidence", "actions"):
                    names[s.name(kind, key, incident)] = kind
            tx._read_originals(names)
            environment = effective(s.name("environment"))
            if environment is None:
                raise unavailable()
            runs = {i: next((r for r in reversed(usage.runs) if r.incident_id == i), None)
                    for i in affected}
            tx._read_originals({s.name("completion", r.id): "completion"
                                for r in runs.values() if r is not None})
            for incident in affected:
                en, an, rn = (s.name(k, key, incident)
                              for k in ("evidence", "actions", "retail"))
                evidence = s._child(effective(en), guest, incident, "evidence")
                actions = s._child(effective(an), guest, incident, "actions")
                run, proof, receipt = runs[incident], None, None
                if run is not None:
                    cn = s.name("completion", run.id)
                    receipt = effective(cn)
                    if receipt is not None and cn not in tx.staged:
                        created, updated = tx.timestamps[cn]
                        if created is None or updated is None:
                            raise unavailable()
                        proof = StoredCompletion(receipt, created, updated)
                selected_environment = s.source_environment(
                    tx, environment, evidence.source_selection, finalize=True)
                snapshot = ActionSnapshot(guest, evidence, selected_environment, actions,
                                          usage, proof)
                previous = tx.reads[rn]
                if incident in prior_incidents:
                    old = self._check(previous, old_guest, old_usage, incident)
                else:
                    if previous is not None:
                        raise unavailable()
                    old = None
                semantic = material_state_hash(snapshot)
                if old is not None and old.material.semantic_state_hash == semantic:
                    material = old.material
                else:
                    material = MaterialUpdate(changed_at=p.guest._now(),
                        sequence=old.material.sequence + 1 if old else 1,
                        semantic_state_hash=semantic, reference="owned-incident-transition")
                projection = p._reduce(key, snapshot, material=material,
                                       pending_completion=receipt if proof is None else None)
                # Completion metadata is always re-read with the queue snapshot.
                projection = replace(projection, acquisition=replace(
                    projection.acquisition, completion=None))
                stored = StoredProjection(projection=projection, completion=receipt)
                self._check(stored, guest, usage, incident)
                summaries.append((rn, stored, previous is None))
        # No partial projection is staged if any affected incident failed validation.
        for name, value, create in summaries:
            tx.write(name, "retail", value, create=create)

    def read(self, capability, *, selected_filter=QueueFilter.ALL, new_verification=None,
             not_after=None):
        """One coherent bounded shop read; no model, objects, repair or history read."""
        s, p = self.store, self.projector
        key = p.guest._key(capability)

        def read(tx):
            guest, usage = s._guest(tx, key)
            p.guest._live(guest, key)
            tx.limit_to(guest.scope.expires_at)
            tx.limit_to(not_after)
            if len(guest.incidents) > min(p.guest.policy.retail.max_incidents,
                                         p.guest.policy.retail.max_summary_rows):
                raise unavailable()
            names = {s.name("environment"): "environment"}
            names.update({s.name("retail", key, i.id): "retail" for i in guest.incidents})
            records = tx.read(names)
            environment = records[s.name("environment")]
            if environment is None:
                raise unavailable()
            stored = tuple(records[s.name("retail", key, i.id)] for i in guest.incidents)
            rows = tuple(self._check(record, guest, usage, incident.id)
                         for record, incident in zip(stored, guest.incidents, strict=True))
            completion_names = {s.name("completion", row.run.id): "completion"
                                for row in rows if row.run and row.run.completion_hash}
            completions = tx.read(completion_names)
            prepared = []
            for value, row in zip(stored, rows, strict=True):
                if value.completion is not None:
                    name = s.name("completion", value.completion.run_id)
                    if completions[name] != value.completion:
                        raise unavailable()
                    created, updated = tx.timestamps[name]
                    if created is None or updated is None:
                        raise unavailable()
                    row = replace(row, acquisition=replace(row.acquisition,
                        completion=CompletionWitness(record=value.completion,
                            created_at=created, updated_at=updated)))
                # This private seam follows namespace/owner/config/usage checks
                # against exclusively server-written summary documents.
                prepared.append(p._seal(row))
            environments = {row.incident_id: s.source_environment(
                tx, environment, row.source_selection) for row in rows}
            environment = s.source_environment(tx, environment, None)
            return guest, usage, tuple(prepared), environment, environments

        guest, usage, prepared, environment, environments = p.guest._storage(
            lambda: s.run(read, not_after=not_after))
        # Recheck expiry and time-derived currentness after commit acknowledgement.
        now = p.guest._now()
        if not_after is not None and now >= not_after:
            raise GuestDenied(429, "refresh_lease_elapsed")
        saved = CapabilityObservation(session_id=guest.scope.session_id,
            capability="SAVED_EVIDENCE", state=CapabilityState.AVAILABLE,
            reason=CapabilityReason.OBSERVED, observed_at=now,
            valid_until=now + timedelta(seconds=p.policy.capability_validity_seconds))
        return p.view(key, guest, usage, prepared, environment,
                      selected_filter=selected_filter, saved_evidence=saved,
                      new_verification=new_verification, environments=environments)
