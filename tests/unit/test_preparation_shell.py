from fastapi.testclient import TestClient

from batchbeacon.app import app


def test_health_does_not_claim_model_or_product_readiness():
    with TestClient(app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {
            "process": "ok", "product": "not_ready", "mode": "local_preparation"
        }


def test_prototype_is_labelled_and_no_action_endpoint_exists():
    with TestClient(app) as client:
        response = client.get("/prototype/")
        assert response.status_code == 200
        assert "Visual prototype" in response.text
        assert client.post("/api/actions", json={"approve": True}).status_code == 404
