import yfinance as yf
import pandas as pd

# Read and print the stock tickers that make up S&P500
tickers = pd.read_html(
    'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]

# # Get the data for this tickers from yahoo finance
# snp2016 = yf.download(tickers.Symbol.to_list(), '2016-01-01', '2016-12-31', auto_adjust=True)
# snp2017 = yf.download(tickers.Symbol.to_list(), '2017-01-01', '2017-12-31', auto_adjust=True)
# snp2018 = yf.download(tickers.Symbol.to_list(), '2018-01-01', '2018-12-31', auto_adjust=True)
# snp2019 = yf.download(tickers.Symbol.to_list(), '2019-01-01', '2019-12-31', auto_adjust=True)
# snp2020 = yf.download(tickers.Symbol.to_list(), '2020-01-01', '2020-12-31', auto_adjust=True)
# snp2021 = yf.download(tickers.Symbol.to_list(), '2021-01-01', '2021-12-31', auto_adjust=True)
# snp2022 = yf.download(tickers.Symbol.to_list(), '2022-01-01', '2022-12-31', auto_adjust=True)
# snp2023 = yf.download(tickers.Symbol.to_list(), '2023-01-01', '2023-12-31', auto_adjust=True)
# snp2024 = yf.download(tickers.Symbol.to_list(), '2024-01-01', '2024-12-31', auto_adjust=True)
years = [yf.download(tickers.Symbol.to_list(), f'20{x}-01-01', f'20{x}-12-31', auto_adjust=True) for x in range(16,25)]

for i, year in enumerate(years):
    year = year.swaplevel(axis=1)
    year = year.stack("Ticker")
    year.to_pickle(f'./QTG/snp/20{i+16}.pkl')
