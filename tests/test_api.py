from app.api.v1.endpoints import risk
from app.core.config import settings

URL = "/api/v1/evaluate-risk"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": settings.PROJECT_NAME}


def test_evaluates_with_the_trained_model(client, payload):
    response = client.post(URL, json=payload)
    assert response.status_code == 200
    body = response.json()
    assert 300 <= body["score"] <= 850
    assert body["is_approved"] == (body["score"] >= settings.MIN_SCORE_APPROVE)
    expected_level = "LOW" if body["score"] >= 750 else "MEDIUM" if body["score"] >= 650 else "HIGH"
    assert body["risk_level"] == expected_level
    assert body["max_approved_amount"] == (payload["monthly_income"] * 10 if body["is_approved"] else 0.0)


def test_response_follows_the_model_decision(client, payload, with_probability):
    with_probability(0.9)
    assert client.post(URL, json=payload).json() == {
        "score": 795, "risk_level": "LOW", "is_approved": True,
        "suggested_interest_rate": 0.13, "max_approved_amount": 80000.0,
    }
    with_probability(0.2)
    assert client.post(URL, json=payload).json() == {
        "score": 410, "risk_level": "HIGH", "is_approved": False,
        "suggested_interest_rate": 0.2, "max_approved_amount": 0.0,
    }


def test_invalid_payload_is_rejected_with_422(client, payload):
    assert client.post(URL, json={**payload, "age": 15}).status_code == 422


def test_missing_model_answers_503_without_internal_details(client, payload, monkeypatch):
    monkeypatch.setattr(risk.risk_service, "model", None)
    response = client.post(URL, json=payload)
    assert response.status_code == 503
    assert response.json() == {"detail": "Risk model is not available. Try again later."}


def test_unexpected_error_answers_500_without_internal_details(client, payload, monkeypatch):
    def fail(_request):
        raise ValueError("internal detail")

    monkeypatch.setattr(risk.risk_service, "evaluate", fail)
    response = client.post(URL, json=payload)
    assert response.status_code == 500
    assert "internal detail" not in response.text
