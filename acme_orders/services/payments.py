from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class PaymentResult:
    accepted: bool
    reference: str
    message: str


def capture(payment_token: str, amount_cents: int) -> PaymentResult:
    """Deterministic stand-in for a payment provider."""
    reference = f"pay_{uuid4().hex}"
    if payment_token == "tok_declined":
        return PaymentResult(False, reference, "card declined")
    if not payment_token.startswith("tok_"):
        return PaymentResult(False, reference, "invalid payment token")
    if amount_cents <= 0:
        return PaymentResult(False, reference, "invalid payment amount")
    return PaymentResult(True, reference, "captured")


def refund(_provider_reference: str, amount_cents: int) -> str:
    if amount_cents <= 0:
        raise ValueError("refund amount must be positive")
    return f"ref_{uuid4().hex}"
