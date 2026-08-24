# MG Engineering Academy

منصة كورسات هندسية كاملة بـ Flask + SQLite، جاهزة للرفع على GitHub ثم النشر على أي استضافة Python تدعم Gunicorn.

## المزايا
- واجهة عربية RTL احترافية Responsive.
- كتالوج كورسات وتصنيفات وبحث.
- حسابات طلاب وتسجيل دخول آمن بكلمات مرور hashed.
- Enrollment للكورسات.
- مشغل تعلم داخل صفحة الدرس مع حفظ التقدم.
- Dashboard للطالب.
- شهادات عند إكمال الكورس + صفحة تحقق عامة بالكود.
- لوحة Admin لإنشاء كورسات ودروس ومتابعة المستخدمين.
- SQLite كبداية بدون إعداد قاعدة بيانات خارجي.
- Gunicorn + Procfile + runtime.txt.

## التشغيل محلياً
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
ثم افتح `http://127.0.0.1:5000`.

## حساب Admin لأول مرة
بعد إنشاء حساب عادي، نفّذ مرة واحدة في SQLite:
```sql
UPDATE users SET role='admin' WHERE email='YOUR_EMAIL';
```

## النشر
ارفع الملفات إلى GitHub ثم استخدم خدمة استضافة Python. أمر التشغيل:
`gunicorn app:app`

> ملاحظة: SQLite مناسب للبداية والاختبار. للإطلاق الكبير استخدم PostgreSQL، وخزّن SECRET_KEY في متغيرات البيئة. الدفع الإلكتروني والفيديوهات الخاصة تحتاج مزود دفع/تخزين فيديو ومفاتيح حقيقية.


## Vercel deployment

This project is configured for Vercel + Flask:
- `api/index.py` exposes the Flask WSGI app.
- `vercel.json` rewrites all public routes to the Flask function.
- `.python-version` pins Python 3.12.
- On Vercel, SQLite is stored under `/tmp` because the serverless filesystem is not persistent.

For production student accounts, enrollments, progress, and certificates, move the database to PostgreSQL (or another persistent database) before launch.
