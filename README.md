# Smart Habit AI 🧠✨

Smart Habit AI is a premium, full-stack habit tracking application that uses machine learning and a rule-based intelligence engine to optimize your daily routine. It predicts potential "slips" in consistency and provides real-time, actionable micro-recommendations to keep you on track.

![Dashboard Preview](interfaces/Screenshot%202026-02-16%20201036.png)

## 🚀 Key Features

- **AI-Powered Slip Prediction:** Uses a Logistic Regression model to calculate your probability of breaking a habit streak based on daily stats.
- **Dynamic Intelligence Engine:** Calculates **Motivation Score**, **Burnout Risk**, and **Routine Strength** using custom weighted algorithms.
- **Interactive Micro-Actions:** Provides tailored recommendations (e.g., "20-minute Study Sprint") with integrated rounded timers and completion rewards.
- **Visual Habit Breakdown:** Real-time, color-coded stability bars (Red/Yellow/Teal) that visualize your habit performance.
- **Gentle Mode:** Automatically detects "Bad Days" based on mood and sleep, adjusting the dashboard to prioritize self-compassion and rest.
- **Premium UI/UX:** Features a glassmorphism design, moving gradients, staggered animations, and celebratory confetti effects.
- **Secure Authentication:** Robust JWT-based Login and Registration system with a modern split-view interface.
- **Theme Support:** Fully functional Light and Dark modes.

## 🛠️ Tech Stack

- **Frontend:** HTML5, CSS3 (Vanilla), JavaScript (ES6+), FontAwesome, Canvas-Confetti.
- **Backend:** Flask (Python), Flask-JWT-Extended, Flask-CORS.
- **Database:** SQLite3 (Direct schema management).
- **Machine Learning:** Scikit-Learn, Pandas, Joblib, NumPy.

## 📈 ML Pipeline

The system utilizes a two-layered logic architecture:
1.  **ML Layer:** A pre-trained Logistic Regression model predicts the `p_slip` probability.
2.  **Logic Layer:** A deterministic engine calculates routine strength using specific weights:
    - **Sleep:** 25% | **Study:** 25% | **Mood:** 20%
    - **Workout:** 10% | **Reading:** 10% | **Journal:** 10%

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.9+
- Pip (Python package manager)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/smart-habit-ai.git
cd smart-habit-ai
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Initialize the Model (Optional)
If you need to retrain the model with the 6 core features:
```bash
python train_model.py
```

### 4. Run the Application
Navigate to the backend directory and start the Flask server:
```bash
cd backend
python app.py
```

### 5. Access the App
Open your browser and navigate to:
**`http://127.0.0.1:5000`**

## 📂 Project Structure

```text
├── backend/
│   ├── app.py             # Flask Entry Point
│   ├── auth.py            # JWT Authentication Logic
│   ├── database.py        # SQLite Schema & Connection
│   └── smart_engine.py    # AI & Rule-Based Logic Engine
├── frontend/
│   ├── index.html         # Main UI Structure
│   ├── style.css          # Premium Styling & Animations
│   └── script.js          # Dynamic UI & API Integration
├── model/
│   ├── feature_scaler.pkl # Pre-trained Scaler
│   └── logistic_regression_model.pkl # Trained ML Model
└── train_model.py         # Model training script
```

---
Developed with ❤️ to help you master your routine.
