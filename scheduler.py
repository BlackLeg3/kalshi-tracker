"""
Automated Updates Scheduler
- Fetches SEC EDGAR filings daily
- Updates case statuses weekly
- Logs all changes
"""

import requests
import sqlite3
import json
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = 'kalshi.db'
SEC_EDGAR_API = "https://www.sec.gov/cgi-bin/browse-edgar"

# Kalshi's CIK (Central Index Key) for SEC EDGAR
KALSHI_CIK = "0001811225"

class KalshiDataScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def start(self):
        """Start the background scheduler"""
        # Daily check for SEC filings at 2 AM
        self.scheduler.add_job(
            self.fetch_sec_filings,
            'cron',
            hour=2,
            minute=0,
            id='fetch_sec_filings'
        )

        # Weekly case status update every Monday at 9 AM
        self.scheduler.add_job(
            self.update_case_statuses,
            'cron',
            day_of_week='mon',
            hour=9,
            minute=0,
            id='update_case_statuses'
        )

        self.scheduler.start()
        logger.info("✓ Scheduler started - Updates configured")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("✓ Scheduler stopped")

    def fetch_sec_filings(self):
        """
        Fetch latest Kalshi litigation and regulatory data from all sources
        """
        logger.info("📄 Fetching latest Kalshi cases from all data sources...")

        try:
            from data_sources import update_data
            updated = update_data(DB_PATH)
            logger.info(f"✅ Data update complete - {updated} cases processed")
        except Exception as e:
            logger.error(f"❌ Error updating data sources: {e}")

    def update_case_statuses(self):
        """
        Update case statuses based on recent developments
        This is a placeholder that can be enhanced with real status tracking
        """
        logger.info("🔄 Updating case statuses...")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Example: Update any cases that should be resolved based on date
        try:
            # Get all active cases
            c.execute('SELECT id, title, date_filed FROM legal_cases WHERE status = ?',
                     ('Active',))
            cases = c.fetchall()

            updates = 0
            for case_id, title, date_filed in cases:
                # Check if case is from more than 2 years ago (example logic)
                if date_filed:
                    case_date = datetime.fromisoformat(date_filed)
                    days_old = (datetime.now() - case_date).days

                    # If older than 730 days, mark as needing review
                    if days_old > 730:
                        c.execute('UPDATE legal_cases SET status = ? WHERE id = ?',
                                 ('Pending Review', case_id))
                        updates += 1
                        logger.info(f"  ✓ Marked for review: {title}")

            conn.commit()
            logger.info(f"✅ Case status update complete - {updates} cases reviewed")

        except Exception as e:
            logger.error(f"❌ Error updating case statuses: {e}")
        finally:
            conn.close()

    def get_status_summary(self):
        """Get a summary of tracked items"""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            c.execute('SELECT COUNT(*) FROM legal_cases WHERE status = ?', ('Active',))
            active = c.fetchone()[0]

            c.execute('SELECT COUNT(*) FROM legal_cases WHERE status = ?', ('Pending',))
            pending = c.fetchone()[0]

            c.execute('SELECT COUNT(*) FROM legal_cases WHERE status = ?', ('Resolved',))
            resolved = c.fetchone()[0]

            conn.close()

            return {
                'active': active,
                'pending': pending,
                'resolved': resolved,
                'total': active + pending + resolved
            }
        except Exception as e:
            logger.error(f"Error getting status summary: {e}")
            return {}


# Global scheduler instance
scheduler_instance = None

def start_scheduler():
    """Start the global scheduler"""
    global scheduler_instance
    if scheduler_instance is None:
        scheduler_instance = KalshiDataScheduler()
        scheduler_instance.start()
    return scheduler_instance

def stop_scheduler():
    """Stop the global scheduler"""
    global scheduler_instance
    if scheduler_instance:
        scheduler_instance.stop()
        scheduler_instance = None


if __name__ == '__main__':
    # Test the scheduler
    print("Starting scheduler for testing...")
    sched = start_scheduler()

    # Run updates immediately for testing
    print("\nRunning immediate updates...")
    sched.fetch_sec_filings()
    sched.update_case_statuses()

    # Show status
    status = sched.get_status_summary()
    print(f"\nCurrent status: {status}")

    print("\nScheduler will run:")
    print("  - Daily SEC filing check at 2:00 AM")
    print("  - Weekly case status update every Monday at 9:00 AM")

    # Keep running
    try:
        print("\nScheduler is running. Press Ctrl+C to stop.")
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_scheduler()
        print("Scheduler stopped.")
