import os
import argparse
import requests
import pandas as pd
from datetime import datetime
import time

import random

# Popular Nasdaq stock tickers featured on the historical quotes lookup page:
POPULAR_TICKERS = ["AAPL", "MSFT", "AMZN", "TSLA", "META", "AMD", "NFLX", "SBUX", "CSCO", "QCOM"]

def parse_args():
    parser = argparse.ArgumentParser(description="Download historical stock data from NASDAQ.")
    parser.add_argument(
        "--symbol", 
        type=str, 
        default="AAPL", 
        help="Stock ticker symbol(s), comma-separated (e.g., 'AAPL,MSFT'), or 'POPULAR' for all popular tickers (default: AAPL)"
    )
    parser.add_argument("--from-date", type=str, default="2010-01-01", help="Start date in YYYY-MM-DD format (default: 2010-01-01)")
    parser.add_argument("--to-date", type=str, default="2026-06-30", help="End date in YYYY-MM-DD format (default: 2026-06-30)")
    parser.add_argument("--output", type=str, default=None, help="Path to save the output CSV file (only used for single symbol downloads)")
    return parser.parse_args()

def fetch_nasdaq_historical(symbol, from_date, to_date, limit=10000):
    """
    Fetches historical stock quote data from the internal NASDAQ API.
    """
    url = f"https://api.nasdaq.com/api/quote/{symbol}/historical"
    
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://www.nasdaq.com',
        'Referer': 'https://www.nasdaq.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    params = {
        'assetclass': 'stocks',
        'fromdate': from_date,
        'todate': to_date,
        'limit': limit
    }
    
    print(f"Fetching data for {symbol} from {from_date} to {to_date}...")
    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        if response.status_code != 200:
            print(f"Failed to fetch data: HTTP {response.status_code}")
            return None
        
        data = response.json()
        if data.get('status', {}).get('rCode') != 200:
            print(f"API error response for {symbol}: {data.get('status', {}).get('bCodeMessage', 'Unknown error')}")
            return None
            
        return data
    except Exception as e:
        print(f"Exception occurred while fetching data for {symbol}: {e}")
        return None

def clean_and_parse_data(api_response):
    """
    Parses the JSON API response and returns a cleaned pandas DataFrame.
    """
    if not api_response or 'data' not in api_response or not api_response['data']:
        print("No valid data found in response.")
        return None
        
    data_payload = api_response['data']
    total_records = data_payload.get('totalRecords', 0)
    print(f"API reports total records available: {total_records}")
    
    trades_table = data_payload.get('tradesTable')
    if not trades_table or 'rows' not in trades_table:
        print("No tradesTable or rows found in data.")
        return None
        
    rows = trades_table['rows']
    if not rows:
        print("Empty rows in response.")
        return None
        
    print(f"Received {len(rows)} rows from API.")
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Nasdaq table row fields usually: date, close, volume, open, high, low
    # Clean the dollar signs and commas
    price_cols = ['close', 'open', 'high', 'low']
    for col in price_cols:
        if col in df.columns:
            # Strip '$' and whitespace, remove commas, convert to numeric
            df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    if 'volume' in df.columns:
        df['volume'] = df['volume'].astype(str).str.replace(',', '', regex=False).str.strip()
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        # Fill NaN volume with 0 or keep as is, let's keep as int/float
        
    if 'date' in df.columns:
        # Convert date from MM/DD/YYYY to YYYY-MM-DD
        df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y', errors='coerce')
        
    # Sort by date ascending (historical quotes usually come descending)
    df = df.sort_values(by='date').reset_index(drop=True)
    
    return df

def main():
    args = parse_args()
    
    from_date = args.from_date
    to_date = args.to_date
    
    symbol_input = args.symbol.strip()
    if symbol_input.upper() == "POPULAR":
        symbols = POPULAR_TICKERS
        print(f"Selected all popular tickers: {symbols}")
    else:
        symbols = [s.strip().upper() for s in symbol_input.split(",") if s.strip()]
        
    if not symbols:
        print("No valid stock symbols provided.")
        return

    # Process each symbol
    for idx, symbol in enumerate(symbols):
        if idx > 0:
            # Delay to avoid IP blocking / rate limiting
            sleep_time = random.uniform(2.0, 5.0)
            print(f"\nWaiting {sleep_time:.2f} seconds before fetching the next symbol...")
            time.sleep(sleep_time)
            
        print(f"\n--- Processing {symbol} ({idx + 1}/{len(symbols)}) ---")
        
        # Determine output file path
        if len(symbols) == 1 and args.output:
            output_file = args.output
        else:
            if args.output:
                print(f"Warning: Multiple symbols provided. Ignoring custom output path '{args.output}' and using standard downloads directory.")
            # Save to downloads directory
            os.makedirs("downloads", exist_ok=True)
            output_file = f"downloads/{symbol}_historical.csv"
            
        # Make sure parent directory of output file exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # Fetch
        raw_data = fetch_nasdaq_historical(symbol, from_date, to_date)
        if not raw_data:
            print(f"Could not retrieve stock data for {symbol}.")
            continue
            
        # Clean
        df = clean_and_parse_data(raw_data)
        if df is not None and not df.empty:
            # Save to CSV
            df.to_csv(output_file, index=False)
            print(f"Successfully saved {len(df)} records to {output_file}")
        else:
            print(f"Data processing resulted in empty or invalid dataset for {symbol}.")

if __name__ == "__main__":
    main()

