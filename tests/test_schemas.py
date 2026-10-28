import pytest
from pydantic import ValidationError

from app.schemas.credit_request import CreditRequest

VALID = dict(client_id=1, age=35, monthly_income=8000, monthly_debt=500, requested_amount=10000, term_in_months=24)


@pytest.mark.parametrize("field, value", [
    ("client_id", 0),
    ("age", 17),
    ("age", 101),
    ("monthly_income", 0),
    ("monthly_debt", -1),
    ("requested_amount", 0),
    ("term_in_months", 0),
    ("term_in_months", 61),
])
def test_rejects_out_of_range_values(field, value):
    with pytest.raises(ValidationError):
        CreditRequest(**{**VALID, field: value})


@pytest.mark.parametrize("field, value", [
    ("age", 18), ("age", 100), ("monthly_debt", 0), ("term_in_months", 1), ("term_in_months", 60),
])
def test_accepts_the_edges(field, value):
    assert getattr(CreditRequest(**{**VALID, field: value}), field) == value


def test_rejects_a_missing_field():
    data = dict(VALID)
    del data["age"]
    with pytest.raises(ValidationError):
        CreditRequest(**data)


def test_debt_to_income_ratio():
    assert CreditRequest(**VALID).debt_to_income_ratio == pytest.approx(500 / 8000)
