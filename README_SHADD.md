# 🚀 سیستم فیلتری شاد

## نصب و اجرا

```bash
# نصب
pip install -r requirements.txt

# اجرای API
python shadd_api.py

# یا فیلتر مستقل
python shadd_filter.py
```

## API Endpoints

### ثبت‌نام
```bash
POST /register
{"username": "user123", "email": "user@shadd.com"}
```

### بررسی پیام
```bash
POST /check-message
{"username": "user123", "message": "سلام!"}
```

### بررسی تماس
```bash
POST /check-call
{"caller": "user1", "receiver": "user2", "duration": 120}
```

### بن کاربر
```bash
POST /ban/<username>
```

## تست

```bash
python shadd_filter.py
```
