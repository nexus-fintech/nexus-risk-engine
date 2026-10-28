import pytest

from app.core.config import settings
from app.schemas.credit_request import CreditRequest
from app.schemas.credit_score import RiskLevel
from app.services.risk_evaluator import ModelUnavailableError, RiskEvaluatorService
from tests.fakes import FakeModel


def service_with(model) -> RiskEvaluatorService:
    service = RiskEvaluatorService.__new__(RiskEvaluatorService)
    service.model = model
    return service


@pytest.fixture
def credit_request(payload):
    return CreditRequest(**payload)


@pytest.mark.parametrize("probability, expected_score", [(0.0, 300), (0.5, 575), (1.0, 850)])
def test_score_maps_the_approval_probability_to_300_850(probability, expected_score, credit_request):
    assert service_with(FakeModel(probability)).evaluate(credit_request).score == expected_score


@pytest.mark.parametrize("score, level", [
    (850, RiskLevel.LOW), (750, RiskLevel.LOW),
    (749, RiskLevel.MEDIUM), (650, RiskLevel.MEDIUM),
    (649, RiskLevel.HIGH), (300, RiskLevel.HIGH),
])
def test_risk_level_thresholds(score, level):
    assert service_with(None)._determine_risk_level(score) == level


def test_approval_follows_the_configured_threshold(credit_request):
    assert settings.MIN_SCORE_APPROVE == 650
    approved = service_with(FakeModel(0.7)).evaluate(credit_request)
    rejected = service_with(FakeModel(0.6)).evaluate(credit_request)
    assert (approved.score, approved.is_approved, approved.risk_level) == (685, True, RiskLevel.MEDIUM)
    assert (rejected.score, rejected.is_approved, rejected.risk_level) == (630, False, RiskLevel.HIGH)


def test_max_amount_is_ten_monthly_incomes_only_when_approved(credit_request):
    assert service_with(FakeModel(0.9)).evaluate(credit_request).max_approved_amount == 80000.0
    assert service_with(FakeModel(0.1)).evaluate(credit_request).max_approved_amount == 0.0


@pytest.mark.parametrize("score, expected", [(800, 0.13), (700, 0.15), (600, 0.2)])
def test_interest_rate_by_risk_band(score, expected):
    assert service_with(None)._calculate_interest_rate(score, 0.15) == expected


@pytest.mark.parametrize("score, expected", [(800, 0.08), (700, 0.1), (600, 0.15)])
def test_interest_rate_has_no_float_noise_with_another_base_rate(score, expected):
    assert service_with(None)._calculate_interest_rate(score, 0.10) == expected


def test_evaluation_without_model_raises_model_unavailable(credit_request):
    with pytest.raises(ModelUnavailableError):
        service_with(None).evaluate(credit_request)


def test_missing_model_file_leaves_the_service_without_model(tmp_path):
    assert RiskEvaluatorService(model_path=tmp_path / "missing.pkl").model is None


def test_features_reach_the_model_in_training_order(credit_request):
    seen = {}

    class SpyModel(FakeModel):
        def predict_proba(self, X):
            seen["columns"] = list(X.columns)
            seen["row"] = X.iloc[0].to_dict()
            return super().predict_proba(X)

    service_with(SpyModel(0.5)).evaluate(credit_request)
    assert seen["columns"] == ["monthly_income", "requested_amount", "term_in_months", "age", "monthly_debt"]
    assert seen["row"] == {
        "monthly_income": 8000, "requested_amount": 10000, "term_in_months": 24, "age": 35, "monthly_debt": 500,
    }
