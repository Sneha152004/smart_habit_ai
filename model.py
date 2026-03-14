import os
import json
import joblib
import warnings
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    ConfusionMatrixDisplay
)

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier

warnings.filterwarnings("ignore")

# --------------------------------------------------
# 1. CONFIG
# --------------------------------------------------
DATA_PATH = "dataset.csv"
MODEL_DIR = "model"
CONFUSION_DIR = os.path.join(MODEL_DIR, "confusion_matrices")
RANDOM_STATE = 42
TEST_SIZE = 0.20

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(CONFUSION_DIR, exist_ok=True)

# --------------------------------------------------
# 2. LOAD DATA
# --------------------------------------------------
df = pd.read_csv(DATA_PATH)

print("Dataset loaded successfully.")
print("Shape:", df.shape)
print("Columns:", list(df.columns))

# Standardize column names
df.columns = [col.strip().lower() for col in df.columns]

# --------------------------------------------------
# 3. BASIC CLEANING
# --------------------------------------------------
required_columns = [
    "sleep_hours",
    "study_hours",
    "workout_minutes",
    "journalling_minutes",
    "reading_minutes",
    "mood",
    "p_slip"
]

missing_cols = [col for col in required_columns if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")

# Optional date-based features
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["day_of_week"] = df["date"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
else:
    df["day_of_week"] = 0
    df["is_weekend"] = 0

# --------------------------------------------------
# 4. FEATURE SELECTION
# --------------------------------------------------
# Avoid leakage: do not use routine_strength, adjusted_strength, p_slip_prob
feature_columns = [
    "sleep_hours",
    "study_hours",
    "workout_minutes",
    "journalling_minutes",
    "reading_minutes",
    "mood",
    "day_of_week",
    "is_weekend"
]

target_column = "p_slip"

X = df[feature_columns].copy()
y = df[target_column].copy()

print("\nTarget distribution:")
print(y.value_counts())

# --------------------------------------------------
# 5. TRAIN-TEST SPLIT
# --------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=y
)

# --------------------------------------------------
# 6. DEFINE CLASSIFIERS
# --------------------------------------------------
models = {
    "logistic_regression": LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=RANDOM_STATE
    ),
    "random_forest": RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_split=5,
        class_weight="balanced",
        random_state=RANDOM_STATE
    ),
    "svm_rbf": SVC(
        kernel="rbf",
        probability=True,
        class_weight="balanced",
        random_state=RANDOM_STATE
    ),
    "knn": KNeighborsClassifier(
        n_neighbors=7
    ),
    "decision_tree": DecisionTreeClassifier(
        max_depth=5,
        min_samples_split=10,
        class_weight="balanced",
        random_state=RANDOM_STATE
    ),
    "gradient_boosting": GradientBoostingClassifier(
        n_estimators=150,
        learning_rate=0.08,
        max_depth=3,
        random_state=RANDOM_STATE
    ),
    "ann_mlp": MLPClassifier(
        hidden_layer_sizes=(32, 16),
        activation="relu",
        solver="adam",
        alpha=0.0005,
        batch_size=32,
        learning_rate_init=0.001,
        max_iter=700,
        random_state=RANDOM_STATE
    )
}

# Models that need scaling
models_needing_scaling = {
    "logistic_regression",
    "svm_rbf",
    "knn",
    "ann_mlp"
}

# --------------------------------------------------
# 7. TRAIN + CROSS VALIDATION + EVALUATION
# --------------------------------------------------
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
scoring = ["accuracy", "precision", "recall", "f1", "roc_auc"]

results = {}
trained_models = {}

for model_name, model in models.items():
    print("\n" + "=" * 60)
    print(f"Training {model_name}")
    print("=" * 60)

    steps = [("imputer", SimpleImputer(strategy="median"))]

    if model_name in models_needing_scaling:
        steps.append(("scaler", StandardScaler()))

    steps.append(("classifier", model))
    pipeline = Pipeline(steps)

    # Cross-validation on training data
    cv_scores = cross_validate(
        pipeline,
        X_train,
        y_train,
        cv=cv,
        scoring=scoring,
        n_jobs=-1
    )

    # Train on full training set
    pipeline.fit(X_train, y_train)

    # Test prediction
    y_pred = pipeline.predict(X_test)

    classifier = pipeline.named_steps["classifier"]

    if hasattr(classifier, "predict_proba"):
        y_proba = pipeline.predict_proba(X_test)[:, 1]
    elif hasattr(classifier, "decision_function"):
        scores = pipeline.decision_function(X_test)
        y_proba = (scores - scores.min()) / (scores.max() - scores.min() + 1e-9)
    else:
        y_proba = y_pred

    test_accuracy = accuracy_score(y_test, y_pred)
    test_precision = precision_score(y_test, y_pred, zero_division=0)
    test_recall = recall_score(y_test, y_pred, zero_division=0)
    test_f1 = f1_score(y_test, y_pred, zero_division=0)
    test_roc_auc = roc_auc_score(y_test, y_proba)
    test_conf_matrix = confusion_matrix(y_test, y_pred)

    # Save confusion matrix as CSV
    cm_df = pd.DataFrame(
        test_conf_matrix,
        index=["Actual_0", "Actual_1"],
        columns=["Predicted_0", "Predicted_1"]
    )
    cm_csv_path = os.path.join(CONFUSION_DIR, f"{model_name}_confusion_matrix.csv")
    cm_df.to_csv(cm_csv_path)

    # Save confusion matrix as PNG
    plt.figure(figsize=(5, 4))
    disp = ConfusionMatrixDisplay(confusion_matrix=test_conf_matrix, display_labels=[0, 1])
    disp.plot(cmap="Blues", values_format="d")
    plt.title(f"Confusion Matrix - {model_name}")
    plt.tight_layout()
    cm_png_path = os.path.join(CONFUSION_DIR, f"{model_name}_confusion_matrix.png")
    plt.savefig(cm_png_path)
    plt.close()

    results[model_name] = {
        "cv_accuracy_mean": round(float(cv_scores["test_accuracy"].mean()), 4),
        "cv_precision_mean": round(float(cv_scores["test_precision"].mean()), 4),
        "cv_recall_mean": round(float(cv_scores["test_recall"].mean()), 4),
        "cv_f1_mean": round(float(cv_scores["test_f1"].mean()), 4),
        "cv_roc_auc_mean": round(float(cv_scores["test_roc_auc"].mean()), 4),
        "test_accuracy": round(float(test_accuracy), 4),
        "test_precision": round(float(test_precision), 4),
        "test_recall": round(float(test_recall), 4),
        "test_f1": round(float(test_f1), 4),
        "test_roc_auc": round(float(test_roc_auc), 4),
        "confusion_matrix": test_conf_matrix.tolist(),
        "confusion_matrix_csv": cm_csv_path,
        "confusion_matrix_png": cm_png_path
    }

    trained_models[model_name] = pipeline

    print(f"CV Accuracy : {results[model_name]['cv_accuracy_mean']}")
    print(f"CV F1       : {results[model_name]['cv_f1_mean']}")
    print(f"Test Acc    : {results[model_name]['test_accuracy']}")
    print(f"Test Prec   : {results[model_name]['test_precision']}")
    print(f"Test Recall : {results[model_name]['test_recall']}")
    print(f"Test F1     : {results[model_name]['test_f1']}")
    print(f"Test AUC    : {results[model_name]['test_roc_auc']}")
    print("Confusion Matrix:")
    print(test_conf_matrix)

# --------------------------------------------------
# 8. CREATE COMPARISON TABLE
# --------------------------------------------------
comparison_rows = []
for model_name, metrics in results.items():
    row = {"model": model_name}
    row.update(metrics)
    comparison_rows.append(row)

comparison_df = pd.DataFrame(comparison_rows)
comparison_df = comparison_df.sort_values(by="test_f1", ascending=False).reset_index(drop=True)

# Final best model selection
best_model_row = comparison_df.iloc[0]
best_model_name = best_model_row["model"]
best_pipeline = trained_models[best_model_name]
best_f1 = best_model_row["test_f1"]

# --------------------------------------------------
# 9. SAVE ARTIFACTS
# --------------------------------------------------
joblib.dump(best_pipeline, os.path.join(MODEL_DIR, "best_model.pkl"))
joblib.dump(trained_models, os.path.join(MODEL_DIR, "all_models.pkl"))
joblib.dump(feature_columns, os.path.join(MODEL_DIR, "feature_columns.pkl"))
comparison_df.to_csv(os.path.join(MODEL_DIR, "model_comparison.csv"), index=False)

summary = {
    "dataset_path": DATA_PATH,
    "feature_columns": feature_columns,
    "target_column": target_column,
    "best_model_name": best_model_name,
    "best_model_test_f1": round(float(best_f1), 4),
    "confusion_matrix_folder": CONFUSION_DIR,
    "results": results
}

with open(os.path.join(MODEL_DIR, "training_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=4)

# --------------------------------------------------
# 10. FINAL OUTPUT
# --------------------------------------------------
print("\n" + "=" * 60)
print("TRAINING COMPLETE")
print("=" * 60)
print(f"Best model: {best_model_name}")
print(f"Best test F1: {best_f1:.4f}")

print("\nModel ranking by Test F1:")
print(
    comparison_df[
        ["model", "test_accuracy", "test_precision", "test_recall", "test_f1", "test_roc_auc"]
    ].to_string(index=False)
)

print("\n" + "=" * 60)
print("FINAL MODEL COMPARISON")
print("=" * 60)
print(
    comparison_df[
        ["model", "test_accuracy", "test_precision", "test_recall", "test_f1", "test_roc_auc"]
    ].to_string(index=False)
)

print("\n" + "=" * 60)
print("BEST MODEL SELECTION")
print("=" * 60)
print(f"Best Classifier : {best_model_row['model']}")
print(f"Accuracy        : {best_model_row['test_accuracy']}")
print(f"Precision       : {best_model_row['test_precision']}")
print(f"Recall          : {best_model_row['test_recall']}")
print(f"F1 Score        : {best_model_row['test_f1']}")
print(f"ROC AUC         : {best_model_row['test_roc_auc']}")

print("\nSaved files:")
print("model/best_model.pkl")
print("model/all_models.pkl")
print("model/feature_columns.pkl")
print("model/model_comparison.csv")
print("model/training_summary.json")
print("model/confusion_matrices/")