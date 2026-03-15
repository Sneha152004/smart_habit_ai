from flask import Flask, request, jsonify, send_from_directory
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
from database import get_db_connection, init_db
from auth import auth_bp
from smart_engine import SmartHabitEngine
from datetime import datetime, timedelta
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
    try:
        rules = {
            'sleep_hours': (0, 24),
            'study_hours': (0, 24),
            'workout_minutes': (0, 180),
            'journal_minutes': (0, 120),
            'reading_minutes': (0, 180)
        }
        for field, (min_val, max_val) in rules.items():
            if field not in data: return False
            val = float(data[field])
            if not (min_val <= val <= max_val): return False
        if 'mood' not in data: return False
        mood = data['mood']
        if not isinstance(mood, int) or not (1 <= mood <= 5): return False
        return True
    except (ValueError, TypeError): return False

@app.route('/')
def index(): return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def static_proxy(path): return send_from_directory(FRONTEND_DIR, path)

def get_calendar_week_range():
    now = datetime.utcnow()
    days_to_sunday = (now.weekday() + 1) % 7 
    sunday = now - timedelta(days=days_to_sunday)
    saturday = sunday + timedelta(days=6)
    return sunday.strftime("%Y-%m-%d"), saturday.strftime("%Y-%m-%d")

def summarize_past_weeks(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    this_sunday_str, _ = get_calendar_week_range()
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
    weeks_to_summarize = {}
    for log in unsummarized_logs:
        log_date = datetime.strptime(log['date'], "%Y-%m-%d")
        days_to_sat = 5 - log_date.weekday()
        if days_to_sat < 0: days_to_sat += 7
        week_end = log_date + timedelta(days=days_to_sat)
        week_end_str = week_end.strftime("%Y-%m-%d")
        if week_end_str not in weeks_to_summarize: weeks_to_summarize[week_end_str] = []
        weeks_to_summarize[week_end_str].append(log['p_slip_prob'])
    last_badge = None
    for week_end_str, probs in weeks_to_summarize.items():
        avg_p_slip = sum(probs) / len(probs)
        badge = engine.calculate_weekly_badge(avg_p_slip)
        cursor.execute('''
            INSERT INTO weekly_summaries (user_id, week_end_date, avg_p_slip, badge_name, badge_icon, supportive_message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (int(user_id), week_end_str, avg_p_slip, badge['name'], badge['icon'], badge['message']))
        last_badge = badge
    conn.commit()
    conn.close()
    return last_badge

@app.route('/api/log', methods=['POST'])
@jwt_required()
def log_daily_data():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    try:
        if not validate_habit_data(data): return jsonify({"error": "Invalid input"}), 400
        insights = engine.get_insights(data)
        conn = get_db_connection()
        cursor = conn.cursor()
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        cursor.execute('SELECT id FROM daily_logs WHERE user_id = ? AND date = ?', (int(current_user_id), today_str))
        existing_log = cursor.fetchone()
        
        if existing_log:
            cursor.execute('''
                UPDATE daily_logs SET 
                    sleep_hours=?, study_hours=?, workout_minutes=?, 
                    journal_minutes=?, reading_minutes=?, mood=?, p_slip_prob=?, 
                    motivation_score=?, difficulty_adjustment=?, streak_protection=?, 
                    bad_day=?, burnout_risk=?, weakest_habit=?, recommendation=?, 
                    timer_seconds=?, norms=?, recommendations=?
                WHERE id = ?
            ''', (
                data['sleep_hours'], data['study_hours'], data['workout_minutes'],
                data['journal_minutes'], data['reading_minutes'], insights['mood'],
                insights['p_slip_prob'], insights['motivation_score'],
                insights['difficulty_adjustment'], 1 if insights['streak_protection'] else 0,
                1 if insights['bad_day'] else 0, insights['burnout_risk'],
                insights['weakest_habit'], insights['recommendation'], insights['timer_seconds'],
                json.dumps(insights['norms']), json.dumps(insights['recommendations']), existing_log['id']
            ))
        else:
            cursor.execute('''
                INSERT INTO daily_logs (
                    user_id, date, sleep_hours, study_hours, workout_minutes, 
                    journal_minutes, reading_minutes, mood, p_slip_prob, 
                    motivation_score, difficulty_adjustment, streak_protection, 
                    bad_day, burnout_risk, weakest_habit, recommendation, timer_seconds, norms, recommendations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                int(current_user_id), today_str,
                data['sleep_hours'], data['study_hours'], data['workout_minutes'],
                data['journal_minutes'], data['reading_minutes'], insights['mood'],
                insights['p_slip_prob'], insights['motivation_score'],
                insights['difficulty_adjustment'], 1 if insights['streak_protection'] else 0,
                1 if insights['bad_day'] else 0, insights['burnout_risk'],
                insights['weakest_habit'], insights['recommendation'], insights['timer_seconds'],
                json.dumps(insights['norms']), json.dumps(insights['recommendations'])
            ))
        conn.commit()
        conn.close()
        weekly_update = summarize_past_weeks(current_user_id)
        response_data = insights.copy()
        if weekly_update: response_data['weekly_badge'] = weekly_update
        return jsonify(response_data), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"msg": "Error", "error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
@jwt_required()
def get_history():
    try:
        current_user_id = get_jwt_identity()
        conn = get_db_connection()
        cursor = conn.cursor()
        monday_str, _ = get_calendar_week_range()
        logs = cursor.execute(
            'SELECT * FROM daily_logs WHERE user_id = ? AND date >= ? ORDER BY date DESC, id DESC',
            (int(current_user_id), monday_str)
        ).fetchall()
        conn.close()
        history_data = []
        for log in logs:
            try:
                recs_json = log['recommendations'] if 'recommendations' in log.keys() else None
                recs = json.loads(recs_json) if recs_json else [{"habit": log['weakest_habit'], "text": log['recommendation'], "duration": log['timer_seconds']}]
            except:
                recs = [{"habit": log['weakest_habit'], "text": log['recommendation'], "duration": log['timer_seconds']}]
            
            history_data.append({
                "date": log['date'], "p_slip_prob": log['p_slip_prob'],
                "motivation_score": log['motivation_score'], "difficulty_adjustment": log['difficulty_adjustment'],
                "streak_protection": bool(log['streak_protection']), "bad_day": bool(log['bad_day']),
                "burnout_risk": log['burnout_risk'], "weakest_habit": log['weakest_habit'],
                "recommendations": recs, "recommendation": log['recommendation'],
                "timer_seconds": log['timer_seconds'], "mood": log['mood'],
                "norms": json.loads(log['norms']) if log['norms'] else None
            })
        return jsonify(history_data), 200
    except Exception as e:
        return jsonify({"msg": "Error"}), 500

@app.route('/api/weekly_summaries', methods=['GET'])
@jwt_required()
def get_weekly_summaries():
    try:
        current_user_id = get_jwt_identity()
        conn = get_db_connection()
        cursor = conn.cursor()
        summarize_past_weeks(current_user_id)
        summaries = cursor.execute(
            'SELECT * FROM weekly_summaries WHERE user_id = ? ORDER BY week_end_date DESC LIMIT 3',
            (int(current_user_id),)
        ).fetchall()
        cursor.execute('SELECT COUNT(*) FROM daily_logs WHERE user_id = ?', (int(current_user_id),))
        total_logs = cursor.fetchone()[0]
        conn.close()
        summary_data = []
        for s in summaries:
            summary_data.append({
                "date": s['week_end_date'], "avg_p_slip": s['avg_p_slip'],
                "name": s['badge_name'], "icon": s['badge_icon'], "message": s['supportive_message']
            })
        return jsonify({"summaries": summary_data, "current_week_count": total_logs % 7}), 200
    except Exception as e: return jsonify({"msg": "Error"}), 500

@app.route('/api/user_stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    try:
        current_user_id = get_jwt_identity()
        conn = get_db_connection()
        user = conn.execute('SELECT level, total_xp, current_streak FROM users WHERE id = ?', (int(current_user_id),)).fetchone()
        conn.close()
        return jsonify({"level": user['level'], "total_xp": user['total_xp'], "next_level_xp": 500, "current_streak": user['current_streak']}), 200
    except Exception as e: return jsonify({"msg": "Error"}), 500

if __name__ == '__main__':
    sunday_str, saturday_str = get_calendar_week_range()
    print(f"INFO: Current tracking week is Sunday, {datetime.strptime(sunday_str, '%Y-%m-%d').strftime('%b %d')} to Saturday, {datetime.strptime(saturday_str, '%Y-%m-%d').strftime('%b %d')}")
    app.run(debug=True, port=5000)
