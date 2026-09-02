# data/generate_dataset.py

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


# =========================================================
# Configuration
# =========================================================

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

NUM_TEST_ROWS = 5000

AS_OF_DATE = datetime(2026, 9, 1, 0, 0, 0)

UNKNOWN_WINDOW_DAYS = 2


# =========================================================
# Failure-code -> failure-stage mapping
# =========================================================

FAILURE_STAGE_MAP = {
    "INSUFFICIENT_FUNDS": "BANK_AUTHORIZATION",
    "PROCESSING_ERROR": "PAYMENT_PROCESSING",
    "BANK_TIMEOUT": "BANK_RESPONSE",
    "CARD_BLOCKED": "CARD_AUTHORIZATION",
    "CUSTOMER_ACTION_REQUIRED": "CUSTOMER_AUTHENTICATION",
}


# =========================================================
# Failure-code weighted distribution
# =========================================================

FAILURE_CODE_WEIGHTS = {
    "INSUFFICIENT_FUNDS": 0.35,
    "PROCESSING_ERROR": 0.25,
    "BANK_TIMEOUT": 0.20,
    "CUSTOMER_ACTION_REQUIRED": 0.12,
    "CARD_BLOCKED": 0.08,
}


# =========================================================
# Baseline recovery probabilities
# =========================================================

BASELINE_RECOVERY_PROBABILITY = {
    "PROCESSING_ERROR": 0.55,
    "INSUFFICIENT_FUNDS": 0.45,
    "CUSTOMER_ACTION_REQUIRED": 0.40,
    "BANK_TIMEOUT": 0.50,
    "CARD_BLOCKED": 0.05,
}


# =========================================================
# Retry-count weighted distribution
# =========================================================

RETRY_COUNT_WEIGHTS = {
    0: 0.55,
    1: 0.25,
    2: 0.13,
    3: 0.07,
}


# =========================================================
# Raw value pools
# =========================================================

PAYMENT_METHODS = [
    "UPI",
    "CARD",
]

BANKS = [
    "SBI",
    "HDFC",
    "ICICI",
    "AXIS",
]

MERCHANT_IDS = [
    f"MERCH{i:03d}"
    for i in range(1, 51)
]

CUSTOMER_IDS = [
    f"CUST{i:04d}"
    for i in range(1, 1001)
]

RECURRING_PROBABILITY = 0.20


# =========================================================
# Generate one transaction
# =========================================================

def generate_one_transaction(transaction_number):

    transaction_id = transaction_number

    merchant_id = random.choice(MERCHANT_IDS)
    customer_id = random.choice(CUSTOMER_IDS)

    payment_method = random.choice(PAYMENT_METHODS)
    bank = random.choice(BANKS)

    # Failure code
    failure_codes = list(FAILURE_CODE_WEIGHTS.keys())
    failure_weights = list(FAILURE_CODE_WEIGHTS.values())

    failure_code = random.choices(
        failure_codes,
        weights=failure_weights,
        k=1
    )[0]

    failure_stage = FAILURE_STAGE_MAP[failure_code]

    # Amount
    amount = random.randint(100, 10000)

    # Timestamp
    end_time = AS_OF_DATE
    start_time = end_time - timedelta(days=30)

    random_seconds = random.randint(
        0,
        int((end_time - start_time).total_seconds())
    )

    timestamp = start_time + timedelta(
        seconds=random_seconds
    )

    # Retry count
    retry_counts = list(RETRY_COUNT_WEIGHTS.keys())
    retry_weights = list(RETRY_COUNT_WEIGHTS.values())

    retry_count = random.choices(
        retry_counts,
        weights=retry_weights,
        k=1
    )[0]

    # Recurring payment
    is_recurring = (
        random.random() < RECURRING_PROBABILITY
    )

    return {
        "transaction_id": transaction_id,
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "payment_method": payment_method,
        "bank": bank,
        "failure_code": failure_code,
        "failure_stage": failure_stage,
        "amount": amount,
        "timestamp": timestamp.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "retry_count": retry_count,
        "is_recurring": is_recurring,
    }


# =========================================================
# Calculate recovery probability
# =========================================================

def calculate_recovery_probability(transaction):

    failure_code = transaction["failure_code"]
    retry_count = transaction["retry_count"]
    is_recurring = transaction["is_recurring"]

    probability = BASELINE_RECOVERY_PROBABILITY[
        failure_code
    ]

    retry_adjustments = {
        0: 0.00,
        1: -0.05,
        2: -0.10,
        3: -0.15,
    }

    probability += retry_adjustments[retry_count]

    if is_recurring:
        probability += 0.03

    probability = max(
        0.0,
        min(1.0, probability)
    )

    return round(probability, 4)


# =========================================================
# Determine whether outcome is unknown
# =========================================================

def is_outcome_unknown(timestamp):

    transaction_time = datetime.strptime(
        timestamp,
        "%Y-%m-%d %H:%M:%S"
    )

    age = AS_OF_DATE - transaction_time

    return age < timedelta(days=UNKNOWN_WINDOW_DAYS)


# =========================================================
# Generate recovery outcome
# =========================================================

def generate_recovery_outcome(
    transaction,
    recovery_probability
):

    if is_outcome_unknown(transaction["timestamp"]):
        return "unknown"

    random_draw = random.random()

    if random_draw < recovery_probability:
        return "recovered"

    return "not_recovered"


# =========================================================
# Save transactions to CSV
# =========================================================

def save_transactions_to_csv(transactions):

    output_path = (
        Path(__file__).resolve().parent
        / "transactions.csv"
    )

    fieldnames = [
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
        "recovery_status",
    ]

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as csvfile:

        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for transaction in transactions:
            writer.writerow(transaction)

    return output_path


# =========================================================
# Print distribution
# =========================================================

def print_distribution(
    title,
    counts,
    total,
    intended=None
):

    print()
    print(title)
    print("=" * 90)

    for key, count in counts.items():

        percentage = (
            count / total
        ) * 100

        if intended and key in intended:

            difference = (
                percentage - intended[key]
            )

            print(
                f"{key}: "
                f"{count} rows "
                f"({percentage:.2f}%) | "
                f"intended={intended[key]:.2f}% | "
                f"difference={difference:+.2f}%"
            )

        else:

            print(
                f"{key}: "
                f"{count} rows "
                f"({percentage:.2f}%)"
            )

    print("=" * 90)


# =========================================================
# Recovery validation
# =========================================================

def print_recovery_validation(transactions):

    print()
    print("Recovery validation by failure code:")
    print("=" * 105)

    print(
        f"{'Failure Code':<35}"
        f"{'Rows':>8}"
        f"{'Avg Probability':>20}"
        f"{'Observable':>13}"
        f"{'Recovered %':>17}"
        f"{'Baseline':>15}"
    )

    print("-" * 105)

    failure_codes = list(
        FAILURE_CODE_WEIGHTS.keys()
    )

    for failure_code in failure_codes:

        rows = [
            t for t in transactions
            if t["failure_code"] == failure_code
        ]

        observable_rows = [
            t for t in rows
            if t["recovery_status"] != "unknown"
        ]

        recovered_rows = [
            t for t in observable_rows
            if t["recovery_status"] == "recovered"
        ]

        if observable_rows:

            recovered_percentage = (
                len(recovered_rows)
                / len(observable_rows)
            ) * 100

        else:

            recovered_percentage = 0

        average_probability = (
            sum(
                t["recovery_probability"]
                for t in rows
            )
            / len(rows)
        ) * 100

        baseline = (
            BASELINE_RECOVERY_PROBABILITY[
                failure_code
            ] * 100
        )

        print(
            f"{failure_code:<35}"
            f"{len(rows):>8}"
            f"{average_probability:>19.2f}%"
            f"{len(observable_rows):>13}"
            f"{recovered_percentage:>16.2f}%"
            f"{baseline:>14.2f}%"
        )

    print("=" * 105)


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    transactions = []

    # Generate dataset
    for transaction_number in range(
        1,
        NUM_TEST_ROWS + 1
    ):

        transaction = generate_one_transaction(
            transaction_number
        )

        recovery_probability = (
            calculate_recovery_probability(
                transaction
            )
        )

        recovery_status = (
            generate_recovery_outcome(
                transaction,
                recovery_probability
            )
        )

        transaction["recovery_probability"] = (
            recovery_probability
        )

        transaction["recovery_status"] = (
            recovery_status
        )

        transactions.append(transaction)

    # =====================================================
    # Retry distribution
    # =====================================================

    retry_counts = {}

    for transaction in transactions:

        retry_count = transaction["retry_count"]

        retry_counts[retry_count] = (
            retry_counts.get(retry_count, 0) + 1
        )

    retry_counts = dict(
        sorted(retry_counts.items())
    )

    retry_intended = {
        0: 55.00,
        1: 25.00,
        2: 13.00,
        3: 7.00,
    }

    print_distribution(
        "Retry-count distribution:",
        retry_counts,
        NUM_TEST_ROWS,
        retry_intended
    )

    # =====================================================
    # Failure-code distribution
    # =====================================================

    failure_counts = {}

    for transaction in transactions:

        failure_code = transaction["failure_code"]

        failure_counts[failure_code] = (
            failure_counts.get(failure_code, 0) + 1
        )

    failure_intended = {
        "INSUFFICIENT_FUNDS": 35.00,
        "PROCESSING_ERROR": 25.00,
        "BANK_TIMEOUT": 20.00,
        "CUSTOMER_ACTION_REQUIRED": 12.00,
        "CARD_BLOCKED": 8.00,
    }

    print_distribution(
        "Failure-code distribution:",
        failure_counts,
        NUM_TEST_ROWS,
        failure_intended
    )

    # =====================================================
    # Recurring distribution
    # =====================================================

    recurring_count = sum(
        1
        for transaction in transactions
        if transaction["is_recurring"]
    )

    recurring_percentage = (
        recurring_count
        / NUM_TEST_ROWS
    ) * 100

    print()
    print("Recurring-payment distribution:")
    print("=" * 70)

    print(
        f"is_recurring=True: "
        f"{recurring_count} rows "
        f"({recurring_percentage:.2f}%)"
    )

    print("Intended: 20.00%")
    print("=" * 70)

    # =====================================================
    # Recovery status distribution
    # =====================================================

    outcome_counts = {
        "recovered": 0,
        "not_recovered": 0,
        "unknown": 0,
    }

    for transaction in transactions:

        status = transaction["recovery_status"]

        outcome_counts[status] += 1

    print_distribution(
        "Recovery-status distribution:",
        outcome_counts,
        NUM_TEST_ROWS
    )

    # =====================================================
    # Validation
    # =====================================================

    print_recovery_validation(transactions)

    # =====================================================
    # Sample transactions
    # =====================================================

    print()
    print("Sample generated transactions:")
    print("=" * 120)

    for transaction in transactions[:10]:

        print(transaction)

    print("=" * 120)

    # =====================================================
    # Save CSV
    # =====================================================

    output_path = save_transactions_to_csv(
        transactions
    )

    print()
    print("Dataset successfully saved!")
    print("=" * 70)
    print(f"File: {output_path}")
    print(f"Rows: {len(transactions)}")
    print(f"Expected CSV lines: {len(transactions) + 1}")
    print("=" * 70)
