import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from policy.decision_engine import evaluate_transaction
from recovery_simulator import simulate_recovery
from data.transaction_store import (
    save_transaction,
    get_all_transactions,
    get_recent_transactions,
    get_transaction_by_id,
    get_next_transaction_id,
)


# ============================================================
# APP INITIALIZATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)

app = Flask(__name__)
CORS(app)


# ============================================================
# CONSTANTS
# ============================================================

REQUIRED_FIELDS = [
    "payment_method",
    "bank",
    "failure_code",
    "failure_stage",
    "amount",
    "retry_count",
    "is_recurring",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def validate_transaction(data):
    """
    Validate that all required transaction fields are present.
    """

    if not isinstance(data, dict):
        return ["Request body must be a JSON object"]

    missing_fields = [
        field for field in REQUIRED_FIELDS
        if field not in data
    ]

    return missing_fields


def build_transaction(data, transaction_id):
    """
    Build a normalized transaction dictionary.
    """

    return {
        "transaction_id": transaction_id,
        "merchant_id": data.get("merchant_id", ""),
        "customer_id": data.get("customer_id", ""),
        "payment_method": data["payment_method"],
        "bank": data["bank"],
        "failure_code": data["failure_code"],
        "failure_stage": data["failure_stage"],
        "amount": float(data["amount"]),
        "timestamp": data.get("timestamp", ""),
        "retry_count": int(data["retry_count"]),
        "is_recurring": bool(data["is_recurring"]),
    }


def build_prediction_response(
    transaction,
    prediction,
    simulation
):
    """
    Combine transaction, ML prediction, policy decision,
    and recovery simulation into a single API response.
    """

    return {
        "transaction_id": transaction["transaction_id"],

        # ML
        "recovery_probability":
            prediction["recovery_probability"],

        # Policy
        "decision": prediction["decision"],
        "risk_level": prediction["risk_level"],
        "policy_rule": prediction["policy_rule"],
        "reason": prediction["reason"],
        "explanation": prediction.get(
            "explanation",
            []
        ),

        # Recovery simulation
        "recovery_attempted":
            simulation["recovery_attempted"],

        "recovery_result":
            simulation["recovery_result"],

        "recovered_amount":
            simulation["recovered_amount"],

        "stopped_reason":
            simulation["stopped_reason"],

        "simulation_score":
            simulation["simulation_score"],
    }


# ============================================================
# FRONTEND
# ============================================================

@app.route("/", methods=["GET"])
def home():
    """
    Serve the existing frontend dashboard.

    The frontend is intentionally kept in the existing
    frontend/ directory and is not replaced.
    """

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


@app.route("/<path:path>", methods=["GET"])
def frontend_static(path):
    """
    Serve frontend static files such as:

        /style.css
        /script.js

    API routes are defined separately below.
    """

    file_path = os.path.join(
        FRONTEND_DIR,
        path
    )

    if os.path.isfile(file_path):
        return send_from_directory(
            FRONTEND_DIR,
            path
        )

    return jsonify({
        "success": False,
        "error": "Resource not found",
    }), 404


# ============================================================
# API INFORMATION
# ============================================================

@app.route("/api-info", methods=["GET"])
def api_info():
    """
    Return API information without interfering with
    the frontend root route.
    """

    return jsonify({
        "success": True,
        "service": "Payment Recovery AI",
        "message": "Payment Recovery AI API is running",
        "endpoints": [
            "/health",
            "/predict",
            "/batch/simulate",
            "/transactions",
            "/transactions/recent",
            "/transactions/<transaction_id>",
            "/transactions/stats",
        ],
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "status": "healthy",
        "service": "Payment Recovery AI",
    })


# ============================================================
# SINGLE TRANSACTION PREDICTION
# ============================================================

@app.route("/predict", methods=["POST"])
def predict():
    """
    Process one live transaction.

    Workflow:

        Transaction
             ↓
        ML probability
             ↓
        Policy engine
             ↓
        AUTOMATE / REVIEW / DO_NOT_RECOVER
             ↓
        Recovery simulation
             ↓
        decision_log.csv
    """

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "success": False,
            "error": "Request must contain valid JSON"
        }), 400

    missing_fields = validate_transaction(data)

    if missing_fields:
        return jsonify({
            "success": False,
            "error": "Missing required transaction fields",
            "missing_fields": missing_fields,
        }), 400

    try:
        # ----------------------------------------------------
        # Generate a new live transaction ID
        # ----------------------------------------------------

        transaction_id = get_next_transaction_id()

        transaction = build_transaction(
            data,
            transaction_id
        )

        # ----------------------------------------------------
        # ML + Policy Evaluation
        # ----------------------------------------------------

        prediction = evaluate_transaction(
            transaction
        )

        # ----------------------------------------------------
        # Recovery Simulation
        # ----------------------------------------------------

        simulation = simulate_recovery(
            transaction_id=transaction["transaction_id"],
            amount=transaction["amount"],
            recovery_probability=prediction[
                "recovery_probability"
            ],
            decision=prediction["decision"],
            reason=prediction["reason"],
        )

        # ----------------------------------------------------
        # Add prediction information
        # ----------------------------------------------------

        transaction["recovery_probability"] = (
            prediction["recovery_probability"]
        )

        transaction["decision"] = (
            prediction["decision"]
        )

        transaction["risk_level"] = (
            prediction["risk_level"]
        )

        transaction["policy_rule"] = (
            prediction["policy_rule"]
        )

        transaction["reason"] = (
            prediction["reason"]
        )

        transaction["explanation"] = (
            prediction.get(
                "explanation",
                []
            )
        )

        # ----------------------------------------------------
        # Add recovery simulation information
        # ----------------------------------------------------

        transaction["recovery_attempted"] = (
            simulation["recovery_attempted"]
        )

        transaction["recovery_result"] = (
            simulation["recovery_result"]
        )

        transaction["recovered_amount"] = (
            simulation["recovered_amount"]
        )

        transaction["stopped_reason"] = (
            simulation["stopped_reason"]
        )

        # ----------------------------------------------------
        # Save LIVE decision
        # ----------------------------------------------------

        save_transaction(transaction)

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return jsonify({
            "success": True,
            "simulation": True,
            "message": (
                "Transaction evaluated successfully. "
                "Recovery workflow was simulated; "
                "no real payment was executed."
            ),
            "prediction": build_prediction_response(
                transaction,
                prediction,
                simulation,
            ),
        })

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


# ============================================================
# BATCH RECOVERY SIMULATION
# ============================================================

@app.route("/batch/simulate", methods=["POST"])
def batch_simulate():
    """
    Simulate recovery decisions for multiple transactions.

    IMPORTANT:
    - This endpoint does NOT execute real payments.
    - This endpoint does NOT modify transactions.csv.
    - Batch results are returned in memory.
    - Batch results are NOT written to decision_log.csv.

    Workflow:

        Multiple Transactions
                 ↓
             ML Model
                 ↓
            Policy Engine
                 ↓
       ┌─────────┼──────────────┐
       ↓         ↓              ↓
    AUTOMATE   REVIEW    DO_NOT_RECOVER
       ↓         ↓              ↓
    Simulate   Pending     Not Attempted
       ↓
    SUCCESS / FAILURE
       ↓
    Batch Metrics
    """

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "success": False,
            "error": "Request must contain valid JSON"
        }), 400

    transactions = data.get(
        "transactions"
    )

    if not isinstance(
        transactions,
        list
    ):
        return jsonify({
            "success": False,
            "error": "'transactions' must be a list"
        }), 400

    if len(transactions) == 0:
        return jsonify({
            "success": False,
            "error": "Transaction list cannot be empty"
        }), 400

    try:
        # ----------------------------------------------------
        # Reserve starting ID ONCE
        # ----------------------------------------------------

        batch_start_id = int(
            get_next_transaction_id()
        )

        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

        automate_count = 0
        review_count = 0
        do_not_recover_count = 0

        automate_value = 0.0
        review_value = 0.0
        do_not_recover_value = 0.0

        simulated_recovered_amount = 0.0
        pending_review_value = 0.0
        stopped_value = 0.0

        results = []

        # ----------------------------------------------------
        # Process every transaction
        # ----------------------------------------------------

        for index, item in enumerate(
            transactions
        ):

            if not isinstance(
                item,
                dict
            ):
                return jsonify({
                    "success": False,
                    "error": (
                        f"Transaction at index {index} "
                        "must be an object"
                    ),
                }), 400

            missing_fields = validate_transaction(
                item
            )

            if missing_fields:
                return jsonify({
                    "success": False,
                    "error": (
                        f"Transaction at index {index} "
                        "is missing required fields"
                    ),
                    "missing_fields":
                        missing_fields,
                }), 400

            # ------------------------------------------------
            # Unique batch transaction ID
            # ------------------------------------------------

            transaction_id = (
                batch_start_id + index
            )

            transaction = build_transaction(
                item,
                transaction_id
            )

            # ------------------------------------------------
            # ML + Policy
            # ------------------------------------------------

            prediction = evaluate_transaction(
                transaction
            )

            decision = prediction[
                "decision"
            ]

            amount = transaction[
                "amount"
            ]

            probability = prediction[
                "recovery_probability"
            ]

            # ------------------------------------------------
            # Recovery simulation
            # ------------------------------------------------

            simulation = simulate_recovery(
                transaction_id=
                    transaction["transaction_id"],
                amount=amount,
                recovery_probability=
                    probability,
                decision=decision,
                reason=prediction["reason"],
            )

            # ------------------------------------------------
            # Decision counts + values
            # ------------------------------------------------

            if decision == "AUTOMATE":

                automate_count += 1
                automate_value += amount

            elif decision == "REVIEW":

                review_count += 1
                review_value += amount
                pending_review_value += amount

            elif decision == "DO_NOT_RECOVER":

                do_not_recover_count += 1
                do_not_recover_value += amount
                stopped_value += amount

            # ------------------------------------------------
            # Recovered amount
            # ------------------------------------------------

            simulated_recovered_amount += float(
                simulation["recovered_amount"]
            )

            # ------------------------------------------------
            # Store result
            # ------------------------------------------------

            results.append({
                "transaction_id":
                    transaction["transaction_id"],

                "amount":
                    amount,

                "recovery_probability":
                    probability,

                "decision":
                    decision,

                "risk_level":
                    prediction["risk_level"],

                "policy_rule":
                    prediction["policy_rule"],

                "reason":
                    prediction["reason"],

                "explanation":
                    prediction.get(
                        "explanation",
                        []
                    ),

                "recovery_attempted":
                    simulation[
                        "recovery_attempted"
                    ],

                "recovery_result":
                    simulation[
                        "recovery_result"
                    ],

                "recovered_amount":
                    simulation[
                        "recovered_amount"
                    ],

                "stopped_reason":
                    simulation[
                        "stopped_reason"
                    ],

                "simulation_score":
                    simulation[
                        "simulation_score"
                    ],
            })

        # ----------------------------------------------------
        # Batch metrics
        # ----------------------------------------------------

        total_transaction_value = (
            automate_value
            + review_value
            + do_not_recover_value
        )

        if total_transaction_value > 0:
            recovery_rate = (
                simulated_recovered_amount
                / total_transaction_value
            ) * 100
        else:
            recovery_rate = 0.0

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return jsonify({
            "success": True,
            "simulation": True,

            "message": (
                "Batch recovery simulation completed. "
                "No real payments were executed."
            ),

            "metrics": {
                "processed_count":
                    len(results),

                "automate_count":
                    automate_count,

                "review_count":
                    review_count,

                "do_not_recover_count":
                    do_not_recover_count,

                "automate_value":
                    round(
                        automate_value,
                        2
                    ),

                "review_value":
                    round(
                        review_value,
                        2
                    ),

                "do_not_recover_value":
                    round(
                        do_not_recover_value,
                        2
                    ),

                "total_transaction_value":
                    round(
                        total_transaction_value,
                        2
                    ),

                "simulated_recovered_amount":
                    round(
                        simulated_recovered_amount,
                        2
                    ),

                "recovery_rate":
                    round(
                        recovery_rate,
                        2
                    ),

                "pending_review_value":
                    round(
                        pending_review_value,
                        2
                    ),

                "stopped_value":
                    round(
                        stopped_value,
                        2
                    ),
            },

            "transactions":
                results,
        })

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


# ============================================================
# ALL TRANSACTIONS
# ============================================================

@app.route(
    "/transactions",
    methods=["GET"]
)
def transactions():

    try:
        records = get_all_transactions()

        return jsonify({
            "success": True,
            "count": len(records),
            "transactions": records,
        })

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


# ============================================================
# RECENT TRANSACTIONS
# ============================================================

@app.route(
    "/transactions/recent",
    methods=["GET"]
)
def recent_transactions():

    try:
        limit = request.args.get(
            "limit",
            default=10,
            type=int
        )

        records = get_recent_transactions(
            limit
        )

        return jsonify({
            "success": True,
            "count": len(records),
            "transactions": records,
        })

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


# ============================================================
# TRANSACTION BY ID
# ============================================================

@app.route(
    "/transactions/<transaction_id>",
    methods=["GET"]
)
def transaction_by_id(
    transaction_id
):

    try:
        transaction = get_transaction_by_id(
            transaction_id
        )

        if transaction is None:
            return jsonify({
                "success": False,
                "error": "Transaction not found",
            }), 404

        return jsonify({
            "success": True,
            "transaction": transaction,
        })

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


# ============================================================
# TRANSACTION STATISTICS
# ============================================================

@app.route(
    "/transactions/stats",
    methods=["GET"]
)
def transaction_stats():

    try:
        records = get_all_transactions()

        total = len(records)

        automate_count = sum(
            1
            for r in records
            if r.get("decision")
            == "AUTOMATE"
        )

        review_count = sum(
            1
            for r in records
            if r.get("decision")
            == "REVIEW"
        )

        do_not_recover_count = sum(
            1
            for r in records
            if r.get("decision")
            == "DO_NOT_RECOVER"
        )

        # ----------------------------------------------------
        # Values
        # ----------------------------------------------------

        total_value = sum(
            float(
                r.get(
                    "amount",
                    0
                ) or 0
            )
            for r in records
        )

        automated_value = sum(
            float(
                r.get(
                    "amount",
                    0
                ) or 0
            )
            for r in records
            if r.get("decision")
            == "AUTOMATE"
        )

        review_value = sum(
            float(
                r.get(
                    "amount",
                    0
                ) or 0
            )
            for r in records
            if r.get("decision")
            == "REVIEW"
        )

        blocked_value = sum(
            float(
                r.get(
                    "amount",
                    0
                ) or 0
            )
            for r in records
            if r.get("decision")
            == "DO_NOT_RECOVER"
        )

        # ----------------------------------------------------
        # ML probability
        # ----------------------------------------------------

        probabilities = []

        for r in records:

            probability = r.get(
                "recovery_probability"
            )

            if probability not in (
                None,
                "",
            ):

                try:
                    probabilities.append(
                        float(probability)
                    )

                except (
                    ValueError,
                    TypeError
                ):
                    pass

        average_recovery_probability = (
            sum(probabilities)
            / len(probabilities)
            if probabilities
            else 0.0
        )

        # ----------------------------------------------------
        # Potential recoverable value
        # ----------------------------------------------------

        potential_recoverable_value = sum(
            float(
                r.get(
                    "amount",
                    0
                ) or 0
            )
            * float(
                r.get(
                    "recovery_probability",
                    0
                ) or 0
            )
            for r in records
        )

        # ----------------------------------------------------
        # Simulation outcomes
        # ----------------------------------------------------

        simulated_recovered_amount = sum(
            float(
                r.get(
                    "recovered_amount",
                    0
                ) or 0
            )
            for r in records
        )

        pending_review_value = sum(
            float(
                r.get(
                    "amount",
                    0
                ) or 0
            )
            for r in records
            if r.get("recovery_result")
            == "pending"
        )

        stopped_value = sum(
            float(
                r.get(
                    "amount",
                    0
                ) or 0
            )
            for r in records
            if r.get("recovery_result")
            == "not_attempted"
        )

        # ----------------------------------------------------
        # Rates
        # ----------------------------------------------------

        automation_rate = (
            automate_count
            / total
            * 100
            if total > 0
            else 0.0
        )

        if total_value > 0:

            value_recovery_rate = (
                simulated_recovered_amount
                / total_value
            ) * 100

        else:

            value_recovery_rate = 0.0

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return jsonify({
            "success": True,

            "stats": {
                "total":
                    total,

                "automate_count":
                    automate_count,

                "review_count":
                    review_count,

                "do_not_recover_count":
                    do_not_recover_count,

                "automation_rate":
                    round(
                        automation_rate,
                        2
                    ),

                "average_recovery_probability":
                    round(
                        average_recovery_probability,
                        4
                    ),

                "total_value":
                    round(
                        total_value,
                        2
                    ),

                "automated_value":
                    round(
                        automated_value,
                        2
                    ),

                "review_value":
                    round(
                        review_value,
                        2
                    ),

                "blocked_value":
                    round(
                        blocked_value,
                        2
                    ),

                "potential_recoverable_value":
                    round(
                        potential_recoverable_value,
                        2
                    ),

                "simulated_recovered_amount":
                    round(
                        simulated_recovered_amount,
                        2
                    ),

                "value_recovery_rate":
                    round(
                        value_recovery_rate,
                        2
                    ),

                "pending_review_value":
                    round(
                        pending_review_value,
                        2
                    ),

                "stopped_value":
                    round(
                        stopped_value,
                        2
                    ),
            },
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )
