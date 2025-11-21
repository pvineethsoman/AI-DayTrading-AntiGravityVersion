from typing import Dict
import math

class ValuationCalculator:
    """Calculates fundamental valuation metrics."""

    @staticmethod
    def calculate_graham_number(eps: float, book_value_per_share: float) -> float:
        """
        Calculates the Graham Number: Sqrt(22.5 * EPS * Book Value per Share)
        """
        if eps <= 0 or book_value_per_share <= 0:
            return 0.0
        return math.sqrt(22.5 * eps * book_value_per_share)

    @staticmethod
    def calculate_dcf(free_cash_flow: float, growth_rate: float, discount_rate: float, terminal_growth_rate: float, years: int = 5) -> float:
        """
        Simple DCF calculation.
        
        Args:
            free_cash_flow: Current Free Cash Flow
            growth_rate: Expected growth rate for the projection period (decimal, e.g. 0.05 for 5%)
            discount_rate: Discount rate (WACC) (decimal)
            terminal_growth_rate: Terminal growth rate (decimal)
            years: Number of years to project
        """
        future_cash_flows = []
        for i in range(1, years + 1):
            fcf = free_cash_flow * ((1 + growth_rate) ** i)
            discounted_fcf = fcf / ((1 + discount_rate) ** i)
            future_cash_flows.append(discounted_fcf)
            
        # Terminal Value
        last_fcf = free_cash_flow * ((1 + growth_rate) ** years)
        terminal_value = (last_fcf * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
        discounted_terminal_value = terminal_value / ((1 + discount_rate) ** years)
        
        total_value = sum(future_cash_flows) + discounted_terminal_value
        return total_value
