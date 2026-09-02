# api/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS

from policy.decision_engine import evaluate_transaction

from data.transaction_store import (
    save_transaction,
    get_all_transactions,
    get_recent_transactions,
    get_transaction_by_id,
)


# =========================================================
# Flask Application
# =========================================================

app = Flask(__name__)

# Allow frontend to communicate with backend
CORS(app)


# =========================================================
# Root Route
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "service": "Payment Recovery AI",
        "status": "running",
        "version": "1.0",
        "message": "AI-powered payment recovery decision system"
    })


# =========================================================
# Health Check
# =========================================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "service": "Payment Recovery AI",
        "status": "healthy"
    })


# =========================================================
# Predict Transaction
# =========================================================

@app.route("/predict", methods=["POST"])
def predict():

    try:

        # -------------------------------------------------
        # Read request data
        # -------------------------------------------------

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "error": "Request body is empty."
            }), 400


        # -------------------------------------------------
        # Required fields
        # -------------------------------------------------

        required_fields = [
            "payment_method",
            "bank",
            "failure_code",
            "failure_stage",
            "amount",
            "retry_count",
            "is_recurring",
        ]


        # -------------------------------------------------
        # Validate required fields
        # -------------------------------------------------

        missing_fields = [
            field
            for field in required_fields
            if field not in data
        ]

        if missing_fields:

            return jsonify({
                "success": False,
                "error": "Missing required fields.",
                "missing_fields": missing_fields
            }), 400


        # -------------------------------------------------
        # Build transaction object
        # -------------------------------------------------

        transaction = {

            "payment_method":
                data["payment_method"],

            "bank":
                data["bank"],

            "failure_code":
                data["failure_code"],

            "failure_stage":
                data["failure_stage"],

            "amount":
                float(data["amount"]),

            "retry_count":
                int(data["retry_count"]),

            "is_recurring":
                data["is_recurring"],
        }


        # -------------------------------------------------
        # Evaluate transaction
        #
        # ML model
        #       ↓
        # Recovery probability
        #       ↓
        # Policy engine
        #       ↓
        # Final decision
        #       ↓
        # Explainability
        # -------------------------------------------------

        result = evaluate_transaction(
            transaction
        )


        # -------------------------------------------------
        # Add AI results to transaction
        # -------------------------------------------------

        transaction["recovery_probability"] = result.get(
            "recovery_probability"
        )

        transaction["decision"] = result.get(
            "decision"
        )

        transaction["reason"] = result.get(
            "reason"
        )

        transaction["risk_level"] = result.get(
            "risk_level"
        )

        transaction["policy_rule"] = result.get(
            "policy_rule"
        )


        # -------------------------------------------------
        # Store explanation
        #
        # CSV stores the explanation as one text field.
        # API response returns it as a list.
        # -------------------------------------------------

        explanation = result.get(
            "explanation",
            []
        )

        transaction["explanation"] = " | ".join(
            explanation
        )


        # -------------------------------------------------
        # Save transaction
        #
        # IMPORTANT:
        # This goes to decision_log.csv,
        # NOT transactions.csv.
        # -------------------------------------------------

        saved_transaction = save_transaction(
            transaction
        )


        # =================================================
        # API Response
        # =================================================

        return jsonify({

            "success": True,

            "input": saved_transaction,

            "prediction": {

                # Final AI decision
                "decision":
                    result.get("decision"),

                # ML probability
                "recovery_probability":
                    result.get(
                        "recovery_probability"
                    ),

                # Human-readable policy reason
                "reason":
                    result.get("reason"),

                # Risk classification
                "risk_level":
                    result.get("risk_level"),

                # Rule that triggered the decision
                "policy_rule":
                    result.get("policy_rule"),

                # Detailed explanation
                "explanation":
                    result.get(
                        "explanation",
                        []
                    )
            }
        })


    # -----------------------------------------------------
    # Validation errors
    # -----------------------------------------------------

    except ValueError as error:

        return jsonify({
            "success": False,
            "error": f"Invalid input: {str(error)}"
        }), 400


    # -----------------------------------------------------
    # General errors
    # -----------------------------------------------------

    except Exception as error:

        print(
            f"Prediction error: {error}"
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# =========================================================
# Get All Transactions
# =========================================================

@app.route("/transactions", methods=["GET"])
def transactions():

    try:

        transaction_list = get_all_transactions()

        return jsonify({
            "success": True,
            "transactions": transaction_list,
            "count": len(transaction_list)
        })


    except Exception as error:

        print(
            f"Transaction retrieval error: {error}"
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# =========================================================
# Get Recent Transactions
# =========================================================

@app.route("/transactions/recent", methods=["GET"])
def recent_transactions():

    try:

        # Default = 10 recent transactions
        limit = int(
            request.args.get(
                "limit",
                10
            )
        )

        transaction_list = get_recent_transactions(
            limit
        )

        return jsonify({
            "success": True,
            "transactions": transaction_list,
            "count": len(transaction_list)
        })


    except ValueError:

        return jsonify({
            "success": False,
            "error": "Invalid limit value."
        }), 400


    except Exception as error:

        print(
            f"Recent transaction error: {error}"
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# =========================================================
# Get Transaction By ID
# =========================================================

@app.route(
    "/transactions/<transaction_id>",
    methods=["GET"]
)
def transaction_by_id(transaction_id):

    try:

        transaction = get_transaction_by_id(
            transaction_id
        )

        if transaction is None:

            return jsonify({
                "success": False,
                "error": "Transaction not found."
            }), 404


        return jsonify({
            "success": True,
            "transaction": transaction
        })


    except Exception as error:

        print(
            f"Transaction lookup error: {error}"
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# =========================================================
# Transaction Statistics
# =========================================================

@app.route(
    "/transactions/stats",
    methods=["GET"]
)
def transaction_stats():

    try:

        transactions = get_all_transactions()


        # -------------------------------------------------
        # Empty dataset
        # -------------------------------------------------

        if not transactions:

            return jsonify({

                "success": True,

                "total_transactions": 0,

                "automate_count": 0,

                "review_count": 0,

                "do_not_recover_count": 0,

                "automation_rate": 0,

                "average_recovery_probability": 0,

                "total_transaction_value": 0,

                "automated_transaction_value": 0,

                "review_transaction_value": 0,

                "do_not_recover_transaction_value": 0,

                "potential_recoverable_value": 0
            })


        # -------------------------------------------------
        # Counters
        # -------------------------------------------------

        total_transactions = len(
            transactions
        )

        automate_count = 0

        review_count = 0

        do_not_recover_count = 0


        # -------------------------------------------------
        # Financial totals
        # -------------------------------------------------

        total_transaction_value = 0.0

        automated_transaction_value = 0.0

        review_transaction_value = 0.0

        do_not_recover_transaction_value = 0.0

        potential_recoverable_value = 0.0


        # -------------------------------------------------
        # Recovery probability
        # -------------------------------------------------

        probability_values = []


        # -------------------------------------------------
        # Process transactions
        # -------------------------------------------------

        for transaction in transactions:

            decision = transaction.get(
                "decision"
            )

            try:

                amount = float(
                    transaction.get(
                        "amount",
                        0
                    )
                )

            except (
                ValueError,
                TypeError
            ):

                amount = 0.0


            try:

                probability = float(
                    transaction.get(
                        "recovery_probability",
                        0
                    )
                )

            except (
                ValueError,
                TypeError
            ):

                probability = 0.0


            # ---------------------------------------------
            # Probability list
            # ---------------------------------------------

            probability_values.append(
                probability
            )


            # ---------------------------------------------
            # Total transaction value
            # ---------------------------------------------

            total_transaction_value += amount


            # ---------------------------------------------
            # Decision counts
            # ---------------------------------------------

            if decision == "AUTOMATE":

                automate_count += 1

                automated_transaction_value += amount

                # AI estimated opportunity
                potential_recoverable_value += (
                    amount * probability
                )


            elif decision == "REVIEW":

                review_count += 1

                review_transaction_value += amount

                # AI estimated opportunity
                potential_recoverable_value += (
                    amount * probability
                )


            elif decision == "DO_NOT_RECOVER":

                do_not_recover_count += 1

                do_not_recover_transaction_value += amount


        # -------------------------------------------------
        # Automation rate
        # -------------------------------------------------

        automation_rate = (
            automate_count
            / total_transactions
            * 100
        )


        # -------------------------------------------------
        # Average recovery probability
        # -------------------------------------------------

        if probability_values:

            average_recovery_probability = (
                sum(probability_values)
                / len(probability_values)
            )

        else:

            average_recovery_probability = 0.0


        # -------------------------------------------------
        # Return statistics
        # -------------------------------------------------

        return jsonify({

            "success": True,

            "total_transactions":
                total_transactions,

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

            "total_transaction_value":
                round(
                    total_transaction_value,
                    2
                ),

            "automated_transaction_value":
                round(
                    automated_transaction_value,
                    2
                ),

            "review_transaction_value":
                round(
                    review_transaction_value,
                    2
                ),

            "do_not_recover_transaction_value":
                round(
                    do_not_recover_transaction_value,
                    2
                ),

            "potential_recoverable_value":
                round(
                    potential_recoverable_value,
                    2
                )
        })


    except Exception as error:

        print(
            f"Statistics error: {error}"
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# =========================================================
# Run Application
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )