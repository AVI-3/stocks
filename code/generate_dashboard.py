import os
import json
import pandas as pd

def generate_dashboard():
    downloads_dir = "downloads"
    output_html = "dashboard.html"
    
    # 1. Read all CSV files in the downloads directory
    data_dict = {}
    
    # Mapping of tickers to company names for a nicer UI
    ticker_names = {
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corporation",
        "AMZN": "Amazon.com, Inc.",
        "TSLA": "Tesla, Inc.",
        "META": "Meta Platforms, Inc.",
        "AMD": "Advanced Micro Devices, Inc.",
        "NFLX": "Netflix, Inc.",
        "SBUX": "Starbucks Corporation",
        "CSCO": "Cisco Systems, Inc.",
        "QCOM": "Qualcomm Incorporated"
    }
    
    if not os.path.exists(downloads_dir):
        print(f"Error: {downloads_dir} directory not found.")
        return
        
    csv_files = [f for f in os.listdir(downloads_dir) if f.endswith("_historical.csv")]
    if not csv_files:
        print("Error: No historical CSV files found in downloads.")
        return
        
    print(f"Scanning downloads/ directory. Found files: {csv_files}")
    
    for file in csv_files:
        ticker = file.replace("_historical.csv", "")
        file_path = os.path.join(downloads_dir, file)
        
        try:
            df = pd.read_csv(file_path)
            # Ensure columns are present and clean
            required_cols = ['date', 'close', 'open', 'high', 'low', 'volume']
            if not all(col in df.columns for col in required_cols):
                print(f"Skipping {file}: missing required columns.")
                continue
                
            # Convert date to string format for JSON serialization
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            
            # Sort by date ascending to make sure charts render properly
            df = df.sort_values(by='date').reset_index(drop=True)
            
            # Format rows as a list of dicts
            records = df.to_dict(orient='records')
            
            # Extract basic metadata
            latest_row = df.iloc[-1]
            prev_row = df.iloc[-2] if len(df) > 1 else latest_row
            
            latest_price = float(latest_row['close'])
            prev_price = float(prev_row['close'])
            change_pct = ((latest_price - prev_price) / prev_price) * 100
            
            data_dict[ticker] = {
                "name": ticker_names.get(ticker, f"{ticker} Corporation"),
                "latestPrice": latest_price,
                "changePct": change_pct,
                "high52": float(df['high'].tail(252).max()) if len(df) >= 252 else float(df['high'].max()),
                "low52": float(df['low'].tail(252).min()) if len(df) >= 252 else float(df['low'].min()),
                "avgVolume": float(df['volume'].tail(30).mean()) if len(df) >= 30 else float(df['volume'].mean()),
                "history": records
            }
            print(f"Loaded {len(records)} historical records for {ticker}.")
            
        except Exception as e:
            print(f"Error loading {file}: {e}")
            
    if not data_dict:
        print("No stock data was successfully parsed.")
        return
        
    # Write the data_dict to JSON to inject into the HTML page
    json_data = json.dumps(data_dict)
    
    # 2. HTML and CSS Template for the Premium Charting Dashboard
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NASDAQ Advanced Market Dashboard</title>
    
    <!-- Premium Fonts and Chart.js -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <style>
        :root {{
            --bg-color: #0b0f19;
            --surface-color: rgba(22, 28, 45, 0.6);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-glow: #00f2fe;
            --accent-solid: #38bdf8;
            --bullish: #10b981;
            --bearish: #ef4444;
            --card-hover: rgba(30, 41, 59, 0.7);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Outfit', sans-serif;
            -webkit-font-smoothing: antialiased;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }}

        /* Scrollbar styling */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: var(--bg-color);
        }}
        ::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}

        header {{
            padding: 1.5rem 2rem;
            background: rgba(11, 15, 25, 0.8);
            border-bottom: 1px solid var(--border-color);
            backdrop-filter: blur(12px);
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .logo-section {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .logo-badge {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.2rem;
            color: #0b0f19;
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.3);
        }}

        .logo-title {{
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -0.5px;
            background: linear-gradient(to right, #ffffff, #cbd5e1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .market-status {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            background: rgba(16, 185, 129, 0.1);
            color: var(--bullish);
            padding: 0.35rem 0.75rem;
            border-radius: 20px;
            border: 1px solid rgba(16, 185, 129, 0.2);
            font-weight: 500;
        }}

        .main-container {{
            display: grid;
            grid-template-columns: 280px 1fr;
            flex-grow: 1;
            height: calc(100vh - 73px);
        }}

        /* Sidebar Section */
        .sidebar {{
            border-right: 1px solid var(--border-color);
            overflow-y: auto;
            background: rgba(15, 23, 42, 0.3);
            display: flex;
            flex-direction: column;
        }}

        .sidebar-header {{
            padding: 1rem 1.25rem;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-color);
        }}

        .ticker-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
        }}

        .ticker-item {{
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--border-color);
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 3px solid transparent;
        }}

        .ticker-item:hover {{
            background: var(--card-hover);
            padding-left: 1.5rem;
        }}

        .ticker-item.active {{
            background: rgba(56, 189, 248, 0.08);
            border-left: 3px solid var(--accent-solid);
        }}

        .ticker-info {{
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }}

        .ticker-symbol {{
            font-weight: 700;
            font-size: 1.05rem;
            color: var(--text-primary);
        }}

        .ticker-name {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            max-width: 140px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .ticker-price-container {{
            text-align: right;
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }}

        .ticker-price {{
            font-weight: 600;
            font-size: 0.95rem;
        }}

        .ticker-change {{
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
            display: inline-block;
        }}

        .change-up {{
            background: rgba(16, 185, 129, 0.15);
            color: var(--bullish);
        }}

        .change-down {{
            background: rgba(239, 68, 68, 0.15);
            color: var(--bearish);
        }}

        /* Content Area */
        .content-area {{
            overflow-y: auto;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}

        /* Summary Stats Cards */
        .stats-header-bar {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .current-asset-title {{
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }}

        .current-asset-title h1 {{
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.5px;
        }}

        .current-asset-title p {{
            color: var(--text-secondary);
            font-size: 0.95rem;
        }}

        .timeframe-selector {{
            display: flex;
            background: rgba(30, 41, 59, 0.5);
            padding: 0.25rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}

        .timeframe-btn {{
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 0.4rem 0.9rem;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .timeframe-btn:hover {{
            color: var(--text-primary);
        }}

        .timeframe-btn.active {{
            background: var(--accent-solid);
            color: #0b0f19;
            box-shadow: 0 2px 8px rgba(56, 189, 248, 0.3);
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }}

        .stat-card {{
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
            backdrop-filter: blur(12px);
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}

        .stat-label {{
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
        }}

        .stat-value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
        }}

        .stat-subtext {{
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}

        /* Main Chart Card */
        .chart-card {{
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            position: relative;
            flex-grow: 1;
            min-height: 480px;
        }}

        .chart-header-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .chart-title-tag {{
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .chart-title-tag::before {{
            content: '';
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: var(--accent-solid);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--accent-glow);
        }}

        .chart-container-inner {{
            position: relative;
            flex-grow: 1;
            width: 100%;
            height: 100%;
        }}

        /* Grid of Small Previews */
        .preview-grid-header {{
            font-size: 1.1rem;
            font-weight: 700;
            margin-top: 1rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
            color: var(--text-primary);
        }}

        .previews-container {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}

        .sparkline-card {{
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1rem;
            cursor: pointer;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}

        .sparkline-card:hover {{
            transform: translateY(-4px);
            background: var(--card-hover);
            border-color: rgba(56, 189, 248, 0.3);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
        }}

        .sparkline-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .sparkline-symbol {{
            font-weight: 700;
            font-size: 1rem;
        }}

        .sparkline-change {{
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .sparkline-body {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}

        .sparkline-price {{
            font-size: 1.2rem;
            font-weight: 700;
        }}

        .sparkline-chart-wrapper {{
            width: 120px;
            height: 50px;
            position: relative;
        }}

        @media (max-width: 900px) {{
            .main-container {{
                grid-template-columns: 1fr;
            }}
            .sidebar {{
                display: none; /* Hide sidebar list on mobile since grid has it */
            }}
        }}
    </style>
</head>
<body>

    <header>
        <div class="logo-section">
            <div class="logo-badge">N</div>
            <div class="logo-title">NASDAQ Advanced Charting</div>
        </div>
        <div class="market-status">
            <span style="display:inline-block; width: 6px; height: 6px; background-color: var(--bullish); border-radius: 50%;"></span>
            10-Year Historical Quotes Active
        </div>
    </header>

    <div class="main-container">
        
        <!-- Sidebar Navigation -->
        <aside class="sidebar">
            <div class="sidebar-header">Watchlist</div>
            <ul class="ticker-list" id="sidebarList">
                <!-- Ticker items will be loaded dynamically -->
            </ul>
        </aside>

        <!-- Main Charting View -->
        <main class="content-area">
            
            <div class="stats-header-bar">
                <div class="current-asset-title">
                    <h1 id="mainTitle">--</h1>
                    <p id="mainSubtitle">--</p>
                </div>
                <div class="timeframe-selector">
                    <button class="timeframe-btn" onclick="changeTimeframe('1Y')">1Y</button>
                    <button class="timeframe-btn" onclick="changeTimeframe('5Y')">5Y</button>
                    <button class="timeframe-btn active" onclick="changeTimeframe('MAX')">10Y</button>
                </div>
            </div>

            <!-- Stats Grid -->
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-label">Last Price</span>
                    <span class="stat-value" id="statPrice">$--</span>
                    <span class="stat-subtext" id="statChange">--</span>
                </div>
                <div class="stat-card">
                    <span class="stat-label">52 Week High</span>
                    <span class="stat-value" id="statHigh">$--</span>
                    <span class="stat-subtext">Yearly Peak</span>
                </div>
                <div class="stat-card">
                    <span class="stat-label">52 Week Low</span>
                    <span class="stat-value" id="statLow">$--</span>
                    <span class="stat-subtext">Yearly Floor</span>
                </div>
                <div class="stat-card">
                    <span class="stat-label">30-Day Avg Volume</span>
                    <span class="stat-value" id="statVolume">--</span>
                    <span class="stat-subtext">Daily volume average</span>
                </div>
            </div>

            <!-- Advanced Area Chart -->
            <div class="chart-card">
                <div class="chart-header-row">
                    <div class="chart-title-tag" id="chartLabel">Price & Volume History</div>
                    <span style="font-size: 0.8rem; color: var(--text-secondary);" id="chartRangeLabel">MAX RANGE</span>
                </div>
                <div class="chart-container-inner">
                    <canvas id="mainChart"></canvas>
                </div>
            </div>

            <!-- Previews / Grid View of all companies (individual plots) -->
            <div class="preview-grid-header">All Companies Sparklines</div>
            <div class="previews-container" id="sparklinesContainer">
                <!-- Sparkline cards will be dynamically generated -->
            </div>

        </main>
    </div>

    <script>
        // Inject data from python
        const stockData = {json_data};
        
        let currentTicker = Object.keys(stockData)[0] || 'AAPL';
        let currentTimeframe = 'MAX'; // '1Y', '5Y', 'MAX'
        let mainChartInstance = null;
        let sparklineInstances = {{}};

        // Initialize App
        window.addEventListener('load', () => {{
            buildSidebar();
            buildSparklines();
            loadTicker(currentTicker);
        }});

        function buildSidebar() {{
            const listContainer = document.getElementById('sidebarList');
            listContainer.innerHTML = '';

            Object.keys(stockData).forEach(ticker => {{
                const data = stockData[ticker];
                const isPositive = data.changePct >= 0;
                
                const item = document.createElement('li');
                item.className = `ticker-item ${{ticker === currentTicker ? 'active' : ''}}`;
                item.id = `sidebar-${{ticker}}`;
                item.onclick = () => loadTicker(ticker);

                item.innerHTML = `
                    <div class="ticker-info">
                        <span class="ticker-symbol">${{ticker}}</span>
                        <span class="ticker-name">${{data.name}}</span>
                    </div>
                    <div class="ticker-price-container">
                        <span class="ticker-price">$${{data.latestPrice.toFixed(2)}}</span>
                        <span class="ticker-change ${{isPositive ? 'change-up' : 'change-down'}}">
                            ${{isPositive ? '+' : ''}}${{data.changePct.toFixed(2)}}%
                        </span>
                    </div>
                `;
                listContainer.appendChild(item);
            }});
        }}

        function buildSparklines() {{
            const container = document.getElementById('sparklinesContainer');
            container.innerHTML = '';

            Object.keys(stockData).forEach(ticker => {{
                const data = stockData[ticker];
                const isPositive = data.changePct >= 0;
                
                const card = document.createElement('div');
                card.className = 'sparkline-card';
                card.onclick = () => loadTicker(ticker);

                card.innerHTML = `
                    <div class="sparkline-header">
                        <span class="sparkline-symbol">${{ticker}}</span>
                        <span class="sparkline-change ${{isPositive ? 'change-up' : 'change-down'}}" style="padding: 0.1rem 0.3rem; border-radius: 4px;">
                            ${{isPositive ? '+' : ''}}${{data.changePct.toFixed(2)}}%
                        </span>
                    </div>
                    <div class="sparkline-body">
                        <span class="sparkline-price">$${{data.latestPrice.toFixed(2)}}</span>
                        <div class="sparkline-chart-wrapper">
                            <canvas id="spark-${{ticker}}"></canvas>
                        </div>
                    </div>
                `;
                container.appendChild(card);

                // Create miniature sparkline chart
                createSparkline(ticker, data.history);
            }});
        }}

        function createSparkline(ticker, history) {{
            const canvas = document.getElementById(`spark-${{ticker}}`);
            if (!canvas) return;

            // Take last 60 points for the sparkline to represent recent trend
            const recentHistory = history.slice(-65);
            const prices = recentHistory.map(row => row.close);
            const labels = recentHistory.map(row => row.date);
            
            const isPositive = stockData[ticker].changePct >= 0;
            const strokeColor = isPositive ? '#10b981' : '#ef4444';
            
            // Get gradient fill
            const ctx = canvas.getContext('2d');
            const gradient = ctx.createLinearGradient(0, 0, 0, 50);
            gradient.addColorStop(0, isPositive ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)');
            gradient.addColorStop(1, 'rgba(11, 15, 25, 0)');

            if (sparklineInstances[ticker]) {{
                sparklineInstances[ticker].destroy();
            }}

            sparklineInstances[ticker] = new Chart(canvas, {{
                type: 'line',
                data: {{
                    labels: labels,
                    datasets: [{{
                        data: prices,
                        borderColor: strokeColor,
                        borderWidth: 1.5,
                        fill: true,
                        backgroundColor: gradient,
                        pointRadius: 0,
                        tension: 0.15
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{ enabled: false }}
                    }},
                    scales: {{
                        x: {{ display: false }},
                        y: {{ display: false }}
                    }}
                }}
            }});
        }}

        function loadTicker(ticker) {{
            // Update active state in sidebar
            const prevActive = document.querySelector('.ticker-item.active');
            if (prevActive) prevActive.classList.remove('active');
            
            const nextActive = document.getElementById(`sidebar-${{ticker}}`);
            if (nextActive) nextActive.classList.add('active');

            currentTicker = ticker;
            const data = stockData[ticker];

            // Update UI elements
            document.getElementById('mainTitle').innerText = data.name;
            document.getElementById('mainSubtitle').innerText = `${{ticker}} • NASDAQ Stock Price History`;
            document.getElementById('statPrice').innerText = `$${{data.latestPrice.toFixed(2)}}`;
            
            const isPositive = data.changePct >= 0;
            const changeText = `${{isPositive ? '+' : ''}}${{data.changePct.toFixed(2)}}% today`;
            const changeElement = document.getElementById('statChange');
            changeElement.innerText = changeText;
            changeElement.className = `stat-subtext ${{isPositive ? 'change-up' : 'change-down'}}`
            
            document.getElementById('statHigh').innerText = `$${{data.high52.toFixed(2)}}`;
            document.getElementById('statLow').innerText = `$${{data.low52.toFixed(2)}}`;
            document.getElementById('statVolume').innerText = formatVolume(data.avgVolume);
            
            document.getElementById('chartLabel').innerText = `${{ticker}} Detailed Price & Volume`;

            renderMainChart();
        }}

        function formatVolume(val) {{
            if (val >= 1e6) return `${{(val / 1e6).toFixed(2)}}M`;
            if (val >= 1e3) return `${{(val / 1e3).toFixed(2)}}K`;
            return val.toFixed(0);
        }}

        function changeTimeframe(timeframe) {{
            currentTimeframe = timeframe;
            
            // Toggle active button style
            document.querySelectorAll('.timeframe-btn').forEach(btn => {{
                btn.classList.remove('active');
                if (btn.innerText === (timeframe === 'MAX' ? '10Y' : timeframe)) {{
                    btn.classList.add('active');
                }}
            }});
            
            document.getElementById('chartRangeLabel').innerText = timeframe === 'MAX' ? 'MAX RANGE (10 Years)' : `${{timeframe}} RANGE`;
            
            renderMainChart();
        }}

        function getFilteredHistory() {{
            const data = stockData[currentTicker].history;
            if (currentTimeframe === '1Y') {{
                return data.slice(-252); // Approx 252 trading days in a year
            }} else if (currentTimeframe === '5Y') {{
                return data.slice(-1260); // 5 years * 252 trading days
            }}
            return data; // Max historical data
        }}

        function renderMainChart() {{
            const filteredData = getFilteredHistory();
            const dates = filteredData.map(row => row.date);
            const prices = filteredData.map(row => row.close);
            const volumes = filteredData.map(row => row.volume);

            const canvas = document.getElementById('mainChart');
            const ctx = canvas.getContext('2d');

            // Price gradient (Neon Blue to Deep Blue/Transparent)
            const priceGradient = ctx.createLinearGradient(0, 0, 0, canvas.height || 400);
            priceGradient.addColorStop(0, 'rgba(56, 189, 248, 0.4)');
            priceGradient.addColorStop(1, 'rgba(11, 15, 25, 0)');

            // Volume color list (Green for up days, Red for down days)
            const volumeColors = [];
            for (let i = 0; i < filteredData.length; i++) {{
                const row = filteredData[i];
                const prevClose = i > 0 ? filteredData[i-1].close : row.open;
                if (row.close >= prevClose) {{
                    volumeColors.push('rgba(16, 185, 129, 0.3)');
                }} else {{
                    volumeColors.push('rgba(239, 68, 68, 0.3)');
                }}
            }}

            // Destroy previous instance
            if (mainChartInstance) {{
                mainChartInstance.destroy();
            }}

            const maxVolume = Math.max(...volumes);

            mainChartInstance = new Chart(canvas, {{
                type: 'line',
                data: {{
                    labels: dates,
                    datasets: [
                        {{
                            label: 'Stock Price',
                            data: prices,
                            borderColor: '#38bdf8',
                            borderWidth: 2,
                            fill: true,
                            backgroundColor: priceGradient,
                            pointRadius: 0,
                            pointHoverRadius: 5,
                            pointHoverBackgroundColor: '#00f2fe',
                            pointHoverBorderColor: '#ffffff',
                            tension: 0.1,
                            yAxisID: 'yPrice'
                        }},
                        {{
                            label: 'Volume',
                            type: 'bar',
                            data: volumes,
                            backgroundColor: volumeColors,
                            borderWidth: 0,
                            barPercentage: 0.85,
                            categoryPercentage: 0.85,
                            yAxisID: 'yVolume'
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    plugins: {{
                        legend: {{
                            display: false
                        }},
                        tooltip: {{
                            backgroundColor: 'rgba(15, 23, 42, 0.95)',
                            titleColor: '#f8fafc',
                            bodyColor: '#e2e8f0',
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: true,
                            callbacks: {{
                                label: function(context) {{
                                    let label = context.dataset.label || '';
                                    if (label) {{
                                        label += ': ';
                                    }}
                                    if (context.datasetIndex === 0) {{
                                        label += '$' + context.raw.toFixed(2);
                                    }} else {{
                                        label += context.raw.toLocaleString();
                                    }}
                                    return label;
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            grid: {{
                                display: false
                            }},
                            ticks: {{
                                color: '#94a3b8',
                                font: {{
                                    size: 11
                                }},
                                maxTicksLimit: 12
                            }}
                        }},
                        yPrice: {{
                            type: 'linear',
                            position: 'right',
                            grid: {{
                                color: 'rgba(255, 255, 255, 0.05)'
                            }},
                            ticks: {{
                                color: '#94a3b8',
                                font: {{
                                    size: 11
                                }},
                                callback: function(value) {{
                                    return '$' + value.toFixed(2);
                                }}
                            }}
                        }},
                        yVolume: {{
                            type: 'linear',
                            position: 'left',
                            display: false,
                            grid: {{
                                drawOnChartArea: false
                            }},
                            max: maxVolume * 4 // Compresses the volume bars to the bottom 25% of the chart
                        }}
                    }}
                }}
            }});
        }}
    </script>
</body>
</html>
"""
    
    # Write the formatted HTML content to the output file
    try:
        with open(output_html, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Successfully generated {output_html} with {len(data_dict)} stock datasets!")
        print(f"To view the dashboard, open: {os.path.abspath(output_html)}")
    except Exception as e:
        print(f"Failed to write dashboard HTML file: {e}")

if __name__ == "__main__":
    generate_dashboard()
