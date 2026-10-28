import joblib
import pandas as pd
import pytest

from app.services.risk_evaluator import MODEL_PATH

FEATURES = ["monthly_income", "requested_amount", "term_in_months", "age", "monthly_debt"]
STRONG = {"monthly_income": 8000, "requested_amount": 10000, "term_in_months": 24, "age": 35, "monthly_debt": 500}
WEAK = {"monthly_income": 1200, "requested_amount": 40000, "term_in_months": 60, "age": 22, "monthly_debt": 1000}


@pytest.fixture(scope="module")
def model():
    return joblib.load(MODEL_PATH)


def test_the_trained_model_ships_with_the_repo():
    assert MODEL_PATH.exists()


def test_model_expects_the_features_the_service_sends(model):
    assert list(model.feature_names_in_) == FEATURES
    # The service reads column 1 as the approval probability
    assert list(model.classes_) == [0, 1]


def test_model_returns_valid_probabilities(model):
    proba = model.predict_proba(pd.DataFrame([STRONG, WEAK]))
    assert proba.shape == (2, 2)
    assert ((proba >= 0) & (proba <= 1)).all()
    assert proba.sum(axis=1) == pytest.approx([1, 1])


def test_model_is_deterministic(model):
    X = pd.DataFrame([STRONG])
    assert (model.predict_proba(X) == model.predict_proba(X)).all()


def test_model_ranks_a_strong_profile_above_a_weak_one(model):
    approval = model.predict_proba(pd.DataFrame([STRONG, WEAK]))[:, 1]
    assert approval[0] > approval[1]
