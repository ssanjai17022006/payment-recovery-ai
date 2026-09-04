"""
Recovery Simulator
------------------
Simulates a bounded payment recovery workflow.

IMPORTANT:
This module does NOT execute real payments.
It is a deterministic simulation for hackathon demonstration.

Workflow:
    AUTOMATE       -> simulated recovery attempt -> SUCCESS / FAILURE
    REVIEW         -> PENDING human review
    DO_NOT_RECOVER -> NOT_ATTEMPTED / STOPPED
"""

import hashlib


def _deterministic_score(transaction_id: str) -> float:
    """
    Generate a deterministic value between 0 and 1.

    The same transaction_id always produces the same value.
    This makes demo results reproducible.
    """
    digest = hashlib.sha256(
        str(transaction_id).encode("utf-8")
    ).hexdigest()

    integer_value = int(digest[:16], 16)

    return integer_value / float(16**16 - 1)


def simulate_recovery(
    transaction_id,
    amount,
    recovery_probability,
    decision,
    reason=None,
):
    """
    Simulate the recovery outcome based on the AI recovery probability
    and the bounded policy decision.

    Parameters
    ----------
    transaction_id : str
        Unique transaction identifier.

    amount : float
        Transaction amount.

    recovery_probability : float
        ML-predicted probability of recovery.

    decision : str
        AUTOMATE, REVIEW, or DO_NOT_RECOVER.

    reason : str, optional
        Policy reason for the decision.

    Returns
    -------
    dict
        Recovery simulation result.
    """

    amount = float(amount)
    recovery_probability = float(recovery_probability)

    # Safety: probability must remain within [0, 1].
    recovery_probability = max(
        0.0,
        min(1.0, recovery_probability)
    )

    # ---------------------------------------------------------
    # AUTOMATE
    # ---------------------------------------------------------
    if decision == "AUTOMATE":

        score = _deterministic_score(transaction_id)

        if score < recovery_probability:
            return {
                "recovery_attempted": True,
                "recovery_result": "success",
                "recovered_amount": round(amount, 2),
                "stopped_reason": "",
                "simulation_score": round(score, 6),
            }

        return {
            "recovery_attempted": True,
            "recovery_result": "failure",
            "recovered_amount": 0.0,
            "stopped_reason": "",
            "simulation_score": round(score, 6),
        }

    # ---------------------------------------------------------
    # REVIEW
    # ---------------------------------------------------------
    if decision == "REVIEW":

        return {
            "recovery_attempted": False,
            "recovery_result": "pending",
            "recovered_amount": 0.0,
            "stopped_reason": reason or "Manual review required",
            "simulation_score": None,
        }

    # ---------------------------------------------------------
    # DO_NOT_RECOVER
    # ---------------------------------------------------------
    if decision == "DO_NOT_RECOVER":

        return {
            "recovery_attempted": False,
            "recovery_result": "not_attempted",
            "recovered_amount": 0.0,
            "stopped_reason": reason or "Recovery stopped by policy",
            "simulation_score": None,
        }

    # ---------------------------------------------------------
    # Invalid decision
    # ---------------------------------------------------------
    raise ValueError(
        f"Invalid recovery decision: {decision}"
    )