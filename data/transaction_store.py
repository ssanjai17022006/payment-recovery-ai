# data/transaction_store.py

import os
import csv
import pandas as pd
from datetime import datetime


# =========================================================
# Project paths
# =========================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DECISION_LOG_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "decision_log.csv"
)


# =========================================================
# Decision log columns
# =========================================================

FIELDNAMES = [
    "transaction_id",
    "merchant_id",
    "customer_id",
    "payment_method",
    "bank",
    "failure_code",
    "failure_stage",
    "amount",
    "timestamp",
    "retry_count",
    "is_recurring",
    "recovery_probability",
    "decision",
    "risk_level",
    "policy_rule",
    "reason",
    "explanation"
]


# =========================================================
# Ensure decision log exists
# =========================================================

def _ensure_file():

    os.makedirs(
        os.path.dirname(DECISION_LOG_FILE),
        exist_ok=True
    )

    if not os.path.exists(DECISION_LOG_FILE):

        with open(
            DECISION_LOG_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=FIELDNAMES
            )

            writer.writeheader()


# =========================================================
# Migrate existing decision log
# =========================================================

def _migrate_decision_log():

    if not os.path.exists(DECISION_LOG_FILE):
        return

    try:

        with open(
            DECISION_LOG_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            existing_fieldnames = (
                reader.fieldnames or []
            )

            rows = list(reader)


        # -------------------------------------------------
        # Check whether migration is required
        # -------------------------------------------------

        if all(
            field in existing_fieldnames
            for field in FIELDNAMES
        ):
            return


        # -------------------------------------------------
        # Add missing fields
        # -------------------------------------------------

        for row in rows:

            for field in FIELDNAMES:

                if field not in row:
                    row[field] = ""


        # -------------------------------------------------
        # Rewrite file using new schema
        # -------------------------------------------------

        with open(
            DECISION_LOG_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=FIELDNAMES
            )

            writer.writeheader()

            writer.writerows(rows)


        print(
            "Decision log schema migrated successfully."
        )


    except Exception as e:

        print(
            f"Warning: Could not migrate decision log: {e}"
        )


# =========================================================
# Read all decisions
# =========================================================

def get_all_transactions():

    _ensure_file()

    _migrate_decision_log()

    transactions = []

    with open(
        DECISION_LOG_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            transactions.append(
                _convert_types(row)
            )

    return transactions


# =========================================================
# Convert CSV values
# =========================================================

def _convert_types(transaction):

    # -----------------------------------------------------
    # Transaction ID
    # -----------------------------------------------------

    if transaction.get("transaction_id"):

        try:

            transaction["transaction_id"] = int(
                transaction["transaction_id"]
            )

        except (ValueError, TypeError):

            pass


    # -----------------------------------------------------
    # Amount
    # -----------------------------------------------------

    if transaction.get("amount"):

        try:

            transaction["amount"] = float(
                transaction["amount"]
            )

        except (ValueError, TypeError):

            pass


    # -----------------------------------------------------
    # Retry count
    # -----------------------------------------------------

    if transaction.get("retry_count"):

        try:

            transaction["retry_count"] = int(
                transaction["retry_count"]
            )

        except (ValueError, TypeError):

            pass


    # -----------------------------------------------------
    # Recurring flag
    # -----------------------------------------------------

    if isinstance(
        transaction.get("is_recurring"),
        str
    ):

        transaction["is_recurring"] = (
            transaction["is_recurring"]
            .strip()
            .lower()
            in ["true", "1", "yes"]
        )


    # -----------------------------------------------------
    # Recovery probability
    # -----------------------------------------------------

    if transaction.get(
        "recovery_probability"
    ):

        try:

            transaction[
                "recovery_probability"
            ] = float(
                transaction[
                    "recovery_probability"
                ]
            )

        except (ValueError, TypeError):

            pass


    return transaction


# =========================================================
# Generate next transaction ID
# =========================================================

def _get_next_transaction_id():
    """
    Generate the next unique transaction ID for live
    transactions.

    Training dataset uses IDs 1-5000.
    Live operational transactions start at 5001.
    """

    max_id = 5000

    if os.path.exists(DECISION_LOG_FILE):

        try:

            df = pd.read_csv(
                DECISION_LOG_FILE
            )

            if (
                not df.empty
                and "transaction_id" in df.columns
            ):

                existing_ids = pd.to_numeric(
                    df["transaction_id"],
                    errors="coerce"
                ).dropna()

                if not existing_ids.empty:

                    max_id = max(
                        max_id,
                        int(existing_ids.max())
                    )

        except Exception as e:

            print(
                f"Warning: Could not read "
                f"existing transaction IDs: {e}"
            )

    return max_id + 1


# =========================================================
# Save AI decision
# =========================================================

def save_transaction(transaction):

    _ensure_file()

    _migrate_decision_log()

    transaction = dict(
        transaction
    )


    # -----------------------------------------------------
    # Generate transaction ID
    # -----------------------------------------------------

    if not transaction.get(
        "transaction_id"
    ):

        transaction[
            "transaction_id"
        ] = _get_next_transaction_id()


    # -----------------------------------------------------
    # Add timestamp if missing
    # -----------------------------------------------------

    if not transaction.get(
        "timestamp"
    ):

        transaction[
            "timestamp"
        ] = datetime.now().isoformat(
            timespec="seconds"
        )


    # -----------------------------------------------------
    # Optional fields
    # -----------------------------------------------------

    transaction.setdefault(
        "merchant_id",
        ""
    )

    transaction.setdefault(
        "customer_id",
        ""
    )

    transaction.setdefault(
        "recovery_probability",
        ""
    )

    transaction.setdefault(
        "decision",
        ""
    )

    transaction.setdefault(
        "risk_level",
        ""
    )

    transaction.setdefault(
        "policy_rule",
        ""
    )

    transaction.setdefault(
        "reason",
        ""
    )

    transaction.setdefault(
        "explanation",
        ""
    )


    # -----------------------------------------------------
    # Convert explanation list to CSV-safe text
    # -----------------------------------------------------

    if isinstance(
        transaction.get("explanation"),
        list
    ):

        transaction[
            "explanation"
        ] = " | ".join(
            str(item)
            for item in transaction[
                "explanation"
            ]
        )


    # -----------------------------------------------------
    # Convert boolean
    # -----------------------------------------------------

    if isinstance(
        transaction.get("is_recurring"),
        bool
    ):

        transaction[
            "is_recurring"
        ] = (
            "True"
            if transaction[
                "is_recurring"
            ]
            else "False"
        )


    # -----------------------------------------------------
    # Create CSV row
    # -----------------------------------------------------

    row = {}

    for field in FIELDNAMES:

        row[field] = transaction.get(
            field,
            ""
        )


    # -----------------------------------------------------
    # Append decision
    # -----------------------------------------------------

    with open(
        DECISION_LOG_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES
        )

        writer.writerow(row)


    return _convert_types(row)


# =========================================================
# Get decision by ID
# =========================================================

def get_transaction_by_id(
    transaction_id
):

    transactions = get_all_transactions()

    try:

        transaction_id = int(
            transaction_id
        )

    except (ValueError, TypeError):

        pass


    for transaction in transactions:

        if transaction.get(
            "transaction_id"
        ) == transaction_id:

            return transaction


    return None


# =========================================================
# Get recent decisions
# =========================================================

def get_recent_transactions(
    limit=10
):

    transactions = get_all_transactions()

    return transactions[
        -limit:
    ][::-1]


# =========================================================
# Get decision count
# =========================================================

def get_transaction_count():

    return len(
        get_all_transactions()
    )


# =========================================================
# Backward-compatible aliases
# =========================================================

save_decision = save_transaction

get_all_decisions = get_all_transactions

get_decision_by_id = get_transaction_by_id

get_recent_decisions = get_recent_transactions

get_decision_count = get_transaction_count