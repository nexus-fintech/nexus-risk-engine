class FakeModel:
    """Stands in for the Random Forest: always returns the same approval probability."""

    def __init__(self, approval_probability: float):
        self.approval_probability = approval_probability

    def predict_proba(self, X):
        return [[1 - self.approval_probability, self.approval_probability]]
