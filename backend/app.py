from flask import Flask, request, jsonify, send_from_directory
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
from database import get_db_connection, init_db
from auth import auth_bp
from smart_engine import SmartHabitEngine
from datetime import datetime
import os
import json
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

app.config['JWT_SECRET_KEY'] = 'super-secret-habit-tracker-key-32-chars-long!!'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False

jwt = JWTManager(app)
engine = SmartHabitEngine()

app.register_blueprint(auth_bp, url_prefix='/api/auth')

init_db()

def validate_habit_data(data):
    """Task 1: Backend Input Validation"""
    try:
        # Check required fields and numeric types
        rules = {
            'sleep_hours': (0, 24),
            'study_hours': (0, 24),
            'workout_minutes': (0, 180),
            'journal_minutes': (0, 120),
            'reading_minutes': (0, 180)
        }
        
        for field, (min_val, max_val) in rules.items():
            if field not in data:
                return False
            val = float(data[field])
            if not (min_val <= val <= max_val):
                return False
                
        # Mood validation: 1 to 5 (integer only)
        if 'mood' not in data:
            return False
        mood = data['mood']
        if not isinstance(mood, int) or not (1 <= mood <= 5):
            return False
            
        return True
    except (ValueError, TypeError):
        return False

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(FRONTEND_DIR, path)

@app.route('/api/log', methods=['POST'])
@jwt_required()
def log_daily_data():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # Task 1: Validation
    if not validate_habit_data(data):
        return jsonify({"error": "Invalid input value"}), 400

    try:
        insights = engine.get_insights(data)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO daily_logs (
                user_id, date, sleep_hours, study_hours, workout_minutes, 
                journal_minutes, reading_minutes, mood, p_slip_prob, 
                motivation_score, difficulty_adjustment, streak_protection, 
                bad_day, burnout_risk, weakest_habit, recommendation, timer_seconds, norms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            int(current_user_id), datetime.utcnow().strftime("%Y-%m-%d"),
            data['sleep_hours'], data['study_hours'], data['workout_minutes'],
            data['journal_minutes'], data['reading_minutes'], insights['mood'],
            insights['p_slip_prob'], insights['motivation_score'],
            insights['difficulty_adjustment'], 1 if insights['streak_protection'] else 0,
            1 if insights['bad_day'] else 0, insights['burnout_risk'],
            insights['weakest_habit'], insights['recommendation'], insights['timer_seconds'],
            json.dumps(insights['norms'])
        ))
        conn.commit()
        conn.close()
        return jsonify(insights), 200
    except Exception as e:
        print(f"Error in /api/log: {str(e)}")
        traceback.print_exc()
        return jsonify({"msg": "Failed to process data", "error": str(e)}), 500

@app.route('/history', methods=['GET']) # Task 3: New Route Only
@app.route('/api/history', methods=['GET'])
@jwt_required()
def get_history():
    try:
        current_user_id = get_jwt_identity()
        conn = get_db_connection()
        cursor = conn.cursor()
        logs = cursor.execute(
            'SELECT * FROM daily_logs WHERE user_id = ? ORDER BY id DESC',
            (int(current_user_id),)
        ).fetchall()
        conn.close()
        history_data = []
        for log in logs:
            history_data.append({
                "date": log['date'],
                "p_slip_prob": log['p_slip_prob'],
                "motivation_score": log['motivation_score'],
                "difficulty_adjustment": log['difficulty_adjustment'],
                "streak_protection": bool(log['streak_protection']),
                "bad_day": bool(log['bad_day']),
                "burnout_risk": log['burnout_risk'],
                "weakest_habit": log['weakest_habit'],
                "recommendations": json.loads(log['norms']) if log['norms'] else [], # Fallback or use a better way to store? Let's fix this properly.
                "recommendation": log['recommendation'],
                "timer_seconds": log['timer_seconds'],
                "mood": log['mood'],
                "norms": json.loads(log['norms']) if log['norms'] else None
            })
        return jsonify(history_data), 200
    except Exception as e:
        print(f"Error in /api/history: {str(e)}")
        return jsonify({"msg": "Failed to fetch history"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
