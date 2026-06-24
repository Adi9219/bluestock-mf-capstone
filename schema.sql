-- SQLite Star Schema DDL for Bluestock Mutual Fund Analytics Database

-- 1. Dimension Tables
CREATE TABLE dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    category TEXT,
    sub_category TEXT,
    plan TEXT,
    launch_date TEXT, -- YYYY-MM-DD
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    min_sip_amount REAL,
    min_lumpsum_amount REAL,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

CREATE TABLE dim_date (
    date TEXT PRIMARY KEY, -- YYYY-MM-DD
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL, -- 0-6 (Sunday-Saturday) or 1-7
    is_weekend INTEGER NOT NULL, -- 0 or 1
    month_name TEXT NOT NULL
);

-- 2. Fact Tables
CREATE TABLE fact_nav (
    amfi_code INTEGER NOT NULL,
    nav_date TEXT NOT NULL, -- renamed from date
    nav REAL NOT NULL,
    PRIMARY KEY (amfi_code, nav_date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (nav_date) REFERENCES dim_date(date)
);

CREATE TABLE fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    transaction_date TEXT NOT NULL, -- renamed from transaction_date
    amfi_code INTEGER NOT NULL,
    transaction_type TEXT NOT NULL,
    amount_inr REAL NOT NULL,
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (transaction_date) REFERENCES dim_date(date)
);

CREATE TABLE fact_performance (
    amfi_code INTEGER PRIMARY KEY,
    scheme_name TEXT,
    fund_house TEXT,
    category TEXT,
    plan TEXT,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore REAL,
    expense_ratio_pct REAL,
    morningstar_rating INTEGER,
    risk_grade TEXT,
    negative_sharpe_flag INTEGER DEFAULT 0, -- 0 or 1
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE fact_aum (
    date TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    aum_lakh_crore REAL,
    aum_crore REAL,
    num_schemes INTEGER,
    PRIMARY KEY (date, fund_house),
    FOREIGN KEY (date) REFERENCES dim_date(date)
);

-- 3. Auxiliary / Market Tables
CREATE TABLE portfolio_holdings (
    holding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER NOT NULL,
    stock_symbol TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    sector TEXT,
    weight_pct REAL,
    market_value_cr REAL,
    current_price_inr REAL,
    portfolio_date TEXT NOT NULL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (portfolio_date) REFERENCES dim_date(date)
);

CREATE TABLE monthly_sip_inflows (
    month_date TEXT PRIMARY KEY, -- YYYY-MM-01
    sip_inflow_crore REAL,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh REAL,
    sip_aum_lakh_crore REAL,
    yoy_growth_pct REAL,
    FOREIGN KEY (month_date) REFERENCES dim_date(date)
);

CREATE TABLE category_inflows (
    month_date TEXT NOT NULL, -- YYYY-MM-01
    category TEXT NOT NULL,
    net_inflow_crore REAL,
    PRIMARY KEY (month_date, category),
    FOREIGN KEY (month_date) REFERENCES dim_date(date)
);

CREATE TABLE industry_folio_count (
    month_date TEXT PRIMARY KEY, -- YYYY-MM-01
    total_folios_crore REAL,
    equity_folios_crore REAL,
    debt_folios_crore REAL,
    hybrid_folios_crore REAL,
    others_folios_crore REAL,
    FOREIGN KEY (month_date) REFERENCES dim_date(date)
);

CREATE TABLE benchmark_indices (
    date TEXT NOT NULL,
    index_name TEXT NOT NULL,
    close_value REAL NOT NULL,
    PRIMARY KEY (date, index_name),
    FOREIGN KEY (date) REFERENCES dim_date(date)
);

-- 4. Indexes for Query Optimization
CREATE INDEX idx_fact_nav_amfi_date ON fact_nav (amfi_code, nav_date);
CREATE INDEX idx_fact_transactions_amfi_date ON fact_transactions (amfi_code, transaction_date);

-- Additional lookup indexes for performance tuning
CREATE INDEX idx_fact_nav_date ON fact_nav (nav_date);
CREATE INDEX idx_fact_transactions_date ON fact_transactions (transaction_date);
CREATE INDEX idx_portfolio_holdings_amfi ON portfolio_holdings (amfi_code);
CREATE INDEX idx_benchmark_indices_date ON benchmark_indices (date);
