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

from datetime import datetime, timedelta

# ... (keep existing imports)

def get_calendar_week_range():
    """Returns the start (Sunday) and end (Saturday) of the current week."""
    now = datetime.utcnow()
    # Sunday is 6 in Python's weekday() if we adjust, but standard is:
    # 0=Mon, 1=Tue, ..., 6=Sun.
    # To get to the previous Sunday:
    days_to_sunday = (now.weekday() + 1) % 7 
    sunday = now - timedelta(days=days_to_sunday)
    saturday = sunday + timedelta(days=6)
    return sunday.strftime("%Y-%m-%d"), saturday.strftime("%Y-%m-%d")

def summarize_past_weeks(user_id):
    """Automatically summarizes any completed weeks that don't have a badge yet."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Current week's Sunday
    this_sunday_str, _ = get_calendar_week_range()
    
    # Find all logs that are BEFORE this week's Sunday and NOT yet summarized
    cursor.execute('''
        SELECT date, p_slip_prob FROM daily_logs 
        WHERE user_id = ? AND date < ? 
        AND date > (SELECT COALESCE(MAX(week_end_date), '1970-01-01') FROM weekly_summaries WHERE user_id = ?)
        ORDER BY date ASC
    ''', (int(user_id), this_sunday_str, int(user_id)))
    
    unsummarized_logs = cursor.fetchall()
    if not unsummarized_logs:
        conn.close()
        return None

    # Group logs by their week-ending Saturday
    weeks_to_summarize = {}
    for log in unsummarized_logs:
        log_date = datetime.strptime(log['date'], "%Y-%m-%d")
        # Find the Saturday for this log's week
        days_to_sat = 5 - log_date.weekday()
        if days_to_sat < 0: days_to_sat += 7 # It was a Sunday
        week_end = log_date + timedelta(days=days_to_sat)
        week_end_str = week_end.strftime("%Y-%m-%d")
        
        if week_end_str not in weeks_to_summarize:
            weeks_to_summarize[week_end_str] = []
        weeks_to_summarize[week_end_str].append(log['p_slip_prob'])

    last_badge = None
    for week_end_str, probs in weeks_to_summarize.items():
        avg_p_slip = sum(probs) / len(probs)
        badge = engine.calculate_weekly_badge(avg_p_slip)
        
        cursor.execute('''
            INSERT INTO weekly_summaries (
                user_id, week_end_date, avg_p_slip, badge_name, badge_icon, supportive_message
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            int(user_id), week_end_str,
            avg_p_slip, badge['name'], badge['icon'], badge['message']
        ))
        last_badge = badge

    conn.commit()
    conn.close()
    return last_badge

@app.route('/api/log', methods=['POST'])
@jwt_required()
def log_daily_data():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    model_choice = data.get('model_choice')
    
    if not validate_habit_data(data):
        return jsonify({"error": "Invalid input value"}), 400

    try:
        insights = engine.get_insights(data, model_choice=model_choice)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Insert today's log
        cursor.execute('''
            INSERT INTO daily_logs (
                user_id, date, sleep_hours, study_hours, workout_minutes, 
                journal_minutes, reading_minutes, mood, p_slip_prob, 
                motivation_score, difficulty_adjustment, streak_protection, 
                bad_day, burnout_risk, weakest_habit, recommendation, timer_seconds, norms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            int(current_user_id), today_str,
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

        # Proactively summarize past weeks
        weekly_update = summarize_past_weeks(current_user_id)

        response_data = insights.copy()
        if weekly_update:
            response_data['weekly_badge'] = weekly_update
            
        return jsonify(response_data), 200
    except Exception as e:
        print(f"Error in /api/log: {str(e)}")
        traceback.print_exc()
        return jsonify({"msg": "Failed to process data", "error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
@jwt_required()
def get_history():
    try:
        current_user_id = get_jwt_identity()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Only fetch logs for the CURRENT calendar week
        monday_str, _ = get_calendar_week_range()
        
        logs = cursor.execute(
            'SELECT * FROM daily_logs WHERE user_id = ? AND date >= ? ORDER BY date DESC',
            (int(current_user_id), monday_str)
        ).fetchall()
        conn.close()
        # ... (rest of the formatting logic remains the same)
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

@app.route('/api/weekly_summaries', methods=['GET'])
@jwt_required()
def get_weekly_summaries():
    try:
        current_user_id = get_jwt_identity()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # New: Automatically check for and award past badges on view
        summarize_past_weeks(current_user_id)
        
        # Limit to LATEST 3 weeks only
        summaries = cursor.execute(
            'SELECT * FROM weekly_summaries WHERE user_id = ? ORDER BY week_end_date DESC LIMIT 3',
            (int(current_user_id),)
        ).fetchall()
        
        # Also get count of logs in current week
        cursor.execute('SELECT COUNT(*) FROM daily_logs WHERE user_id = ?', (int(current_user_id),))
        total_logs = cursor.fetchone()[0]
        current_week_count = total_logs % 7
        
        conn.close()
        
        summary_data = []
        for s in summaries:
            summary_data.append({
                "date": s['week_end_date'],
                "avg_p_slip": s['avg_p_slip'],
                "name": s['badge_name'],
                "icon": s['badge_icon'],
                "message": s['supportive_message']
            })
            
        return jsonify({
            "summaries": summary_data,
            "current_week_count": current_week_count
        }), 200
    except Exception as e:
        print(f"Error in weekly summaries: {str(e)}")
        return jsonify({"msg": "Failed to fetch summaries"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
