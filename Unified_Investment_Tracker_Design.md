
# Unified Investment Tracker Design Document

## 1. Requirements
- Track all personal investments: mutual funds (via CAS), stocks (ICICIdirect), fixed deposits, crypto (CoinDCX).
- Use direct APIs wherever possible.
- Automatic daily updates.
- Unified dashboard for positions, valuations, returns, and performance.
- Local personal use only—no client aggregation or advisory use.
- Scalable to add future asset types.

## 2. CAS (Consolidated Account Statement) Age & Limitations
- CAS is generated monthly by CAMS and NSDL.
- A newly downloaded CAS PDF reflects your latest transactions up to the generation date.
- If you request an on-demand CAS, it usually includes transactions until the previous business day.
- CAS is NOT real-time and is ideal for historical + monthly reconciliation, not live updates.

## 3. APIs for Each Investment Type
### Mutual Funds
- CAMS/NSDL do not provide open public APIs for portfolio extraction.
- You can parse CAS using CAS Parser API for transaction and holdings data.
- For NAVs, use MFAPI or AMFI endpoints.

### Stocks (ICICIdirect)
- ICICIdirect has a Partner API Program (official API access).
- You must apply and obtain API keys (may be paid).
- Provides order book, positions, and historical data.

### Crypto (CoinDCX)
- CoinDCX provides public and private REST APIs.
- Private APIs allow balances, positions, trades, deposits, withdrawals.

### Fixed Deposits
- Banks rarely provide personal portfolio APIs.
- You will maintain FD data manually or via a small CSV maintained in your system.

## 4. Recommended Architecture
- A modular backend system with connectors for each asset type.
- Central database holding unified normalized investment data.
- Scheduler to trigger daily updates.
- Portfolio calculator layer to compute P&L, XIRR, asset allocation.
- Frontend dashboard for visualization.

## 5. Detailed System Design
### A. Data Source Connectors
- MF Connector (NAV): Pull daily NAVs via MFAPI.
- CAS Connector: Upload and parse CAS every month.
- CoinDCX Connector: Live balance + market prices via APIs.
- ICICIdirect Connector: Pull stock holdings via authenticated API.
- FD Connector: Reads FD data from local DB/CSV.

### B. Normalized Data Model
Tables:
- **assets_master** (asset_id, type, name, ISIN, symbol)
- **holdings** (asset_id, quantity, invested_amount, avg_price)
- **transactions** (timestamp, asset_id, type, amount, price, units)
- **prices** (asset_id, date, price)
- **portfolio_snapshot** (date, networth, asset_allocations)

### C. Processing Logic
- Daily price updater pulls MF, stock, and crypto prices.
- Holdings refresher updates quantities and valuations.
- Portfolio engine computes returns and trends.

## 6. Workflow
### 1. Initial Setup
- Parse latest CAS.
- Connect CoinDCX APIs.
- Set up ICICIdirect API credentials.
- Add FD data manually.

### 2. Daily Run
- Fetch NAVs.
- Fetch CoinDCX positions.
- Fetch ICICIdirect positions.
- Recalculate holdings.
- Update net worth.

## 7. Future Enhancements
- Add more exchanges (NSE, BSE) price feeds.
- Add goal-based tracking.
- Add tax harvesting reports.
- Automate CAS fetching when APIs become available.

## 8. Conclusion
This system provides a robust, API-driven unified investment tracker for personal use, combining mutual funds, stocks, crypto, and fixed deposits. The design ensures modularity, scalability, and privacy while leveraging the best available data sources.
