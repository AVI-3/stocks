import requests
import json
import time

def fetch_historical_data(symbol, from_date, to_date):
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
        'limit': 10000  # High limit to fetch as much as possible at once
    }
    
    print(f"Requesting URL: {url} with params: {params}")
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"Response status code: {response.status_code}")
        
        # If response was successful
        if response.status_code == 200:
            return response.json()
        else:
            print("Response text snippet:", response.text[:500])
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    # Test fetch for AAPL from 2025-01-01 to 2026-06-30
    data = fetch_historical_data("AAPL", "2025-01-01", "2026-06-30")
    if data:
        print("Success! Keys in response:", data.keys())
        if 'data' in data and data['data']:
            print("Keys under 'data':", data['data'].keys())
            trades_table = data['data'].get('tradesTable')
            if trades_table:
                print("Trades table keys:", trades_table.keys())
                rows = trades_table.get('rows', [])
                print(f"Number of rows fetched: {len(rows)}")
                if rows:
                    print("Sample row:", rows[0])
            else:
                print("No 'tradesTable' found in response 'data'. Full data object keys:", data['data'].keys())
        else:
            print("Response structure: data key is missing or null.")
    else:
        print("Failed to fetch data.")
