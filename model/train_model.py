# model/train_model.py

import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# =========================================================
# Configuration
# =========================================================

DATA_FILE = "data/transactions.csv"
MODEL_DIR = "model"

MODEL_FILE = "model/recovery_model.joblib"


# =========================================================
# Load dataset
# =========================================================

print("\nLoading dataset...")
print("=" * 70)

df = pd.read_csv(DATA_FILE)

print(f"Total rows loaded: {len(df)}")
print(f"Total columns: {len(df.columns)}")


# =========================================================
# Remove unknown outcomes
# =========================================================

print("\nRecovery-status distribution before filtering:")
print(df["recovery_status"].value_counts())

df = df[
    df["recovery_status"].isin(
        ["recovered", "not_recovered"]
    )
].copy()

print("\nRows available for supervised training:")
print(len(df))


# =========================================================
# Define features and target
# =========================================================

FEATURE_COLUMNS = [
    "payment_method",
    "bank",
    "failure_code",
    "failure_stage",
    "amount",
    "retry_count",
    "is_recurring",
]

TARGET_COLUMN = "recovery_status"


X = df[FEATURE_COLUMNS]
y = df[TARGET_COLUMN]


# =========================================================
# Feature types
# =========================================================

CATEGORICAL_FEATURES = [
    "payment_method",
    "bank",
    "failure_code",
    "failure_stage",
]

NUMERICAL_FEATURES = [
    "amount",
    "retry_count",
    "is_recurring",
]


# =========================================================
# Preprocessing
# =========================================================

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            CATEGORICAL_FEATURES,
        ),
        (
            "numerical",
            "passthrough",
            NUMERICAL_FEATURES,
        ),
    ]
)


# =========================================================
# Model
# =========================================================

classifier = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    min_samples_split=10,
    min_samples_leaf=4,
    random_state=42,
    class_weight="balanced",
)


# =========================================================
# Complete ML pipeline
# =========================================================

model = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "classifier",
            classifier
        ),
    ]
)


# =========================================================
# Train/test split
# =========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)


print("\nDataset split:")
print("=" * 70)
print(f"Training rows: {len(X_train)}")
print(f"Testing rows : {len(X_test)}")


# =========================================================
# Train model
# =========================================================

print("\nTraining Random Forest model...")
print("=" * 70)

model.fit(
    X_train,
    y_train
)

print("Training completed.")


# =========================================================
# Prediction
# =========================================================

y_pred = model.predict(X_test)


# =========================================================
# Evaluation
# =========================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

print("\nModel evaluation:")
print("=" * 70)

print(
    f"Accuracy: {accuracy * 100:.2f}%"
)

print("\nClassification report:")
print(
    classification_report(
        y_test,
        y_pred,
        target_names=[
            "not_recovered",
            "recovered"
        ]
    )
)

print("Confusion matrix:")
print(
    confusion_matrix(
        y_test,
        y_pred
    )
)


# =========================================================
# Feature importance
# =========================================================

print("\nFeature importance:")
print("=" * 70)

preprocessor_fitted = model.named_steps[
    "preprocessor"
]

classifier_fitted = model.named_steps[
    "classifier"
]

feature_names = (
    preprocessor_fitted
    .get_feature_names_out()
)

importances = classifier_fitted.feature_importances_

importance_df = pd.DataFrame(
    {
        "feature": feature_names,
        "importance": importances,
    }
)

importance_df = importance_df.sort_values(
    "importance",
    ascending=False
)

print(
    importance_df.head(15).to_string(
        index=False
    )
)


# =========================================================
# Save model
# =========================================================

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)

joblib.dump(
    model,
    MODEL_FILE
)

print("\nModel saved successfully!")
print("=" * 70)
print(
    f"Model file: {os.path.abspath(MODEL_FILE)}"
)
print("=" * 70)