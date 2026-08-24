import os
import sqlite3
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join('/tmp', 'mg_engineering_academy.db') if os.environ.get('VERCEL') else os.path.join(BASE_DIR, 'instance', 'academy.db')
app = Flask(__name__, root_path=BASE_DIR, static_folder=os.path.join(BASE_DIR, 'public'), template_folder=os.path.join(BASE_DIR, 'templates'), static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret-key-in-production')
app.config['DATABASE'] = DB_PATH

_db_initialized = False

@app.before_request
def ensure_database():
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True

@app.route('/health')
def health():
    return {'ok': True, 'service': 'MG Engineering Academy'}


def db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = db()
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE,
      password TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'student',
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS courses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      slug TEXT NOT NULL UNIQUE,
      title TEXT NOT NULL,
      subtitle TEXT NOT NULL,
      category TEXT NOT NULL,
      level TEXT NOT NULL,
      price REAL NOT NULL DEFAULT 0,
      old_price REAL NOT NULL DEFAULT 0,
      rating REAL NOT NULL DEFAULT 4.8,
      students INTEGER NOT NULL DEFAULT 0,
      duration TEXT NOT NULL,
      icon TEXT NOT NULL,
      accent TEXT NOT NULL DEFAULT 'gold',
      description TEXT NOT NULL,
      featured INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS lessons (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      course_id INTEGER NOT NULL,
      title TEXT NOT NULL,
      duration TEXT NOT NULL,
      sort_order INTEGER NOT NULL,
      is_free INTEGER NOT NULL DEFAULT 0,
      FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS enrollments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      course_id INTEGER NOT NULL,
      progress INTEGER NOT NULL DEFAULT 0,
      enrolled_at TEXT NOT NULL,
      UNIQUE(user_id, course_id),
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS lesson_progress (
      user_id INTEGER NOT NULL,
      lesson_id INTEGER NOT NULL,
      completed INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(user_id, lesson_id),
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY(lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS certificates (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      course_id INTEGER NOT NULL,
      code TEXT NOT NULL UNIQUE,
      issued_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
    );
    ''')
    seed(conn)
    conn.commit()
    conn.close()


def seed(conn):
    count = conn.execute('SELECT COUNT(*) FROM courses').fetchone()[0]
    if count:
        return
    courses = [
      ('autocad-pro','AutoCAD من الصفر للاحتراف','الرسم الهندسي باحتراف من أول أمر حتى مشروع كامل','CAD','مبتدئ → متقدم',399,799,4.9,1280,'18 ساعة','⌬','gold','كورس عملي يعلّمك AutoCAD خطوة بخطوة مع تمارين ومشاريع حقيقية.',1),
      ('civil3d-master','Civil 3D Masterclass','سطحيات وطرق وقطاعات وحجوم ومشاريع تطبيقية','Civil 3D','متوسط → متقدم',499,999,4.9,860,'22 ساعة','◈','blue','تعلّم workflow احترافي في Civil 3D من الاستيراد حتى إخراج اللوحات.',1),
      ('surveying','أساسيات المساحة وTotal Station','من المبادئ إلى العمل الميداني والحسابات','Surveying','مبتدئ',349,699,4.8,1430,'16 ساعة','⌁','green','أساسيات المساحة، الميزانية، الترافيرس، Total Station وتطبيقات عملية.',1),
      ('gis','GIS وArcGIS عملي','خرائط وتحليل مكاني ومشروعات GIS','GIS','متوسط',299,599,4.8,710,'12 ساعة','◎','violet','بناء خرائط وتحليلات مكانية ومشروعات GIS من البداية للنهاية.',0),
      ('technical-office','Technical Office Pro','الحصر والمستخلصات والتسعير وShop Drawing','Technical Office','متوسط',449,899,4.9,1120,'20 ساعة','▦','orange','مسار متكامل للمكتب الفني مع ملفات Excel ومشروعات تطبيقية.',1),
      ('quantity-surveying','Quantity Surveying','حصر كميات احترافي للخرسانة والتشطيبات','Quantities','مبتدئ → متقدم',329,649,4.7,940,'14 ساعة','▤','cyan','تعلّم منهجية الحصر وإعداد الجداول والمراجعة باحتراف.',0),
    ]
    for c in courses:
        cur = conn.execute('''INSERT INTO courses(slug,title,subtitle,category,level,price,old_price,rating,students,duration,icon,accent,description,featured)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', c)
        cid = cur.lastrowid
        lesson_titles = [
          'مقدمة وتجهيز بيئة العمل', 'فهم الواجهة والأوامر الأساسية', 'التطبيق الأول خطوة بخطوة',
          'تنظيم المشروع والـLayers', 'أدوات الرسم والتعديل', 'مشروع تطبيقي كامل', 'إخراج احترافي وتسليم المشروع'
        ]
        for i, title in enumerate(lesson_titles, 1):
            conn.execute('INSERT INTO lessons(course_id,title,duration,sort_order,is_free) VALUES(?,?,?,?,?)',
                         (cid, title, f'{7+i*3} دقيقة', i, 1 if i == 1 else 0))


def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    conn = db(); user = conn.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone(); conn.close()
    return user


@app.context_processor
def inject_globals():
    return {'current_user': current_user(), 'year': datetime.now().year}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            flash('سجّل دخولك أولاً للمتابعة.', 'warning')
            return redirect(url_for('login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        u = current_user()
        if not u or u['role'] != 'admin': abort(403)
        return view(*args, **kwargs)
    return wrapped


@app.route('/')
def home():
    conn=db(); featured=conn.execute('SELECT * FROM courses WHERE featured=1 ORDER BY id DESC').fetchall(); categories=conn.execute('SELECT DISTINCT category FROM courses ORDER BY category').fetchall(); conn.close()
    return render_template('home.html', featured=featured, categories=categories)

@app.route('/courses')
def courses():
    q=request.args.get('q','').strip(); cat=request.args.get('category','').strip()
    conn=db(); sql='SELECT * FROM courses WHERE 1=1'; params=[]
    if q: sql += ' AND (title LIKE ? OR subtitle LIKE ? OR category LIKE ?)'; params += [f'%{q}%',f'%{q}%',f'%{q}%']
    if cat: sql += ' AND category=?'; params.append(cat)
    sql += ' ORDER BY featured DESC, id DESC'; items=conn.execute(sql,params).fetchall(); cats=conn.execute('SELECT DISTINCT category FROM courses ORDER BY category').fetchall(); conn.close()
    return render_template('courses.html', courses=items, categories=cats, q=q, selected=cat)

@app.route('/course/<slug>')
def course(slug):
    conn=db(); c=conn.execute('SELECT * FROM courses WHERE slug=?',(slug,)).fetchone()
    if not c: abort(404)
    lessons=conn.execute('SELECT * FROM lessons WHERE course_id=? ORDER BY sort_order',(c['id'],)).fetchall()
    enrolled=False
    if session.get('user_id'):
        enrolled=bool(conn.execute('SELECT 1 FROM enrollments WHERE user_id=? AND course_id=?',(session['user_id'],c['id'])).fetchone())
    conn.close(); return render_template('course.html', course=c, lessons=lessons, enrolled=enrolled)

@app.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll(course_id):
    conn=db(); c=conn.execute('SELECT * FROM courses WHERE id=?',(course_id,)).fetchone()
    if not c: abort(404)
    existed=conn.execute('SELECT 1 FROM enrollments WHERE user_id=? AND course_id=?',(session['user_id'],course_id)).fetchone()
    if not existed:
        conn.execute('INSERT INTO enrollments(user_id,course_id,enrolled_at) VALUES(?,?,?)',(session['user_id'],course_id,datetime.utcnow().isoformat()))
        conn.execute('UPDATE courses SET students=students+1 WHERE id=?',(course_id,))
    conn.commit(); conn.close(); flash('تم إضافة الكورس إلى حسابك. ابدأ التعلم الآن 🚀','success'); return redirect(url_for('learn',slug=c['slug']))

@app.route('/learn/<slug>')
@login_required
def learn(slug):
    conn=db(); c=conn.execute('SELECT * FROM courses WHERE slug=?',(slug,)).fetchone()
    if not c: abort(404)
    enrollment=conn.execute('SELECT * FROM enrollments WHERE user_id=? AND course_id=?',(session['user_id'],c['id'])).fetchone()
    if not enrollment:
        conn.close(); return redirect(url_for('course',slug=slug))
    lessons=conn.execute('''SELECT l.*, COALESCE(lp.completed,0) completed FROM lessons l LEFT JOIN lesson_progress lp ON lp.lesson_id=l.id AND lp.user_id=? WHERE l.course_id=? ORDER BY l.sort_order''',(session['user_id'],c['id'])).fetchall()
    done=sum(x['completed'] for x in lessons); total=len(lessons); progress=round(done/total*100) if total else 0
    conn.execute('UPDATE enrollments SET progress=? WHERE id=?',(progress,enrollment['id'])); conn.commit(); conn.close()
    return render_template('learn.html', course=c, lessons=lessons, progress=progress)

@app.route('/lesson/<int:lesson_id>/complete', methods=['POST'])
@login_required
def complete_lesson(lesson_id):
    conn=db(); lesson=conn.execute('SELECT * FROM lessons WHERE id=?',(lesson_id,)).fetchone()
    if not lesson: abort(404)
    enrolled=conn.execute('SELECT 1 FROM enrollments WHERE user_id=? AND course_id=?',(session['user_id'],lesson['course_id'])).fetchone()
    if not enrolled: abort(403)
    conn.execute('INSERT INTO lesson_progress(user_id,lesson_id,completed) VALUES(?,?,1) ON CONFLICT(user_id,lesson_id) DO UPDATE SET completed=1',(session['user_id'],lesson_id))
    lessons=conn.execute('SELECT COUNT(*) total, SUM(CASE WHEN lp.completed=1 THEN 1 ELSE 0 END) done FROM lessons l LEFT JOIN lesson_progress lp ON lp.lesson_id=l.id AND lp.user_id=? WHERE l.course_id=?',(session['user_id'],lesson['course_id'])).fetchone()
    progress=round((lessons['done'] or 0)/lessons['total']*100) if lessons['total'] else 0
    conn.execute('UPDATE enrollments SET progress=? WHERE user_id=? AND course_id=?',(progress,session['user_id'],lesson['course_id']))
    if progress == 100:
        code=f'MG-{lesson["course_id"]}-{session["user_id"]}-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}'
        conn.execute('INSERT OR IGNORE INTO certificates(user_id,course_id,code,issued_at) VALUES(?,?,?,?)',(session['user_id'],lesson['course_id'],code,datetime.utcnow().isoformat()))
    conn.commit(); conn.close(); return jsonify({'ok':True,'progress':progress})

@app.route('/dashboard')
@login_required
def dashboard():
    conn=db(); enroll=conn.execute('''SELECT c.*, e.progress, e.enrolled_at FROM enrollments e JOIN courses c ON c.id=e.course_id WHERE e.user_id=? ORDER BY e.enrolled_at DESC''',(session['user_id'],)).fetchall(); certs=conn.execute('''SELECT cert.*, c.title FROM certificates cert JOIN courses c ON c.id=cert.course_id WHERE cert.user_id=? ORDER BY cert.issued_at DESC''',(session['user_id'],)).fetchall(); conn.close(); return render_template('dashboard.html', enrollments=enroll, certificates=certs)

@app.route('/certificates')
@login_required
def certificates():
    conn=db(); certs=conn.execute('SELECT cert.*, c.title FROM certificates cert JOIN courses c ON c.id=cert.course_id WHERE cert.user_id=? ORDER BY cert.issued_at DESC',(session['user_id'],)).fetchall(); conn.close(); return render_template('certificates.html', certificates=certs)

@app.route('/verify/<code>')
def verify(code):
    conn=db(); cert=conn.execute('''SELECT cert.code,cert.issued_at,c.title,u.name FROM certificates cert JOIN courses c ON c.id=cert.course_id JOIN users u ON u.id=cert.user_id WHERE cert.code=?''',(code,)).fetchone(); conn.close(); return render_template('verify.html', certificate=cert, code=code)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form['name'].strip(); email=request.form['email'].strip().lower(); password=request.form['password']
        if len(password)<6: flash('كلمة المرور لازم تكون 6 أحرف على الأقل.','danger'); return render_template('register.html')
        conn=db()
        try:
            conn.execute('INSERT INTO users(name,email,password,created_at) VALUES(?,?,?,?)',(name,email,generate_password_hash(password),datetime.utcnow().isoformat())); conn.commit(); uid=conn.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone()['id']; session['user_id']=uid; flash('أهلاً بيك في MG Engineering Academy 🎓','success'); return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError: flash('البريد الإلكتروني مستخدم بالفعل.','danger')
        finally: conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form['email'].strip().lower(); password=request.form['password']; conn=db(); user=conn.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone(); conn.close()
        if user and check_password_hash(user['password'],password): session['user_id']=user['id']; return redirect(request.args.get('next') or url_for('dashboard'))
        flash('بيانات الدخول غير صحيحة.','danger')
    return render_template('login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))

@app.route('/admin')
@admin_required
def admin():
    conn=db(); courses=conn.execute('SELECT * FROM courses ORDER BY id DESC').fetchall(); users=conn.execute('SELECT id,name,email,role,created_at FROM users ORDER BY id DESC').fetchall(); stats={'courses':len(courses),'users':len(users),'enrollments':conn.execute('SELECT COUNT(*) FROM enrollments').fetchone()[0]}; conn.close(); return render_template('admin.html',courses=courses,users=users,stats=stats)

@app.route('/admin/course/new', methods=['GET','POST'])
@admin_required
def admin_new_course():
    if request.method=='POST':
        data=request.form; conn=db()
        conn.execute('''INSERT INTO courses(slug,title,subtitle,category,level,price,old_price,rating,students,duration,icon,accent,description,featured) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
            data['slug'],data['title'],data['subtitle'],data['category'],data['level'],float(data.get('price') or 0),float(data.get('old_price') or 0),4.8,0,data.get('duration',''),data.get('icon','⌘'),data.get('accent','gold'),data['description'],1 if data.get('featured') else 0))
        cid=conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        for i in range(1,6):
            title=data.get(f'lesson_{i}','').strip()
            if title: conn.execute('INSERT INTO lessons(course_id,title,duration,sort_order,is_free) VALUES(?,?,?,?,?)',(cid,title,'10 دقائق',i,1 if i==1 else 0))
        conn.commit(); conn.close(); flash('تم إنشاء الكورس.','success'); return redirect(url_for('admin'))
    return render_template('admin_course.html')

@app.errorhandler(403)
def forbidden(e): return render_template('error.html',code=403,message='ليس لديك صلاحية للوصول إلى هذه الصفحة.'),403
@app.errorhandler(404)
def not_found(e): return render_template('error.html',code=404,message='الصفحة التي تبحث عنها غير موجودة.'),404

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)), debug=os.environ.get('FLASK_DEBUG','0')=='1')
