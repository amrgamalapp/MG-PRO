import sys
from getpass import getpass
from werkzeug.security import generate_password_hash
from app import db, init_db

init_db()
name = input('Admin name: ').strip()
email = input('Admin email: ').strip().lower()
pw = getpass('Admin password (6+ chars): ')
if len(pw) < 6: raise SystemExit('Password too short')
conn=db()
conn.execute('INSERT OR REPLACE INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,datetime(\'now\'))',(name,email,generate_password_hash(pw),'admin'))
conn.commit(); conn.close()
print('Admin created:', email)
