# policy/decision_engine.py
#
# Payment Recovery AI
# Policy & Risk Decision Engine
#
# Decision flow:
# Transaction
#     ↓
# ML Recovery Probability
#     ↓
# Policy / Risk Engine
#     ↓
# AUTOMATE / REVIEW / DO_NOT_RECOVER

import os
import joblib
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_FILE = os.path.join(
    "model",
    "recovery_model.joblib"
)

# Recovery probability thresholds
AUTOMATE_THRESHOLD = 0.70
REVIEW_THRESHOLD = 0.40

# Risk / policy thresholds
HIGH_VALUE_THRESHOLD = 7500
MAX_RETRY_COUNT = 3


# ============================================================
# LOAD ML MODEL
# ============================================================

def load_model():
    """
    Load the trained recovery prediction model.
    """

    if not os.path.exists(MODEL_FILE):
        raise FileNotFoundError(
            f"Model file not found: {MODEL_FILE}"
        )

    return joblib.load(MODEL_FILE)


# ============================================================
# ML PREDICTION
# ============================================================

def predict_recovery(transaction):
    """
    Predict recovery probability using the trained ML model.

    Returns:
        float: Probability that the failed payment can be recovered.
    """

    model = load_model()

    input_data = pd.DataFrame([{
        "payment_method": transaction["payment_method"],
        "bank": transaction["bank"],
        "failure_code": transaction["failure_code"],
        "failure_stage": transaction["failure_stage"],
        "amount": float(transaction["amount"]),
        "retry_count": int(transaction["retry_count"]),
        "is_recurring": bool(transaction["is_recurring"])
    }])

    probabilities = model.predict_proba(input_data)

    # Find probability corresponding to the "recovered" class
    classes = list(model.classes_)

    if "recovered" not in classes:
        raise ValueError(
            "The trained model does not contain "
            "'recovered' as a target class."
        )

    recovered_index = classes.index("recovered")

    recovery_probability = probabilities[0][recovered_index]

    return float(recovery_probability)


# ============================================================
# POLICY / RISK DECISION
# ============================================================

def make_decision(transaction, recovery_probability):
    """
    Apply deterministic policy rules to the ML probability.

    Policy priority:

    1. CARD_BLOCKED
    2. MAX_RETRY_LIMIT
    3. BANK_TIMEOUT
    4. HIGH_VALUE_TRANSACTION
    5. HIGH_RECOVERY_PROBABILITY
    6. MEDIUM_RECOVERY_PROBABILITY
    7. LOW_RECOVERY_PROBABILITY

    Returns:
        dict containing:
            decision
            risk_level
            policy_rule
            reason
            explanation
    """

    failure_code = str(
        transaction.get("failure_code", "")
    ).upper()

    retry_count = int(
        transaction.get("retry_count", 0)
    )

    amount = float(
        transaction.get("amount", 0)
    )

    recovery_probability = float(
        recovery_probability
    )

    # ========================================================
    # RULE 1 — CARD BLOCKED
    # ========================================================

    if failure_code == "CARD_BLOCKED":
        return {
            "decision": "DO_NOT_RECOVER",
            "risk_level": "HIGH",
            "policy_rule": "CARD_BLOCKED",
            "reason": (
                "Card is blocked and automatic recovery "
                "is not permitted."
            ),
            "explanation": [
                "Card blocked condition detected.",
                "Automatic recovery could repeatedly fail.",
                "Further recovery attempts are unsafe.",
                "Recovery action is blocked."
            ]
        }

    # ========================================================
    # RULE 2 — MAXIMUM RETRY LIMIT
    # ========================================================

    if retry_count >= MAX_RETRY_COUNT:
        return {
            "decision": "DO_NOT_RECOVER",
            "risk_level": "HIGH",
            "policy_rule": "MAX_RETRY_LIMIT",
            "reason": (
                "Maximum retry limit reached. "
                "Further automatic recovery attempts are blocked."
            ),
            "explanation": [
                "Maximum retry limit has been reached.",
                "Additional automatic retries could increase payment risk.",
                "Recovery action is blocked."
            ]
        }

    # ========================================================
    # RULE 3 — BANK TIMEOUT
    # ========================================================

    if failure_code == "BANK_TIMEOUT":
        return {
            "decision": "REVIEW",
            "risk_level": "HIGH",
            "policy_rule": "BANK_TIMEOUT",
            "reason": (
                "Bank timeout requires review because "
                "the payment may have been processed "
                "without confirmation."
            ),
            "explanation": [
                "Bank timeout occurred.",
                "Payment processing status is uncertain.",
                "The bank may have processed the payment.",
                "Automatic retry could create a duplicate charge.",
                "Human review is required before recovery."
            ]
        }

    # ========================================================
    # RULE 4 — HIGH VALUE TRANSACTION
    # ========================================================

    if amount >= HIGH_VALUE_THRESHOLD:
        return {
            "decision": "REVIEW",
            "risk_level": "HIGH",
            "policy_rule": "HIGH_VALUE_TRANSACTION",
            "reason": (
                f"Transaction amount is high "
                f"(>= {HIGH_VALUE_THRESHOLD}). "
                "Human review is required before recovery."
            ),
            "explanation": [
                "High-value transaction detected.",
                "Financial impact of an incorrect recovery attempt is significant.",
                "Automatic recovery is restricted for high-value transactions.",
                "Human review is required."
            ]
        }

    # ========================================================
    # RULE 5 — HIGH RECOVERY PROBABILITY
    # ========================================================

    if recovery_probability >= AUTOMATE_THRESHOLD:
        return {
            "decision": "AUTOMATE",
            "risk_level": "LOW",
            "policy_rule": "HIGH_RECOVERY_PROBABILITY",
            "reason": (
                "Recovery probability is high and "
                "no blocking policy rule was triggered."
            ),
            "explanation": [
                "ML model predicts a high recovery probability.",
                "No hard safety restriction was triggered.",
                "Transaction amount is below the high-value threshold.",
                "Automatic recovery is permitted."
            ]
        }

    # ========================================================
    # RULE 6 — MEDIUM RECOVERY PROBABILITY
    # ========================================================

    if recovery_probability >= REVIEW_THRESHOLD:
        return {
            "decision": "REVIEW",
            "risk_level": "MEDIUM",
            "policy_rule": "MEDIUM_RECOVERY_PROBABILITY",
            "reason": (
                "Recovery probability is moderate. "
                "Human review is required before recovery."
            ),
            "explanation": [
                "ML model predicts a moderate recovery probability.",
                "Prediction confidence is not high enough for automation.",
                "Human review is required before recovery."
            ]
        }

    # ========================================================
    # RULE 7 — LOW RECOVERY PROBABILITY
    # ========================================================

    return {
        "decision": "DO_NOT_RECOVER",
        "risk_level": "LOW",
        "policy_rule": "LOW_RECOVERY_PROBABILITY",
        "reason": (
            "Recovery probability is too low "
            "to justify another recovery attempt."
        ),
        "explanation": [
            "ML model predicts a low recovery probability.",
            "Automatic recovery is unlikely to succeed.",
            "Another attempt could waste resources or create additional risk.",
            "Recovery action is not recommended."
        ]
    }


# ============================================================
# COMPLETE TRANSACTION EVALUATION
# ============================================================

def evaluate_transaction(transaction):
    """
    Complete AI evaluation pipeline.

    1. Predict recovery probability using ML.
    2. Apply deterministic policy rules.
    3. Return combined result.
    """

    recovery_probability = predict_recovery(
        transaction
    )

    policy_result = make_decision(
        transaction,
        recovery_probability
    )

    return {
        "recovery_probability": recovery_probability,
        "decision": policy_result["decision"],
        "risk_level": policy_result["risk_level"],
        "policy_rule": policy_result["policy_rule"],
        "reason": policy_result["reason"],
        "explanation": policy_result["explanation"]
    }


# ============================================================
# TEST TRANSACTIONS
# ============================================================

if __name__ == "__main__":

    test_transactions = [

        # ----------------------------------------------------
        # TEST 1 — HIGH RECOVERY PROBABILITY
        # Expected: AUTOMATE
        # ----------------------------------------------------
        {
            "payment_method": "UPI",
            "bank": "HDFC",
            "failure_code": "PROCESSING_ERROR",
            "failure_stage": "PROCESSING",
            "amount": 1200,
            "retry_count": 0,
            "is_recurring": False
        },

        # ----------------------------------------------------
        # TEST 2 — CARD BLOCKED
        # Expected: DO_NOT_RECOVER
        # ----------------------------------------------------
        {
            "payment_method": "CARD",
            "bank": "SBI",
            "failure_code": "CARD_BLOCKED",
            "failure_stage": "AUTHORIZATION",
            "amount": 2500,
            "retry_count": 0,
            "is_recurring": False
        },

        # ----------------------------------------------------
        # TEST 3 — HIGH VALUE
        # Expected: REVIEW
        # ----------------------------------------------------
        {
            "payment_method": "UPI",
            "bank": "ICICI",
            "failure_code": "INSUFFICIENT_FUNDS",
            "failure_stage": "AUTHORIZATION",
            "amount": 8500,
            "retry_count": 0,
            "is_recurring": True
        },

        # ----------------------------------------------------
        # TEST 4 — BANK TIMEOUT
        # Expected: REVIEW
        # ----------------------------------------------------
        {
            "payment_method": "UPI",
            "bank": "SBI",
            "failure_code": "BANK_TIMEOUT",
            "failure_stage": "PROCESSING",
            "amount": 1800,
            "retry_count": 0,
            "is_recurring": False
        },

        # ----------------------------------------------------
        # TEST 5 — BANK TIMEOUT, LOW VALUE
        # Expected: REVIEW
        # This proves BANK_TIMEOUT overrides probability.
        # ----------------------------------------------------
        {
            "payment_method": "UPI",
            "bank": "HDFC",
            "failure_code": "BANK_TIMEOUT",
            "failure_stage": "PROCESSING",
            "amount": 500,
            "retry_count": 0,
            "is_recurring": False
        },

        # ----------------------------------------------------
        # TEST 6 — BANK TIMEOUT + MAX RETRIES
        # Expected: DO_NOT_RECOVER
        # MAX_RETRY_LIMIT must override BANK_TIMEOUT.
        # ----------------------------------------------------
        {
            "payment_method": "UPI",
            "bank": "HDFC",
            "failure_code": "BANK_TIMEOUT",
            "failure_stage": "PROCESSING",
            "amount": 500,
            "retry_count": 3,
            "is_recurring": False
        }
    ]


    print("\n" + "=" * 70)
    print("PAYMENT RECOVERY AI - POLICY ENGINE TEST")
    print("=" * 70)


    for index, transaction in enumerate(
        test_transactions,
        start=1
    ):

        print(f"\n{'-' * 70}")
        print(f"TEST TRANSACTION {index}")
        print(f"{'-' * 70}")

        try:

            result = evaluate_transaction(
                transaction
            )

            print(
                f"Recovery Probability : "
                f"{result['recovery_probability'] * 100:.2f}%"
            )

            print(
                f"Decision              : "
                f"{result['decision']}"
            )

            print(
                f"Risk Level            : "
                f"{result['risk_level']}"
            )

            print(
                f"Policy Rule           : "
                f"{result['policy_rule']}"
            )

            print(
                f"Reason                : "
                f"{result['reason']}"
            )

            print("Explanation:")

            for explanation in result["explanation"]:
                print(f"  - {explanation}")

        except Exception as error:

            print(
                f"ERROR: {error}"
            )


    # ========================================================
    # DIRECT POLICY EDGE-CASE TEST
    # ========================================================
    #
    # This test intentionally supplies a 90% probability
    # without invoking the ML model.
    #
    # BANK_TIMEOUT + retry_count=3
    # MUST return DO_NOT_RECOVER because MAX_RETRY_LIMIT
    # has higher priority.
    # ========================================================

    print("\n" + "=" * 70)
    print("DIRECT POLICY PRIORITY TEST")
    print("=" * 70)

    edge_case = {
        "failure_code": "BANK_TIMEOUT",
        "retry_count": 3,
        "amount": 500
    }

    result = make_decision(
        edge_case,
        0.90
    )

    print(
        f"Decision     : {result['decision']}"
    )

    print(
        f"Risk Level   : {result['risk_level']}"
    )

    print(
        f"Policy Rule  : {result['policy_rule']}"
    )

    print(
        f"Reason       : {result['reason']}"
    )

    print("\nExpected:")
    print("Decision     : DO_NOT_RECOVER")
    print("Risk Level   : HIGH")
    print("Policy Rule  : MAX_RETRY_LIMIT")

    print("\n" + "=" * 70)
    print("POLICY ENGINE TEST COMPLETE")
    print("=" * 70)