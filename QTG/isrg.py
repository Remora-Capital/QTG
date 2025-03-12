import yfinance as yf
import pandas as pd


isrg = yf.download(["ISRG", "AAPL"], '2024-12-10', '2025-02-10')

isrg.to_pickle("./QTG/ISRG.pkl")