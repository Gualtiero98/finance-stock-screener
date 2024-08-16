import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Step 1: Scrape tickers from Yahoo Finance
def scrape_tickers_from_yahoo(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    tickers = []
    for row in soup.find_all('tr', {'class': 'simpTblRow'}):
        ticker = row.find('td', {'aria-label': 'Symbol'}).text.strip()
        tickers.append(ticker)
    
    return tickers

# Example URLs for Yahoo Finance screens
url = 'https://finance.yahoo.com/gainers'  # URL for the "Top Gainers" page
# Other examples:
# url = 'https://finance.yahoo.com/losers'  # Top Losers
# url = 'https://finance.yahoo.com/most-active'  # Most Active Stocks

# Scrape the tickers
tickers = scrape_tickers_from_yahoo(url)

# Step 2: Fetch data for each ticker
end_date = datetime.today()
start_date = end_date - timedelta(days=365 * 3)  # Last 3 years

def fetch_data(ticker):
    return yf.download(ticker, start=start_date, end=end_date)

stock_data = {ticker: fetch_data(ticker) for ticker in tickers[:10]}  # Limit to first 10 tickers for demo

# Step 3: Screening logic
def calculate_metrics(data):
    data['Daily Return'] = data['Adj Close'].pct_change()
    data['200-Day Moving Average'] = data['Adj Close'].rolling(window=200).mean()
    return data

def screen_stocks(stock_data):
    screened_stocks = {}
    
    for ticker, data in stock_data.items():
        data = calculate_metrics(data)
        avg_return = data['Daily Return'].tail(60).mean()  # Last 60 days average return
        current_price = data['Adj Close'].iloc[-1]
        moving_avg_200 = data['200-Day Moving Average'].iloc[-1]
        
        if avg_return > 0 and current_price > moving_avg_200:
            screened_stocks[ticker] = {
                'Average Return (3 months)': avg_return,
                'Current Price': current_price,
                '200-Day Moving Average': moving_avg_200
            }
    
    return screened_stocks

# Apply screening
screened_stocks = screen_stocks(stock_data)

# Print the screened stocks
print("Screened Stocks:")
for ticker, metrics in screened_stocks.items():
    print(f"{ticker}: {metrics}")
