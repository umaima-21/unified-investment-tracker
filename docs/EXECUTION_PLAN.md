# Unified Investment Tracker - Execution Plan

## Overview

This document outlines the detailed execution plan for building the Unified Investment Tracker system based on the design document.

---

## Phase 1: Project Setup & Infrastructure

### 1.1 Technology Stack Selection

- **Backend**: Python (FastAPI/Flask) or Node.js (Express)
- **Database**: PostgreSQL or SQLite (for local use)
- **Frontend**: React + TailwindCSS + shadcn/ui
- **Scheduler**: APScheduler (Python) or node-cron (Node.js)
- **Authentication**: Local auth (no external users)

### 1.2 Project Structure

```
unified-investment-tracker/
├── backend/
│   ├── connectors/          # API connectors for each source
│   ├── models/              # Database models
│   ├── services/            # Business logic
│   ├── schedulers/          # Daily update jobs
│   ├── utils/               # Helper functions
│   └── main.py/app.js       # Entry point
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Dashboard pages
│   │   ├── services/        # API calls
│   │   └── utils/           # Utilities
├── database/
│   ├── migrations/          # DB migrations
│   └── seeds/               # Initial data
├── config/
│   └── config.yaml          # Configuration
└── docs/
```

### 1.3 Environment Setup

- [ ] Initialize Git repository
- [ ] Create `.gitignore` (exclude API keys, database files)
- [ ] Set up virtual environment/node_modules
- [ ] Create `.env.example` file for environment variables
- [ ] Install core dependencies

### 1.4 Configuration Management

- [ ] Create config file for API credentials
- [ ] Set up environment variables
- [ ] Create secure credential storage mechanism

**Duration**: 2-3 days

---

## Phase 2: Database Schema & Models

### 2.1 Database Tables

Implement the following normalized schema:

#### Table: `assets_master`

```sql
CREATE TABLE assets_master (
    asset_id UUID PRIMARY KEY,
    asset_type VARCHAR(20) NOT NULL, -- 'MF', 'STOCK', 'CRYPTO', 'FD'
    name VARCHAR(255) NOT NULL,
    symbol VARCHAR(50),
    isin VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Table: `holdings`

```sql
CREATE TABLE holdings (
    holding_id UUID PRIMARY KEY,
    asset_id UUID REFERENCES assets_master(asset_id),
    quantity DECIMAL(18, 6) NOT NULL,
    invested_amount DECIMAL(18, 2) NOT NULL,
    avg_price DECIMAL(18, 6),
    current_value DECIMAL(18, 2),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Table: `transactions`

```sql
CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY,
    asset_id UUID REFERENCES assets_master(asset_id),
    transaction_type VARCHAR(20) NOT NULL, -- 'BUY', 'SELL', 'DIVIDEND', etc.
    transaction_date TIMESTAMP NOT NULL,
    units DECIMAL(18, 6),
    price DECIMAL(18, 6),
    amount DECIMAL(18, 2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Table: `prices`

```sql
CREATE TABLE prices (
    price_id UUID PRIMARY KEY,
    asset_id UUID REFERENCES assets_master(asset_id),
    price_date DATE NOT NULL,
    price DECIMAL(18, 6) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(asset_id, price_date)
);
```

#### Table: `portfolio_snapshot`

```sql
CREATE TABLE portfolio_snapshot (
    snapshot_id UUID PRIMARY KEY,
    snapshot_date DATE NOT NULL UNIQUE,
    total_invested DECIMAL(18, 2),
    total_current_value DECIMAL(18, 2),
    total_returns DECIMAL(18, 2),
    returns_percentage DECIMAL(8, 2),
    asset_allocation JSONB, -- Store as JSON
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2.2 ORM Models

- [ ] Create ORM models for all tables
- [ ] Add validation and constraints
- [ ] Create database migration scripts
- [ ] Implement database connection pool

### 2.3 Database Utilities

- [ ] Create CRUD helper functions
- [ ] Add transaction management
- [ ] Create backup scripts

**Duration**: 3-4 days

---

## Phase 3: Data Source Connectors - Mutual Funds

### 3.1 CAS Parser Connector

- [ ] Research CAS Parser API or PDF parsing libraries
- [ ] Implement CAS file upload functionality
- [ ] Parse mutual fund holdings and transactions
- [ ] Map data to `assets_master` and `transactions` tables
- [ ] Handle duplicate detection

### 3.2 NAV Fetcher (MFAPI)

- [ ] Integrate with MFAPI (https://www.mfapi.in/)
- [ ] Create NAV fetcher service
- [ ] Store daily NAVs in `prices` table
- [ ] Handle API rate limits
- [ ] Add error handling and retry logic

### 3.3 Mutual Fund Service

- [ ] Calculate current holdings from transactions
- [ ] Update holdings table with latest NAVs
- [ ] Calculate XIRR for mutual funds
- [ ] Generate MF performance reports

**Duration**: 5-6 days

---

## Phase 4: Data Source Connectors - Stocks (ICICIdirect)

### 4.1 ICICIdirect API Integration

- [ ] Apply for ICICIdirect Partner API access
- [ ] Obtain API credentials (may require time)
- [ ] Study API documentation
- [ ] Implement authentication flow
- [ ] Test API connectivity

### 4.2 Stock Holdings Connector

- [ ] Fetch current holdings via API
- [ ] Map to `assets_master` and `holdings`
- [ ] Handle stock corporate actions (splits, bonuses)
- [ ] Sync transaction history

### 4.3 Stock Price Updater

- [ ] Fetch live/EOD stock prices
- [ ] Alternative: Use Yahoo Finance or NSE API for prices
- [ ] Store prices in `prices` table
- [ ] Handle market holidays

**Duration**: 6-7 days (plus API approval wait time)

---

## Phase 5: Data Source Connectors - Crypto (CoinDCX)

### 5.1 CoinDCX API Integration

- [ ] Create CoinDCX account and generate API keys
- [ ] Study CoinDCX API documentation
- [ ] Implement authentication (HMAC signing)
- [ ] Test API connectivity

### 5.2 Crypto Holdings Connector

- [ ] Fetch balances via private API
- [ ] Map crypto assets to `assets_master`
- [ ] Fetch transaction history
- [ ] Calculate holdings and invested amounts

### 5.3 Crypto Price Updater

- [ ] Fetch live crypto prices via public API
- [ ] Store prices in INR in `prices` table
- [ ] Handle API rate limits
- [ ] Add WebSocket support for real-time prices (optional)

**Duration**: 4-5 days

---

## Phase 6: Data Source Connectors - Fixed Deposits

### 6.1 Manual FD Entry System

- [ ] Create FD management API endpoints
- [ ] Allow manual entry of FD details (bank, amount, rate, maturity)
- [ ] Store in `assets_master` and `holdings`
- [ ] Calculate maturity values

### 6.2 FD Calculator

- [ ] Calculate interest accrued
- [ ] Handle quarterly/monthly interest compounding
- [ ] Generate maturity alerts
- [ ] Track active vs matured FDs

**Duration**: 2-3 days

---

## Phase 7: Portfolio Engine & Calculations

### 7.1 Holdings Calculator

- [ ] Implement holdings aggregation logic
- [ ] Calculate current values from latest prices
- [ ] Update `holdings` table daily
- [ ] Handle missing price data gracefully

### 7.2 Returns Calculator

- [ ] Implement absolute returns calculation
- [ ] Implement percentage returns
- [ ] Implement XIRR/IRR calculation
- [ ] Calculate day-wise, month-wise, year-wise returns

### 7.3 Portfolio Analytics

- [ ] Calculate asset allocation (MF, Stocks, Crypto, FD)
- [ ] Generate portfolio snapshot
- [ ] Calculate portfolio beta/volatility (optional)
- [ ] Track portfolio performance vs benchmarks (Nifty, Sensex)

### 7.4 Snapshot Service

- [ ] Create daily portfolio snapshot
- [ ] Store in `portfolio_snapshot` table
- [ ] Generate historical trend data

**Duration**: 5-6 days

---

## Phase 8: Daily Scheduler & Automation

### 8.1 Scheduler Setup

- [ ] Install and configure scheduler (APScheduler/node-cron)
- [ ] Create job definitions
- [ ] Set up logging for scheduled tasks
- [ ] Add error notifications

### 8.2 Daily Update Jobs

- [ ] **Job 1**: Fetch MF NAVs (run at 8 PM IST)
- [ ] **Job 2**: Fetch stock prices (run at 6 PM IST)
- [ ] **Job 3**: Fetch crypto prices (run at 9 PM IST)
- [ ] **Job 4**: Update holdings (run at 9:30 PM IST)
- [ ] **Job 5**: Generate portfolio snapshot (run at 10 PM IST)

### 8.3 Manual Triggers

- [ ] Create API endpoints to manually trigger updates
- [ ] Add force-refresh functionality
- [ ] Create monthly CAS upload trigger

**Duration**: 3-4 days

---

## Phase 9: Frontend Dashboard

### 9.1 Project Setup

- [ ] Initialize React project with Vite/Create React App
- [ ] Install TailwindCSS and shadcn/ui
- [ ] Set up routing (React Router)
- [ ] Create base layout and navigation

### 9.2 Dashboard Pages

#### Page 1: Overview Dashboard

- [ ] Net worth card
- [ ] Total returns (absolute & percentage)
- [ ] Asset allocation pie chart
- [ ] Recent transactions list

#### Page 2: Mutual Funds

- [ ] List all MF holdings
- [ ] Show current value, invested amount, returns
- [ ] Filter by fund type (equity, debt, hybrid)
- [ ] Transaction history

#### Page 3: Stocks

- [ ] List all stock holdings
- [ ] Show current value, P&L
- [ ] Live price updates
- [ ] Transaction history

#### Page 4: Crypto

- [ ] List all crypto holdings
- [ ] Show current value in INR
- [ ] Live price updates
- [ ] Transaction history

#### Page 5: Fixed Deposits

- [ ] List all FDs
- [ ] Show maturity dates and values
- [ ] Interest earned
- [ ] Add/edit FD functionality

#### Page 6: Analytics

- [ ] Portfolio performance charts (line chart)
- [ ] Returns comparison across asset types
- [ ] XIRR visualization
- [ ] Historical snapshots

### 9.3 UI Components

- [ ] Data tables with sorting and filtering
- [ ] Charts (Recharts or Chart.js)
- [ ] Cards for summary metrics
- [ ] Forms for manual data entry
- [ ] Upload component for CAS files

### 9.4 API Integration

- [ ] Create API service layer
- [ ] Implement data fetching hooks
- [ ] Add loading states
- [ ] Add error handling

**Duration**: 10-12 days

---

## Phase 10: Testing & Deployment

### 10.1 Testing

- [ ] Unit tests for connectors
- [ ] Unit tests for portfolio calculations
- [ ] Integration tests for API endpoints
- [ ] Frontend component tests
- [ ] End-to-end testing
- [ ] Performance testing (large datasets)

### 10.2 Documentation

- [ ] API documentation (Swagger/OpenAPI)
- [ ] User guide for initial setup
- [ ] README with installation instructions
- [ ] Configuration guide for API keys

### 10.3 Security & Privacy

- [ ] Secure API key storage
- [ ] Add input validation
- [ ] Sanitize data before storage
- [ ] Enable HTTPS (if deploying)
- [ ] Data encryption at rest (optional)

### 10.4 Deployment

- [ ] Containerize with Docker (optional)
- [ ] Set up local deployment scripts
- [ ] Configure backup automation
- [ ] Set up monitoring and logging

### 10.5 Initial Data Load

- [ ] Upload and parse latest CAS
- [ ] Configure CoinDCX API keys
- [ ] Configure ICICIdirect API keys
- [ ] Add FD data manually
- [ ] Run initial price updates
- [ ] Verify data accuracy

**Duration**: 5-6 days

---

## Critical Questions Before Starting

### 1. **Technology Preferences**

- Do you prefer Python or Node.js for the backend?
- Database: PostgreSQL (robust) or SQLite (simpler for local use)?

### 2. **API Access Status**

- Do you already have access to ICICIdirect Partner API?
- Do you have CoinDCX API credentials?
- Are you comfortable with API key management?

### 3. **Deployment Environment**

- Will this run on your local machine 24/7?
- Do you need cloud deployment (AWS, GCP, Azure)?
- Do you want mobile access?

### 4. **Data Sources**

- Can you provide a sample CAS file for testing?
- How frequently do you trade (for determining sync frequency)?
- Are there other asset types you want to add initially?

### 5. **Timeline & Effort**

- Total estimated duration: **45-55 days** (full-time equivalent)
- Part-time work: 3-4 months
- Are you comfortable with this timeline?

---

## Recommended Execution Order

1. **Start with Phase 1-2** (Setup & Database) - Foundation
2. **Phase 3** (Mutual Funds) - Easiest API integration
3. **Phase 5** (Crypto) - Second easiest
4. **Phase 6** (Fixed Deposits) - Manual entry, no external dependency
5. **Phase 4** (Stocks) - May have API approval delays
6. **Phase 7-8** (Portfolio Engine & Scheduler) - Core logic
7. **Phase 9** (Frontend) - Visualization
8. **Phase 10** (Testing & Deployment) - Finalization

---

## Next Steps

Please answer the critical questions above so I can:

1. Finalize the technology stack
2. Start with Phase 1 implementation
3. Create initial project scaffolding
4. Set up the development environment

Would you like me to proceed with any specific phase, or do you have questions about the plan?
