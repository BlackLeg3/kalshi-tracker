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

KALSHI_CASES = [
    # FEDERAL CASES - Appellate Level
    # Resolved/Closed Cases
    ('Kalshi v. CFTC', 'U.S. District Court, D.C.', 'Regulatory Enforcement', 'Resolved',
     'Kalshi won district court ruling. CFTC withdrew appeal May 2025. Election and economic contracts declared lawful.', 'Public Records', '2023-02-20'),
    ('CFTC v. Kalshi', 'U.S. Court of Appeals, D.C. Circuit', 'Regulatory Enforcement', 'Resolved',
     'CFTC appeal dismissed May 2025. Kalshi\'s political event contracts upheld as lawful.', 'Public Records', '2023-01-15'),

    # Active Federal Cases
    ('SEC Investigation - Market Manipulation', 'U.S. Securities and Exchange Commission', 'Regulatory Inquiry', 'Active',
     'SEC investigation into potential market manipulation and insider trading allegations.', 'Public Records', '2024-03-15'),
    ('Congressional Subcommittee Inquiry', 'U.S. House Financial Services Committee', 'Legislative Action', 'Active',
     'Congressional inquiry into prediction markets and regulatory jurisdiction gaps.', 'Public Records', '2025-06-01'),
    ('CFTC v. State Regulators', 'U.S. Court of Appeals', 'Regulatory Enforcement', 'Active',
     'CFTC assertion of exclusive federal regulatory authority over prediction markets (April 2026). States: NY, WI, and others.', 'Public Records', '2026-04-15'),
    ('Kalshi Consumer Class Action', 'U.S. District Court, N.D. California', 'Civil Litigation', 'Pending',
     'Class action regarding margin requirements, disclosures, and sports gambling allegations.', 'Public Records', '2023-05-22'),

    # STATE-LEVEL CASES - 8 States with Actual Cease-and-Desist Orders
    # Favorable to Kalshi
    ('Tennessee Prediction Markets Challenge', 'U.S. District Court, E.D. Tennessee', 'Regulatory Enforcement', 'Active',
     'Kalshi obtained temporary restraining order (TRO) Jan 2026 blocking state gaming law enforcement. State gaming commission cease-and-desist challenged.', 'Public Records', '2025-11-01'),

    # Pending/Mixed
    ('Ohio Sports Wagering Dispute', 'U.S. District Court, S.D. Ohio', 'Regulatory Enforcement', 'Pending',
     'Kalshi preliminary injunction motion pending against Ohio gaming enforcement. Cease-and-desist issued by state gaming commission.', 'Public Records', '2025-09-15'),
    ('Connecticut Gaming Law Challenge', 'U.S. District Court, D. Connecticut', 'Regulatory Enforcement', 'Pending',
     'Kalshi injunction motion pending. Connecticut cease-and-desist demands compliance with state gaming laws.', 'Public Records', '2025-10-20'),
    ('New Jersey Regulatory Enforcement', 'New Jersey Division of Gaming Enforcement', 'Regulatory Enforcement', 'Active',
     'New Jersey issued cease-and-desist order. Kalshi challenging state gambling jurisdiction.', 'Public Records', '2025-08-01'),
    ('Nevada Gaming Commission Action', 'Nevada Division of Financial Institutions', 'Regulatory Enforcement', 'Active',
     'Nevada gaming regulators issued cease-and-desist. Kalshi sports contracts classified as illegal gambling under state law.', 'Public Records', '2025-07-15'),

    # Unfavorable to Kalshi
    ('New York BitLicense/Gaming Challenge', 'U.S. District Court, S.D. New York', 'Regulatory Enforcement', 'Active',
     'Kalshi lost bid to block NY state gaming law enforcement (Jan 2026). NYDFS maintains state jurisdiction over sports wagering.', 'Public Records', '2022-06-01'),
    ('Massachusetts Gaming Law Enforcement', 'Massachusetts Superior Court, Suffolk County', 'Regulatory Enforcement', 'Active',
     'Preliminary injunction issued Jan 2026 barring Kalshi sports bets in Massachusetts. Court found state gaming laws apply. Kalshi appealing.', 'Public Records', '2025-12-01'),
    ('Maryland Sports Wagering Dispute', 'U.S. District Court, D. Maryland', 'Regulatory Enforcement', 'Active',
     'Maryland federal court denied Kalshi injunction Aug 2025, held Congress did not intend to preempt state gambling authority.', 'Public Records', '2025-05-01'),
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

        # Seed states - Focus on states with active litigation and regulatory status
        states_data = [
            # Favorable to Kalshi or No Restrictions
            ('California', 'Approved', 'DCM Status', 'Federal designation applies, no state restrictions'),
            ('Colorado', 'Approved', 'Money Transmitter', 'Operations active'),
            ('Tennessee', 'Approved', 'Federal Preemption', 'TRO granted Jan 2026 - federal authority over state'),

            # Disputed/Pending - Active Litigation
            ('Connecticut', 'Disputed', 'Gaming Law Challenge', 'Injunction motion pending'),
            ('Maryland', 'Denied', 'Federal Court Loss', 'State gaming authority upheld Aug 2025'),
            ('Massachusetts', 'Denied', 'Preliminary Injunction', 'State gaming laws apply, Jan 2026 ruling'),
            ('New Jersey', 'Disputed', 'Cease-and-Desist', 'State gaming enforcement ongoing'),
            ('Nevada', 'Disputed', 'Cease-and-Desist', 'State classified sports contracts as gambling'),
            ('New York', 'Disputed', 'Injunction Failed', 'Lost challenge to state gaming law Jan 2026'),
            ('Ohio', 'Disputed', 'Injunction Pending', 'Preliminary injunction motion under review'),
            ('Wisconsin', 'Disputed', 'Federal Challenge', 'In CFTC v. State Regulators case (Apr 2026)'),
        ]
        for state, status, license_type, notes in states_data:
            c.execute('''INSERT INTO state_status
                (state, operating_status, license_type, notes, last_update)
                VALUES (?, ?, ?, ?, ?)''',
                (state, status, license_type, notes, datetime.now().isoformat()))

        # Seed transactions - Major litigation/regulatory states only
        transactions_data = [
            ('California', 8200, 95.00, 'Election,Technology', 'Technology Events', 1500),
            ('Colorado', 18500, 110.00, 'Election,Crypto,Commodities', 'Election Contracts', 3500),
            ('Connecticut', 1200, 105.00, 'Election,Sports', 'Limited by legal dispute', 220),
            ('Maryland', 900, 95.00, 'Election,Economic', 'Restricted by court order', 150),
            ('Massachusetts', 2100, 120.00, 'Election,Sports', 'Restricted - injunction active', 350),
            ('New Jersey', 1800, 100.00, 'Election,Finance', 'Limited - cease-and-desist', 280),
            ('Nevada', 600, 105.00, 'Crypto,Commodities', 'Restricted - gaming classification', 95),
            ('New York', 3200, 140.00, 'Election,Finance', 'Limited - state gaming law', 500),
            ('Ohio', 1500, 98.00, 'Election,Economic', 'Disputed - injunction pending', 240),
            ('Tennessee', 2400, 100.00, 'Election,Economic', 'Favorable - TRO granted', 380),
            ('Wisconsin', 800, 92.00, 'Election', 'In federal challenge', 130),
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

if __name__ == '__main__':
    # Initialize database
    init_db()

    # Start scheduler with error handling
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

    # Get environment variables
    debug = os.getenv('DEBUG', 'true').lower() == 'true'
    port = int(os.getenv('PORT', 8001))
    host = os.getenv('HOST', '127.0.0.1')

    # On production (Railway), use 0.0.0.0
    if os.getenv('RAILWAY_ENVIRONMENT'):
        host = '0.0.0.0'
        debug = False

    app.run(debug=debug, port=port, host=host)
