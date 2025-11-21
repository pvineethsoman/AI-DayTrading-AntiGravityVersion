import schedule
import time
import threading
import sys
import os
from rich.console import Console
from src.ui.cli import TradingCLI

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

console = Console()

def run_automation():
    """Background thread for scheduled tasks."""
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    console.print(Panel.fit("[bold blue]AI Day Trading Bot[/bold blue]\n[italic]Iteration 3: UI & Automation[/italic]"))
    
    # Start automation thread (daemon so it dies with main)
    automation_thread = threading.Thread(target=run_automation, daemon=True)
    automation_thread.start()
    
    # Start CLI
    try:
        TradingCLI().cmdloop()
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting...[/yellow]")

if __name__ == "__main__":
    from rich.panel import Panel # Import here to avoid circular if at top level before path fix
    main()
