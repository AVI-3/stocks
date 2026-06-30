import os
import pandas as pd
import numpy as np

def calculate_volatility_metrics():
    downloads_dir = "downloads"
    
    ticker_names = {
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "AMZN": "Amazon",
        "TSLA": "Tesla",
        "META": "Meta",
        "AMD": "AMD",
        "NFLX": "Netflix",
        "SBUX": "Starbucks",
        "CSCO": "Cisco",
        "QCOM": "Qualcomm"
    }
    
    if not os.path.exists(downloads_dir):
        print(f"Error: {downloads_dir} directory not found.")
        return
        
    csv_files = [f for f in os.listdir(downloads_dir) if f.endswith("_historical.csv")]
    if not csv_files:
        print("Error: No historical CSV files found in downloads.")
        return
        
    results = []
    
    for file in csv_files:
        ticker = file.replace("_historical.csv", "")
        file_path = os.path.join(downloads_dir, file)
        
        try:
            df = pd.read_csv(file_path)
            # Ensure columns are sorted by date
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values(by='date').reset_index(drop=True)
            
            # 1. Daily percentage returns
            df['returns'] = df['close'].pct_change()
            
            # 2. Daily absolute percentage change
            df['abs_returns'] = df['returns'].abs()
            
            # 3. Intra-day range percentage: (High - Low) / Close
            df['intraday_range_pct'] = (df['high'] - df['low']) / df['close'] * 100
            
            # 4. Overnight Gap percentage: absolute change between Open and previous Close
            prev_close = df['close'].shift(1)
            df['gap_pct'] = (df['open'] - prev_close).abs() / prev_close * 100
            
            # Calculate metrics
            avg_abs_daily_change = df['abs_returns'].mean() * 100
            daily_volatility = df['returns'].std() * 100
            annualized_volatility = daily_volatility * np.sqrt(252)
            avg_intraday_swing = df['intraday_range_pct'].mean()
            avg_overnight_gap = df['gap_pct'].mean()
            
            # Overnight Gap Ratio: average gap relative to average intraday range
            # Higher ratio means more overnight news vulnerability; lower means intraday trend active
            gap_ratio = avg_overnight_gap / avg_intraday_swing if avg_intraday_swing > 0 else 0
            
            # Max single-day drop and gain
            max_daily_gain = df['returns'].max() * 100
            max_daily_loss = df['returns'].min() * 100
            
            results.append({
                "Ticker": ticker,
                "Company": ticker_names.get(ticker, ticker),
                "Avg Daily Move (%)": avg_abs_daily_change,
                "Intraday Swing (%)": avg_intraday_swing,
                "Avg Overnight Gap (%)": avg_overnight_gap,
                "Overnight Gap Ratio": gap_ratio,
                "Annualized Volatility (%)": annualized_volatility,
                "Max Daily Gain (%)": max_daily_gain,
                "Max Daily Loss (%)": max_daily_loss
            })
            
        except Exception as e:
            print(f"Error processing {file}: {e}")
            
    # Create DataFrame and sort by Annualized Volatility descending (most rapid changes first)
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(by="Annualized Volatility (%)", ascending=False).reset_index(drop=True)
    
    # Save the summary to a CSV in downloads
    results_df.to_csv("downloads/volatility_summary.csv", index=False)
    
    # Print formatted output
    print("\n" + "="*80)
    print("STOCK PRICE RAPIDITY / VOLATILITY SUMMARY (Sorted by Annualized Volatility)")
    print("="*80)
    print(results_df.to_string(index=False, formatters={
        "Avg Daily Move (%)": "{:.2f}%".format,
        "Intraday Swing (%)": "{:.2f}%".format,
        "Avg Overnight Gap (%)": "{:.3f}%".format,
        "Overnight Gap Ratio": "{:.3f}".format,
        "Annualized Volatility (%)": "{:.2f}%".format,
        "Max Daily Gain (%)": "{:+.2f}%".format,
        "Max Daily Loss (%)": "{:+.2f}%".format
    }))
    print("="*80)
    
    return results_df

if __name__ == "__main__":
    calculate_volatility_metrics()

