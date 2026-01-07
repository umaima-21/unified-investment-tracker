# Unified Investment Tracker 📊

A comprehensive personal investment tracking system that consolidates mutual funds, stocks, crypto, and fixed deposits into a single dashboard with automated daily updates.

---

## ✨ Features

- 🎯 **Unified Dashboard**: Track all investments in one place
- 📈 **Real-time Tracking**: Daily automated updates for all assets
- 💰 **Portfolio Analytics**: Returns, XIRR, asset allocation, performance metrics
- 🔄 **Multiple Asset Types**:
  - Mutual Funds (via CAS parsing + MFAPI)
  - Stocks (ICICIdirect API)
  - Cryptocurrency (CoinDCX API)
  - Fixed Deposits (manual entry)
- 📊 **Historical Performance**: Track portfolio growth over time
- 🔒 **Privacy First**: Local deployment, your data stays with you

---

## 🛠️ Tech Stack

### Backend
- **Framework**: Python + FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Scheduler**: APScheduler
- **API Clients**: Requests, HTTPX

### Frontend (Coming Soon)
- **Framework**: React + TypeScript
- **UI**: TailwindCSS + shadcn/ui
- **Charts**: Recharts
- **State**: React Query

---

## 📁 Project Structure

```
unified-investment-tracker/
├── backend/
│   ├── config/              # Configuration management
│   ├── database/            # Database connection & base
│   ├── models/              # SQLAlchemy models
│   ├── connectors/          # API integrations (TBD)
│   ├── services/            # Business logic (TBD)
│   ├── api/                 # FastAPI routes (TBD)
│   ├── schedulers/          # Daily update jobs (TBD)
│   ├── utils/               # Helper functions (TBD)
│   ├── requirements.txt     # Python dependencies
│   └── main.py              # Application entry point
├── frontend/                # React app (TBD)
├── .env                     # Environment variables (create this!)
├── .env.example             # Example environment file
├── .gitignore              
└── README.md                # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- PostgreSQL 15 or higher
- pip (Python package manager)

### Step 1: Clone & Setup

```powershell
# Navigate to project directory
cd "c:\Users\40044254\OneDrive - LTTS\Projects\Self-study\unified-investment-tracker"

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

### Step 2: Database Setup

```powershell
# Make sure PostgreSQL is running
Get-Service postgresql*

# Create database
psql -U postgres
CREATE DATABASE investment_tracker;
\q
```

### Step 3: Configuration

```powershell
# Copy example environment file
Copy-Item .env.example .env

# Edit .env and add your credentials
# See API_CREDENTIALS_GUIDE.md for detailed instructions
notepad .env
```

**Minimum required in .env:**
```env
DB_PASSWORD=your_postgres_password
SECRET_KEY=generate_random_string_here
```

### Step 4: Run Application

```powershell
# Navigate to backend directory
cd backend

# Run the application
python main.py
```

The API will be available at: http://localhost:8000

- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

---

## 📋 API Credentials Setup

You'll need to obtain API credentials for different services. Follow the detailed guide:

👉 **[API_CREDENTIALS_GUIDE.md](./API_CREDENTIALS_GUIDE.md)**

### Quick Checklist:
- [ ] PostgreSQL installed and running
- [ ] Database created
- [ ] `.env` file created with DB credentials
- [ ] Secret key generated
- [ ] CoinDCX API keys (if trading crypto)
- [ ] ICICIdirect API keys (if trading stocks)
- [ ] Download latest CAS file for mutual funds

---

## 🗄️ Database Schema

### Core Tables:
1. **assets_master**: All investment assets metadata
2. **holdings**: Current holdings and positions
3. **transactions**: All buy/sell/dividend transactions
4. **prices**: Daily prices (NAV/close price)
5. **portfolio_snapshot**: Daily portfolio summary

See `backend/models/` for detailed schema definitions.

---

## 🔌 API Endpoints (Coming Soon)

### Assets
- `GET /api/assets` - List all assets
- `POST /api/assets` - Add new asset
- `GET /api/assets/{id}` - Get asset details

### Holdings
- `GET /api/holdings` - Get current holdings
- `GET /api/holdings/summary` - Get holdings summary by type

### Transactions
- `GET /api/transactions` - List transactions
- `POST /api/transactions` - Add transaction

### Portfolio
- `GET /api/portfolio/summary` - Portfolio overview
- `GET /api/portfolio/performance` - Returns & performance
- `GET /api/portfolio/allocation` - Asset allocation
- `GET /api/portfolio/history` - Historical snapshots

### Updates
- `POST /api/updates/mutual-funds` - Update MF NAVs
- `POST /api/updates/stocks` - Update stock prices
- `POST /api/updates/crypto` - Update crypto prices
- `POST /api/updates/portfolio` - Recalculate portfolio

---

## 📈 Development Roadmap

### Phase 1: Core Infrastructure ✅ (In Progress)
- [x] Project structure
- [x] Database models
- [x] Configuration management
- [x] FastAPI setup
- [ ] Database migrations

### Phase 2: Data Connectors
- [ ] Mutual Funds connector (MFAPI)
- [ ] CAS parser
- [ ] CoinDCX connector
- [ ] ICICIdirect connector
- [ ] Fixed Deposits module

### Phase 3: Portfolio Engine
- [ ] Holdings calculator
- [ ] Returns calculator (absolute, %, XIRR)
- [ ] Asset allocation calculator
- [ ] Portfolio snapshot generator

### Phase 4: Automation
- [ ] Daily scheduler setup
- [ ] Automated price updates
- [ ] Portfolio recalculation jobs

### Phase 5: Frontend Dashboard
- [ ] React project setup
- [ ] Dashboard UI
- [ ] Holdings views
- [ ] Charts & analytics
- [ ] Transaction management

### Phase 6: Enhancements
- [ ] Goal tracking
- [ ] Tax reports
- [ ] Benchmarking (Nifty/Sensex)
- [ ] Alerts & notifications

---

## 🧪 Testing

```powershell
# Run tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_models.py
```

---

## 🐛 Debugging

### Check if database is accessible
```python
from backend.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print(result.fetchone())
```

### Check if tables are created
```python
from backend.database import engine, Base
Base.metadata.create_all(bind=engine)
```

---

## 📝 Code Style

We follow Python best practices:
- **Formatting**: Black
- **Linting**: Flake8
- **Type Checking**: MyPy

```powershell
# Format code
black backend/

# Lint code
flake8 backend/

# Type check
mypy backend/
```

---

## 🔒 Security Notes

- **Never commit `.env` file** (already in .gitignore)
- Store API keys securely
- Use strong passwords for database
- Regularly backup your database
- Keep dependencies updated

---

## 📚 Documentation

- [Design Document](./Unified_Investment_Tracker_Design.md)
- [Execution Plan](./EXECUTION_PLAN.md)
- [API Credentials Guide](./API_CREDENTIALS_GUIDE.md)

---

## 🤝 Contributing

This is a personal project, but suggestions are welcome!

---

## 📄 License

Private project for personal use.

---

## 🆘 Support

If you encounter issues:
1. Check logs in console
2. Verify `.env` configuration
3. Ensure PostgreSQL is running
4. Check API credentials
5. Review error messages in FastAPI docs

---

## 🎯 Next Steps

After setup:
1. ✅ Set up all API credentials
2. ✅ Run the backend server
3. ✅ Test database connection
4. ✅ Start building connectors
5. ✅ Upload first CAS file
6. ✅ Add manual FD entries
7. ✅ View dashboard (once frontend is ready)

---

**Happy Tracking! 📊🚀**
