from app.schemas.credit_request import CreditRequest
from app.schemas.credit_score import CreditScore, RiskLevel
from app.core.config import settings

class RiskEvaluatorService:
    """
    Domain service responsible for calculating the credit score.
    Applies financial heuristic rules based on income, debt, and age.
    """

    def evaluate(self, request: CreditRequest) -> CreditScore:
        # 1. Base Calculation (Simulated FICO Score: 300 - 850)
        score = self._calculate_base_score(request)

        # 2. Determine Risk Level
        risk_level = self._determine_risk_level(score)

        # 3. Approval Decision
        is_approved = score >= settings.MIN_SCORE_APPROVE

        # 4. Suggested Interest Rate Calculation (Higher risk => higher rate)
        interest_rate = self._calculate_interest_rate(score, settings.BASE_INTEREST_RATE)

        # 5. Maximum Loan Amount (Based on payment capacity)
        max_amount = self._calculate_max_amount(request.monthly_income, request.monthly_debt)

        # If not approved, limit the amount to 0
        if not is_approved:
            max_amount = 0.0

        return CreditScore(
            score=score,
            risk_level=risk_level,
            is_approved=is_approved,
            suggested_interest_rate=interest_rate,
            max_approved_amount=round(max_amount, 2)
        )

    def _calculate_base_score(self, request: CreditRequest) -> int:
        """Calculates a score between 300 and 850 based on weighted rules."""
        score = 600  # Neutral base score

        # Factor 1: Debt-to-Income Ratio (DTI) – most critical
        dti = request.debt_to_income_ratio
        if dti < 0.30:
            score += 100  # Excellent capacity
        elif dti < 0.50:
            score += 50   # Acceptable
        elif dti > 0.70:
            score -= 100  # Highly indebted

        # Factor 2: Age (Implied financial stability)
        if 25 <= request.age <= 55:
            score += 50
        elif request.age < 21:
            score -= 20

        # Factor 3: High Income
        if request.monthly_income > 3000:  # Reference value in USD or local currency
            score += 50

        # Normalization (Clamp) between 300 and 850
        return max(300, min(850, score))

    def _determine_risk_level(self, score: int) -> RiskLevel:
        if score >= 750:
            return RiskLevel.LOW
        elif score >= 650:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def _calculate_interest_rate(self, score: int, base_rate: float) -> float:
        """Reduces the rate if the score is good, increases it if the score is poor."""
        if score >= 750:
            return base_rate - 0.02  # 2% discount
        elif score >= 650:
            return base_rate         # Base rate
        else:
            return base_rate + 0.05  # 5% penalty

    def _calculate_max_amount(self, income: float, debt: float) -> float:
        """
        Rule: The installment should not exceed 40% of net disposable income.
        Simplified estimation of total borrowing capacity.
        """
        disposable_income = income - debt
        return max(0.0, disposable_income * 10)  # Example: 10 times the free income
