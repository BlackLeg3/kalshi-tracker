import sqlite3
import json
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os

BASE_DIR = '/Users/jamescarroll/Desktop/Kalshi'
app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
CORS(app)

DB_PATH = os.path.join(BASE_DIR, 'kalshi.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS legal_cases (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        jurisdiction TEXT,
        case_type TEXT,
        status TEXT,
        description TEXT,
        source TEXT,
        date_filed TEXT,
        last_update TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS state_status (
        id INTEGER PRIMARY KEY,
        state TEXT UNIQUE,
        operating_status TEXT,
        license_type TEXT,
        notes TEXT,
        last_update TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS transaction_data (
        id INTEGER PRIMARY KEY,
        state TEXT UNIQUE,
        monthly_volume INTEGER,
        avg_contract_value REAL,
        contract_types TEXT,
        top_contract TEXT,
        active_users INTEGER,
        last_update TEXT
    )''')

    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/api/cases', methods=['GET'])
def get_cases():
    conn = get_db()
    c = conn.cursor()

    jurisdiction = request.args.get('jurisdiction')
    status = request.args.get('status')

    query = 'SELECT * FROM legal_cases WHERE 1=1'
    params = []

    if jurisdiction:
        query += ' AND jurisdiction = ?'
        params.append(jurisdiction)
    if status:
        query += ' AND status = ?'
        params.append(status)

    c.execute(query, params)
    cases = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(cases)

@app.route('/api/cases', methods=['POST'])
def add_case():
    data = request.json
    conn = get_db()
    c = conn.cursor()

    c.execute('''INSERT INTO legal_cases
        (title, jurisdiction, case_type, status, description, source, date_filed, last_update)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (data.get('title'), data.get('jurisdiction'), data.get('case_type'),
         data.get('status'), data.get('description'), data.get('source'),
         data.get('date_filed'), datetime.now().isoformat()))

    conn.commit()
    conn.close()
    return jsonify({'status': 'success'}), 201

@app.route('/api/states', methods=['GET'])
def get_states():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM state_status ORDER BY state')
    states = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(states)

@app.route('/api/states', methods=['POST'])
def add_state():
    data = request.json
    conn = get_db()
    c = conn.cursor()

    c.execute('''INSERT OR REPLACE INTO state_status
        (state, operating_status, license_type, notes, last_update)
        VALUES (?, ?, ?, ?, ?)''',
        (data.get('state'), data.get('operating_status'), data.get('license_type'),
         data.get('notes'), datetime.now().isoformat()))

    conn.commit()
    conn.close()
    return jsonify({'status': 'success'}), 201

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    conn = get_db()
    c = conn.cursor()

    state = request.args.get('state')

    if state:
        c.execute('SELECT * FROM transaction_data WHERE state = ?', (state,))
        result = c.fetchone()
        if result:
            row_dict = dict(result)
            row_dict['contract_types'] = row_dict['contract_types'].split(',') if row_dict['contract_types'] else []
            conn.close()
            return jsonify(row_dict)
        conn.close()
        return jsonify({}), 404

    c.execute('SELECT * FROM transaction_data ORDER BY monthly_volume DESC')
    transactions = []
    for row in c.fetchall():
        row_dict = dict(row)
        row_dict['contract_types'] = row_dict['contract_types'].split(',') if row_dict['contract_types'] else []
        transactions.append(row_dict)
    conn.close()
    return jsonify(transactions)

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    data = request.json
    conn = get_db()
    c = conn.cursor()

    contract_types_str = ','.join(data.get('contract_types', []))

    c.execute('''INSERT OR REPLACE INTO transaction_data
        (state, monthly_volume, avg_contract_value, contract_types, top_contract, active_users, last_update)
        VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (data.get('state'), data.get('monthly_volume'), data.get('avg_contract_value'),
         contract_types_str, data.get('top_contract'), data.get('active_users'),
         datetime.now().isoformat()))

    conn.commit()
    conn.close()
    return jsonify({'status': 'success'}), 201

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    c = conn.cursor()

    c.execute('SELECT COUNT(*) FROM legal_cases')
    total_cases = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM state_status WHERE operating_status = "Approved"')
    approved_states = c.fetchone()[0]

    c.execute('SELECT status, COUNT(*) FROM legal_cases GROUP BY status')
    status_breakdown = {row[0]: row[1] for row in c.fetchall()}

    c.execute('SELECT SUM(monthly_volume) FROM transaction_data')
    total_volume = c.fetchone()[0] or 0

    conn.close()
    return jsonify({
        'total_cases': total_cases,
        'approved_states': approved_states,
        'status_breakdown': status_breakdown,
        'total_monthly_volume': total_volume
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=8001, host='127.0.0.1')
