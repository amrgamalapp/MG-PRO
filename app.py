import os, json, secrets
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, abort, flash
from werkzeug.utils import secure_filename

ROOT = Path(__file__).resolve().parent
DATA_DIR, UPLOAD_DIR = ROOT / "data", ROOT / "uploads"
DATA_DIR.mkdir(exist_ok=True); UPLOAD_DIR.mkdir(exist_ok=True)
DB = DATA_DIR / "courses.json"
ALLOWED = {".pdf", ".xlsx", ".xls", ".csv", ".zip", ".dwg", ".png", ".jpg", ".jpeg", ".mp4", ".webm", ".docx", ".pptx"}
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "CHANGE-ME-BEFORE-DEPLOYMENT")
app.config["MAX_CONTENT_LENGTH"] = 250 * 1024 * 1024

def read_courses():
    if not DB.exists(): DB.write_text("[]", encoding="utf-8")
    try:
        items = json.loads(DB.read_text(encoding="utf-8"))
        return items if isinstance(items, list) else []
    except (json.JSONDecodeError, OSError):
        return []

def write_courses(items):
    temp = DB.with_suffix(".tmp")
    temp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(DB)

def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            if request.path.startswith("/api/"):
                return jsonify(error="يجب تسجيل دخول المدير أولاً"), 401
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def save_upload(file):
    if not file or not file.filename: return None, None
    original = secure_filename(file.filename)
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED: raise ValueError("نوع الملف غير مسموح")
    stored = secrets.token_hex(16) + ext
    file.save(UPLOAD_DIR / stored)
    return stored, original

@app.get("/")
def home():
    courses = [c for c in read_courses() if c.get("published", True)]
    return render_template("index.html", courses=courses)

@app.get("/course/<course_id>")
def course_detail(course_id):
    course = next((c for c in read_courses() if c["id"] == course_id and c.get("published", True)), None)
    if not course: abort(404)
    return render_template("course.html", course=course)

@app.get("/admin/login")
def login():
    if session.get("is_admin"): return redirect(url_for("admin"))
    return render_template("login.html", error=None)

@app.post("/admin/login")
def login_post():
    username = os.environ.get("ADMIN_USERNAME")
    password = os.environ.get("ADMIN_PASSWORD")
    if not username or not password:
        return render_template("login.html", error="بيانات المدير غير مضبوطة في إعدادات الاستضافة."), 503
    u, p = request.form.get("username", ""), request.form.get("password", "")
    if secrets.compare_digest(u, username) and secrets.compare_digest(p, password):
        session.clear(); session["is_admin"] = True
        return redirect(url_for("admin"))
    return render_template("login.html", error="اسم المستخدم أو كلمة المرور غير صحيحة."), 401

@app.post("/admin/logout")
@require_admin
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.get("/admin")
@require_admin
def admin():
    return render_template("admin.html", courses=read_courses())

@app.get("/api/courses")
def api_courses():
    return jsonify([c for c in read_courses() if c.get("published", True)])

@app.get("/api/admin/courses")
@require_admin
def api_admin_courses():
    return jsonify(read_courses())

@app.post("/api/admin/courses")
@require_admin
def api_create_course():
    title = request.form.get("title", "").strip()
    if not title: return jsonify(error="عنوان الكورس مطلوب"), 400
    try: stored, original = save_upload(request.files.get("file"))
    except ValueError as e: return jsonify(error=str(e)), 400
    item = {
        "id": secrets.token_urlsafe(9), "title": title,
        "category": request.form.get("category", "هندسة المساحة").strip(),
        "description": request.form.get("description", "").strip(),
        "video": request.form.get("video", "").strip(),
        "file": stored, "filename": original,
        "published": request.form.get("published") == "on",
        "created_at": __import__("datetime").datetime.now().strftime("%Y-%m-%d")
    }
    items = read_courses(); items.insert(0, item); write_courses(items)
    return jsonify(item), 201

@app.put("/api/admin/courses/<course_id>")
@require_admin
def api_update_course(course_id):
    items = read_courses()
    item = next((c for c in items if c["id"] == course_id), None)
    if not item: return jsonify(error="الكورس غير موجود"), 404
    title = request.form.get("title", "").strip()
    if not title: return jsonify(error="عنوان الكورس مطلوب"), 400
    item.update(title=title, category=request.form.get("category", "").strip(),
                description=request.form.get("description", "").strip(),
                video=request.form.get("video", "").strip(),
                published=request.form.get("published") == "on")
    try:
        if request.files.get("file") and request.files["file"].filename:
            old = item.get("file")
            stored, original = save_upload(request.files["file"])
            item["file"], item["filename"] = stored, original
            if old:
                try: (UPLOAD_DIR / old).unlink(missing_ok=True)
                except OSError: pass
    except ValueError as e: return jsonify(error=str(e)), 400
    write_courses(items)
    return jsonify(item)

@app.delete("/api/admin/courses/<course_id>")
@require_admin
def api_delete_course(course_id):
    items = read_courses()
    item = next((c for c in items if c["id"] == course_id), None)
    if not item: return jsonify(error="الكورس غير موجود"), 404
    items = [c for c in items if c["id"] != course_id]
    write_courses(items)
    if item.get("file"):
        try: (UPLOAD_DIR / item["file"]).unlink(missing_ok=True)
        except OSError: pass
    return jsonify(ok=True)

@app.get("/files/<path:filename>")
def download_file(filename):
    # الملفات التجريبية عامة؛ استخدم تخزينًا خاصًا وروابط موقعة للمحتوى المدفوع.
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
