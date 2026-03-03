import joblib
import numpy as np
import pandas as pd
import os
import traceback

class SmartHabitEngine:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_dir = os.path.join(os.path.dirname(self.base_dir), 'model')
        
        self.model_path = os.path.join(self.model_dir, 'logistic_regression_model.pkl')
        self.scaler_path = os.path.join(self.model_dir, 'feature_scaler.pkl')

        try:
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            print("Models loaded successfully.")
        except Exception as e:
            print(f"ML Model not loaded, using deterministic fallback: {str(e)}")
            self.model = None
            self.scaler = None

    def calculate_routine_strength(self, data):
        # Normalization from Pipeline PDF Page 1
        norms = {
            'sleep': float(data.get('sleep_hours', 0)) / 8.0,
            'study': float(data.get('study_hours', 0)) / 5.0,
            'workout': float(data.get('workout_minutes', 0)) / 60.0,
            'journal': float(data.get('journal_minutes', 0)) / 30.0,
            'reading': float(data.get('reading_minutes', 0)) / 60.0,
            'mood': float(data.get('mood', 0)) / 5.0
        }
        
        # Weights from Pipeline PDF Page 4
        # 0.25*sleep + 0.25*study + 0.20*mood + 0.10*workout + 0.10*reading + 0.10*journal
        strength = (
            0.25 * norms['sleep'] +
            0.25 * norms['study'] +
            0.20 * norms['mood'] +
            0.10 * norms['workout'] +
            0.10 * norms['reading'] +
            0.10 * norms['journal']
        )
        return min(strength, 1.0), norms

    def get_insights(self, data):
        routine_strength, norms = self.calculate_routine_strength(data)
        motivation_score = routine_strength * 100

        # Deterministic Base (Pipeline Page 1)
        p_slip_prob = 1.0 - routine_strength
        
        if self.model and self.scaler:
            try:
                # Prepare data for ML refine
                features_df = pd.DataFrame([{
                    'sleep_hours': float(data['sleep_hours']),
                    'study_hours': float(data['study_hours']),
                    'workout_minutes': float(data['workout_minutes']),
                    'journal_minutes': float(data['journal_minutes']),
                    'reading_minutes': float(data['reading_minutes']),
                    'mood': float(data['mood'])
                }])
                scaled_X = self.scaler.transform(features_df)
                ml_prob = self.model.predict_proba(scaled_X)[0][1]
                # Refine slip probability with ML prediction
                p_slip_prob = (p_slip_prob + ml_prob) / 2
            except Exception as e:
                print(f"ML refine error: {e}")

        p_slip_class = 1 if p_slip_prob > 0.6 else 0

        # Dynamic Difficulty Adjustment (Pipeline Page 3)
        difficulty = "Maintain"
        if motivation_score < 40:
            difficulty = "Reduce difficulty by 20-30%"
        elif motivation_score > 75:
            difficulty = "Increase challenge slightly"

        # Burnout Detection (Pipeline Page 6)
        burnout_risk = ((norms['study'] + norms['workout']) / 2) * (1 - norms['mood'])

        # Bad Day Detection (Pipeline Page 5)
        bad_day = norms['mood'] < 0.4 and norms['sleep'] < 0.6

        # Streak Protection Mode (Pipeline Page 4)
        streak_protection = p_slip_prob > 0.7

        # Micro-Recommendations (Pipeline Page 4)
        # Find all habits that are "weak" (below 0.6 norm)
        weak_habits = [h for h, v in norms.items() if v < 0.6]
        # If none are below 0.6, just take the minimum one
        if not weak_habits:
            weak_habits = [min(norms, key=norms.get)]
        
        all_recommendations = []
        for habit in weak_habits:
            h_norm = norms[habit]
            dynamic_mins = max(5, round(((1.0 - h_norm) * 30) / 5) * 5)
            dynamic_seconds = dynamic_mins * 60
            
            recs_map = {
                'sleep': {"text": "Sleep 30 minutes earlier tonight.", "duration": 0},
                'study': {"text": f"Try a {dynamic_mins}-minute focused study session.", "duration": dynamic_seconds},
                'workout': {"text": f"Do a {dynamic_mins}-minute light workout.", "duration": dynamic_seconds},
                'journal': {"text": f"Write for {dynamic_mins} minutes about your day.", "duration": dynamic_seconds},
                'reading': {"text": f"Read for {dynamic_mins} minutes.", "duration": dynamic_seconds},
                'mood': {"text": "Take a 5-minute deep breathing break.", "duration": 300}
            }
            
            # Streak Protection Overrides
            if streak_protection:
                if habit == 'study':
                    recs_map['study'] = {"text": "Mini Session: 15 minutes study.", "duration": 900}
                elif habit == 'workout':
                    recs_map['workout'] = {"text": "Mini Session: 5 minute stretch.", "duration": 300}
            
            res_rec = recs_map.get(habit)
            if res_rec:
                all_recommendations.append({
                    "habit": habit,
                    "text": res_rec["text"],
                    "duration": res_rec["duration"]
                })

        # For backward compatibility and breakdown pinpointing
        primary_weakest = min(norms, key=norms.get)

        # Task 2: Slip Percentage Category Messaging
        slip_percentage = round(float(p_slip_prob) * 100)
        category = "On Track"
        if 31 <= slip_percentage <= 60:
            category = "Moderate Risk"
        elif 61 <= slip_percentage <= 80:
            category = "High Risk"
        elif 81 <= slip_percentage <= 100:
            category = "Very High Risk"

        return {
            "p_slip_prob": round(float(p_slip_prob), 2),
            "slip_percentage": slip_percentage,
            "category": category,
            "p_slip_class": int(p_slip_class),
            "motivation_score": round(motivation_score, 1),
            "difficulty_adjustment": difficulty,
            "streak_protection": bool(streak_protection),
            "bad_day": bool(bad_day),
            "burnout_risk": round(float(burnout_risk), 2),
            "weakest_habit": primary_weakest,
            "recommendations": all_recommendations, # New multi-rec field
            "recommendation": all_recommendations[0]["text"], # Primary for display
            "timer_seconds": all_recommendations[0]["duration"], # Primary for display
            "mood": int(data.get('mood', 3)),
            "norms": norms
        }
