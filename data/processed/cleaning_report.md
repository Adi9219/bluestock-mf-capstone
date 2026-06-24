# Data Cleaning Summary Report
Generated on: 2026-06-24

## Executive Summary
This report details the results of cleaning the 10 mutual fund datasets. All financial metrics that were empty or missing have been preserved as NULL values (rather than coerced to 0.0) as per requirements. Invalid records violating business rules or referential integrity have been filtered or flagged.

### 1. Fund Master (`clean_fund_master.csv`)
- **Original Rows**: 40
- **Cleaned Rows**: 40
- **Duplicates/Invalids Removed**: 0
- **Unique AMFI Codes**: 40
- **Notes**: Standardized string column formatting. Ensured primary key constraint on `amfi_code`.

### 2. NAV History (`clean_nav_history.csv`)
- **Original Rows**: 46000
- **Cleaned Rows**: 46000
- **Referential Integrity Violations Removed**: 0 (Invalid AMFI codes: [])
- **Non-positive NAV Rows Removed**: 0
- **Duplicates Removed**: 0
- **Missing NAVs Forward-Filled**: 0 (NaNs remaining: 0)
- **Notes**: Sorted by `amfi_code` and `date`. Forward filled values are isolated per fund.

### 3. AUM by Fund House (`clean_aum_by_fund_house.csv`)
- **Original Rows**: 90
- **Cleaned Rows**: 90
- **Duplicates Removed**: 0
- **Notes**: Validated dates and fund house names. Preserved numeric columns.

### 4. Monthly SIP Inflows (`clean_monthly_sip_inflows.csv`)
- **Original Rows**: 48
- **Cleaned Rows**: 48
- **Preserved NULL YoY Growth Metrics**: 12
- **Duplicates Removed**: 0
- **Notes**: Standardized month format to `YYYY-MM`. YoY growth rate left blank for the first year due to missing historical benchmark.

### 5. Category Inflows (`clean_category_inflows.csv`)
- **Original Rows**: 144
- **Cleaned Rows**: 144
- **Duplicates Removed**: 0
- **Notes**: Standardized month formatting and category descriptions.

### 6. Industry Folio Count (`clean_industry_folio_count.csv`)
- **Original Rows**: 21
- **Cleaned Rows**: 21
- **Duplicates Removed**: 0
- **Notes**: Converted all folio count metrics to floats and verified month constraints.

### 7. Scheme Performance (`clean_scheme_performance.csv`)
- **Original Rows**: 40
- **Cleaned Rows**: 40
- **Referential Integrity Violations Removed**: 0 (Invalid AMFI codes: [])
- **Negative Sharpe Ratios Flagged**: 0 schemes flagged
- **Expense Ratio Range Violations (>5% or <0%)**: 0 schemes found
- **Preserved NULL Metrics**: Detailed missing financial metrics preserved as NULLs (blank in CSV).
- **Notes**: Retained original metrics, added `negative_sharpe_flag` column.

### 8. Investor Transactions (`clean_investor_transactions.csv`)
- **Original Rows**: 32778
- **Cleaned Rows**: 32778
- **Referential Integrity Violations Removed**: 0 (Invalid AMFI codes: [])
- **Negative or Zero Amount Rows Removed**: 0
- **Coerced Invalid KYC Status to 'Pending'**: 0
- **Notes**: Standardized transaction types to uppercase: `SIP`, `LUMPSUM`, `REDEMPTION`. Validated all transaction amounts and dates.

### 9. Portfolio Holdings (`clean_portfolio_holdings.csv`)
- **Original Rows**: 322
- **Cleaned Rows**: 322
- **Referential Integrity Violations Removed**: 0 (Invalid AMFI codes: [])
- **Notes**: Structured weights and prices. Filtered out records with missing symbols or dates.

### 10. Benchmark Indices (`clean_benchmark_indices.csv`)
- **Original Rows**: 8050
- **Cleaned Rows**: 8050
- **Duplicates Removed**: 0
- **Notes**: Cleaned date values and index names. Ensured unique indexes per date.
