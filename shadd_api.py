#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from shadd_filter import ShaddMessageFilter, ShaddCallFilter, ShaddBehaviorAnalyzer
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
message_filter = ShaddMessageFilter()
call_filter = ShaddCallFilter()
behavior_analyzer = ShaddBehaviorAnalyzer()

DB_FILE = 'shadd_accounts.db'

def init_db():
    """ایجاد پایگاه داده"""
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE users
                     (username TEXT PRIMARY KEY,
                      email TEXT,
                      status TEXT DEFAULT 'active',
                      created_at TEXT)''')
        conn.commit()
        conn.close()

def register_user(username, email):
    """ثبت‌نام کاربر"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users VALUES (?, ?, ?, ?)',
                  (username, email, 'active', datetime.now().isoformat()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def is_user_banned(username):
    """بررسی بن شدن کاربر"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT status FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 'banned'

def ban_user(username):
    """بن کردن کاربر"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE users SET status = ? WHERE username = ?', ('banned', username))
    conn.commit()
    conn.close()

# ============================================
# 🏠 صفحه اصلی
# ============================================

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'name': '🚀 API فیلتری شاد',
        'version': '1.0.0',
        'status': '✅ فعال',
        'features': ['✓ فیلتری فحاشی', '✓ فیلتری تماس', '✓ تحلیل رفتار'],
    }), 200

# ============================================
# 👤 کاربران
# ============================================

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    
    if not username:
        return jsonify({'error': '❌ نام کاربری الزامی'}), 400
    
    if register_user(username, email):
        return jsonify({'success': True, 'message': f'✅ {username} ثبت‌نام شد'}), 201
    return jsonify({'error': '❌ کاربر قبلاً ثبت‌نام شده'}), 400

# ============================================
# 💬 پیام‌ها
# ============================================

@app.route('/check-message', methods=['POST'])
def check_message():
    data = request.get_json()
    username = data.get('username')
    message = data.get('message')
    
    if not username or not message:
        return jsonify({'error': '❌ نام کاربری و پیام الزامی'}), 400
    
    if is_user_banned(username):
        return jsonify({'blocked': True, 'reason': '🔒 اکانت بن شده'}), 403
    
    result = message_filter.check_message(message, username)
    
    if result['is_banned']:
        ban_user(username)
        return jsonify({
            'filter_result': result,
            'auto_banned': True,
            'message': '🔒 اکانت خودکار بن شد!'
        }), 403
    
    return jsonify({'filter_result': result}), 200

# ============================================
# ☎️ تماس‌ها
# ============================================

@app.route('/check-call', methods=['POST'])
def check_call():
    data = request.get_json()
    caller = data.get('caller')
    receiver = data.get('receiver')
    duration = data.get('duration', 0)
    
    if not caller or not receiver:
        return jsonify({'error': '❌ نام فراخوان و گیرنده الزامی'}), 400
    
    if is_user_banned(caller):
        return jsonify({'blocked': True, 'reason': '🔒 اکانت بن شده'}), 403
    
    result = call_filter.check_call(caller, receiver, duration)
    return jsonify({'filter_result': result}), 200

# ============================================
# 📊 رفتار
# ============================================

@app.route('/analyze-behavior', methods=['POST'])
def analyze_behavior():
    data = request.get_json()
    username = data.get('username')
    activities = data.get('activities', [])
    
    if not username:
        return jsonify({'error': '❌ نام کاربری الزامی'}), 400
    
    result = behavior_analyzer.analyze_user(username, activities)
    return jsonify({'analysis': result}), 200

# ============================================
# 🔒 بن
# ============================================

@app.route('/ban/<username>', methods=['POST'])
def manual_ban(username):
    ban_user(username)
    return jsonify({'success': True, 'message': f'🔒 {username} بن شد'}), 200

if __name__ == '__main__':
    init_db()
    print("""
╔════════════════════════════════════════╗
║  🚀 API شاد شروع شد                   ║
║  🌐 http://localhost:5001            ║
║  ✅ فیلتری فحاشی: فعال               ║
╚════════════════════════════════════════╝
    """)
    app.run(debug=True, port=5001)
