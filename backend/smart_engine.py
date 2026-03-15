import joblib
import numpy as np
import pandas as pd
import os
import json
import traceback

class SmartHabitEngine:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_dir = os.path.join(os.path.dirname(self.base_dir), 'model')
        
        self.best_model_path = os.path.join(self.model_dir, 'best_model.pkl')
        self.all_models_path = os.path.join(self.model_dir, 'all_models.pkl')
        self.feature_cols_path = os.path.join(self.model_dir, 'feature_columns.pkl')

        try:
            self.best_model = joblib.load(self.best_model_path)
            self.all_models = joblib.load(self.all_models_path)
            self.feature_columns = joblib.load(self.feature_cols_path)
            print(f"Loaded {len(self.all_models)} models successfully.")
        except Exception as e:
            print(f"ML Models not loaded, using fallback: {str(e)}")
            self.best_model = None
            self.all_models = {}
            self.feature_columns = None

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

    def get_insights(self, data, model_choice=None):
        routine_strength, norms = self.calculate_routine_strength(data)
        motivation_score = routine_strength * 100
        p_slip_prob = 1.0 - routine_strength
        
        # Determine which model to use
        active_model = self.best_model
        model_display_name = "Advanced ML"
        
        if model_choice and model_choice in self.all_models:
            active_model = self.all_models[model_choice]
            model_display_name = model_choice.replace('_', ' ').title()
        elif self.best_model:
            # Get best model name from summary
            summary_path = os.path.join(self.model_dir, 'training_summary.json')
            if os.path.exists(summary_path):
                with open(summary_path, 'r') as f:
                    summary = json.load(f)
                    best_name = summary.get('best_model_name', 'best_model')
                    model_display_name = best_name.replace('_', ' ').title()
        
        if active_model and self.feature_columns:
            try:
                from datetime import datetime
                now = datetime.now()
                features_dict = {
                    'sleep_hours': float(data.get('sleep_hours', 0)),
                    'study_hours': float(data.get('study_hours', 0)),
                    'workout_minutes': float(data.get('workout_minutes', 0)),
                    'journalling_minutes': float(data.get('journal_minutes', 0)),
                    'reading_minutes': float(data.get('reading_minutes', 0)),
                    'mood': float(data.get('mood', 3)),
                    'day_of_week': now.weekday(),
                    'is_weekend': 1 if now.weekday() in [5, 6] else 0
                }
                features_df = pd.DataFrame([features_dict])
                # Ensure correct column order
                features_df = features_df[self.feature_columns]
                
                ml_prob = active_model.predict_proba(features_df)[0][1]
                p_slip_prob = (p_slip_prob + ml_prob) / 2
            except Exception as e:
                print(f"ML error: {e}")
                traceback.print_exc()

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
        weak_habits = [h for h, v in norms.items() if v < 0.6]
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

        primary_weakest = min(norms, key=norms.get)
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
            "model_name": model_display_name,
            "p_slip_class": int(p_slip_class),
            "motivation_score": round(motivation_score, 1),
            "difficulty_adjustment": difficulty,
            "streak_protection": bool(streak_protection),
            "bad_day": bool(bad_day),
            "burnout_risk": round(float(burnout_risk), 2),
            "weakest_habit": primary_weakest,
            "recommendations": all_recommendations,
            "recommendation": all_recommendations[0]["text"],
            "timer_seconds": all_recommendations[0]["duration"],
            "mood": int(data.get('mood', 3)),
            "norms": norms
        }
