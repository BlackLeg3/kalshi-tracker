import sqlite3
from datetime import datetime
import sys
import os

os.chdir('/Users/jamescarroll/Desktop/Kalshi')
DB_PATH = 'kalshi.db'

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

    conn.commit()
    conn.close()

# Sample data based on public Kalshi information
CASES = [
    {
        'title': 'CFTC v. Kalshi',
        'jurisdiction': 'Federal (D.C.)',
        'case_type': 'Regulatory Enforcement',
        'status': 'Active',
        'description': 'CFTC challenge to Kalshi\'s event contracts. Dispute over classification of contracts.',
        'source': 'SEC Filings',
        'date_filed': '2023-01-15'
    },
    {
        'title': 'New York Department of Financial Services Review',
        'jurisdiction': 'New York',
        'case_type': 'Regulatory Approval',
        'status': 'Pending',
        'description': 'BitLicense application review process.',
        'source': 'NYDFS',
        'date_filed': '2022-06-01'
    },
    {
        'title': 'Illinois State Investigation',
        'jurisdiction': 'Illinois',
        'case_type': 'Regulatory Inquiry',
        'status': 'Pending',
        'description': 'State inquiry into contract offerings and consumer protections.',
        'source': 'Illinois AG',
        'date_filed': '2023-03-20'
    },
    {
        'title': 'Class Action - Consumer Protections',
        'jurisdiction': 'California',
        'case_type': 'Civil Litigation',
        'status': 'Pending',
        'description': 'Class action regarding margin requirements and consumer disclosures.',
        'source': 'Court Filings',
        'date_filed': '2023-05-10'
    },
]

STATES = [
    {'state': 'New York', 'operating_status': 'Pending', 'license_type': 'BitLicense', 'notes': 'Under review by NYDFS'},
    {'state': 'California', 'operating_status': 'Pending', 'license_type': 'Money Transmitter', 'notes': 'Compliance review ongoing'},
    {'state': 'Illinois', 'operating_status': 'Approved', 'license_type': 'Regulated', 'notes': 'Limited offerings available'},
    {'state': 'Texas', 'operating_status': 'Pending', 'license_type': 'Money Transmitter', 'notes': 'License application submitted'},
    {'state': 'Florida', 'operating_status': 'Denied', 'license_type': 'N/A', 'notes': 'Regulatory concerns cited'},
    {'state': 'Massachusetts', 'operating_status': 'Approved', 'license_type': 'Fintech License', 'notes': 'Full operations'},
    {'state': 'Colorado', 'operating_status': 'Approved', 'license_type': 'Regulated', 'notes': 'Operations commenced'},
    {'state': 'Oregon', 'operating_status': 'Pending', 'license_type': 'License Application', 'notes': 'Awaiting review'},
]

TRANSACTIONS = [
    {'state': 'Illinois', 'monthly_volume': 45000, 'avg_contract_value': 150.00,
     'contract_types': 'Election,Economic,Weather', 'top_contract': 'Election Contracts', 'active_users': 8900},
    {'state': 'Massachusetts', 'monthly_volume': 32000, 'avg_contract_value': 125.00,
     'contract_types': 'Election,Sports,Political', 'top_contract': 'Political Outcomes', 'active_users': 6200},
    {'state': 'Colorado', 'monthly_volume': 18500, 'avg_contract_value': 110.00,
     'contract_types': 'Election,Crypto,Commodities', 'top_contract': 'Election Contracts', 'active_users': 3500},
    {'state': 'California', 'monthly_volume': 8200, 'avg_contract_value': 95.00,
     'contract_types': 'Election,Technology', 'top_contract': 'Technology Events', 'active_users': 1500},
    {'state': 'Texas', 'monthly_volume': 5400, 'avg_contract_value': 105.00,
     'contract_types': 'Election,Weather', 'top_contract': 'Election Contracts', 'active_users': 950},
    {'state': 'New York', 'monthly_volume': 3200, 'avg_contract_value': 140.00,
     'contract_types': 'Finance,Markets', 'top_contract': 'Market Outcomes', 'active_users': 620},
    {'state': 'Florida', 'monthly_volume': 0, 'avg_contract_value': 0.00,
     'contract_types': '', 'top_contract': 'N/A', 'active_users': 0},
    {'state': 'Oregon', 'monthly_volume': 1800, 'avg_contract_value': 100.00,
     'contract_types': 'Election,Weather', 'top_contract': 'Election Contracts', 'active_users': 340},
]

def seed_db():
    init_db()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Clear existing data
    c.execute('DELETE FROM legal_cases')
    c.execute('DELETE FROM state_status')

    # Insert cases
    for case in CASES:
        c.execute('''INSERT INTO legal_cases
            (title, jurisdiction, case_type, status, description, source, date_filed, last_update)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (case['title'], case['jurisdiction'], case['case_type'], case['status'],
             case['description'], case['source'], case['date_filed'], datetime.now().isoformat()))

    # Insert states
    for state in STATES:
        c.execute('''INSERT INTO state_status
            (state, operating_status, license_type, notes, last_update)
            VALUES (?, ?, ?, ?, ?)''',
            (state['state'], state['operating_status'], state['license_type'],
             state['notes'], datetime.now().isoformat()))

    # Insert transaction data
    for tx in TRANSACTIONS:
        c.execute('''INSERT INTO transaction_data
            (state, monthly_volume, avg_contract_value, contract_types, top_contract, active_users, last_update)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (tx['state'], tx['monthly_volume'], tx['avg_contract_value'],
             tx['contract_types'], tx['top_contract'], tx['active_users'],
             datetime.now().isoformat()))

    conn.commit()
    conn.close()
    print("✅ Database seeded with initial data")

if __name__ == '__main__':
    seed_db()
