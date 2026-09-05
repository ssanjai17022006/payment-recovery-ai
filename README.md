# Razorpay Payment Failure Recovery AI

**🚀 [Live Demo](https://payment-recovery-ai-99pi.onrender.com/)**
**📂 [GitHub Repository](https://github.com/ssanjai17022006/payment-recovery-ai)**

> AI-assisted payment recovery decision system that combines machine learning with deterministic risk and policy rules to recommend safe recovery actions.

---

## Problem Statement

Razorpay handles a large number of merchant payment transactions, and some payment attempts fail. The internal merchant-success team needs to understand why these payments fail, where the failure happens, how many transactions are affected, and which failures have a genuine opportunity to become successful payments.

This project uses AI to analyze payment-failure patterns, identify potential recovery opportunities, prioritize important cases, and recommend whether the case should be automatically handled, reviewed by a human analyst, or not recovered.

The system is designed around one core principle:

> **ML predicts. Policy decides.**

---

## Solution Overview

Payment Recovery AI follows a two-stage decision architecture:

```text
Payment Failure
       │
       ▼
Transaction Features
       │
       ▼
Machine Learning Model
       │
       ▼
Recovery Probability
       │
       ▼
Policy & Risk Engine
       │
       ├───────────────┬────────────────────┐
       ▼               ▼                    ▼
   AUTOMATE          REVIEW          DO_NOT_RECOVER
       │               │                    │
       └───────────────┴────────────────────┘
                       │
                       ▼
                 Audit / Decision Log
                       │
                       ▼
                  Web Dashboard
```

The ML model estimates the probability that a failed payment can be recovered.

The policy and risk engine then evaluates that probability along with transaction-level safety rules before producing the final recommendation.

This prevents the ML model from directly controlling a financial action.

---

## Key Design Principle

### ML predicts. Policy decides.

The machine learning model answers:

> **"How likely is this transaction to be recovered?"**

The policy engine answers:

> **"Given this probability and the transaction risk, what action is allowed?"**

This separation makes the system easier to understand, audit, and modify.

A high ML probability does not automatically mean that recovery is safe.

For example, a `BANK_TIMEOUT` may have a high recovery probability, but automatically retrying could create a duplicate-charge risk if the bank has already processed the transaction.

---

## Decisions

The system produces one of three recommendations:

| Decision           | Meaning                                                                                                                        |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| **AUTOMATE**       | Recovery can be automatically attempted when probability is sufficiently high and no higher-priority policy blocks automation. |
| **REVIEW**         | Recovery may be possible, but the transaction requires human review because of risk, uncertainty, or policy restrictions.      |
| **DO_NOT_RECOVER** | Recovery should not be attempted because the transaction violates a recovery policy or has a low recovery probability.         |

---

## Project Structure

```text
payment-recovery-ai/
│
├── api/
│   ├── __init__.py
│   └── app.py
│
├── classifier/
│
├── compliance/
│
├── data/
│   ├── __init__.py
│   ├── generate_dataset.py
│   ├── seed_demo_transactions.py
│   ├── transaction_store.py
│   ├── transactions.csv
│   └── decision_log.csv
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── model/
│   ├── train_model.py
│   └── recovery_model.joblib
│
├── policy/
│   ├── __init__.py
│   └── decision_engine.py
│
├── tests/
│
├── venv/
│
├── .gitignore
├── README.md
├── recovery_simulator.py
└── requirements.txt
```

---

# Machine Learning

## ML Pipeline

The model uses transaction-level features related to the payment attempt and failure context.

### Input Features

```text
payment_method
bank
failure_code
failure_stage
amount
retry_count
is_recurring
```

The following fields are intentionally excluded from model training:

```text
recovery_probability
merchant_id
customer_id
timestamp
```

`recovery_probability` is excluded because it would cause target leakage: it is the value the model is expected to predict.

---

## Dataset

The project uses a generated dataset containing:

* **5,000 transactions**
* **4,691 supervised records**
* **309 records with unknown recovery status**

Recovery status values are:

```text
recovered
not_recovered
unknown
```

Only `recovered` and `not_recovered` records are used for supervised training and evaluation.

### Example Transaction Features

```text
payment_method
bank
failure_code
failure_stage
amount
retry_count
is_recurring
```

The dataset is intentionally synthetic and is used to demonstrate the end-to-end architecture.

---

## Machine Learning Model

The project uses a **Random Forest Classifier** with preprocessing through a scikit-learn pipeline.

### Model Configuration

```text
n_estimators = 300
max_depth = 10
min_samples_split = 10
min_samples_leaf = 4
class_weight = balanced
random_state = 42
```

Categorical features are encoded using `OneHotEncoder`.

The trained model is stored at:

```text
model/recovery_model.joblib
```

---

# Model Evaluation

The supervised dataset was divided into:

```text
Training set: 3,752 records
Test set:       939 records
```

### Results

| Metric   | Random Forest | Majority Baseline |
| -------- | ------------: | ----------------: |
| Accuracy |    **58.47%** |            58.04% |
| Macro-F1 |    **58.45%** |            36.73% |

The accuracy is relatively close to the majority-class baseline because the dataset contains more `not_recovered` transactions.

However, the **macro-F1 improvement is significant**, showing that the model provides substantially more balanced classification performance than simply predicting the majority class.

### Class-Level Performance

| Class         | Precision | Recall | F1-score |
| ------------- | --------: | -----: | -------: |
| not_recovered |       69% |    52% |      59% |
| recovered     |       50% |    67% |      58% |

The model identifies a substantial portion of the recovered class while maintaining reasonable performance on the not-recovered class.

> **Important:** This is a prototype trained on synthetic data. These results should not be interpreted as production payment-recovery performance.

---

# Policy & Risk Engine

The policy engine applies deterministic business and safety rules after the ML prediction.

## Policy Hierarchy

```text
1. CARD_BLOCKED
        ↓
   DO_NOT_RECOVER

2. retry_count >= 3
        ↓
   DO_NOT_RECOVER

3. BANK_TIMEOUT
        ↓
   REVIEW

4. amount >= ₹7,500
        ↓
   REVIEW

5. recovery probability >= 70%
        ↓
   AUTOMATE

6. recovery probability >= 40%
        ↓
   REVIEW

7. otherwise
        ↓
   DO_NOT_RECOVER
```

The hierarchy is intentional.

A higher-priority safety rule can override a high ML recovery probability.

### Example

A transaction may have a high recovery probability but still be sent to `REVIEW` when the failure is:

```text
BANK_TIMEOUT
```

This is because the bank may have processed the payment even though confirmation was not received.

Automatically retrying such a payment could potentially result in a duplicate charge.

---

# Decision Categories

## AUTOMATE

Used when:

* Recovery probability is high enough.
* No higher-priority policy rule blocks automation.
* The transaction is considered suitable for automated recovery.

Typical reason:

```text
HIGH_RECOVERY_PROBABILITY
```

---

## REVIEW

Used when:

* Recovery may be possible.
* Additional human verification is required.
* A safety or business rule prevents automatic recovery.

Examples:

```text
BANK_TIMEOUT
HIGH_VALUE_TRANSACTION
MEDIUM_RECOVERY_PROBABILITY
```

---

## DO_NOT_RECOVER

Used when:

* Recovery is unsafe.
* Retry limits have been exceeded.
* The card is blocked.
* Recovery probability is too low.

Examples:

```text
CARD_BLOCKED
MAX_RETRY_LIMIT
LOW_RECOVERY_PROBABILITY
```

---

# Explainable Decisions

The system returns more than just a final recommendation.

Each decision contains:

```text
Decision
Risk Level
Policy Rule
Reason
Explanation
Recovery Probability
```

Example:

```text
Decision: REVIEW
Risk Level: HIGH
Policy Rule: BANK_TIMEOUT

Reason:
Bank timeout requires review because the payment
may have been processed without confirmation.
```

The explanation is generated from the same policy decision used by the backend.

This keeps the frontend explanation consistent with the actual decision logic.

---

# Recovery Simulation

The project includes a bounded recovery simulator to demonstrate what could happen after a decision.

```text
AUTOMATE
    ↓
Simulated Recovery Attempt
    ↓
SUCCESS / FAILURE
```

For:

```text
REVIEW
    ↓
PENDING HUMAN REVIEW
```

For:

```text
DO_NOT_RECOVER
    ↓
NOT ATTEMPTED
```

The simulator uses a deterministic transaction-based score so that the same transaction produces the same simulation result.

### Important

The simulator **does not execute real payments**.

It is included only to demonstrate the recovery workflow and estimate potential outcomes.

---

# Potential Recoverable Value

The dashboard estimates potential recoverable value using the ML recovery probability.

For transactions eligible for recovery:

```text
Potential Recoverable Value
=
Transaction Amount × Recovery Probability
```

`DO_NOT_RECOVER` transactions are excluded from this calculation.

This gives the merchant-success team a business-oriented estimate of the value represented by potentially recoverable transactions.

---

# Audit Trail

The project deliberately separates historical training data from live operational decisions.

## Training / Ground Truth Dataset

```text
data/transactions.csv
```

This contains historical/static transaction records and their recovery outcomes.

It is **not modified by live API predictions**.

## Operational Decision Log

```text
data/decision_log.csv
```

Live API predictions are stored separately.

The decision log contains fields such as:

```text
transaction_id
merchant_id
customer_id
payment_method
bank
failure_code
failure_stage
amount
timestamp
retry_count
is_recurring
recovery_probability
decision
risk_level
policy_rule
reason
explanation
recovery_attempted
recovery_result
recovered_amount
stopped_reason
```

This separation prevents live predictions from contaminating the training dataset.

---

# Backend API

The backend is implemented using **Flask**.

## Health Check

```text
GET /health
```

Used to verify that the API is running.

---

## Prediction

```text
POST /predict
```

Accepts transaction features and returns:

```text
recovery_probability
decision
risk_level
policy_rule
reason
explanation
recovery_attempted
recovery_result
recovered_amount
stopped_reason
```

---

## Batch Simulation

```text
POST /batch/simulate
```

Accepts multiple transactions and simulates the recovery decision workflow without modifying the operational decision log.

The endpoint returns aggregated metrics including:

```text
processed transactions
AUTOMATE count
REVIEW count
DO_NOT_RECOVER count
transaction value
automated value
review value
stopped value
simulated recovered amount
recovery rate
```

No real payments are executed.

---

## Transactions

```text
GET /transactions
GET /transactions/recent
GET /transactions/<transaction_id>
```

These endpoints provide access to operational decision records.

---

## Statistics

```text
GET /transactions/stats
```

Provides dashboard-level operational metrics including:

```text
total transactions
AUTOMATE count
REVIEW count
DO_NOT_RECOVER count
automation rate
average recovery probability
transaction value
automated value
review value
do-not-recover value
potential recoverable value
simulated recovered amount
pending review value
stopped value
value recovery rate
```

---

## API Information

```text
GET /api-info
```

Returns information about the available API endpoints.

---

# Frontend Dashboard

The project includes a web dashboard for interacting with the recovery engine.

The dashboard allows users to:

1. Enter payment-failure information.
2. Submit the transaction to the backend.
3. View the ML recovery probability.
4. View the final policy decision.
5. View the risk level.
6. View the policy rule.
7. Understand why the decision was made.
8. View recovery simulation results.
9. View operational statistics.
10. View recent transaction decisions.

The frontend consumes the backend decision rather than independently reimplementing the policy logic.

This avoids having separate decision logic in the frontend and backend.

---

# Installation

## 1. Clone the Repository

```powershell
git clone https://github.com/ssanjai17022006/payment-recovery-ai.git
cd payment-recovery-ai
```

## 2. Create a Virtual Environment

```powershell
python -m venv venv
```

## 3. Activate the Environment

```powershell
.\venv\Scripts\Activate.ps1
```

## 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

# Running Locally

## Start the Backend

Run from the project root:

```powershell
python -m api.app
```

The API runs at:

```text
http://127.0.0.1:5000
```

## Start the Frontend

In another PowerShell window:

```powershell
python -m http.server 8000 --directory frontend
```

Then open:

```text
http://127.0.0.1:8000
```

---

# Training the Model

The repository already contains the trained model.

If retraining is required:

```powershell
python model\train_model.py
```

The trained model is saved to:

```text
model\recovery_model.joblib
```

To generate a new synthetic dataset:

```powershell
python data\generate_dataset.py
```

If the dataset is regenerated, retrain the model afterward.

---

# Demo Scenarios

The application is designed around several important payment-failure scenarios.

## Scenario 1 — High Recovery Probability

```text
Failure: PROCESSING_ERROR
Recovery probability: High
Retry count: 0
No blocking policy condition
```

Result:

```text
AUTOMATE
```

The system considers the transaction suitable for an automated recovery attempt.

---

## Scenario 2 — Bank Timeout

```text
Failure: BANK_TIMEOUT
Recovery probability: Potentially high
Risk: High
```

Result:

```text
REVIEW
```

The policy engine overrides the possibility of automation because the payment may already have been processed by the bank.

This demonstrates the safety principle:

> **High probability does not always mean safe to automate.**

---

## Scenario 3 — Card Blocked

```text
Failure: CARD_BLOCKED
```

Result:

```text
DO_NOT_RECOVER
```

The card-blocked policy takes priority over the ML probability.

---

## Scenario 4 — Maximum Retries

```text
Retry count: 3 or more
```

Result:

```text
DO_NOT_RECOVER
```

The system stops additional recovery attempts to prevent unnecessary retries.

---

## Scenario 5 — High-Value Transaction

```text
Amount: ₹7,500 or higher
```

Result:

```text
REVIEW
```

Higher-value transactions require human review before recovery.

---

# Technology Stack

## Backend

* Python
* Flask
* Flask-CORS

## Machine Learning

* scikit-learn
* Random Forest
* OneHotEncoder
* joblib

## Data Processing

* Pandas
* NumPy

## Frontend

* HTML
* CSS
* JavaScript

## Storage

* CSV-based training dataset
* CSV-based operational decision log

## Deployment

* Render
* Gunicorn

---

# Engineering Decisions

## 1. ML and Policy Are Separate

The ML model estimates recovery probability.

The policy engine determines whether recovery is allowed.

This prevents an ML prediction from directly triggering a financial action.

---

## 2. Training Data and Live Decisions Are Separate

The training dataset remains unchanged during live predictions.

Operational predictions are stored in a separate decision log.

This prevents training-data contamination.

---

## 3. Safety Rules Have Priority

Certain conditions such as:

```text
CARD_BLOCKED
retry_count >= 3
BANK_TIMEOUT
HIGH_VALUE_TRANSACTION
```

can override ML probability.

This is important for financial systems where incorrect automation can have a higher cost than missing a recovery opportunity.

---

## 4. Explainability Is Built Into the Decision

Every operational decision records:

```text
decision
risk level
policy rule
reason
explanation
```

The system therefore provides an auditable explanation rather than returning only a probability.

---

## 5. Recovery Is Simulated

The project does not execute real payment retries.

Recovery actions are simulated to demonstrate the complete decision workflow safely.

---

# Current Dashboard Demo

The deployed demonstration currently contains:

```text
Total Transactions: 14
AUTOMATE:            4
REVIEW:              5
DO_NOT_RECOVER:      5
```

The dashboard also displays:

* Total transaction value
* Automated transaction value
* Review value
* Potential recoverable value
* Simulated recovered amount
* Pending review value
* Stopped value
* Average recovery probability
* Automation rate

---

# Current Limitations

This implementation is a prototype designed to demonstrate the architecture and decision workflow.

Important limitations include:

* The dataset is generated rather than sourced from real payment-network data.
* Model performance is currently moderate.
* Recovery probability is an ML estimate, not a guaranteed recovery outcome.
* The current operational store uses CSV rather than a production database.
* The system does not execute real payment retries.
* Recovery outcomes are simulated.
* Policy rules are deterministic and manually defined.
* No production-grade authentication or authorization layer is included.
* The model has not been validated against live production traffic.

Therefore, the system should be considered a:

> **Decision-support prototype, not a production payment-recovery service.**

---

# Future Improvements

## Model Improvements

* Larger and more representative payment datasets
* Better feature engineering
* Hyperparameter optimization
* Probability calibration
* Model monitoring
* Data drift detection

## Explainability

* Feature-level explanations
* SHAP-based analysis
* Policy-vs-ML decision visualization

## Production Infrastructure

* PostgreSQL or another transactional database
* Authentication and role-based access
* Asynchronous recovery workflows
* Queue-based processing
* Monitoring and alerting
* Production-grade logging

## Recovery Simulation

A future version can simulate:

```text
Transaction
    ↓
Recovery Decision
    ↓
Retry Simulation
    ↓
Success / Failure
    ↓
Business Impact
```

This would allow merchant-success teams to estimate the effect of different recovery strategies before deploying them.

---

# Project Status

## Completed

* [x] Project structure
* [x] Synthetic transaction dataset
* [x] Random Forest recovery model
* [x] Model evaluation
* [x] Majority-class baseline comparison
* [x] Policy/risk engine
* [x] BANK_TIMEOUT safety rule
* [x] AUTOMATE / REVIEW / DO_NOT_RECOVER decisions
* [x] Backend prediction API
* [x] Batch recovery simulation
* [x] Operational audit log
* [x] Training-data / decision-log separation
* [x] Frontend dashboard integration
* [x] Policy explanation display
* [x] Transaction statistics
* [x] Recovery simulation
* [x] Dependency pinning
* [x] Render deployment
* [x] Repository cleanup

## Next Development Areas

* [ ] Recovery-action simulation improvements
* [ ] Advanced model explainability
* [ ] Production database
* [ ] Model monitoring
* [ ] Real-world payment data validation
* [ ] Production authentication
* [ ] Production deployment hardening

---

# Design Philosophy

The project is built around four principles.

### 1. Predict Conservatively

Machine learning should estimate recovery opportunity rather than directly control financial actions.

### 2. Policy Overrides Probability

High model confidence does not automatically mean that recovery is safe.

### 3. Every Decision Should Be Explainable

The system records why a transaction was automated, reviewed, or rejected.

### 4. Training Data Must Remain Clean

Historical/ground-truth data and live operational decisions are maintained separately to avoid data contamination and unintended training leakage.

---

# Summary

**Payment Recovery AI** combines machine learning, deterministic business policy, risk evaluation, recovery simulation, and audit logging to help merchant-success teams make safer payment-recovery decisions.

The central workflow is:

```text
Payment Failure
      ↓
ML Recovery Probability
      ↓
Policy & Risk Evaluation
      ↓
AUTOMATE / REVIEW / DO_NOT_RECOVER
      ↓
Recovery Simulation
      ↓
Explainable Audit Record
```

The architecture intentionally avoids allowing an ML prediction to directly trigger a financial action.

Instead:

```text
ML → estimates recovery opportunity

Policy → evaluates safety

Decision Engine → recommends the action

Simulator → demonstrates the possible outcome

Audit Log → records what happened
```

This makes the system a strong foundation for a more production-oriented payment recovery platform while keeping the current implementation safe, explainable, and demonstrable.

---

## Links

**🚀 Live Demo:**
https://payment-recovery-ai-99pi.onrender.com/

**📂 GitHub Repository:**
https://github.com/ssanjai17022006/payment-recovery-ai
