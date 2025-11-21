from src.models.trading import Portfolio
from rich.table import Table
from rich.console import Console

class PerformanceReporter:
    """Generates performance reports."""
    
    @staticmethod
    def generate_text_report(portfolio: Portfolio) -> str:
        lines = []
        lines.append("=== Performance Report ===")
        lines.append(f"Total Value: ${portfolio.total_value:,.2f}")
        lines.append(f"Cash:        ${portfolio.cash:,.2f}")
        lines.append(f"Positions:   {len(portfolio.positions)}")
        return "\n".join(lines)

    @staticmethod
    def print_rich_report(portfolio: Portfolio):
        console = Console()
        table = Table(title="Performance Report")
        table.add_column("Metric")
        table.add_column("Value")
        
        table.add_row("Total Value", f"${portfolio.total_value:,.2f}")
        table.add_row("Cash", f"${portfolio.cash:,.2f}")
        table.add_row("Positions Count", str(len(portfolio.positions)))
        
        console.print(table)
