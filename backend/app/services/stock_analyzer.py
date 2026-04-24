import yfinance as yf
from typing import Dict
from datetime import datetime

class StockAnalyzerService:
    def analyze(self, symbol: str) -> Dict:
        # Convert to yfinance ticker if it's an NSE stock
        yf_ticker = f"{symbol}.NS" if not symbol.endswith(".NS") and "^" not in symbol else symbol
        ticker = yf.Ticker(yf_ticker)
        
        info = ticker.info
        
        # Next quarterly result
        earnings_date = "N/A"
        try:
            # yfinance returns a list of potential dates or a timestamp
            calendar = ticker.calendar
            if calendar and isinstance(calendar, dict) and "Earnings Date" in calendar:
                dates = calendar["Earnings Date"]
                if dates and len(dates) > 0:
                    earnings_date = dates[0].strftime("%B %d, %Y")
        except:
            pass

        # If earnings_date is still N/A, try to extract from other fields or leave as N/A
        
        # Calculate heuristics for strengths, weaknesses, investability, risk
        strengths = []
        weaknesses = []
        
        # Risk assessment
        risk_level = "Medium"
        risk_reasons = []
        
        # Basic Price Data
        current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
        fiftyTwoWeekHigh = info.get("fiftyTwoWeekHigh", 0)
        fiftyTwoWeekLow = info.get("fiftyTwoWeekLow", 0)
        beta = info.get("beta", 1.0)
        debtToEquity = info.get("debtToEquity", 0)
        profitMargins = info.get("profitMargins", 0)
        
        if current_price and fiftyTwoWeekHigh:
            dist_from_high = (fiftyTwoWeekHigh - current_price) / fiftyTwoWeekHigh * 100
            if dist_from_high < 5:
                strengths.append(f"Trading near 52-week high (₹{fiftyTwoWeekHigh})")
            elif dist_from_high > 40:
                weaknesses.append(f"Down {dist_from_high:.1f}% from 52-week high")
                
        if profitMargins > 0.15:
            strengths.append(f"Strong profit margins ({profitMargins*100:.1f}%)")
        elif profitMargins < 0:
            weaknesses.append("Company is currently loss-making")
            risk_level = "High"
            
        if debtToEquity and debtToEquity > 150:
            weaknesses.append(f"High debt-to-equity ratio ({debtToEquity}%)")
            risk_level = "High"
            risk_reasons.append("Highly leveraged balance sheet")
        elif debtToEquity and debtToEquity < 50:
            strengths.append("Low debt burden")
            
        if beta > 1.5:
            risk_level = "High"
            risk_reasons.append(f"High volatility (Beta: {beta:.2f})")
        elif beta < 0.8:
            risk_level = "Low"
            strengths.append(f"Low volatility stock (Beta: {beta:.2f})")

        # Recommendation
        recommendation = info.get("recommendationKey", "none").upper()
        if recommendation in ["BUY", "STRONG_BUY"]:
            can_invest = "Yes - Analyst consensus is positive."
        elif recommendation in ["SELL", "STRONG_SELL"]:
            can_invest = "Caution - Analyst consensus is negative."
        else:
            can_invest = "Hold - Wait for better entry levels or clearer trend."

        if not risk_reasons:
            if risk_level == "Low":
                risk_reasons.append("Stable large-cap with manageable debt and low volatility.")
            else:
                risk_reasons.append("Standard market risk applies.")

        return {
            "symbol": symbol,
            "name": info.get("longName", info.get("shortName", symbol)),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "description": info.get("longBusinessSummary", "No description available.")[:500] + "...",
            "current_price": current_price,
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else "N/A",
            "next_earnings_date": earnings_date,
            "strengths": strengths if strengths else ["Stable market position"],
            "weaknesses": weaknesses if weaknesses else ["Vulnerable to sector rotation"],
            "can_invest": can_invest,
            "risk_level": risk_level,
            "risk_analysis": " | ".join(risk_reasons)
        }
