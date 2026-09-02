import requests
import time

API_URL = "http://127.0.0.1:5000/predict"

demo_transactions = [
    {
        "merchant_id": "MERCHANT_001",
        "customer_id": "CUSTOMER_001",
        "payment_method": "UPI",
        "bank": "HDFC",
        "failure_code": "PROCESSING_ERROR",
        "failure_stage": "PAYMENT_PROCESSING",
        "amount": 1200,
        "retry_count": 0,
        "is_recurring": False
    },
    {
        "merchant_id": "MERCHANT_001",
        "customer_id": "CUSTOMER_002",
        "payment_method": "CARD",
        "bank": "ICICI",
        "failure_code": "BANK_TIMEOUT",
        "failure_stage": "PAYMENT_PROCESSING",
        "amount": 2000,
        "retry_count": 1,
        "is_recurring": True
    },
    {
        "merchant_id": "MERCHANT_002",
        "customer_id": "CUSTOMER_003",
        "payment_method": "UPI",
        "bank": "SBI",
        "failure_code": "INSUFFICIENT_FUNDS",
        "failure_stage": "PAYMENT_AUTHORIZATION",
        "amount": 850,
        "retry_count": 0,
        "is_recurring": False
    },
    {
        "merchant_id": "MERCHANT_002",
        "customer_id": "CUSTOMER_004",
        "payment_method": "CARD",
        "bank": "HDFC",
        "failure_code": "CARD_BLOCKED",
        "failure_stage": "PAYMENT_AUTHORIZATION",
        "amount": 1500,
        "retry_count": 1,
        "is_recurring": False
    },
    {
        "merchant_id": "MERCHANT_003",
        "customer_id": "CUSTOMER_005",
        "payment_method": "UPI",
        "bank": "ICICI",
        "failure_code": "PROCESSING_ERROR",
        "failure_stage": "PAYMENT_PROCESSING",
        "amount": 5000,
        "retry_count": 0,
        "is_recurring": True
    },
    {
        "merchant_id": "MERCHANT_003",
        "customer_id": "CUSTOMER_006",
        "payment_method": "CARD",
        "bank": "SBI",
        "failure_code": "CUSTOMER_ACTION_REQUIRED",
        "failure_stage": "CUSTOMER_ACTION",
        "amount": 750,
        "retry_count": 1,
        "is_recurring": False
    },
    {
        "merchant_id": "MERCHANT_004",
        "customer_id": "CUSTOMER_007",
        "payment_method": "UPI",
        "bank": "HDFC",
        "failure_code": "PROCESSING_ERROR",
        "failure_stage": "PAYMENT_PROCESSING",
        "amount": 2500,
        "retry_count": 2,
        "is_recurring": False
    },
    {
        "merchant_id": "MERCHANT_004",
        "customer_id": "CUSTOMER_008",
        "payment_method": "CARD",
        "bank": "ICICI",
        "failure_code": "INSUFFICIENT_FUNDS",
        "failure_stage": "PAYMENT_AUTHORIZATION",
        "amount": 3200,
        "retry_count": 2,
        "is_recurring": True
    },
    {
        "merchant_id": "MERCHANT_005",
        "customer_id": "CUSTOMER_009",
        "payment_method": "UPI",
        "bank": "SBI",
        "failure_code": "BANK_TIMEOUT",
        "failure_stage": "PAYMENT_PROCESSING",
        "amount": 1800,
        "retry_count": 1,
        "is_recurring": False
    },
    {
        "merchant_id": "MERCHANT_005",
        "customer_id": "CUSTOMER_010",
        "payment_method": "CARD",
        "bank": "HDFC",
        "failure_code": "PROCESSING_ERROR",
        "failure_stage": "PAYMENT_PROCESSING",
        "amount": 1000,
        "retry_count": 3,
        "is_recurring": False
    },
    {
        "merchant_id": "MERCHANT_001",
        "customer_id": "CUSTOMER_011",
        "payment_method": "UPI",
        "bank": "ICICI",
        "failure_code": "PROCESSING_ERROR",
        "failure_stage": "PAYMENT_PROCESSING",
        "amount": 6500,
        "retry_count": 0,
        "is_recurring": True
    },
    {
        "merchant_id": "MERCHANT_002",
        "customer_id": "CUSTOMER_012",
        "payment_method": "CARD",
        "bank": "SBI",
        "failure_code": "BANK_TIMEOUT",
        "failure_stage": "PAYMENT_PROCESSING",
        "amount": 900,
        "retry_count": 1,
        "is_recurring": False
    }
]


def main():
    print("=" * 60)
    print("Payment Recovery AI - Demo Transaction Seeder")
    print("=" * 60)

    try:
        response = requests.get(
            "http://127.0.0.1:5000/health",
            timeout=5
        )

        if response.status_code != 200:
            print("ERROR: Flask API is not healthy.")
            return

        print("API status: HEALTHY")
        print(f"Creating {len(demo_transactions)} demo transactions...\n")

    except requests.RequestException as error:
        print("ERROR: Could not connect to Flask API.")
        print(error)
        print("\nStart Flask first, then run this script again.")
        return

    successful = 0
    failed = 0

    for index, transaction in enumerate(demo_transactions, start=1):

        try:
            response = requests.post(
                API_URL,
                json=transaction,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                prediction = data.get("prediction", {})

                transaction_id = (
                    data.get("transaction_id")
                    or data.get("input", {}).get("transaction_id")
                    or "N/A"
                )

                decision = prediction.get(
                    "decision",
                    data.get("decision", "N/A")
                )

                probability = prediction.get(
                    "recovery_probability",
                    data.get("recovery_probability", 0)
                )

                print(
                    f"{index:02d}. "
                    f"Transaction {transaction_id} | "
                    f"{decision:<15} | "
                    f"{float(probability) * 100:6.2f}% | "
                    f"₹{transaction['amount']}"
                )

                successful += 1

            else:
                print(
                    f"{index:02d}. FAILED | "
                    f"HTTP {response.status_code}"
                )

                try:
                    print(response.json())
                except ValueError:
                    print(response.text)

                failed += 1

        except requests.RequestException as error:
            print(f"{index:02d}. FAILED | {error}")
            failed += 1

        # Small delay so timestamps are easy to distinguish.
        time.sleep(0.2)

    print("\n" + "=" * 60)
    print("DEMO SEEDING COMPLETE")
    print("=" * 60)
    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()