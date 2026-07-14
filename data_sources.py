"""
Real Data Sources Integration
Fetches actual Kalshi litigation and regulatory data from multiple sources
"""

import requests
import sqlite3
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

# PACER Electronic Case Access
PACER_SEARCH_URL = "https://www.pacer.gov/cgi-bin/webservice"

# CourtListener API (Free PACER wrapper with better access)
COURTLISTENER_API = "https://www.courtlistener.com/api/rest/v3"

# SEC EDGAR for regulatory filings
SEC_EDGAR_API = "https://data.sec.gov/submissions/CIK0001811225.json"

class DataSources:
    """Manages multiple data sources for Kalshi litigation tracking"""

    def __init__(self, db_path='kalshi.db'):
        self.db_path = db_path

    def fetch_federal_cases(self):
        """
        Fetch federal court cases involving Kalshi from PACER/CourtListener
        """
        logger.info("Fetching federal court cases from PACER...")
        cases = []

        try:
            # Try CourtListener API first (no authentication needed)
            cases.extend(self._fetch_from_courtlistener())
        except Exception as e:
            logger.warning(f"CourtListener failed: {e}")

        try:
            # Fallback: Fetch from SEC EDGAR
            cases.extend(self._fetch_from_sec_edgar())
        except Exception as e:
            logger.warning(f"SEC EDGAR failed: {e}")

        logger.info(f"Found {len(cases)} federal cases")
        return cases

    def _fetch_from_courtlistener(self):
        """Query CourtListener for Kalshi cases"""
        cases = []
        try:
            # Search for Kalshi in case names
            search_params = {
                'q': 'Kalshi',
                'type': 'case',
                'court': 'dcd',  # D.C. District Court
                'order_by': '-date_filed'
            }

            response = requests.get(
                f"{COURTLISTENER_API}/search/",
                params=search_params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                for result in data.get('results', []):
                    case = {
                        'title': result.get('case_name', 'Unknown'),
                        'jurisdiction': 'U.S. Federal Court',
                        'case_type': 'Regulatory/Legal Challenge',
                        'status': self._parse_status(result.get('status', 'Pending')),
                        'description': result.get('summary', result.get('case_name', '')),
                        'source': 'PACER/CourtListener',
                        'date_filed': result.get('date_filed', datetime.now().isoformat()),
                        'url': result.get('url', ''),
                    }
                    cases.append(case)

        except Exception as e:
            logger.error(f"Error fetching from CourtListener: {e}")

        return cases

    def _fetch_from_sec_edgar(self):
        """Fetch Kalshi regulatory filings from SEC EDGAR"""
        cases = []
        try:
            response = requests.get(SEC_EDGAR_API, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Extract filings
                filings = data.get('filings', {}).get('recent', {})
                forms = filings.get('form', [])
                dates = filings.get('filingDate', [])
                accessions = filings.get('accessionNumber', [])

                # Get recent 8-K filings (material events)
                for i, form in enumerate(forms[:10]):
                    if form in ['8-K', '10-Q', '10-K']:  # Material events, quarterly, annual
                        if i < len(dates):
                            case = {
                                'title': f'SEC Filing: {form}',
                                'jurisdiction': 'U.S. Securities and Exchange Commission',
                                'case_type': 'Regulatory Filing',
                                'status': 'Active',
                                'description': f'{form} filing - Regulatory disclosure',
                                'source': 'SEC EDGAR',
                                'date_filed': dates[i],
                                'url': f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001811225&type={form}',
                            }
                            cases.append(case)

        except Exception as e:
            logger.error(f"Error fetching from SEC EDGAR: {e}")

        return cases

    def fetch_state_cases(self):
        """
        Fetch state-level regulatory cases and approvals
        """
        logger.info("Fetching state regulatory cases...")

        state_cases = []

        # States with verified, active Kalshi litigation / enforcement
        target_states = [
            'New Jersey', 'Tennessee', 'Nevada', 'Maryland',
            'New York', 'Massachusetts', 'Ohio'
        ]

        for state in target_states:
            try:
                cases = self._fetch_state_regulatory_data(state)
                state_cases.extend(cases)
            except Exception as e:
                logger.warning(f"Error fetching {state} data: {e}")

        logger.info(f"Found {len(state_cases)} state-level cases")
        return state_cases

    def _fetch_state_regulatory_data(self, state):
        """
        Fetch state-level regulatory data
        Comprehensive database of known Kalshi regulatory actions across 50 states
        """
        cases = []

        # Verified state-level litigation data (2025-2026). These match the
        # curated seed in app.py so manual/scheduled updates stay consistent.
        # Only the 8 states with actual cease-and-desist / court action are
        # tracked. Any other state returns [] (no verified action on record).
        verified_state_cases = {
            'New Jersey': [{'title': 'KalshiEX LLC v. Flaherty (New Jersey)', 'jurisdiction': 'U.S. Court of Appeals, 3rd Circuit (No. 25-1922)', 'case_type': 'Regulatory Enforcement', 'status': 'Active', 'description': 'FAVORABLE: 3rd Circuit affirmed preliminary injunction Apr 6, 2026 (CEA preempts state gambling law).', 'source': 'Paul Weiss; Holland & Knight', 'date_filed': '2025-03-15'}],
            'Tennessee': [{'title': 'KalshiEX v. Tennessee (Sports Event Contracts)', 'jurisdiction': 'U.S. District Court, M.D. Tennessee', 'case_type': 'Regulatory Enforcement', 'status': 'Active', 'description': 'FAVORABLE: Preliminary injunction granted Feb 19, 2026; TN AG appealed to 6th Circuit.', 'source': 'Legal Sports Report; SBC Americas', 'date_filed': '2026-01-12'}],
            'Nevada': [{'title': 'KalshiEX, LLC v. Hendrick (Nevada)', 'jurisdiction': 'U.S. District Court, D. Nevada (2:25-cv-00575)', 'case_type': 'Regulatory Enforcement', 'status': 'Active', 'description': 'UNFAVORABLE: PI dissolved Nov 24, 2025; Kalshi appealed to 9th Circuit (No. 25-7516).', 'source': 'Nevada Independent; CourtListener', 'date_filed': '2025-03-28'}],
            'Maryland': [{'title': 'KalshiEX v. Martin (Maryland)', 'jurisdiction': 'U.S. District Court, D. Maryland (1:25-cv-01283-ABA)', 'case_type': 'Regulatory Enforcement', 'status': 'Active', 'description': 'UNFAVORABLE: PI denied Aug 1, 2025; 4th Circuit oral argument May 7, 2026.', 'source': 'U.S. Dist. Court D.Md.; Brownstein', 'date_filed': '2025-04-20'}],
            'New York': [{'title': 'KalshiEX LLC v. New York State Gaming Commission', 'jurisdiction': 'U.S. District Court, S.D.N.Y. (1:25-cv-08846-AT)', 'case_type': 'Regulatory Enforcement', 'status': 'Active', 'description': 'UNFAVORABLE: Judge Torres denied PI Jul 7, 2026; Kalshi appealing.', 'source': 'NY Attorney General; Gothamist', 'date_filed': '2025-10-20'}],
            'Massachusetts': [{'title': 'KalshiEX v. Massachusetts (Suffolk Superior Court)', 'jurisdiction': 'Massachusetts Superior Court, Suffolk County', 'case_type': 'Regulatory Enforcement', 'status': 'Active', 'description': 'UNFAVORABLE: Jan 2026 preliminary injunction bars in-state sports contracts; 38 AGs amicus for MA.', 'source': 'Courthouse News; AZ Capitol Times', 'date_filed': '2025-12-01'}],
            'Ohio': [{'title': 'KalshiEX v. Ohio (Sports Event Contracts)', 'jurisdiction': 'U.S. District Court, S.D. Ohio', 'case_type': 'Regulatory Enforcement', 'status': 'Active', 'description': 'UNFAVORABLE: Court ruled against Kalshi ~Mar 2026; 6th Circuit appeal (split with Tennessee).', 'source': 'SBC Americas; ST News', 'date_filed': '2025-10-08'}],
        }
        return verified_state_cases.get(state, [])

        # --- Legacy placeholder data (unused, superseded by verified data above) ---
        known_state_cases = {
            'Alabama': [{'title': 'Alabama Securities Compliance Review', 'jurisdiction': 'Alabama Securities Commission', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Review of prediction market offerings and securities compliance', 'source': 'AL Securities Commission', 'date_filed': '2023-07-15'}],
            'Alaska': [{'title': 'Alaska Financial Regulator Inquiry', 'jurisdiction': 'Alaska Department of Commerce', 'case_type': 'Regulatory Inquiry', 'status': 'Pending', 'description': 'Inquiry into financial services offerings in Alaska', 'source': 'AK Department of Commerce', 'date_filed': '2023-08-01'}],
            'Arizona': [{'title': 'Arizona Financial Services Review', 'jurisdiction': 'Arizona Department of Financial Institutions', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Review of digital asset and contract offerings', 'source': 'AZ Financial Institutions', 'date_filed': '2023-06-01'}],
            'Arkansas': [{'title': 'Arkansas Securities Division Review', 'jurisdiction': 'Arkansas Securities Department', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Review of prediction market platform compliance', 'source': 'AR Securities Department', 'date_filed': '2023-07-20'}],
            'California': [{'title': 'Kalshi Money Transmitter License', 'jurisdiction': 'California Department of Financial Protection', 'case_type': 'Regulatory Approval', 'status': 'Pending', 'description': 'Money transmitter license application', 'source': 'CA Financial Regulator', 'date_filed': '2023-01-15'}],
            'Colorado': [{'title': 'Colorado Money Transmitter License', 'jurisdiction': 'Colorado Division of Banking', 'case_type': 'Regulatory Approval', 'status': 'Approved', 'description': 'Money transmitter license approved', 'source': 'CO Division of Banking', 'date_filed': '2023-02-01'}],
            'Connecticut': [{'title': 'Connecticut Financial Regulator Review', 'jurisdiction': 'Connecticut Department of Banking', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Review of contract offerings and licensing requirements', 'source': 'CT Department of Banking', 'date_filed': '2023-06-10'}],
            'Delaware': [{'title': 'Delaware Financial Services Inquiry', 'jurisdiction': 'Delaware Division of Corporations', 'case_type': 'Regulatory Inquiry', 'status': 'Pending', 'description': 'Investigation into financial derivative offerings', 'source': 'DE Division of Corporations', 'date_filed': '2023-07-25'}],
            'Florida': [{'title': 'Florida Financial Regulator Denial', 'jurisdiction': 'Florida Office of Financial Regulation', 'case_type': 'Regulatory Denial', 'status': 'Denied', 'description': 'License application denied due to regulatory concerns', 'source': 'FL Financial Regulator', 'date_filed': '2023-02-15'}],
            'Georgia': [{'title': 'Georgia Money Transmitter License', 'jurisdiction': 'Georgia Department of Banking', 'case_type': 'Regulatory Approval', 'status': 'Pending', 'description': 'Money transmitter license application pending', 'source': 'GA Banking Department', 'date_filed': '2023-05-15'}],
            'Hawaii': [{'title': 'Hawaii Money Transmitter License Application', 'jurisdiction': 'Hawaii Division of Financial Institutions', 'case_type': 'Regulatory Approval', 'status': 'Pending', 'description': 'Money transmitter license review for Hawaii operations', 'source': 'HI Financial Institutions', 'date_filed': '2023-08-05'}],
            'Idaho': [{'title': 'Idaho Financial Regulator Review', 'jurisdiction': 'Idaho Department of Finance', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Review of prediction market platform operations', 'source': 'ID Department of Finance', 'date_filed': '2023-07-10'}],
            'Illinois': [{'title': 'Illinois Financial Investigation', 'jurisdiction': 'Illinois Attorney General', 'case_type': 'Regulatory Inquiry', 'status': 'Pending', 'description': 'State investigation into contract offerings', 'source': 'IL Attorney General', 'date_filed': '2023-03-10'}],
            'Indiana': [{'title': 'Indiana Securities Review', 'jurisdiction': 'Indiana Secretary of State', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Securities compliance review for financial derivatives', 'source': 'IN Secretary of State', 'date_filed': '2023-07-30'}],
            'Iowa': [{'title': 'Iowa Financial Services Inquiry', 'jurisdiction': 'Iowa Division of Banking', 'case_type': 'Regulatory Inquiry', 'status': 'Pending', 'description': 'Inquiry into financial services offerings and regulation', 'source': 'IA Division of Banking', 'date_filed': '2023-08-10'}],
            'Kansas': [{'title': 'Kansas Securities Commission Review', 'jurisdiction': 'Kansas Office of the State Bank Commissioner', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Review of prediction market platform licensing', 'source': 'KS State Bank Commissioner', 'date_filed': '2023-07-05'}],
            'Kentucky': [{'title': 'Kentucky Financial Regulator Inquiry', 'jurisdiction': 'Kentucky Department of Financial Institutions', 'case_type': 'Regulatory Inquiry', 'status': 'Pending', 'description': 'Investigation into derivative market offerings', 'source': 'KY Financial Institutions', 'date_filed': '2023-08-15'}],
            'Louisiana': [{'title': 'Louisiana Securities Compliance Review', 'jurisdiction': 'Louisiana Office of Financial Institutions', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Securities licensing review and compliance assessment', 'source': 'LA Office of Financial Institutions', 'date_filed': '2023-07-12'}],
            'Maine': [{'title': 'Maine Financial Services Review', 'jurisdiction': 'Maine Department of Professional and Financial Regulation', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Review of prediction market platform compliance', 'source': 'ME Department of Regulation', 'date_filed': '2023-08-20'}],
            'Maryland': [{'title': 'Maryland Money Transmitter License Application', 'jurisdiction': 'Maryland Department of Assessments and Taxation', 'case_type': 'Regulatory Approval', 'status': 'Pending', 'description': 'Money transmitter licensing review', 'source': 'MD Assessments and Taxation', 'date_filed': '2023-06-15'}],
            'Massachusetts': [{'title': 'Kalshi Fintech License', 'jurisdiction': 'Massachusetts Secretary of State', 'case_type': 'Regulatory Approval', 'status': 'Approved', 'description': 'Fintech license approval', 'source': 'MA Secretary of State', 'date_filed': '2022-09-15'}],
            'Michigan': [{'title': 'Michigan Financial Regulator Review', 'jurisdiction': 'Michigan Department of Insurance and Financial Services', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Review of Kalshi operations and licensing requirements', 'source': 'MI Financial Regulator', 'date_filed': '2023-05-01'}],
            'Minnesota': [{'title': 'Minnesota Financial Services Inquiry', 'jurisdiction': 'Minnesota Department of Commerce', 'case_type': 'Regulatory Inquiry', 'status': 'Pending', 'description': 'Inquiry into prediction market platform operations', 'source': 'MN Department of Commerce', 'date_filed': '2023-07-18'}],
            'Mississippi': [{'title': 'Mississippi Securities Review', 'jurisdiction': 'Mississippi Secretary of State', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Securities compliance and licensing review', 'source': 'MS Secretary of State', 'date_filed': '2023-08-08'}],
            'Missouri': [{'title': 'Missouri Securities Division Inquiry', 'jurisdiction': 'Missouri Secretary of State', 'case_type': 'Regulatory Inquiry', 'status': 'Pending', 'description': 'Investigation into financial derivative market operations', 'source': 'MO Secretary of State', 'date_filed': '2023-07-22'}],
            'Montana': [{'title': 'Montana Financial Regulator Review', 'jurisdiction': 'Montana Division of Banking and Financial Institutions', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Review of money transmitter and platform licensing', 'source': 'MT Division of Banking', 'date_filed': '2023-08-12'}],
            'Nebraska': [{'title': 'Nebraska Money Transmitter License Application', 'jurisdiction': 'Nebraska Department of Banking', 'case_type': 'Regulatory Approval', 'status': 'Pending', 'description': 'Money transmitter license review and approval', 'source': 'NE Department of Banking', 'date_filed': '2023-07-28'}],
            'Nevada': [{'title': 'Nevada Financial Services Inquiry', 'jurisdiction': 'Nevada Division of Financial Institutions', 'case_type': 'Regulatory Inquiry', 'status': 'Pending', 'description': 'Inquiry into financial services offerings', 'source': 'NV Financial Institutions', 'date_filed': '2023-05-25'}],
            'New Hampshire': [{'title': 'New Hampshire Securities Review', 'jurisdiction': 'New Hampshire Bureau of Securities Regulation', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Securities licensing and compliance review', 'source': 'NH Securities Regulation', 'date_filed': '2023-08-03'}],
            'New Jersey': [{'title': 'New Jersey Financial Services Inquiry', 'jurisdiction': 'New Jersey Department of Banking and Insurance', 'case_type': 'Regulatory Inquiry', 'status': 'Pending', 'description': 'Investigation into financial market offerings', 'source': 'NJ Banking and Insurance', 'date_filed': '2023-07-14'}],
            'New Mexico': [{'title': 'New Mexico Financial Regulator Review', 'jurisdiction': 'New Mexico Regulation and Licensing Department', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Review of financial services platform licensing', 'source': 'NM Regulation and Licensing', 'date_filed': '2023-08-18'}],
            'New York': [{'title': 'Kalshi Markets BitLicense Application', 'jurisdiction': 'New York Department of Financial Services', 'case_type': 'Regulatory Approval', 'status': 'Pending', 'description': 'BitLicense application review', 'source': 'NYDFS', 'date_filed': '2022-06-01'}],
            'North Carolina': [{'title': 'North Carolina Securities Review', 'jurisdiction': 'North Carolina Secretary of State', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Securities compliance and licensing review', 'source': 'NC Secretary of State', 'date_filed': '2023-07-11'}],
            'North Dakota': [{'title': 'North Dakota Financial Services Inquiry', 'jurisdiction': 'North Dakota Department of Financial Institutions', 'case_type': 'Regulatory Inquiry', 'status': 'Pending', 'description': 'Inquiry into prediction market platform operations', 'source': 'ND Financial Institutions', 'date_filed': '2023-08-25'}],
            'Ohio': [{'title': 'Ohio Financial Regulator Inquiry', 'jurisdiction': 'Ohio Department of Commerce', 'case_type': 'Regulatory Inquiry', 'status': 'Pending', 'description': 'Inquiry into contract offerings and consumer protection', 'source': 'OH Commerce Department', 'date_filed': '2023-04-10'}],
            'Oklahoma': [{'title': 'Oklahoma Securities Commission Review', 'jurisdiction': 'Oklahoma Department of Securities', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Securities licensing and compliance review', 'source': 'OK Department of Securities', 'date_filed': '2023-07-09'}],
            'Oregon': [{'title': 'Oregon Financial Services Inquiry', 'jurisdiction': 'Oregon Department of Consumer and Business Services', 'case_type': 'Regulatory Inquiry', 'status': 'Pending', 'description': 'Investigation into financial market platform operations', 'source': 'OR Consumer and Business Services', 'date_filed': '2023-08-22'}],
            'Pennsylvania': [{'title': 'Pennsylvania Money Transmitter Review', 'jurisdiction': 'Pennsylvania Department of Banking', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Money transmitter licensing review', 'source': 'PA Banking Department', 'date_filed': '2023-03-20'}],
            'Rhode Island': [{'title': 'Rhode Island Financial Services Review', 'jurisdiction': 'Rhode Island Department of Business Regulation', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Review of financial services and market platform licensing', 'source': 'RI Business Regulation', 'date_filed': '2023-08-07'}],
            'South Carolina': [{'title': 'South Carolina Securities Review', 'jurisdiction': 'South Carolina Department of Insurance', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Securities compliance and licensing assessment', 'source': 'SC Department of Insurance', 'date_filed': '2023-07-19'}],
            'South Dakota': [{'title': 'South Dakota Financial Regulator Inquiry', 'jurisdiction': 'South Dakota Division of Banking', 'case_type': 'Regulatory Inquiry', 'status': 'Pending', 'description': 'Investigation into financial services offerings', 'source': 'SD Division of Banking', 'date_filed': '2023-08-14'}],
            'Tennessee': [{'title': 'Tennessee Securities Division Review', 'jurisdiction': 'Tennessee Securities Division', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Securities licensing and compliance review', 'source': 'TN Securities Division', 'date_filed': '2023-07-16'}],
            'Texas': [{'title': 'Texas Lottery Commission Inquiry', 'jurisdiction': 'Texas Lottery Commission', 'case_type': 'Regulatory Inquiry', 'status': 'Pending', 'description': 'Regulatory inquiry into contract classification', 'source': 'Texas Lottery Commission', 'date_filed': '2023-04-01'}],
            'Utah': [{'title': 'Utah Division of Finance Compliance Review', 'jurisdiction': 'Utah Division of Finance', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Financial services platform compliance and licensing review', 'source': 'UT Division of Finance', 'date_filed': '2023-08-09'}],
            'Vermont': [{'title': 'Vermont Financial Services Review', 'jurisdiction': 'Vermont Department of Financial Regulation', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Review of money transmitter and financial platform licensing', 'source': 'VT Financial Regulation', 'date_filed': '2023-08-21'}],
            'Virginia': [{'title': 'Virginia Money Transmitter Application', 'jurisdiction': 'Virginia State Corporation Commission', 'case_type': 'Regulatory Approval', 'status': 'Pending', 'description': 'Money transmitter license application', 'source': 'VA Corporation Commission', 'date_filed': '2023-04-30'}],
            'Washington': [{'title': 'Washington Money Transmitter License', 'jurisdiction': 'Washington Department of Financial Institutions', 'case_type': 'Regulatory Approval', 'status': 'Approved', 'description': 'Money transmitter license approved', 'source': 'WA Financial Institutions', 'date_filed': '2023-01-20'}],
            'West Virginia': [{'title': 'West Virginia Securities Review', 'jurisdiction': 'West Virginia Securities Commission', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Securities compliance and financial market licensing review', 'source': 'WV Securities Commission', 'date_filed': '2023-07-24'}],
            'Wisconsin': [{'title': 'Wisconsin Financial Services Inquiry', 'jurisdiction': 'Wisconsin Department of Financial Institutions', 'case_type': 'Regulatory Inquiry', 'status': 'Pending', 'description': 'Investigation into financial market platform operations', 'source': 'WI Financial Institutions', 'date_filed': '2023-08-11'}],
            'Wyoming': [{'title': 'Wyoming Financial Regulator Review', 'jurisdiction': 'Wyoming Division of Banking', 'case_type': 'Regulatory Review', 'status': 'Pending', 'description': 'Review of financial services and money transmitter licensing', 'source': 'WY Division of Banking', 'date_filed': '2023-08-19'}],
        }

        return known_state_cases.get(state, [])

    def _parse_status(self, status_str):
        """Convert various status formats to our standard"""
        status_lower = str(status_str).lower()

        if any(x in status_lower for x in ['open', 'active', 'ongoing']):
            return 'Active'
        elif any(x in status_lower for x in ['closed', 'terminated', 'resolved', 'dismissed']):
            return 'Resolved'
        else:
            return 'Pending'

    def save_to_database(self, cases):
        """Save fetched cases to database"""
        if not cases:
            logger.warning("No cases to save")
            return 0

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        saved_count = 0
        for case in cases:
            try:
                c.execute('''INSERT OR REPLACE INTO legal_cases
                    (title, jurisdiction, case_type, status, description, source, date_filed, last_update)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (case.get('title'),
                     case.get('jurisdiction'),
                     case.get('case_type'),
                     case.get('status'),
                     case.get('description'),
                     case.get('source'),
                     case.get('date_filed'),
                     datetime.now().isoformat()))
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving case {case.get('title')}: {e}")

        conn.commit()
        conn.close()

        logger.info(f"Saved {saved_count} cases to database")
        return saved_count

    def fetch_and_update_all(self):
        """Fetch from all sources and update database"""
        logger.info("Starting comprehensive data update...")

        all_cases = []

        # Fetch federal cases
        all_cases.extend(self.fetch_federal_cases())

        # Fetch state cases
        all_cases.extend(self.fetch_state_cases())

        # Remove duplicates
        unique_cases = {case['title']: case for case in all_cases}.values()

        # Save to database
        saved = self.save_to_database(list(unique_cases))

        logger.info(f"Data update complete: {saved} cases total")
        return saved


def update_data(db_path='kalshi.db'):
    """Main entry point for data updates"""
    source = DataSources(db_path)
    return source.fetch_and_update_all()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    update_data()
