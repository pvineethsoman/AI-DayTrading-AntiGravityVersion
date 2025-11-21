import schedule
import time
import threading
import logging
from datetime import datetime
from src.services.portfolio_manager import PortfolioManager

logger = logging.getLogger(__name__)

class AgentScheduler:
    """
    Runs the PortfolioManager on a schedule in a background thread.
    """
    
    def __init__(self, portfolio_manager: PortfolioManager):
        self.portfolio_manager = portfolio_manager
        self.running = False
        self.thread = None
        
    def start(self):
        """Starts the scheduler in a background thread."""
        if self.running:
            return
            
        self.running = True
        
        # Define Schedule
        # Note: System time must be correct.
        schedule.every().day.at("09:25").do(self.run_job, "Pre-Market")
        schedule.every().day.at("14:00").do(self.run_job, "Afternoon")
        
        # For testing/demo purposes, run every hour too? No, stick to request.
        
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Scheduler started.")
        
    def stop(self):
        """Stops the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        logger.info("Scheduler stopped.")
        
    def _run_loop(self):
        while self.running:
            schedule.run_pending()
            time.sleep(1)
            
    def run_job(self, name: str):
        """Wrapper to run the job."""
        logger.info(f"Scheduler triggering job: {name}")
        # We use a default persona for scheduled runs, e.g., "General" or user preference if stored
        # For now, "General" is safe.
        self.portfolio_manager.run_cycle(persona="General")
        
    def get_next_run(self):
        """Returns the next scheduled run time."""
        return schedule.next_run()
