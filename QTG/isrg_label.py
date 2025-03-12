import pandas as pd
import numpy as np
import os


def get_percentiles(df: pd.DataFrame, col: str) -> list[pd.DataFrame]:
    return [df.groupby(level=0, group_keys=False).apply(lambda x: x.sort_values(col, ascending=False)).groupby(level=0, group_keys=False).apply(lambda x: x.iloc[i-5:i]) for i in range(5, 30, 5)]


market = pd.read_pickle("./QTG/isrg.pkl")
market = market.stack()

market["Day Percent Change"] = (market["Close"] - market["Open"]) / market["Open"]
market['Previous Close'] = market.groupby(level='Ticker')['Close'].shift(1)
market['Percent Change'] = (market['Close'] - market['Previous Close']) / market['Previous Close']

market["Next Day Close"] = market.groupby(level='Ticker')['Close'].shift(-1)
market['Next Day Percent Change'] = (market['Next Day Close'] - market['Close']) / market['Close']


market['2 Week Close'] = market.groupby(level='Ticker')['Close'].shift(-10)
market['1 Week Close'] = market.groupby(level="Ticker")['Close'].shift(-5)
market['Percent 2 Week Growth'] = (market['2 Week Close'] - market['Close']) / market['Close']
market['Percent 1 Week Growth'] = (market['1 Week Close'] - market['Close']) / market['Close']
market["Percent 1 to 2 Week Growth"] = (market['2 Week Close'] - market['1 Week Close']) / market['1 Week Close']

market["6 Days Prev Close"] = market.groupby(level='Ticker')['Close'].shift(6)
market["6 Days Prev Change"] = (market["Previous Close"] - market["6 Days Prev Close"]) / market["6 Days Prev Close"]
market["1 Month Prev Close"] = market.groupby(level='Ticker')['Close'].shift(24)
market["1 Month Prev Change"] = (market["Previous Close"] - market["1 Month Prev Close"]) / market["1 Month Prev Close"]
market["3 Months Prev Close"] = market.groupby(level='Ticker')['Close'].shift(72)
market["3 Months Prev Change"] = (market["Previous Close"] - market["3 Months Prev Close"]) / market["3 Months Prev Close"]
market["6 Months Prev Close"] = market.groupby(level='Ticker')['Close'].shift(148)
market["6 Months Prev Change"] = (market["Previous Close"] - market["6 Months Prev Close"]) / market["6 Months Prev Close"]


market['-10 Day Avg Volume'] = market.groupby(level='Ticker')['Volume'].apply(lambda x: x.rolling(window=10).mean().shift(1)).reset_index(level=0, drop=True)
market['Prop -10 Day Avg Volume'] = market["Volume"] / market["-10 Day Avg Volume"]

market['5 Day Avg Volume'] = market.groupby(level='Ticker')["Volume"].apply(lambda x: x.rolling(window=5).mean().shift(-4)).reset_index(level=0, drop=True)
market["Prop 5 to -10 Day Avg Volume"] = market["5 Day Avg Volume"] / market["-10 Day Avg Volume"]

market['-20 Day Avg Volume'] = market.groupby(level='Ticker')['Volume'].apply(lambda x: x.rolling(window=20).mean().shift(1)).reset_index(level=0, drop=True)
market['Prop -20 Day Avg Volume'] = market["Volume"] / market["-20 Day Avg Volume"]

market["Prop 5 to -20 Day Avg Volume"] = market["5 Day Avg Volume"] / market["-20 Day Avg Volume"]

market["Close Change"] = market.groupby(level="Ticker")["Close"].diff()
market["RSI"] = 100 - (100 / (1 + ((market["Close Change"].where(market["Close Change"] > 0, 0)).groupby(level="Ticker").rolling(window=14).mean().reset_index(level=0, drop=True) / (-market["Close Change"].where(market["Close Change"] < 0, 0)).groupby(level="Ticker").rolling(window=14).mean().reset_index(level=0, drop=True))))

sorted_data = market.groupby(level=0, group_keys=False).apply(lambda x: x.sort_values('Percent Change', ascending=False))

top_25_stocks = sorted_data.groupby(level=0, group_keys=False).apply(lambda x: x.nlargest(25, 'Percent Change'))
bottom_25_stocks = sorted_data.groupby(level=0, group_keys=False).apply(lambda x: x.nsmallest(25, 'Percent Change'))


market['Gainer'] = market.index.isin(top_25_stocks.index)
market['Loser'] = market.index.isin(bottom_25_stocks.index)

top_25_stocks_percentiles_self = [top_25_stocks.groupby(level=0, group_keys=False).apply(lambda x: x.iloc[i-5:i]) for i in range(5, 30, 5)]
bottom_25_stocks_percentiles_self = [bottom_25_stocks.groupby(level=0, group_keys=False).apply(lambda x: x.iloc[i-5:i]) for i in range(5, 30, 5)]

categories = ['Percent 2 Week Growth', 'Percent 1 Week Growth', '6 Days Prev Change', '1 Month Prev Change', "3 Months Prev Change", "6 Months Prev Change"]

gainers_percentiles = [get_percentiles(top_25_stocks, category) for category in categories]
losers_percentiles = [get_percentiles(bottom_25_stocks, category) for category in categories]

for i in range(5):
    market[f"Gainer Percent {(i+1)*20}"] = market.index.isin(top_25_stocks_percentiles_self[i].index)
    market[f"Loser Percent {(i+1)*20}"] = market.index.isin(bottom_25_stocks_percentiles_self[i].index)
    for cat in range(len(gainers_percentiles)):
        market[f"Gainer {categories[cat]} Percent {(i+1)*20}"] = market.index.isin(gainers_percentiles[cat][i].index)
        market[f"Loser {categories[cat]} Percent {(i+1)*20}"] = market.index.isin(losers_percentiles[cat][i].index)


market.to_pickle("./QTG/isrg_label.pkl")


