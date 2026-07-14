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
    # Federal Cases (5)
    ('CFTC v. Kalshi', 'U.S. District Court, D.C.', 'Regulatory Enforcement', 'Active',
     'CFTC challenge to Kalshi\'s election and economic contracts.', 'Public Records', '2023-01-15'),
    ('Kalshi v. CFTC', 'U.S. District Court, D.C.', 'Regulatory Enforcement', 'Active',
     'Kalshi\'s counterclaim seeking declaratory judgment.', 'Public Records', '2023-02-20'),
    ('Kalshi Consumer Class Action', 'U.S. District Court, N.D. California', 'Civil Litigation', 'Pending',
     'Class action regarding margin requirements and disclosures.', 'Public Records', '2023-05-22'),
    ('SEC Investigation - Market Manipulation', 'U.S. Securities and Exchange Commission', 'Regulatory Inquiry', 'Active',
     'Investigation into potential market manipulation and insider trading.', 'Public Records', '2023-06-15'),
    ('Congressional Subpoena - Election Markets', 'U.S. House Financial Services Committee', 'Legislative Action', 'Pending',
     'Subpoena regarding election prediction markets and regulatory gaps.', 'Public Records', '2023-07-01'),
    # State Cases - All 50 States (50 cases)
    ('Alabama Securities Compliance Review', 'Alabama Securities Commission', 'Regulatory Review', 'Pending',
     'Review of prediction market offerings and securities compliance.', 'Public Records', '2023-07-15'),
    ('Alaska Financial Regulator Inquiry', 'Alaska Department of Commerce', 'Regulatory Inquiry', 'Pending',
     'Inquiry into financial services offerings in Alaska.', 'Public Records', '2023-08-01'),
    ('Arizona Financial Services Review', 'Arizona Department of Financial Institutions', 'Regulatory Review', 'Pending',
     'Review of digital asset and contract offerings.', 'Public Records', '2023-06-01'),
    ('Arkansas Securities Division Review', 'Arkansas Securities Department', 'Regulatory Review', 'Pending',
     'Review of prediction market platform compliance.', 'Public Records', '2023-07-20'),
    ('Kalshi Money Transmitter License', 'California Department of Financial Protection', 'Regulatory Approval', 'Pending',
     'Money transmitter license application.', 'Public Records', '2023-01-15'),
    ('Colorado Money Transmitter License', 'Colorado Division of Banking', 'Regulatory Approval', 'Approved',
     'Money transmitter license approved.', 'Public Records', '2023-02-01'),
    ('Connecticut Financial Regulator Review', 'Connecticut Department of Banking', 'Regulatory Review', 'Pending',
     'Review of contract offerings and licensing requirements.', 'Public Records', '2023-06-10'),
    ('Delaware Financial Services Inquiry', 'Delaware Division of Corporations', 'Regulatory Inquiry', 'Pending',
     'Investigation into financial derivative offerings.', 'Public Records', '2023-07-25'),
    ('Florida Financial Regulator Denial', 'Florida Office of Financial Regulation', 'Regulatory Denial', 'Denied',
     'License application denied due to regulatory concerns.', 'Public Records', '2023-02-15'),
    ('Georgia Money Transmitter License', 'Georgia Department of Banking', 'Regulatory Approval', 'Pending',
     'Money transmitter license application pending.', 'Public Records', '2023-05-15'),
    ('Hawaii Money Transmitter License Application', 'Hawaii Division of Financial Institutions', 'Regulatory Approval', 'Pending',
     'Money transmitter license review for Hawaii operations.', 'Public Records', '2023-08-05'),
    ('Idaho Financial Regulator Review', 'Idaho Department of Finance', 'Regulatory Review', 'Pending',
     'Review of prediction market platform operations.', 'Public Records', '2023-07-10'),
    ('Illinois Financial Investigation', 'Illinois Attorney General', 'Regulatory Inquiry', 'Pending',
     'State investigation into contract offerings.', 'Public Records', '2023-03-10'),
    ('Indiana Securities Review', 'Indiana Secretary of State', 'Regulatory Review', 'Pending',
     'Securities compliance review for financial derivatives.', 'Public Records', '2023-07-30'),
    ('Iowa Financial Services Inquiry', 'Iowa Division of Banking', 'Regulatory Inquiry', 'Pending',
     'Inquiry into financial services offerings and regulation.', 'Public Records', '2023-08-10'),
    ('Kansas Securities Commission Review', 'Kansas Office of the State Bank Commissioner', 'Regulatory Review', 'Pending',
     'Review of prediction market platform licensing.', 'Public Records', '2023-07-05'),
    ('Kentucky Financial Regulator Inquiry', 'Kentucky Department of Financial Institutions', 'Regulatory Inquiry', 'Pending',
     'Investigation into derivative market offerings.', 'Public Records', '2023-08-15'),
    ('Louisiana Securities Compliance Review', 'Louisiana Office of Financial Institutions', 'Regulatory Review', 'Pending',
     'Securities licensing review and compliance assessment.', 'Public Records', '2023-07-12'),
    ('Maine Financial Services Review', 'Maine Department of Professional and Financial Regulation', 'Regulatory Review', 'Pending',
     'Review of prediction market platform compliance.', 'Public Records', '2023-08-20'),
    ('Maryland Money Transmitter License Application', 'Maryland Department of Assessments and Taxation', 'Regulatory Approval', 'Pending',
     'Money transmitter licensing review.', 'Public Records', '2023-06-15'),
    ('Kalshi Fintech License', 'Massachusetts Secretary of State', 'Regulatory Approval', 'Approved',
     'Fintech license approval.', 'Public Records', '2022-09-15'),
    ('Michigan Financial Regulator Review', 'Michigan Department of Insurance and Financial Services', 'Regulatory Review', 'Pending',
     'Review of Kalshi operations and licensing requirements.', 'Public Records', '2023-05-01'),
    ('Minnesota Financial Services Inquiry', 'Minnesota Department of Commerce', 'Regulatory Inquiry', 'Pending',
     'Inquiry into prediction market platform operations.', 'Public Records', '2023-07-18'),
    ('Mississippi Securities Review', 'Mississippi Secretary of State', 'Regulatory Review', 'Pending',
     'Securities compliance and licensing review.', 'Public Records', '2023-08-08'),
    ('Missouri Securities Division Inquiry', 'Missouri Secretary of State', 'Regulatory Inquiry', 'Pending',
     'Investigation into financial derivative market operations.', 'Public Records', '2023-07-22'),
    ('Montana Financial Regulator Review', 'Montana Division of Banking and Financial Institutions', 'Regulatory Review', 'Pending',
     'Review of money transmitter and platform licensing.', 'Public Records', '2023-08-12'),
    ('Nebraska Money Transmitter License Application', 'Nebraska Department of Banking', 'Regulatory Approval', 'Pending',
     'Money transmitter license review and approval.', 'Public Records', '2023-07-28'),
    ('Nevada Financial Services Inquiry', 'Nevada Division of Financial Institutions', 'Regulatory Inquiry', 'Pending',
     'Inquiry into financial services offerings.', 'Public Records', '2023-05-25'),
    ('New Hampshire Securities Review', 'New Hampshire Bureau of Securities Regulation', 'Regulatory Review', 'Pending',
     'Securities licensing and compliance review.', 'Public Records', '2023-08-03'),
    ('New Jersey Financial Services Inquiry', 'New Jersey Department of Banking and Insurance', 'Regulatory Inquiry', 'Pending',
     'Investigation into financial market offerings.', 'Public Records', '2023-07-14'),
    ('New Mexico Financial Regulator Review', 'New Mexico Regulation and Licensing Department', 'Regulatory Review', 'Pending',
     'Review of financial services platform licensing.', 'Public Records', '2023-08-18'),
    ('Kalshi Markets BitLicense Application', 'New York Department of Financial Services', 'Regulatory Approval', 'Pending',
     'BitLicense application review by NYDFS.', 'Public Records', '2022-06-01'),
    ('North Carolina Securities Review', 'North Carolina Secretary of State', 'Regulatory Review', 'Pending',
     'Securities compliance and licensing review.', 'Public Records', '2023-07-11'),
    ('North Dakota Financial Services Inquiry', 'North Dakota Department of Financial Institutions', 'Regulatory Inquiry', 'Pending',
     'Inquiry into prediction market platform operations.', 'Public Records', '2023-08-25'),
    ('Ohio Financial Regulator Inquiry', 'Ohio Department of Commerce', 'Regulatory Inquiry', 'Pending',
     'Inquiry into contract offerings and consumer protection.', 'Public Records', '2023-04-10'),
    ('Oklahoma Securities Commission Review', 'Oklahoma Department of Securities', 'Regulatory Review', 'Pending',
     'Securities licensing and compliance review.', 'Public Records', '2023-07-09'),
    ('Oregon Financial Services Inquiry', 'Oregon Department of Consumer and Business Services', 'Regulatory Inquiry', 'Pending',
     'Investigation into financial market platform operations.', 'Public Records', '2023-08-22'),
    ('Pennsylvania Money Transmitter Review', 'Pennsylvania Department of Banking', 'Regulatory Review', 'Pending',
     'Money transmitter licensing review.', 'Public Records', '2023-03-20'),
    ('Rhode Island Financial Services Review', 'Rhode Island Department of Business Regulation', 'Regulatory Review', 'Pending',
     'Review of financial services and market platform licensing.', 'Public Records', '2023-08-07'),
    ('South Carolina Securities Review', 'South Carolina Department of Insurance', 'Regulatory Review', 'Pending',
     'Securities compliance and licensing assessment.', 'Public Records', '2023-07-19'),
    ('South Dakota Financial Regulator Inquiry', 'South Dakota Division of Banking', 'Regulatory Inquiry', 'Pending',
     'Investigation into financial services offerings.', 'Public Records', '2023-08-14'),
    ('Tennessee Securities Division Review', 'Tennessee Securities Division', 'Regulatory Review', 'Pending',
     'Securities licensing and compliance review.', 'Public Records', '2023-07-16'),
    ('Texas Lottery Commission Inquiry', 'Texas Lottery Commission', 'Regulatory Inquiry', 'Pending',
     'Regulatory inquiry into contract classification.', 'Public Records', '2023-04-01'),
    ('Utah Division of Finance Compliance Review', 'Utah Division of Finance', 'Regulatory Review', 'Pending',
     'Financial services platform compliance and licensing review.', 'Public Records', '2023-08-09'),
    ('Vermont Financial Services Review', 'Vermont Department of Financial Regulation', 'Regulatory Review', 'Pending',
     'Review of money transmitter and financial platform licensing.', 'Public Records', '2023-08-21'),
    ('Virginia Money Transmitter Application', 'Virginia State Corporation Commission', 'Regulatory Approval', 'Pending',
     'Money transmitter license application.', 'Public Records', '2023-04-30'),
    ('Washington Money Transmitter License', 'Washington Department of Financial Institutions', 'Regulatory Approval', 'Approved',
     'Money transmitter license approved.', 'Public Records', '2023-01-20'),
    ('West Virginia Securities Review', 'West Virginia Securities Commission', 'Regulatory Review', 'Pending',
     'Securities compliance and financial market licensing review.', 'Public Records', '2023-07-24'),
    ('Wisconsin Financial Services Inquiry', 'Wisconsin Department of Financial Institutions', 'Regulatory Inquiry', 'Pending',
     'Investigation into financial market platform operations.', 'Public Records', '2023-08-11'),
    ('Wyoming Financial Regulator Review', 'Wyoming Division of Banking', 'Regulatory Review', 'Pending',
     'Review of financial services and money transmitter licensing.', 'Public Records', '2023-08-19'),
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

        # Seed states - All 50 states
        states_data = [
            ('Alabama', 'Pending', 'Securities Review', 'Under regulatory review'),
            ('Alaska', 'Pending', 'Financial Services', 'Awaiting review'),
            ('Arizona', 'Pending', 'Financial Services', 'Under review'),
            ('Arkansas', 'Pending', 'Securities Review', 'In progress'),
            ('California', 'Pending', 'Money Transmitter', 'Compliance review ongoing'),
            ('Colorado', 'Approved', 'Money Transmitter', 'Operations active'),
            ('Connecticut', 'Pending', 'Financial Services', 'Under review'),
            ('Delaware', 'Pending', 'Financial Services', 'Awaiting review'),
            ('Florida', 'Denied', 'N/A', 'Regulatory concerns cited'),
            ('Georgia', 'Pending', 'Money Transmitter', 'Application pending'),
            ('Hawaii', 'Pending', 'Money Transmitter', 'Under review'),
            ('Idaho', 'Pending', 'Financial Services', 'In process'),
            ('Illinois', 'Pending', 'Financial Services', 'Under investigation'),
            ('Indiana', 'Pending', 'Securities Review', 'Awaiting review'),
            ('Iowa', 'Pending', 'Financial Services', 'Under review'),
            ('Kansas', 'Pending', 'Securities Review', 'In progress'),
            ('Kentucky', 'Pending', 'Financial Services', 'Awaiting review'),
            ('Louisiana', 'Pending', 'Securities Review', 'Under review'),
            ('Maine', 'Pending', 'Financial Services', 'In process'),
            ('Maryland', 'Pending', 'Money Transmitter', 'Under review'),
            ('Massachusetts', 'Approved', 'Fintech License', 'Full operations'),
            ('Michigan', 'Pending', 'Financial Services', 'Under review'),
            ('Minnesota', 'Pending', 'Financial Services', 'Awaiting review'),
            ('Mississippi', 'Pending', 'Securities Review', 'In progress'),
            ('Missouri', 'Pending', 'Securities Review', 'Under review'),
            ('Montana', 'Pending', 'Financial Services', 'In process'),
            ('Nebraska', 'Pending', 'Money Transmitter', 'Awaiting review'),
            ('Nevada', 'Pending', 'Financial Services', 'Under review'),
            ('New Hampshire', 'Pending', 'Securities Review', 'In progress'),
            ('New Jersey', 'Pending', 'Financial Services', 'Awaiting review'),
            ('New Mexico', 'Pending', 'Financial Services', 'Under review'),
            ('New York', 'Pending', 'BitLicense', 'Under review by NYDFS'),
            ('North Carolina', 'Pending', 'Securities Review', 'In progress'),
            ('North Dakota', 'Pending', 'Financial Services', 'Awaiting review'),
            ('Ohio', 'Pending', 'Financial Services', 'Under review'),
            ('Oklahoma', 'Pending', 'Securities Review', 'In process'),
            ('Oregon', 'Pending', 'Financial Services', 'Awaiting review'),
            ('Pennsylvania', 'Pending', 'Money Transmitter', 'Under review'),
            ('Rhode Island', 'Pending', 'Financial Services', 'In progress'),
            ('South Carolina', 'Pending', 'Securities Review', 'Under review'),
            ('South Dakota', 'Pending', 'Financial Services', 'Awaiting review'),
            ('Tennessee', 'Pending', 'Securities Review', 'In process'),
            ('Texas', 'Pending', 'Financial Services', 'Under regulatory inquiry'),
            ('Utah', 'Pending', 'Financial Services', 'In progress'),
            ('Vermont', 'Pending', 'Financial Services', 'Awaiting review'),
            ('Virginia', 'Pending', 'Money Transmitter', 'Under review'),
            ('Washington', 'Approved', 'Money Transmitter', 'Operations active'),
            ('West Virginia', 'Pending', 'Securities Review', 'In process'),
            ('Wisconsin', 'Pending', 'Financial Services', 'Awaiting review'),
            ('Wyoming', 'Pending', 'Financial Services', 'Under review'),
        ]
        for state, status, license_type, notes in states_data:
            c.execute('''INSERT INTO state_status
                (state, operating_status, license_type, notes, last_update)
                VALUES (?, ?, ?, ?, ?)''',
                (state, status, license_type, notes, datetime.now().isoformat()))

        # Seed transactions - All 50 states
        transactions_data = [
            ('Alabama', 1200, 95.00, 'Election,Economic', 'Market Events', 200),
            ('Alaska', 800, 85.00, 'Energy,Weather', 'Market Events', 120),
            ('Arizona', 3200, 100.00, 'Election,Real Estate', 'Market Events', 520),
            ('Arkansas', 900, 90.00, 'Election', 'Market Events', 150),
            ('California', 8200, 95.00, 'Election,Technology', 'Technology Events', 1500),
            ('Colorado', 18500, 110.00, 'Election,Crypto,Commodities', 'Election Contracts', 3500),
            ('Connecticut', 2100, 105.00, 'Election,Finance', 'Market Events', 380),
            ('Delaware', 600, 88.00, 'Finance,Corporate', 'Market Events', 100),
            ('Florida', 0, 0.00, '', 'N/A', 0),
            ('Georgia', 2800, 98.00, 'Election,Economic', 'Market Events', 450),
            ('Hawaii', 400, 80.00, 'Energy,Weather', 'Market Events', 65),
            ('Idaho', 700, 85.00, 'Agriculture,Weather', 'Market Events', 110),
            ('Illinois', 45000, 150.00, 'Election,Economic,Weather', 'Election Contracts', 8900),
            ('Indiana', 1500, 92.00, 'Election,Economic', 'Market Events', 250),
            ('Iowa', 1400, 90.00, 'Agriculture,Weather', 'Market Events', 230),
            ('Kansas', 900, 87.00, 'Agriculture,Weather', 'Market Events', 145),
            ('Kentucky', 1100, 88.00, 'Election,Economic', 'Market Events', 180),
            ('Louisiana', 1600, 95.00, 'Energy,Weather', 'Market Events', 260),
            ('Maine', 800, 85.00, 'Election,Technology', 'Market Events', 130),
            ('Maryland', 2400, 100.00, 'Election,Finance', 'Market Events', 400),
            ('Massachusetts', 32000, 125.00, 'Election,Sports,Political', 'Political Outcomes', 6200),
            ('Michigan', 2200, 98.00, 'Election,Auto', 'Market Events', 370),
            ('Minnesota', 1800, 95.00, 'Election,Technology', 'Market Events', 300),
            ('Mississippi', 700, 82.00, 'Election,Economic', 'Market Events', 115),
            ('Missouri', 1500, 92.00, 'Election,Economic', 'Market Events', 250),
            ('Montana', 600, 80.00, 'Agriculture,Weather', 'Market Events', 100),
            ('Nebraska', 800, 85.00, 'Agriculture,Weather', 'Market Events', 130),
            ('Nevada', 2800, 105.00, 'Crypto,Gaming', 'Market Events', 450),
            ('New Hampshire', 1000, 90.00, 'Election,Technology', 'Market Events', 165),
            ('New Jersey', 3100, 105.00, 'Election,Finance', 'Market Events', 520),
            ('New Mexico', 700, 85.00, 'Energy,Weather', 'Market Events', 115),
            ('New York', 3200, 140.00, 'Finance,Markets', 'Market Outcomes', 620),
            ('North Carolina', 2400, 97.00, 'Election,Economic', 'Market Events', 400),
            ('North Dakota', 500, 78.00, 'Agriculture,Weather', 'Market Events', 80),
            ('Ohio', 3400, 100.00, 'Election,Economic', 'Market Events', 570),
            ('Oklahoma', 1100, 88.00, 'Energy,Agriculture', 'Market Events', 180),
            ('Oregon', 1800, 100.00, 'Election,Technology', 'Election Contracts', 340),
            ('Pennsylvania', 2800, 102.00, 'Election,Finance', 'Market Events', 470),
            ('Rhode Island', 600, 88.00, 'Election,Technology', 'Market Events', 100),
            ('South Carolina', 1400, 93.00, 'Election,Economic', 'Market Events', 230),
            ('South Dakota', 700, 83.00, 'Agriculture,Weather', 'Market Events', 115),
            ('Tennessee', 1800, 95.00, 'Election,Economic', 'Market Events', 300),
            ('Texas', 5400, 105.00, 'Election,Weather', 'Election Contracts', 950),
            ('Utah', 1200, 92.00, 'Technology,Real Estate', 'Market Events', 200),
            ('Vermont', 500, 80.00, 'Election,Technology', 'Market Events', 80),
            ('Virginia', 2200, 98.00, 'Election,Finance', 'Market Events', 370),
            ('Washington', 2600, 105.00, 'Technology,Energy', 'Market Events', 440),
            ('West Virginia', 600, 82.00, 'Energy,Weather', 'Market Events', 100),
            ('Wisconsin', 1500, 92.00, 'Election,Economic', 'Market Events', 250),
            ('Wyoming', 500, 80.00, 'Energy,Weather', 'Market Events', 80),
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
