import os
import joblib
import pandas as pd

MODEL_PATH = os.path.join("model", "best_model.pkl")
FEATURE_COLUMNS_PATH = os.path.join("model", "feature_columns.pkl")

def get_float_input(prompt_text, min_value=None, max_value=None):
    while True:
        try:
            value = float(input(prompt_text))
            if min_value is not None and value < min_value:
                print(f"Value must be at least {min_value}.")
                continue
            if max_value is not None and value > max_value:
                print(f"Value must be at most {max_value}.")
                continue
            return value
        except ValueError:
            print("Please enter a valid number.")

def get_int_input(prompt_text, min_value=None, max_value=None):
    while True:
        try:
            value = int(input(prompt_text))
            if min_value is not None and value < min_value:
                print(f"Value must be at least {min_value}.")
                continue
            if max_value is not None and value > max_value:
                print(f"Value must be at most {max_value}.")
                continue
            return value
        except ValueError:
            print("Please enter a valid integer.")

def main():
    if not os.path.exists(MODEL_PATH):
        print("Best model not found.")
        print("Please run train_model.py first.")
        return

    if not os.path.exists(FEATURE_COLUMNS_PATH):
        print("Feature columns file not found.")
        print("Please run train_model.py first.")
        return

    model = joblib.load(MODEL_PATH)
    feature_columns = joblib.load(FEATURE_COLUMNS_PATH)

    print("=" * 60)
    print("HABIT SLIP PREDICTION")
    print("=" * 60)

    sleep_hours = get_float_input("Enter sleep hours (0-24): ", 0, 24)
    study_hours = get_float_input("Enter study hours (0-24): ", 0, 24)
    workout_minutes = get_float_input("Enter workout minutes (0-300): ", 0, 300)
    journalling_minutes = get_float_input("Enter journalling minutes (0-300): ", 0, 300)
    reading_minutes = get_float_input("Enter reading minutes (0-300): ", 0, 300)
    mood = get_int_input("Enter mood score (1-5): ", 1, 5)
    day_of_week = get_int_input("Enter day of week (0=Mon, 1=Tue, ..., 6=Sun): ", 0, 6)

    is_weekend = 1 if day_of_week in [5, 6] else 0

    input_data = {
        "sleep_hours": sleep_hours,
        "study_hours": study_hours,
        "workout_minutes": workout_minutes,
        "journalling_minutes": journalling_minutes,
        "reading_minutes": reading_minutes,
        "mood": mood,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend
    }

    input_df = pd.DataFrame([input_data])

    # Ensure column order matches training
    input_df = input_df[feature_columns]

    prediction = model.predict(input_df)[0]

    if hasattr(model, "predict_proba"):
        probability = model.predict_proba(input_df)[0][1]
    else:
        probability = None

    print("\n" + "=" * 60)
    print("PREDICTION RESULT")
    print("=" * 60)

    if probability is not None:
        print(f"Slip Probability : {probability:.4f} ({probability * 100:.2f}%)")

    if prediction == 1:
        print("Prediction       : Likely to slip")
    else:
        print("Prediction       : Not likely to slip")

if __name__ == "__main__":
    main()