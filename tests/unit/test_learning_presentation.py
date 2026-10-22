"""Owned eligibility projection agrees with the existing mutation boundaries."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from batchbeacon.extraction_api import ExtractionHTTPPolicy
from batchbeacon.guest_service import GuestDenied
from batchbeacon.retail_contracts import FeedbackDetail
from batchbeacon.retail_refresh import RefreshPolicy, RetailRefresh
from batchbeacon.workbench import create_workbench_test_app
from tests.unit.domain_fixtures import known
from tests.unit.test_learning_service import candidate
from tests.unit.test_learning_service import env as env  # noqa: F401
from tests.unit.test_learning_service import learning as learning  # noqa: F401
from tests.unit.test_learning_service import setup as setup  # noqa: F401


def complete_lot(c):
    before = c[7].read_evidence(c[2], c[1].incident_id)
    c[7].correct(
        c[2],
        c[1].incident_id,
        "complete-lot",
        before.observation.revision,
        "LOT",
        known("232511", evidence=before.observation.captures[0]),
    )
    binding = c[7].verification_binding(c[2], c[1].incident_id)
    c[0].shared.reserve_verification(c[6].capability_hash, c[1].incident_id, "verify-lot", binding)
    c[7].publish_verification(c[2], c[1].incident_id, "verify-lot", binding)


def test_complete_label_cannot_offer_guidance_or_unsupported_candidate(learning):
    c, service = learning
    complete_lot(c)
    _, context = service.presentation(c[2], c[1].incident_id)
    assert not context["actions"]["request"]["available"]
    assert "no missing required fields" in context["summary"]
    with pytest.raises(GuestDenied, match="guidance_not_available"):
        service.guidance(c[2], c[1].incident_id, "blocked-guidance")
    feedback = service.feedback(
        c[2], c[1].incident_id, "unsupported-feedback", FeedbackDetail.LOT_CODE_UNCLEAR
    )
    _, context = service.presentation(c[2], c[1].incident_id)
    assert not context["actions"]["candidate"]["available"]
    assert context["feedback_id"] == feedback.id
    with pytest.raises(GuestDenied, match="no_safe_candidate"):
        service.candidate(c[2], "blocked-candidate", (feedback.id,))
    assert len(c[4]) == 2


def test_eligibility_tracks_supported_chain_and_stale_evidence(learning):
    c, service = learning
    _, initial = service.presentation(c[2], c[1].incident_id)
    assert initial["actions"]["request"]["available"]
    assert not initial["actions"]["candidate"]["available"]
    _, _, proposal = candidate(learning)
    _, proposed = service.presentation(c[2], c[1].incident_id)
    assert proposed["candidate_id"] == proposal.id
    assert proposed["actions"]["evaluate"]["available"]
    assert not proposed["actions"]["activate"]["available"]
    evaluation = service.evaluate(c[2], "evaluate", proposal.id)
    _, evaluated = service.presentation(c[2], c[1].incident_id)
    assert evaluated["evaluation_id"] == evaluation.id
    assert evaluated["actions"]["activate"]["available"]
    complete_lot(c)
    _, stale = service.presentation(c[2], c[1].incident_id)
    assert not stale["actions"]["activate"]["available"]
    assert not stale["actions"]["evaluate"]["available"]
    assert not stale["actions"]["candidate"]["available"]


def test_projection_does_not_reveal_foreign_incident_or_invent_capacity(learning):
    c, service = learning
    other, _ = c[3][2].issue()
    with pytest.raises(GuestDenied):
        service.presentation(other, c[1].incident_id)
    _, empty = service.presentation(c[2])
    assert empty["incident_id"] is None
    assert not any(action["available"] for action in empty["actions"].values())
    service.capability = None
    _, unavailable = service.presentation(c[2], c[1].incident_id)
    assert not unavailable["actions"]["request"]["available"]
    c[3][5][0] = c[6].scope.expires_at
    with pytest.raises(GuestDenied):
        service.presentation(c[2], c[1].incident_id)


def test_http_context_is_owned_and_refresh_is_admitted_once(learning):
    c, service = learning
    stores = c[3][0]
    app = create_workbench_test_app(
        c[0],
        c[8],
        RetailRefresh(stores.retail, RefreshPolicy()),
        ExtractionHTTPPolicy(),
        learning=service,
    )
    client = TestClient(app, base_url=c[3][2].policy.origin)
    client.cookies.set(c[3][2].policy.cookie_name, c[2])
    response = client.get(
        "/api/learning",
        params={"incident": c[1].incident_id},
        headers={"Idempotency-Key": "read-context"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["context"]["actions"]["request"]["available"]
    assert len(service.read(c[2]).refresh_keys) == 1
    c[3][5][0] += timedelta(seconds=service.policy.refresh_interval_seconds)
    other, _ = c[3][2].issue()
    client.cookies.set(c[3][2].policy.cookie_name, other)
    denied = client.get(
        "/api/learning",
        params={"incident": c[1].incident_id},
        headers={"Idempotency-Key": "foreign-context"},
    )
    assert denied.status_code == 404
    assert c[1].incident_id not in denied.text
    assert len(c[4]) == 2
