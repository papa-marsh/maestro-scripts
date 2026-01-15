from dataclasses import dataclass

import requests

from scripts.config.secrets import FINNHUB_TOKEN

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


@dataclass
class FinnhubResponse:
    """
    Stock quote as returned from the Finnhub API.
    c=Current Price, d=Change, dp=Percent Change,
    h=High, l=Low, o=Open, pc=Previous Close, t=Update Timestamp
    """

    c: float  # Current Price
    d: float  # Change
    dp: float  # Percent Change
    h: float  # High
    l: float  # Low
    o: float  # Open
    pc: float  # Previous Close
    t: float  # Update Timestamp


def get_stock_quote(symbol: str = "SPY") -> FinnhubResponse:
    """Returns a stock quote for the given stock symbol"""
    url = f"{FINNHUB_BASE_URL}/quote"
    params = {"symbol": symbol.upper(), "token": FINNHUB_TOKEN}

    response = requests.get(url, params, timeout=30)
    quote = FinnhubResponse(**response.json())

    return quote
