# Smart Habit AI 🧠✨

Smart Habit AI is a premium, full-stack habit tracking application that uses a **Hybrid Intelligence Engine**—combining optimized Machine Learning with a rule-based deterministic layer—to optimize your daily routine. It predicts behavioral "slips" and provides proactive, psychologically-informed coaching to ensure long-term consistency.

![Dashboard Preview](interfaces/Screenshot%202026-02-16%20201036.png)

## 🚀 Key Features

- **Hybrid Slip Prediction:** Uses a consensus between a high-precision **ANN (MLP Classifier)** and a deterministic behavioral engine to predict routine instability.
- **7-Model ML Hub:** Features a pre-trained library of 7 AI classifiers (Random Forest, SVM, Gradient Boosting, etc.) used to identify the optimal "Champion Model" for prediction.
- **Weekly Adaptive Badges:** A calendar-aware (Mon-Sun) reward system that assigns psychological badges and supportive feedback based on your weekly slip-probability averages.
- **Dynamic Intelligence Engine:** Calculates **Motivation Score**, **Burnout Risk**, and **Routine Strength** using custom weighted behavioral algorithms.
- **Interactive Micro-Actions:** Provides tailored recommendations (e.g., "15-minute Study Sprint") with integrated countdown timers and celebratory rewards.
- **Mistake-Proof Logging:** Intelligent "Log Overwriting" architecture allows you to correct daily entries without creating duplicates or desyncing your dashboard.
- **Premium Glassmorphism UI:** A modern, immersive interface with frosted-glass effects, moving gradients, and real-time habit visualizations.
- **Secure Authentication:** Robust JWT-based security with salted password hashing for a seamless login/registration experience.

## 🛠️ Tech Stack

- **Frontend:** HTML5, CSS3 (Vanilla Glassmorphism), JavaScript (ES6+), Chart.js, FontAwesome, Canvas-Confetti.
- **Backend:** Flask (Python), Flask-JWT-Extended, Flask-CORS, Werkzeug Security.
- **Database:** SQLite3 (Relational schema with automated log synchronization).
- **Machine Learning:** Scikit-Learn, Pandas, Joblib, NumPy.

## 🧠 Advanced Intelligence Engine

The system employs a multi-layered analytical approach:
1.  **Hybrid Ensemble Layer:** The system averages the probability from the **Champion ML Model** (ANN) with a **Deterministic Strength Score** to provide a grounded, "fail-safe" slip probability.
2.  **Deterministic Layer:** Real-time habit scoring based on validated behavioral weights:
    - **Sleep:** 25% | **Study:** 25% | **Mood:** 20%
    - **Workout:** 10% | **Reading:** 10% | **Journal:** 10%
3.  **Adaptive Feedback:** Motivational tone and badge assignments are dynamically adjusted based on the predicted psychological state and burnout risk of the user.

## 📂 Project Structure

```text
Smart Habit AI/
├── backend/               # Flask API & Intelligence Engine
│   ├── app.py             # Main entry point (JWT, Routes, Logic)
│   ├── smart_engine.py    # Hybrid ML + Rule-based Engine
│   ├── auth.py            # Secure JWT Authentication & Hashing
│   └── database.py        # SQLite schema & persistence
├── frontend/              # Vanilla JS/CSS3 Glassmorphism UI
├── model/                 # AI Model Hub
│   ├── all_models.pkl     # Library of 7 Pre-trained Classifiers
│   ├── best_model.pkl     # Primary ANN MLP Champion Model
│   └── training_summary.json # Performance stats & Model Comparison
├── archive/               # Historical development artifacts
├── model.py               # ML Training Factory (Pipeline & Scaling)
├── dataset.csv            # Synthetic behavioral training data
└── predict.py             # CLI stress-testing prediction tool
```

## ⚙️ Installation & Setup

### 1. Clone & Install
```bash
git clone https://github.com/Sneha152004/smart_habit_ai.git
cd smart_habit_ai
pip install -r backend/requirements.txt
```

### 2. Run the Application
```bash
cd backend
python app.py
```
Open **`http://127.0.0.1:5000`** to access your dashboard.

---
Developed with ❤️ to help you master your routine.
