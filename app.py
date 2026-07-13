import sqlite3
import json
import logging
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os

# Set up logging
logger = logging.getLogger(__name__)

# Import scheduler
from scheduler import start_scheduler, stop_scheduler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
CORS(app)

DB_PATH = os.path.join(BASE_DIR, 'kalshi.db')

# Initialize database
init_db()

# Start background scheduler (with error handling)
scheduler = None
try:
    scheduler = start_scheduler()
    # Trigger initial data update on startup
    try:
        from data_sources import update_data
        logger.info("Running initial data update on startup...")
        update_data(DB_PATH)
    except Exception as e:
        logger.warning(f"Initial data update failed: {e}")
except Exception as e:
    logger.error(f"Failed to start scheduler: {e}")
    scheduler = None

KALSHI_CASES = [
    ('CFTC v. Kalshi', 'U.S. District Court, D.C.', 'Regulatory Enforcement', 'Active',
     'CFTC challenge to Kalshi\'s election and economic contracts.', 'Public Records', '2023-01-15'),
    ('Kalshi v. CFTC', 'U.S. District Court, D.C.', 'Regulatory Enforcement', 'Active',
     'Kalshi\'s counterclaim seeking declaratory judgment.', 'Public Records', '2023-02-20'),
    ('Kalshi Markets - BitLicense', 'New York Department of Financial Services', 'Regulatory Approval', 'Pending',
     'BitLicense application review by NYDFS.', 'Public Records', '2022-06-15'),
    ('Illinois Financial Regulator Investigation', 'Illinois Attorney General', 'Regulatory Inquiry', 'Pending',
     'State investigation into contract offerings.', 'Public Records', '2023-03-10'),
    ('Kalshi Consumer Class Action', 'U.S. District Court, N.D. California', 'Civil Litigation', 'Pending',
     'Class action regarding margin requirements and disclosures.', 'Public Records', '2023-05-22'),
    ('Texas Lottery Commission Inquiry', 'Texas Lottery Commission', 'Regulatory Inquiry', 'Pending',
     'Regulatory inquiry into contract classification.', 'Public Records', '2023-04-01'),
]

def seed_initial_data(c, conn):
    """Seed initial Kalshi cases, states, and transactions"""
    try:
        # Clear existing data to avoid duplicates
        c.execute('DELETE FROM legal_cases')
        c.execute('DELETE FROM state_status')
        c.execute('DELETE FROM transaction_data')

        # Seed cases
        for title, jurisdiction, case_type, status, description, source, date_filed in KALSHI_CASES:
            c.execute('''INSERT INTO legal_cases
                (title, jurisdiction, case_type, status, description, source, date_filed, last_update)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (title, jurisdiction, case_type, status, description, source, date_filed, datetime.now().isoformat()))

        # Seed states
        states_data = [
            ('Illinois', 'Approved', 'Regulated', 'Limited offerings available'),
            ('Massachusetts', 'Approved', 'Fintech License', 'Full operations'),
            ('Colorado', 'Approved', 'Regulated', 'Operations commenced'),
            ('New York', 'Pending', 'BitLicense', 'Under review by NYDFS'),
            ('California', 'Pending', 'Money Transmitter', 'Compliance review ongoing'),
            ('Texas', 'Pending', 'Money Transmitter', 'License application submitted'),
            ('Florida', 'Denied', 'N/A', 'Regulatory concerns cited'),
            ('Oregon', 'Pending', 'License Application', 'Awaiting review'),
        ]
        for state, status, license_type, notes in states_data:
            c.execute('''INSERT INTO state_status
                (state, operating_status, license_type, notes, last_update)
                VALUES (?, ?, ?, ?, ?)''',
                (state, status, license_type, notes, datetime.now().isoformat()))

        # Seed transactions
        transactions_data = [
            ('Illinois', 45000, 150.00, 'Election,Economic,Weather', 'Election Contracts', 8900),
            ('Massachusetts', 32000, 125.00, 'Election,Sports,Political', 'Political Outcomes', 6200),
            ('Colorado', 18500, 110.00, 'Election,Crypto,Commodities', 'Election Contracts', 3500),
            ('California', 8200, 95.00, 'Election,Technology', 'Technology Events', 1500),
            ('Texas', 5400, 105.00, 'Election,Weather', 'Election Contracts', 950),
            ('New York', 3200, 140.00, 'Finance,Markets', 'Market Outcomes', 620),
            ('Florida', 0, 0.00, '', 'N/A', 0),
            ('Oregon', 1800, 100.00, 'Election,Weather', 'Election Contracts', 340),
        ]
        for state, volume, avg_value, contracts, top, users in transactions_data:
            c.execute('''INSERT INTO transaction_data
                (state, monthly_volume, avg_contract_value, contract_types, top_contract, active_users, last_update)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (state, volume, avg_value, contracts, top, users, datetime.now().isoformat()))

        conn.commit()
        logger.info(f"Seeded {len(KALSHI_CASES)} cases, {len(states_data)} states, {len(transactions_data)} transactions")
    except Exception as e:
        logger.error(f"Error seeding data: {e}")

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

    # Seed data if any table is empty
    c.execute('SELECT COUNT(*) FROM state_status')
    state_count = c.fetchone()[0]

    if state_count == 0:
        logger.info("Seeding database with initial data...")
        seed_initial_data(c, conn)

    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def before_request():
    """Ensure database exists before processing requests"""
    try:
        # Just verify DB exists, don't re-init every request
        if not os.path.exists(DB_PATH):
            init_db()
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        pass

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

@app.route('/api/scheduler/status', methods=['GET'])
def scheduler_status():
    """Get scheduler status and summary"""
    try:
        if scheduler is None:
            return jsonify({'status': 'disabled', 'message': 'Scheduler not available'})

        status = scheduler.get_status_summary()
        return jsonify({
            'status': 'running',
            'cases_summary': status,
            'next_sec_check': 'Daily at 2:00 AM',
            'next_status_update': 'Weekly Monday at 9:00 AM',
            'last_update': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduler/update-now', methods=['POST'])
def trigger_update():
    """Manually trigger an immediate update"""
    try:
        if scheduler is None:
            return jsonify({'status': 'error', 'message': 'Scheduler not available'}), 503

        action = request.json.get('action', 'all') if request.json else 'all'

        if action in ['sec', 'all']:
            scheduler.fetch_sec_filings()

        if action in ['cases', 'all']:
            scheduler.update_case_statuses()

        return jsonify({
            'status': 'success',
            'message': f'Triggered {action} update',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    """Stop scheduler on app shutdown"""
    stop_scheduler()

if __name__ == '__main__':
    init_db()

    # Get environment variables
    debug = os.getenv('DEBUG', 'true').lower() == 'true'
    port = int(os.getenv('PORT', 8001))
    host = os.getenv('HOST', '127.0.0.1')

    # On production (Railway), use 0.0.0.0
    if os.getenv('RAILWAY_ENVIRONMENT'):
        host = '0.0.0.0'
        debug = False

    app.run(debug=debug, port=port, host=host)
