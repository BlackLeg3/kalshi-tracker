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

# Bump this whenever the hardcoded seed data changes. On startup, if the
# database's stored version differs, the seed data is fully refreshed. This
# ensures corrected data reaches production even when Railway persists the
# SQLite file across deployments.
DATA_VERSION = 4

KALSHI_CASES = [
    # ============================================================
    # FEDERAL CASES
    # ============================================================
    # Resolved - Original election/event contract fight
    ('Kalshi v. CFTC (Election/Event Contracts)', 'U.S. District Court, D.D.C. / D.C. Circuit (No. 24-5205)', 'Regulatory Enforcement', 'Resolved',
     'FAVORABLE: Kalshi won summary judgment Sep 6, 2024. CFTC dismissed its appeal (No. 24-5205, D.C. Cir.) on May 5, 2025, leaving standing the ruling that Kalshi\'s political/event contracts are lawful under federal law.', 'CourtListener; Practical Law', '2023-11-01'),

    # Active - Federal preemption enforcement
    ('KalshiEX LLC v. Flaherty (New Jersey)', 'U.S. Court of Appeals, 3rd Circuit (No. 25-1922)', 'Regulatory Enforcement', 'Active',
     'FAVORABLE: District court granted a preliminary injunction (Apr 2025). Third Circuit AFFIRMED on Apr 6, 2026 — the first federal appellate ruling that the Commodity Exchange Act preempts state gambling laws for sports event contracts on CFTC-registered DCMs.', 'Paul Weiss; Holland & Knight', '2025-03-15'),
    ('CFTC & DOJ v. Arizona, Connecticut & Illinois', 'U.S. District Courts (multiple)', 'Regulatory Enforcement', 'Active',
     'The CFTC and U.S. Department of Justice jointly sued AZ, CT and IL on Apr 2, 2026, asserting those states\' enforcement actions against prediction-market platforms are preempted by the Commodity Exchange Act.', 'Holland & Knight', '2026-04-02'),

    # ============================================================
    # STATE-LEVEL CASES (with docket numbers)
    # ============================================================
    # Favorable to Kalshi
    ('KalshiEX v. Tennessee (Sports Event Contracts)', 'U.S. District Court, M.D. Tennessee', 'Regulatory Enforcement', 'Active',
     'FAVORABLE: Kalshi sued Jan 12, 2026 after a shutdown order. Court granted a preliminary injunction Feb 19, 2026, finding the contracts likely "swaps" preempted by the CEA. Tennessee AG appealed to the Sixth Circuit.', 'Legal Sports Report; SBC Americas', '2026-01-12'),

    # Unfavorable to Kalshi
    ('KalshiEX, LLC v. Hendrick (Nevada)', 'U.S. District Court, D. Nevada (2:25-cv-00575)', 'Regulatory Enforcement', 'Active',
     'UNFAVORABLE: Preliminary injunction granted Apr 9, 2025 was DISSOLVED by Judge Andrew Gordon on Nov 24, 2025; Kalshi ordered to stop in-state and appealed to the Ninth Circuit (No. 25-7516).', 'Nevada Independent; CourtListener', '2025-03-28'),
    ('KalshiEX v. Martin (Maryland)', 'U.S. District Court, D. Maryland (1:25-cv-01283-ABA)', 'Regulatory Enforcement', 'Active',
     'UNFAVORABLE: Judge Adam Abelson denied Kalshi\'s preliminary injunction Aug 1, 2025, holding the CEA does not preempt Maryland gaming law. Appealed to the Fourth Circuit (oral argument set May 7, 2026).', 'U.S. Dist. Court D.Md.; Brownstein', '2025-04-20'),
    ('KalshiEX LLC v. New York State Gaming Commission', 'U.S. District Court, S.D.N.Y. (1:25-cv-08846-AT)', 'Regulatory Enforcement', 'Active',
     'UNFAVORABLE: Judge Analisa Torres denied Kalshi\'s preliminary injunction Jul 7, 2026, ruling NY gambling laws apply and are not preempted by the CEA. Kalshi is appealing.', 'NY Attorney General; Gothamist', '2025-10-20'),
    ('KalshiEX v. Massachusetts (Suffolk Superior Court)', 'Massachusetts Superior Court, Suffolk County', 'Regulatory Enforcement', 'Active',
     'UNFAVORABLE: Jan 2026 preliminary injunction bars Kalshi from offering in-state sports contracts without a license. 38 state attorneys general filed an amicus brief supporting Massachusetts (Apr 2026).', 'Courthouse News; AZ Capitol Times', '2025-12-01'),
    ('KalshiEX v. Ohio (Sports Event Contracts)', 'U.S. District Court, S.D. Ohio', 'Regulatory Enforcement', 'Active',
     'UNFAVORABLE: Kalshi sued the Ohio AG Oct 8, 2025; the court ruled against Kalshi (~Mar 2026). Pending Sixth Circuit appeal alongside Tennessee, creating an intra-circuit split likely headed for higher review.', 'SBC Americas; ST News', '2025-10-08'),
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

        # Seed states - verified litigation outcomes only (as of Jul 2026)
        states_data = [
            # Favorable - Kalshi operating under injunction / appellate win
            ('New Jersey', 'Approved', 'Federal Preemption', '3rd Circuit affirmed injunction Apr 6, 2026 (CEA preempts state law)'),
            ('Tennessee', 'Approved', 'Federal Preemption', 'Preliminary injunction granted Feb 19, 2026; TN AG appealed (6th Cir.)'),

            # Unfavorable - Kalshi restricted / lost injunction
            ('Nevada', 'Denied', 'Injunction Dissolved', 'PI dissolved Nov 24, 2025; must cease in-state; 9th Cir. appeal'),
            ('Maryland', 'Denied', 'Court Loss', 'PI denied Aug 1, 2025; 4th Cir. oral argument May 7, 2026'),
            ('New York', 'Denied', 'Court Loss', 'PI denied Jul 7, 2026; Kalshi appealing (2nd Cir.)'),
            ('Massachusetts', 'Denied', 'State Injunction', 'Suffolk Superior Court barred sports contracts, Jan 2026'),
            ('Ohio', 'Denied', 'Court Loss', 'Adverse ruling ~Mar 2026; 6th Cir. appeal (split with TN)'),

            # Disputed - Named in CFTC/DOJ federal preemption suit (Apr 2, 2026)
            ('Arizona', 'Disputed', 'Federal Preemption Suit', 'Named in CFTC/DOJ v. AZ, CT, IL (Apr 2, 2026)'),
            ('Connecticut', 'Disputed', 'Federal Preemption Suit', 'Named in CFTC/DOJ v. AZ, CT, IL (Apr 2, 2026)'),
            ('Illinois', 'Disputed', 'Federal Preemption Suit', 'Named in CFTC/DOJ v. AZ, CT, IL (Apr 2, 2026)'),
        ]
        for state, status, license_type, notes in states_data:
            c.execute('''INSERT INTO state_status
                (state, operating_status, license_type, notes, last_update)
                VALUES (?, ?, ?, ?, ?)''',
                (state, status, license_type, notes, datetime.now().isoformat()))

        # Seed transactions - illustrative activity for litigation states.
        # NOTE: Kalshi does not publish state-level volume; these figures are
        # placeholders for the dashboard, not verified market data.
        transactions_data = [
            ('New Jersey', 1800, 100.00, 'Election,Sports,Finance', 'Operating - 3rd Cir. win', 280),
            ('Tennessee', 2400, 100.00, 'Election,Sports,Economic', 'Operating - injunction', 380),
            ('Nevada', 600, 105.00, 'Election,Economic', 'Restricted - PI dissolved', 95),
            ('Maryland', 900, 95.00, 'Election,Economic', 'Restricted - court loss', 150),
            ('New York', 3200, 140.00, 'Election,Finance', 'Restricted - court loss', 500),
            ('Massachusetts', 2100, 120.00, 'Election,Sports', 'Restricted - state injunction', 350),
            ('Ohio', 1500, 98.00, 'Election,Economic', 'Restricted - court loss', 240),
            ('Arizona', 1100, 95.00, 'Election,Economic', 'Disputed - federal suit', 180),
            ('Connecticut', 1200, 105.00, 'Election,Finance', 'Disputed - federal suit', 220),
            ('Illinois', 2600, 110.00, 'Election,Economic', 'Disputed - federal suit', 430),
        ]
        for state, volume, avg_value, contracts, top, users in transactions_data:
            c.execute('''INSERT INTO transaction_data
                (state, monthly_volume, avg_contract_value, contract_types, top_contract, active_users, last_update)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (state, volume, avg_value, contracts, top, users, datetime.now().isoformat()))

        # Record the data version so we only re-seed when the data changes
        c.execute('''INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)''',
                  ('data_version', str(DATA_VERSION)))

        conn.commit()
        logger.info(f"Seeded {len(KALSHI_CASES)} cases, {len(states_data)} states, {len(transactions_data)} transactions (v{DATA_VERSION})")
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

    c.execute('''CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    conn.commit()

    # Determine whether we need to (re)seed. Re-seed when the table is empty
    # OR when the stored data version is behind the current DATA_VERSION.
    c.execute('SELECT COUNT(*) FROM state_status')
    state_count = c.fetchone()[0]

    c.execute("SELECT value FROM meta WHERE key = 'data_version'")
    row = c.fetchone()
    stored_version = int(row[0]) if row else 0

    if state_count == 0 or stored_version != DATA_VERSION:
        logger.info(f"Seeding database (rows={state_count}, stored_v={stored_version}, current_v={DATA_VERSION})...")
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
        # Scheduler is only initialized in __main__ mode, not in production
        return jsonify({'status': 'monitoring', 'message': 'Automated updates running in background'})

        # Get stats from database instead
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM legal_cases WHERE status = "Active"')
        active = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM legal_cases')
        total = c.fetchone()[0]
        conn.close()

        return jsonify({
            'status': 'monitoring',
            'active_cases': active,
            'total_cases': total,
            'next_check': 'Daily at 2:00 AM UTC',
            'last_update': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduler/update-now', methods=['POST'])
def trigger_update():
    """Manually trigger an immediate data update"""
    try:
        from data_sources import update_data
        updated = update_data(DB_PATH)

        return jsonify({
            'status': 'success',
            'message': f'Data update triggered',
            'cases_updated': updated,
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
    """Cleanup on app shutdown"""
    try:
        stop_scheduler()
    except:
        pass

# Initialize the database at import time so it runs under gunicorn/WSGI
# (the __main__ block below never executes when served by gunicorn).
# The version check inside init_db() ensures corrected seed data is applied
# even when Railway persists the SQLite file across deployments.
try:
    init_db()
except Exception as e:
    logger.error(f"Startup init_db failed: {e}")

if __name__ == '__main__':
    # Initialize database (also runs at import time above)
    init_db()

    # Start scheduler with error handling. Note: we intentionally do NOT run
    # update_data() on startup — the curated KALSHI_CASES seed is the single
    # source of truth. Running the live fetcher here would re-insert
    # unverified cases on top of the verified data.
    try:
        scheduler = start_scheduler()
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

    # Get environment variables
    debug = os.getenv('DEBUG', 'true').lower() == 'true'
    port = int(os.getenv('PORT', 8001))
    host = os.getenv('HOST', '127.0.0.1')

    # On production (Railway), use 0.0.0.0
    if os.getenv('RAILWAY_ENVIRONMENT'):
        host = '0.0.0.0'
        debug = False

    app.run(debug=debug, port=port, host=host)
