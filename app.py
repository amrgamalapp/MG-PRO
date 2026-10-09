import os,json,secrets
from pathlib import Path
from functools import wraps
from flask import Flask,request,redirect,session,jsonify,send_from_directory
from werkzeug.utils import secure_filename
R=Path(__file__).parent; (R/'data').mkdir(exist_ok=True); (R/'uploads').mkdir(exist_ok=True); DB=R/'data/courses.json'
app=Flask(__name__); app.secret_key=os.environ.get('FLASK_SECRET_KEY','CHANGE_THIS_SECRET')
def read():
 if not DB.exists(): DB.write_text('[]',encoding='utf-8')
 try:return json.loads(DB.read_text(encoding='utf-8'))
 except:return []
def write(x): DB.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def protected(f):
 @wraps(f)
 def w(*a,**k):
  if not session.get('admin'):return (jsonify(error='تسجيل الدخول مطلوب'),401) if request.path.startswith('/api/admin') else redirect('/admin/login')
  return f(*a,**k)
 return w
@app.get('/')
def home():return send_from_directory(R,'index.html')
@app.route('/admin/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  u=os.environ.get('ADMIN_USERNAME');p=os.environ.get('ADMIN_PASSWORD')
  if not u or not p:return 'Set ADMIN_USERNAME and ADMIN_PASSWORD environment variables',503
  if secrets.compare_digest(request.form.get('username',''),u) and secrets.compare_digest(request.form.get('password',''),p):session.clear();session['admin']=True;return redirect('/admin')
  return 'بيانات الدخول غير صحيحة',401
 return '<meta charset=utf-8><form method=post dir=rtl><h2>دخول مدير MG Academy</h2><input name=username placeholder="اسم المستخدم" required><input name=password type=password placeholder="كلمة المرور" required><button>دخول</button></form>'
@app.get('/admin')
@protected
def admin():return send_from_directory(R,'admin.html')
@app.post('/admin/logout')
@protected
def logout():session.clear();return redirect('/admin/login')
@app.get('/api/courses')
def courses():return jsonify(read())
@app.get('/api/admin/courses')
@protected
def admin_courses():return jsonify(read())
@app.post('/api/admin/courses')
@protected
def create():
 title=request.form.get('title','').strip()
 if not title:return jsonify(error='العنوان مطلوب'),400
 item={'id':secrets.token_hex(8),'title':title,'category':request.form.get('category',''),'description':request.form.get('description',''),'video':request.form.get('video',''),'file':None,'filename':None}
 f=request.files.get('file')
 if f and f.filename:
  name=secure_filename(f.filename);ext=Path(name).suffix.lower()
  if ext not in {'.pdf','.xlsx','.xls','.csv','.zip','.dwg','.png','.jpg','.jpeg','.mp4','.webm'}:return jsonify(error='نوع الملف غير مسموح'),400
  stored=secrets.token_hex(12)+ext;f.save(R/'uploads'/stored);item['file']='/uploads/'+stored;item['filename']=name
 a=read();a.insert(0,item);write(a);return jsonify(item),201
@app.delete('/api/admin/courses/<cid>')
@protected
def delete(cid):
 a=read();b=[x for x in a if x['id']!=cid]
 if len(a)==len(b):return jsonify(error='غير موجود'),404
 write(b);return jsonify(ok=True)
@app.get('/uploads/<path:name>')
def uploads(name):return send_from_directory(R/'uploads',name)
if __name__=='__main__':app.run(debug=False,port=int(os.environ.get('PORT','5000')))
