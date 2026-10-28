import pandas as pd
import joblib
from pathlib import Path
from app.schemas.credit_request import CreditRequest
from app.schemas.credit_score import CreditScore, RiskLevel
from app.core.config import settings

# The .pkl sits at the project root: next to the Dockerfile locally, /app inside the container
MODEL_PATH = Path(__file__).resolve().parents[2] / "nexus_risk_model.pkl"

class ModelUnavailableError(RuntimeError):
    """The trained model is not loaded, so no evaluation can be made."""

class RiskEvaluatorService:
    """
    Domain service responsible for calculating credit scores using a pre-trained 
    Random Forest Classifier. It performs inference on client data to determine 
    loan eligibility.
    """

    def __init__(self, model_path: Path = MODEL_PATH):
        # 1. Model Loading (Implicit Singleton)
        # Resolved from this file, so it works from any working directory
        if model_path.exists():
            self.model = joblib.load(model_path)
            print(f"AI Model loaded successfully from: {model_path}")
        else:
            # Security fallback in case build context failed
            print(f"warning: {model_path} not found. Service will fail on evaluation.")
            self.model = None

    def evaluate(self, request: CreditRequest) -> CreditScore:
        # Operational Safety Check
        if self.model is None:
            raise ModelUnavailableError("AI Model is not initialized or found.")

        # 2. Data Vectorization (Feature Mapping)
        # Keys (Left): Must match Training Features exactly (nexus_credit_data.xlsx headers)
        # Values (Right): Must match Pydantic Input Schema (snake_case)
        input_data = pd.DataFrame([{
            'monthly_income':   request.monthly_income,
            'requested_amount': request.requested_amount,
            'term_in_months':   request.term_in_months,
            'age':              request.age,
            'monthly_debt':     request.monthly_debt
        }])

        # 3. Inference (Prediction)
        # predict_proba returns [[prob_reject, prob_approve]]
        # We extract index 1 (probability of approval)
        approval_probability = self.model.predict_proba(input_data)[0][1]

        # 4. Score Transformation (Mapping)
        # Convert probability (e.g., 0.72) to simulated FICO scale (300 - 850)
        # Formula: Base 300 + (Probability * 550 possible points)
        score = int(300 + (approval_probability * 550))

        # 5. Risk Classification & Decision
        risk_level = self._determine_risk_level(score)
        
        # Approval Threshold (defined in settings, e.g., 650)
        is_approved = score >= settings.MIN_SCORE_APPROVE

        # 6. Financial Calculations (Business Logic)
        # Calculate max capacity based on income if approved
        max_amount = request.monthly_income * 10 if is_approved else 0.0
        
        interest_rate = self._calculate_interest_rate(score, settings.BASE_INTEREST_RATE)

        return CreditScore(
            score=score,
            risk_level=risk_level,
            is_approved=is_approved,
            suggested_interest_rate=interest_rate,
            max_approved_amount=round(max_amount, 2)
        )

    def _determine_risk_level(self, score: int) -> RiskLevel:
        if score >= 750: return RiskLevel.LOW
        elif score >= 650: return RiskLevel.MEDIUM
        return RiskLevel.HIGH

    def _calculate_interest_rate(self, score: int, base_rate: float) -> float:
        # Rate adjustment based on AI Score, rounded because the base rate is configurable
        # and float sums leak noise (0.10 + 0.05 = 0.15000000000000002)
        if score >= 750: rate = base_rate - 0.02
        elif score >= 650: rate = base_rate
        else: rate = base_rate + 0.05
        return round(rate, 4)