import logging

from fastapi import APIRouter, HTTPException, status
from app.schemas.credit_request import CreditRequest
from app.schemas.credit_score import CreditScore
from app.services.risk_evaluator import ModelUnavailableError, RiskEvaluatorService

logger = logging.getLogger(__name__)

router = APIRouter()
risk_service = RiskEvaluatorService()

@router.post(
    "/evaluate-risk",
    response_model=CreditScore,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Credit Risk",
    description="Analyzes a client's financial profile and determines their eligibility for a loan."
)
def evaluate_risk(request: CreditRequest):
    """
    Main endpoint for the risk engine.
    Receives client data (Income, Debt, Age) and returns a CreditScore.
    """
    try:
        result = risk_service.evaluate(request)
        return result
    except ModelUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Risk model is not available. Try again later."
        )
    except Exception:
        # The cause goes to the log, never to the client
        logger.exception("Risk evaluation failed for client %s", request.client_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing risk evaluation."
        )
