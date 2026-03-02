from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from database import get_db_connection
import sqlite3

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (data['username'], generate_password_hash(data['password']))
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"msg": "Username already exists"}), 400
    finally:
        conn.close()
        
    return jsonify({"msg": "User created successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user = cursor.execute(
        'SELECT * FROM users WHERE username = ?', (data['username'],)
    ).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], data['password']):
        access_token = create_access_token(identity=str(user['id']))
        return jsonify(access_token=access_token), 200
    
    return jsonify({"msg": "Bad username or password"}), 401
