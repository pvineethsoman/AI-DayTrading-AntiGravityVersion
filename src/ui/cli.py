import cmd
import sys
import threading
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.models.domain import Stock
from src.providers.yahoo import YahooFinanceProvider
from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.rsi_reversion import RSIMeanReversionStrategy
from src.backtesting.engine import Backtester
from src.execution.paper_engine import PaperTradingEngine

console = Console()

class TradingCLI(cmd.Cmd):
    intro = 'Welcome to the AI Day Trading Bot. Type help or ? to list commands.\n'
    prompt = '(bot) '
    
    def __init__(self):
        super().__init__()
        self.provider = YahooFinanceProvider()
        self.engine = PaperTradingEngine()
        self.active_traders = {} # symbol -> thread
        self.stop_events = {} # symbol -> event

    def do_status(self, arg):
        """Show current portfolio status."""
        table = Table(title="Portfolio Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Cash", f"${self.engine.portfolio.cash:,.2f}")
        table.add_row("Total Value", f"${self.engine.portfolio.total_value:,.2f}")
        
        console.print(table)
        
        if self.engine.portfolio.positions:
            pos_table = Table(title="Positions")
            pos_table.add_column("Symbol")
            pos_table.add_column("Qty")
            pos_table.add_column("Avg Price")
            pos_table.add_column("Current Price")
            pos_table.add_column("PnL")
            
            for sym, pos in self.engine.portfolio.positions.items():
                pnl = pos.unrealized_pnl
                color = "green" if pnl >= 0 else "red"
                pos_table.add_row(
                    sym, 
                    str(pos.quantity), 
                    f"${pos.average_price:.2f}", 
                    f"${pos.current_price:.2f}", 
                    f"[{color}]${pnl:.2f}[/{color}]"
                )
            console.print(pos_table)
        else:
            console.print("[yellow]No active positions.[/yellow]")

    def do_backtest(self, arg):
        """Run backtest. Usage: backtest <symbol> <strategy_type> (sma|rsi)"""
        args = arg.split()
        if len(args) < 2:
            console.print("[red]Usage: backtest <symbol> <strategy_type>[/red]")
            return
            
        symbol = args[0].upper()
        strategy_type = args[1].lower()
        
        with console.status(f"[bold green]Fetching data for {symbol}...[/bold green]"):
            try:
                stock = self.provider.get_stock_data(symbol)
            except Exception as e:
                console.print(f"[red]Error fetching data: {e}[/red]")
                return

        strategy = None
        if strategy_type == 'sma':
            strategy = SMACrossoverStrategy()
        elif strategy_type == 'rsi':
            strategy = RSIMeanReversionStrategy()
        else:
            console.print(f"[red]Unknown strategy: {strategy_type}[/red]")
            return
            
        console.print(f"[bold]Running {strategy.name} backtest on {symbol}...[/bold]")
        backtester = Backtester(strategy)
        backtester.run(stock)

    def do_quit(self, arg):
        """Exit the CLI."""
        console.print("Goodbye!")
        return True

    def do_exit(self, arg):
        """Exit the CLI."""
        return self.do_quit(arg)

if __name__ == '__main__':
    TradingCLI().cmdloop()
