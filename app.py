#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from ban_system import BanSystem
from sorush_filter import SorushMessageFilter, SorushCallFilter, SorushBehaviorAnalyzer
from datetime import datetime
import json

app = Flask(__name__)
ban_system = BanSystem('sorush_accounts.db')
message_filter = SorushMessageFilter()
call_filter = SorushCallFilter()
behavior_analyzer = SorushBehaviorAnalyzer()

# ============================================
# 🏠 صفحه اصلی
# ============================================

@app.route('/', methods=['GET'])
def home():
    """صفحه اصلی سیستم"""
    return jsonify({
        'name': '🔒 سیستم فیلتری و بن سروش',
        'version': '2.0.0',
        'status': '✅ فعال',
        'description': 'سیستم فیلتری پیشرفته برای سروش',
        'features': [
            '✓ فیلترینگ پیام‌ها',
            '✓ فیلترینگ تماس‌ها',
            '✓ تحلیل رفتار',
            '✓ بن خودکار',
            '✓ سیستم امتیاز',
        ],
        'endpoints': {
            'register': {'method': 'POST', 'path': '/register'},
            'check_message': {'method': 'POST', 'path': '/check-message'},
            'check_call': {'method': 'POST', 'path': '/check-call'},
            'user_status': {'method': 'GET', 'path': '/user-status/<username>'},
            'banned_users': {'method': 'GET', 'path': '/banned-users'},
            'manual_ban': {'method': 'POST', 'path': '/manual-ban'},
            'analyze_behavior': {'method': 'POST', 'path': '/analyze-behavior'},
        }
    }), 200

# ============================================
# 👤 مدیریت کاربران
# ============================================

@app.route('/register', methods=['POST'])
def register():
    """ثبت‌نام کاربر جدید"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        
        if not username:
            return jsonify({'error': '❌ نام کاربری الزامی است'}), 400
        
        success, message = ban_system.register_user(username, email)
        
        return jsonify({
            'success': success,
            'message': message,
            'username': username,
            'timestamp': datetime.now().isoformat()
        }), 201 if success else 400
    except Exception as e:
        return jsonify({'error': f'❌ خطا: {str(e)}'}), 500

@app.route('/user-status/<username>', methods=['GET'])
def user_status(username):
    """دریافت وضعیت کاربر"""
    try:
        status = ban_system.get_user_status(username)
        
        if not status:
            return jsonify({
                'error': '❌ کاربر پیدا نشد',
                'username': username
            }), 404
        
        return jsonify({
            'username': username,
            'status': status,
            'is_banned': ban_system.is_user_banned(username),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': f'❌ خطا: {str(e)}'}), 500

@app.route('/banned-users', methods=['GET'])
def banned_users():
    """دریافت تمام کاربران بن شده"""
    try:
        users = ban_system.get_banned_users()
        return jsonify({
            'total': len(users),
            'banned_users': users,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': f'❌ خطا: {str(e)}'}), 500

# ============================================
# 💬 فیلترینگ پیام‌ها
# ============================================

@app.route('/check-message', methods=['POST'])
def check_message():
    """بررسی پیام برای تخلفات"""
    try:
        data = request.get_json()
        username = data.get('username')
        message = data.get('message')
        
        if not username or not message:
            return jsonify({'error': '❌ نام کاربری و پیام الزامی است'}), 400
        
        # بررسی اینکه کاربر بن شده است
        if ban_system.is_user_banned(username):
            return jsonify({
                'blocked': True,
                'reason': '🔒 اکانت بن شده است',
                'username': username,
                'timestamp': datetime.now().isoformat()
            }), 403
        
        # فیلترینگ پیام
        filter_result = message_filter.check_message(message, username)
        
        response = {
            'username': username,
            'message_length': len(message),
            'filter_result': filter_result,
            'timestamp': datetime.now().isoformat()
        }
        
        # اگر تخلف شناسایی شد
        if filter_result['has_violation']:
            response['action'] = filter_result['action']
            response['violations_count'] = len(filter_result['violations'])
            response['total_risk'] = filter_result['total_risk']
            
            # بن خودکار اگر امتیاز از 100 تجاوز کنه
            if filter_result['is_banned']:
                ban_system.manual_ban(
                    username,
                    f'تخلفات متعدد - امتیاز خطر: {filter_result["total_risk"]}',
                    'خودکار'
                )
                response['auto_banned'] = True
                response['ban_message'] = '🔒 اکانت خودکار بن شد!'
                return jsonify(response), 403
        
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': f'❌ خطا: {str(e)}'}), 500

# ============================================
# ☎️ فیلترینگ تماس‌ها
# ============================================

@app.route('/check-call', methods=['POST'])
def check_call():
    """بررسی تماس برای رفتار مشکوک"""
    try:
        data = request.get_json()
        caller = data.get('caller')
        receiver = data.get('receiver')
        duration = data.get('duration', 0)
        
        if not caller or not receiver:
            return jsonify({'error': '❌ نام فراخوان و گیرنده الزامی است'}), 400
        
        # بررسی اینکه کاربر بن شده است
        if ban_system.is_user_banned(caller):
            return jsonify({
                'blocked': True,
                'reason': '🔒 اکانت بن شده است',
                'caller': caller,
                'timestamp': datetime.now().isoformat()
            }), 403
        
        # فیلترینگ تماس
        call_result = call_filter.check_call(caller, receiver, duration)
        
        return jsonify({
            'caller': caller,
            'receiver': receiver,
            'duration': duration,
            'filter_result': call_result,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': f'❌ خطا: {str(e)}'}), 500

# ============================================
# 📊 تحلیل رفتار
# ============================================

@app.route('/analyze-behavior', methods=['POST'])
def analyze_behavior():
    """تحلیل رفتار کاربر"""
    try:
        data = request.get_json()
        username = data.get('username')
        activities = data.get('activities', [])
        
        if not username:
            return jsonify({'error': '❌ نام کاربری الزامی است'}), 400
        
        # تحلیل رفتار
        analysis = behavior_analyzer.analyze_user(username, activities)
        
        return jsonify({
            'username': username,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': f'❌ خطا: {str(e)}'}), 500

# ============================================
# 🔒 مدیریت بن
# ============================================

@app.route('/manual-ban', methods=['POST'])
def manual_ban():
    """بن دستی کاربر"""
    try:
        data = request.get_json()
        username = data.get('username')
        reason = data.get('reason', 'تخلف')
        
        if not username:
            return jsonify({'error': '❌ نام کاربری الزامی است'}), 400
        
        success = ban_system.manual_ban(username, reason)
        
        return jsonify({
            'success': success,
            'username': username,
            'reason': reason,
            'message': f'🔒 اکانت {username} بن شد' if success else '❌ خطا در بن کردن',
            'timestamp': datetime.now().isoformat()
        }), 200 if success else 400
    except Exception as e:
        return jsonify({'error': f'❌ خطا: {str(e)}'}), 500

# ============================================
# 🧪 تست سیستم
# ============================================

@app.route('/test', methods=['POST'])
def test_system():
    """تست سیستم"""
    try:
        test_username = 'test_user_123'
        test_email = 'test@sorush.com'
        
        # 1. ثبت‌نام
        reg_result = ban_system.register_user(test_username, test_email)
        
        # 2. بررسی پیام
        msg_result = message_filter.check_message('سلام', test_username)
        
        # 3. بررسی تماس
        call_result = call_filter.check_call(test_username, 'other_user', 120)
        
        return jsonify({
            'registration': {'success': reg_result[0], 'message': reg_result[1]},
            'message_filter': msg_result,
            'call_filter': call_result,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': f'❌ خطا: {str(e)}'}), 500

# ============================================
# ❌ مدیریت خطاها
# ============================================

@app.errorhandler(404)
def not_found(error):
    """صفحه پیدا نشد"""
    return jsonify({'error': '❌ صفحه پیدا نشد'}), 404

@app.errorhandler(500)
def internal_error(error):
    """خطای سرور"""
    return jsonify({'error': '❌ خطای داخلی سرور'}), 500

# ============================================
# 🚀 اجرای اپلیکیشن
# ============================================

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════╗
    ║  🚀 سیستم فیلتری سروش شروع شد               ║
    ║                                            ║
    ║  🌐 آدرس: http://localhost:5000          ║
    ║  ✅ وضعیت: فعال                           ║
    ║  🔒 فیلترینگ: فعال                        ║
    ║  📊 تحلیل: فعال                           ║
    ║                                            ║
    ║  💾 پایگاه داده: sorush_accounts.db       ║
    ║                                            ║
    ╚════════════════════════════════════════════╝
    """)
    
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=True
    )
