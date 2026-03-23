from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import sqlite3
import hashlib
import os
import uuid
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'crm-super-secret-key-2024')
CORS(app, supports_credentials=True)

DB_PATH = os.environ.get('DB_PATH', 'crm.db')

# ── ПОЛЬЗОВАТЕЛИ ──────────────────────────────────────────
USERS = {
    'maxim':   '4f89468b6cda0d9bf7c0cd3411807ebc264829e0daa4d764d80c39d83d002d07',  # Kx9#mP2w
    'partner': '9623b6ca8356e8351063ae140e00a6a5be93680a87028a890334ec3b2a9f22cf'   # Vn4$jR8q
}

def sha256(s):
    return hashlib.sha256(s.encode()).hexdigest()

# ── БАЗА ДАННЫХ ───────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                company TEXT,
                phone TEXT,
                email TEXT,
                source TEXT,
                status TEXT DEFAULT 'new',
                call_status TEXT DEFAULT 'notcalled',
                amount TEXT,
                init_note TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                status TEXT DEFAULT 'new',
                client_id TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                client_id TEXT,
                amount TEXT,
                status TEXT DEFAULT 'new',
                due_date TEXT,
                note TEXT,
                created_at TEXT
            );
        ''')

init_db()

# ── ХЕЛПЕРЫ ───────────────────────────────────────────────
def require_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def new_id():
    return str(uuid.uuid4())[:12].replace('-', '')

def now():
    return datetime.now().strftime('%d.%m.%Y %H:%M')

def now_date():
    return datetime.now().strftime('%d.%m.%Y')

# ── AUTH ──────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = (data.get('username') or '').strip().lower()
    password = data.get('password') or ''
    if USERS.get(username) == sha256(password):
        session['user'] = username
        return jsonify({'ok': True, 'username': username})
    return jsonify({'ok': False, 'error': 'Неверный логин или пароль'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})

@app.route('/api/me')
def me():
    if 'user' in session:
        return jsonify({'ok': True, 'username': session['user']})
    return jsonify({'ok': False}), 401

# ── CLIENTS ───────────────────────────────────────────────
@app.route('/api/clients', methods=['GET'])
@require_auth
def get_clients():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM clients ORDER BY rowid DESC').fetchall()
        clients = []
        for row in rows:
            c = dict(row)
            notes = conn.execute(
                'SELECT * FROM notes WHERE client_id=? ORDER BY rowid ASC', (c['id'],)
            ).fetchall()
            c['notes'] = [dict(n) for n in notes]
            clients.append(c)
    return jsonify(clients)

@app.route('/api/clients', methods=['POST'])
@require_auth
def add_client():
    d = request.json
    cid = new_id()
    note_text = (d.get('init_note') or '').strip()
    with get_db() as conn:
        conn.execute('''
            INSERT INTO clients (id, name, company, phone, email, source, status, call_status, amount, init_note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cid, d['name'], d.get('company',''), d.get('phone',''), d.get('email',''),
              d.get('source','Прямой'), d.get('status','new'), d.get('call_status','notcalled'),
              d.get('amount',''), note_text, now_date()))
        if note_text:
            conn.execute('INSERT INTO notes (id, client_id, text, created_at) VALUES (?,?,?,?)',
                         (new_id(), cid, note_text, now()))
    return jsonify({'ok': True, 'id': cid})

@app.route('/api/clients/<cid>', methods=['PUT'])
@require_auth
def update_client(cid):
    d = request.json
    with get_db() as conn:
        conn.execute('''
            UPDATE clients SET name=?, company=?, phone=?, email=?, source=?,
            status=?, call_status=?, amount=?, init_note=? WHERE id=?
        ''', (d['name'], d.get('company',''), d.get('phone',''), d.get('email',''),
              d.get('source','Прямой'), d.get('status','new'), d.get('call_status','notcalled'),
              d.get('amount',''), d.get('init_note',''), cid))
    return jsonify({'ok': True})

@app.route('/api/clients/<cid>', methods=['DELETE'])
@require_auth
def delete_client(cid):
    with get_db() as conn:
        conn.execute('DELETE FROM notes WHERE client_id=?', (cid,))
        conn.execute('DELETE FROM clients WHERE id=?', (cid,))
    return jsonify({'ok': True})

@app.route('/api/clients/<cid>/field', methods=['PATCH'])
@require_auth
def patch_client_field(cid):
    d = request.json
    field = d.get('field')
    value = d.get('value')
    allowed = {'status', 'call_status'}
    if field not in allowed:
        return jsonify({'error': 'Invalid field'}), 400
    with get_db() as conn:
        conn.execute(f'UPDATE clients SET {field}=? WHERE id=?', (value, cid))
    return jsonify({'ok': True})

# ── NOTES ─────────────────────────────────────────────────
@app.route('/api/clients/<cid>/notes', methods=['POST'])
@require_auth
def add_note(cid):
    d = request.json
    nid = new_id()
    with get_db() as conn:
        conn.execute('INSERT INTO notes (id, client_id, text, created_at) VALUES (?,?,?,?)',
                     (nid, cid, d['text'], now()))
    return jsonify({'ok': True, 'id': nid, 'created_at': now()})

@app.route('/api/notes/<nid>', methods=['DELETE'])
@require_auth
def delete_note(nid):
    with get_db() as conn:
        conn.execute('DELETE FROM notes WHERE id=?', (nid,))
    return jsonify({'ok': True})

# ── TASKS ─────────────────────────────────────────────────
@app.route('/api/tasks', methods=['GET'])
@require_auth
def get_tasks():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM tasks ORDER BY rowid DESC').fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/tasks', methods=['POST'])
@require_auth
def add_task():
    d = request.json
    tid = new_id()
    with get_db() as conn:
        conn.execute('''
            INSERT INTO tasks (id, title, description, due_date, status, client_id, created_at)
            VALUES (?,?,?,?,?,?,?)
        ''', (tid, d['title'], d.get('description',''), d.get('due_date',''),
              d.get('status','new'), d.get('client_id',''), now_date()))
    return jsonify({'ok': True, 'id': tid})

@app.route('/api/tasks/<tid>', methods=['PUT'])
@require_auth
def update_task(tid):
    d = request.json
    with get_db() as conn:
        conn.execute('''
            UPDATE tasks SET title=?, description=?, due_date=?, status=?, client_id=? WHERE id=?
        ''', (d['title'], d.get('description',''), d.get('due_date',''),
              d.get('status','new'), d.get('client_id',''), tid))
    return jsonify({'ok': True})

# ── ORDERS ────────────────────────────────────────────────
@app.route('/api/orders', methods=['GET'])
@require_auth
def get_orders():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM orders ORDER BY rowid DESC').fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/orders', methods=['POST'])
@require_auth
def add_order():
    d = request.json
    oid = new_id()
    with get_db() as conn:
        conn.execute('''
            INSERT INTO orders (id, title, client_id, amount, status, due_date, note, created_at)
            VALUES (?,?,?,?,?,?,?,?)
        ''', (oid, d['title'], d.get('client_id',''), d.get('amount',''),
              d.get('status','new'), d.get('due_date',''), d.get('note',''), now_date()))
    return jsonify({'ok': True, 'id': oid})

@app.route('/api/orders/<oid>', methods=['PUT'])
@require_auth
def update_order(oid):
    d = request.json
    with get_db() as conn:
        conn.execute('''
            UPDATE orders SET title=?, client_id=?, amount=?, status=?, due_date=?, note=? WHERE id=?
        ''', (d['title'], d.get('client_id',''), d.get('amount',''),
              d.get('status','new'), d.get('due_date',''), d.get('note',''), oid))
    return jsonify({'ok': True})

@app.route('/api/orders/<oid>', methods=['DELETE'])
@require_auth
def delete_order(oid):
    with get_db() as conn:
        conn.execute('DELETE FROM orders WHERE id=?', (oid,))
    return jsonify({'ok': True})

# ── STATIC ────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
