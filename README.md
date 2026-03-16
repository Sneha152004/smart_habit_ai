# Smart Habit AI 🧠✨

Smart Habit AI is a premium, full-stack habit tracking application that uses an ensemble of machine learning models and a rule-based intelligence engine to optimize your daily routine. It predicts behavioral "slips" and provides proactive, psychologically-informed coaching to ensure long-term consistency.

![Dashboard Preview](interfaces/Screenshot%202026-02-16%20201036.png)

## 🚀 Key Features

- **Ensemble AI Slip Prediction:** Uses a consensus of **7 different AI classifiers** (ANN, Random Forest, SVM, etc.) to predict routine instability with high precision.
- **Weekly Adaptive Badges:** A calendar-aware (Sun-Sat) reward system that assigns psychological badges and supportive feedback based on your weekly performance.
- **Dynamic Intelligence Engine:** Calculates **Motivation Score**, **Burnout Risk**, and **Routine Strength** using custom weighted algorithms.
- **Interactive Micro-Actions:** Provides tailored recommendations (e.g., "20-minute Study Sprint") with integrated timers and celebratory rewards.
- **Mistake-Proof Logging:** Intelligent "Log Overwriting" allows you to correct daily entries without creating duplicates or desyncing your dashboard.
- **Premium Glassmorphism UI:** A modern, immersive interface with moving gradients, staggered animations, and real-time habit breakdown visualizations.
- **Secure Authentication:** Robust JWT-based security with a seamless login/registration experience.

## 🛠️ Tech Stack

- **Frontend:** HTML5, CSS3 (Vanilla), JavaScript (ES6+), Chart.js, FontAwesome, Canvas-Confetti.
- **Backend:** Flask (Python), Flask-JWT-Extended, Flask-CORS.
- **Database:** SQLite3 (Direct schema management with automated migrations).
- **Machine Learning:** Scikit-Learn, Pandas, Joblib, NumPy.

## 🧠 Advanced Intelligence Engine

The system employs a multi-layered analytical approach:
1.  **Ensemble Layer:** Parallel predictions from 7 pre-trained models are averaged to provide a stable, "wisdom of the crowd" slip probability.
2.  **Deterministic Layer:** Real-time habit scoring based on validated behavioral weights:
    - **Sleep:** 25% | **Study:** 25% | **Mood:** 20%
    - **Workout:** 10% | **Reading:** 10% | **Journal:** 10%
3.  **Adaptive Feedback:** Motivational tone and badge assignments are dynamically adjusted based on the predicted psychological state of the user.

## 📂 Project Structure

```text
Smart Habit AI/
├── backend/               # Flask API & Intelligence Engine
│   ├── app.py             # Main entry point (JWT, Routes)
│   ├── smart_engine.py    # Multi-model Ensemble logic
│   └── database.py        # SQLite schema & persistence
├── frontend/              # Vanilla JS/CSS3 Glassmorphism UI
├── model/                 # AI Model Hub
│   ├── all_models.pkl     # 7-model Ensemble (ANN, RF, SVM, etc.)
│   ├── best_model.pkl     # Primary ANN MLP model
│   └── training_summary.json # Accuracy & Performance stats
├── archive/               # Historical development artifacts
├── model.py               # Advanced Model Training Factory
├── dataset.csv            # Synthetic training data
└── predict.py             # CLI prediction tool
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
