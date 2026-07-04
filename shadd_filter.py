#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
سیستم فیلتری شاد - فیلترینگ پیام‌ها، تماس‌ها و رفتار
فقط فحاشی را فیلتر می‌کند
"""

import re
from datetime import datetime
from typing import Dict, List

class ShaddMessageFilter:
    """فیلتری پیام‌های شاد"""
    
    def __init__(self):
        self.bad_words_fa = {
            'فحاشی': [
                'گاییدم', 'گایید', 'کوفت', 'کجا', 'الاغ', 'خمار',
                'بیشرف', 'حقیر', 'احمق', 'ابله', 'سوسول', 'روسپی',
                'فاسق', 'فاجر', 'شنگول', 'یاغی', 'خائن', 'دغل',
                'هرزه', 'سگ', 'خنزیر', 'لعنت', 'نفرین', 'سوگند',
                'کسخل', 'آشغال', 'حرام‌زاده', 'بنده‌اهو', 'ساکت',
                'بدبخت', 'نحس', 'شقی', 'فاحش', 'زشت', 'کیخه',
                'کوچ‌کاری', 'دنباله‌گرد', 'ملعون', 'پست', 'رذل',
            ]
        }
        
        self.risk_scores = {
            'فحاشی': 10,
        }
    
    def check_message(self, message: str, username: str = None) -> Dict:
        """بررسی پیام برای فحاشی"""
        violations = []
        total_risk = 0
        
        # بررسی کلمات بد (فحاشی)
        for category, words in self.bad_words_fa.items():
            for word in words:
                if self._word_in_message(word, message):
                    risk = self.risk_scores.get(category, 0)
                    violations.append({
                        'type': category,
                        'word': word,
                        'risk_score': risk,
                        'severity': self._get_severity(risk)
                    })
                    total_risk += risk
        
        return {
            'username': username,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'has_violation': len(violations) > 0,
            'violations': violations,
            'total_risk': total_risk,
            'risk_level': self._get_risk_level(total_risk),
            'action': self._get_action(total_risk),
            'is_banned': total_risk >= 100
        }
    
    def _word_in_message(self, word: str, message: str) -> bool:
        """بررسی وجود کلمه در پیام"""
        message_normalized = message.strip().lower()
        word_normalized = word.strip().lower()
        pattern = r'\b' + re.escape(word_normalized) + r'\b'
        return bool(re.search(pattern, message_normalized))
    
    def _get_severity(self, risk: int) -> str:
        """تعیین شدت تخلف"""
        if risk <= 5:
            return 'کم'
        elif risk <= 15:
            return 'متوسط'
        elif risk <= 25:
            return 'بالا'
        else:
            return 'بسیار بالا'
    
    def _get_risk_level(self, score: int) -> str:
        """تعیین سطح خطر کلی"""
        if score == 0:
            return 'سالم'
        elif score <= 10:
            return 'کم'
        elif score <= 30:
            return 'متوسط'
        elif score <= 60:
            return 'بالا'
        else:
            return 'بسیار بالا'
    
    def _get_action(self, score: int) -> str:
        """تعیین عمل لازم"""
        if score == 0:
            return 'قبول'
        elif score <= 10:
            return 'هشدار'
        elif score <= 30:
            return 'محدود کردن'
        elif score < 100:
            return 'تعلیق موقت'
        else:
            return 'بن فوری'


class ShaddCallFilter:
    """فیلتری تماس‌های شاد"""
    
    def __init__(self):
        self.max_calls_per_hour = 50
        self.max_call_duration = 3600  # 1 ساعت
        self.call_history = {}
    
    def check_call(self, caller: str, receiver: str, duration: int) -> Dict:
        """بررسی تماس برای رفتار معقول"""
        violations = []
        risk_score = 0
        
        # بررسی مدت تماس
        if duration > self.max_call_duration:
            violations.append({
                'type': 'تماس طولانی',
                'duration': duration,
                'risk_score': 10
            })
            risk_score += 10
        
        # بررسی تعداد تماس‌ها
        if caller not in self.call_history:
            self.call_history[caller] = []
        
        # پاک کردن تماس‌های قدیمی
        now = datetime.now()
        self.call_history[caller] = [
            t for t in self.call_history[caller]
            if (now - t).seconds < 3600
        ]
        
        if len(self.call_history[caller]) >= self.max_calls_per_hour:
            violations.append({
                'type': 'تماس‌های متعدد',
                'count': len(self.call_history[caller]),
                'risk_score': 15
            })
            risk_score += 15
        
        self.call_history[caller].append(now)
        
        return {
            'caller': caller,
            'receiver': receiver,
            'duration': duration,
            'timestamp': now.isoformat(),
            'has_violation': len(violations) > 0,
            'violations': violations,
            'risk_score': risk_score,
            'action': 'محدود کردن' if risk_score >= 15 else 'قبول'
        }


class ShaddBehaviorAnalyzer:
    """تحلیل رفتار کاربران شاد"""
    
    def __init__(self):
        self.user_activity = {}
    
    def analyze_user(self, username: str, activities: List[Dict]) -> Dict:
        """تحلیل رفتار کاربر"""
        if username not in self.user_activity:
            self.user_activity[username] = []
        
        self.user_activity[username].extend(activities)
        
        violations = []
        total_risk = 0
        
        # بررسی فعالیت غیرمعمول
        message_count = len([a for a in activities if a.get('type') == 'message'])
        call_count = len([a for a in activities if a.get('type') == 'call'])
        
        if message_count > 100:  # بیش از 100 پیام در یک ساعت
            violations.append({
                'type': 'تعداد بیش‌ازحد پیام',
                'count': message_count,
                'risk_score': 20
            })
            total_risk += 20
        
        if call_count > 30:  # بیش از 30 تماس در یک ساعت
            violations.append({
                'type': 'تعداد بیش‌ازحد تماس',
                'count': call_count,
                'risk_score': 25
            })
            total_risk += 25
        
        return {
            'username': username,
            'activity_count': len(activities),
            'message_count': message_count,
            'call_count': call_count,
            'violations': violations,
            'total_risk': total_risk,
            'status': 'مشکوک' if total_risk >= 20 else 'عادی',
            'recommendation': self._get_recommendation(total_risk)
        }
    
    def _get_recommendation(self, risk: int) -> str:
        """توصیه برای اقدام"""
        if risk == 0:
            return 'بدون اقدام'
        elif risk <= 20:
            return 'نظارت'
        elif risk <= 50:
            return 'هشدار'
        else:
            return 'بن موقت یا دائم'


def test_shadd_filter():
    """تست فیلتر شاد"""
    print("\n" + "="*70)
    print("🧪 تست سیستم فیلتری شاد (فقط فحاشی)")
    print("="*70 + "\n")
    
    filter_system = ShaddMessageFilter()
    
    # تست پیام‌های مختلف
    test_messages = [
        ("سلام، چطور می‌تونم کمکت کنم؟", "user1", "✅ پیام عادی"),
        ("سلام دوست!", "user2", "✅ پیام دوستانه"),
        ("گاییدم احمق!", "user3", "❌ فحاشی"),
        ("الاغ بیشرف", "user4", "❌ فحاشی"),
        ("کسخل روسپی", "user5", "❌ فحاشی"),
        ("میتونی کمکم کنی؟", "user6", "✅ سؤال عادی"),
    ]
    
    for message, username, label in test_messages:
        result = filter_system.check_message(message, username)
        print(f"{label}")
        print(f"  👤 کاربر: {username}")
        print(f"  💬 پیام: {message}")
        print(f"  📊 امتیاز خطر: {result['total_risk']}")
        print(f"  ⚠️  سطح: {result['risk_level']}")
        print(f"  🎯 عمل: {result['action']}")
        
        if result['violations']:
            print(f"  ❌ فحاشی‌های تشخیص‌داده‌شده:")
            for v in result['violations']:
                print(f"     • {v['word']} (+{v['risk_score']})")
        
        print()

if __name__ == '__main__':
    test_shadd_filter()
