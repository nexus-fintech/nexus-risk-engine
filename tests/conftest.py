import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints import risk
from app.main import app
from tests.fakes import FakeModel


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def payload():
    return {
        "client_id": 1,
        "age": 35,
        "monthly_income": 8000,
        "monthly_debt": 500,
        "requested_amount": 10000,
        "term_in_months": 24,
    }


@pytest.fixture
def with_probability(monkeypatch):
    """Swaps the loaded model for one that returns the given approval probability."""
    def _apply(probability: float):
        monkeypatch.setattr(risk.risk_service, "model", FakeModel(probability))
    return _apply
