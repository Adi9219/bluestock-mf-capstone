import os
import pandas as pd
import numpy as np

def clean_data():
    raw_dir = r"d:\bluestock_mf_capstone"
    processed_dir = os.path.join(raw_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    # We will accumulate summary statistics for the cleaning report
    report_lines = []
    report_lines.append("# Data Cleaning Summary Report")
    report_lines.append(f"Generated on: 2026-06-24\n")
    report_lines.append("## Executive Summary")
    report_lines.append("This report details the results of cleaning the 10 mutual fund datasets. All financial metrics that were empty or missing have been preserved as NULL values (rather than coerced to 0.0) as per requirements. Invalid records violating business rules or referential integrity have been filtered or flagged.\n")
    
    # -------------------------------------------------------------
    # 1. Clean Fund Master (01_fund_master.csv)
    # -------------------------------------------------------------
    master_path = os.path.join(raw_dir, "01_fund_master.csv")
    df_master = pd.read_csv(master_path)
    orig_master_len = len(df_master)
    
    # Clean strings
    for col in df_master.select_dtypes(include=['object']).columns:
        df_master[col] = df_master[col].astype(str).str.strip()
        
    df_master['amfi_code'] = pd.to_numeric(df_master['amfi_code'], errors='coerce').astype(pd.Int64Dtype())
    df_master = df_master.dropna(subset=['amfi_code'])
    df_master = df_master.drop_duplicates(subset=['amfi_code'])
    
    # Validate formats
    df_master['launch_date'] = pd.to_datetime(df_master['launch_date'], errors='coerce').dt.strftime('%Y-%m-%d')
    df_master['expense_ratio_pct'] = pd.to_numeric(df_master['expense_ratio_pct'], errors='coerce')
    df_master['exit_load_pct'] = pd.to_numeric(df_master['exit_load_pct'], errors='coerce')
    df_master['min_sip_amount'] = pd.to_numeric(df_master['min_sip_amount'], errors='coerce')
    df_master['min_lumpsum_amount'] = pd.to_numeric(df_master['min_lumpsum_amount'], errors='coerce')
    
    valid_amfi_codes = set(df_master['amfi_code'])
    
    master_cleaned_len = len(df_master)
    report_lines.append("### 1. Fund Master (`clean_fund_master.csv`)")
    report_lines.append(f"- **Original Rows**: {orig_master_len}")
    report_lines.append(f"- **Cleaned Rows**: {master_cleaned_len}")
    report_lines.append(f"- **Duplicates/Invalids Removed**: {orig_master_len - master_cleaned_len}")
    report_lines.append(f"- **Unique AMFI Codes**: {len(valid_amfi_codes)}")
    report_lines.append("- **Notes**: Standardized string column formatting. Ensured primary key constraint on `amfi_code`.\n")
    
    # Save clean_fund_master.csv
    df_master.to_csv(os.path.join(processed_dir, "clean_fund_master.csv"), index=False)
    
    # Helper to validate and report amfi_code referential integrity
    def check_referential_integrity(df, df_name):
        df['amfi_code'] = pd.to_numeric(df['amfi_code'], errors='coerce').astype(pd.Int64Dtype())
        invalid_mask = ~df['amfi_code'].isin(valid_amfi_codes)
        invalid_count = invalid_mask.sum()
        invalid_codes = df.loc[invalid_mask, 'amfi_code'].dropna().unique()
        return invalid_count, invalid_codes, invalid_mask

    # -------------------------------------------------------------
    # 2. Clean NAV History (02_nav_history.csv)
    # -------------------------------------------------------------
    nav_path = os.path.join(raw_dir, "02_nav_history.csv")
    df_nav = pd.read_csv(nav_path)
    orig_nav_len = len(df_nav)
    
    # Referential integrity check
    nav_invalid_count, nav_invalid_codes, nav_invalid_mask = check_referential_integrity(df_nav, "NAV History")
    df_nav = df_nav[~nav_invalid_mask]
    
    # Parse date
    df_nav['date'] = pd.to_datetime(df_nav['date'], errors='coerce')
    df_nav = df_nav.dropna(subset=['date'])
    
    # Sort
    df_nav = df_nav.sort_values(by=['amfi_code', 'date'])
    
    # Remove duplicates
    df_nav = df_nav.drop_duplicates(subset=['amfi_code', 'date'])
    
    # Validate nav > 0
    nav_nonpositive_count = (df_nav['nav'] <= 0).sum()
    df_nav = df_nav[df_nav['nav'] > 0]
    
    # Forward fill missing NAV values grouped by amfi_code
    # To do this correctly, we create a complete date index per scheme, or reindex, or simply use group ffill.
    # Groupby ffill preserves existing rows but fills NaNs. Since we have a daily list, let's verify if there are any NaNs.
    nav_nans_before = df_nav['nav'].isna().sum()
    df_nav['nav'] = df_nav.groupby('amfi_code')['nav'].ffill()
    nav_nans_after = df_nav['nav'].isna().sum()
    
    df_nav['date'] = df_nav['date'].dt.strftime('%Y-%m-%d')
    nav_cleaned_len = len(df_nav)
    
    report_lines.append("### 2. NAV History (`clean_nav_history.csv`)")
    report_lines.append(f"- **Original Rows**: {orig_nav_len}")
    report_lines.append(f"- **Cleaned Rows**: {nav_cleaned_len}")
    report_lines.append(f"- **Referential Integrity Violations Removed**: {nav_invalid_count} (Invalid AMFI codes: {list(nav_invalid_codes)})")
    report_lines.append(f"- **Non-positive NAV Rows Removed**: {nav_nonpositive_count}")
    report_lines.append(f"- **Duplicates Removed**: {orig_nav_len - nav_cleaned_len - nav_invalid_count - nav_nonpositive_count}")
    report_lines.append(f"- **Missing NAVs Forward-Filled**: {nav_nans_before - nav_nans_after} (NaNs remaining: {nav_nans_after})")
    report_lines.append("- **Notes**: Sorted by `amfi_code` and `date`. Forward filled values are isolated per fund.\n")
    
    df_nav.to_csv(os.path.join(processed_dir, "clean_nav_history.csv"), index=False)

    # -------------------------------------------------------------
    # 3. Clean AUM by Fund House (03_aum_by_fund_house.csv)
    # -------------------------------------------------------------
    aum_path = os.path.join(raw_dir, "03_aum_by_fund_house.csv")
    df_aum = pd.read_csv(aum_path)
    orig_aum_len = len(df_aum)
    
    df_aum['fund_house'] = df_aum['fund_house'].astype(str).str.strip()
    df_aum['date'] = pd.to_datetime(df_aum['date'], errors='coerce').dt.strftime('%Y-%m-%d')
    df_aum = df_aum.dropna(subset=['date', 'fund_house'])
    df_aum = df_aum.drop_duplicates(subset=['date', 'fund_house'])
    
    df_aum['aum_lakh_crore'] = pd.to_numeric(df_aum['aum_lakh_crore'], errors='coerce')
    df_aum['aum_crore'] = pd.to_numeric(df_aum['aum_crore'], errors='coerce')
    df_aum['num_schemes'] = pd.to_numeric(df_aum['num_schemes'], errors='coerce').astype(pd.Int64Dtype())
    
    aum_cleaned_len = len(df_aum)
    report_lines.append("### 3. AUM by Fund House (`clean_aum_by_fund_house.csv`)")
    report_lines.append(f"- **Original Rows**: {orig_aum_len}")
    report_lines.append(f"- **Cleaned Rows**: {aum_cleaned_len}")
    report_lines.append(f"- **Duplicates Removed**: {orig_aum_len - aum_cleaned_len}")
    report_lines.append("- **Notes**: Validated dates and fund house names. Preserved numeric columns.\n")
    
    df_aum.to_csv(os.path.join(processed_dir, "clean_aum_by_fund_house.csv"), index=False)

    # -------------------------------------------------------------
    # 4. Clean Monthly SIP Inflows (04_monthly_sip_inflows.csv)
    # -------------------------------------------------------------
    sip_path = os.path.join(raw_dir, "04_monthly_sip_inflows.csv")
    df_sip = pd.read_csv(sip_path)
    orig_sip_len = len(df_sip)
    
    df_sip['month'] = pd.to_datetime(df_sip['month'], errors='coerce').dt.strftime('%Y-%m')
    df_sip = df_sip.dropna(subset=['month'])
    df_sip = df_sip.drop_duplicates(subset=['month'])
    
    df_sip['sip_inflow_crore'] = pd.to_numeric(df_sip['sip_inflow_crore'], errors='coerce')
    df_sip['active_sip_accounts_crore'] = pd.to_numeric(df_sip['active_sip_accounts_crore'], errors='coerce')
    df_sip['new_sip_accounts_lakh'] = pd.to_numeric(df_sip['new_sip_accounts_lakh'], errors='coerce')
    df_sip['sip_aum_lakh_crore'] = pd.to_numeric(df_sip['sip_aum_lakh_crore'], errors='coerce')
    df_sip['yoy_growth_pct'] = pd.to_numeric(df_sip['yoy_growth_pct'], errors='coerce') # Missing values kept as NaN/NULL
    
    sip_null_yoy = df_sip['yoy_growth_pct'].isna().sum()
    sip_cleaned_len = len(df_sip)
    
    report_lines.append("### 4. Monthly SIP Inflows (`clean_monthly_sip_inflows.csv`)")
    report_lines.append(f"- **Original Rows**: {orig_sip_len}")
    report_lines.append(f"- **Cleaned Rows**: {sip_cleaned_len}")
    report_lines.append(f"- **Preserved NULL YoY Growth Metrics**: {sip_null_yoy}")
    report_lines.append(f"- **Duplicates Removed**: {orig_sip_len - sip_cleaned_len}")
    report_lines.append("- **Notes**: Standardized month format to `YYYY-MM`. YoY growth rate left blank for the first year due to missing historical benchmark.\n")
    
    df_sip.to_csv(os.path.join(processed_dir, "clean_monthly_sip_inflows.csv"), index=False)

    # -------------------------------------------------------------
    # 5. Clean Category Inflows (05_category_inflows.csv)
    # -------------------------------------------------------------
    cat_path = os.path.join(raw_dir, "05_category_inflows.csv")
    df_cat = pd.read_csv(cat_path)
    orig_cat_len = len(df_cat)
    
    df_cat['month'] = pd.to_datetime(df_cat['month'], errors='coerce').dt.strftime('%Y-%m')
    df_cat['category'] = df_cat['category'].astype(str).str.strip()
    df_cat = df_cat.dropna(subset=['month', 'category'])
    df_cat = df_cat.drop_duplicates(subset=['month', 'category'])
    
    df_cat['net_inflow_crore'] = pd.to_numeric(df_cat['net_inflow_crore'], errors='coerce')
    
    cat_cleaned_len = len(df_cat)
    report_lines.append("### 5. Category Inflows (`clean_category_inflows.csv`)")
    report_lines.append(f"- **Original Rows**: {orig_cat_len}")
    report_lines.append(f"- **Cleaned Rows**: {cat_cleaned_len}")
    report_lines.append(f"- **Duplicates Removed**: {orig_cat_len - cat_cleaned_len}")
    report_lines.append("- **Notes**: Standardized month formatting and category descriptions.\n")
    
    df_cat.to_csv(os.path.join(processed_dir, "clean_category_inflows.csv"), index=False)

    # -------------------------------------------------------------
    # 6. Clean Industry Folio Count (06_industry_folio_count.csv)
    # -------------------------------------------------------------
    folio_path = os.path.join(raw_dir, "06_industry_folio_count.csv")
    df_folio = pd.read_csv(folio_path)
    orig_folio_len = len(df_folio)
    
    df_folio['month'] = pd.to_datetime(df_folio['month'], errors='coerce').dt.strftime('%Y-%m')
    df_folio = df_folio.dropna(subset=['month'])
    df_folio = df_folio.drop_duplicates(subset=['month'])
    
    for col in ['total_folios_crore', 'equity_folios_crore', 'debt_folios_crore', 'hybrid_folios_crore', 'others_folios_crore']:
        df_folio[col] = pd.to_numeric(df_folio[col], errors='coerce')
        
    folio_cleaned_len = len(df_folio)
    report_lines.append("### 6. Industry Folio Count (`clean_industry_folio_count.csv`)")
    report_lines.append(f"- **Original Rows**: {orig_folio_len}")
    report_lines.append(f"- **Cleaned Rows**: {folio_cleaned_len}")
    report_lines.append(f"- **Duplicates Removed**: {orig_folio_len - folio_cleaned_len}")
    report_lines.append("- **Notes**: Converted all folio count metrics to floats and verified month constraints.\n")
    
    df_folio.to_csv(os.path.join(processed_dir, "clean_industry_folio_count.csv"), index=False)

    # -------------------------------------------------------------
    # 7. Clean Scheme Performance (07_scheme_performance.csv)
    # -------------------------------------------------------------
    perf_path = os.path.join(raw_dir, "07_scheme_performance.csv")
    df_perf = pd.read_csv(perf_path)
    orig_perf_len = len(df_perf)
    
    # Referential integrity check
    perf_invalid_count, perf_invalid_codes, perf_invalid_mask = check_referential_integrity(df_perf, "Scheme Performance")
    df_perf = df_perf[~perf_invalid_mask]
    
    df_perf = df_perf.drop_duplicates(subset=['amfi_code'])
    
    # Clean and validate numeric return columns
    numeric_cols = [
        'return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct',
        'alpha', 'beta', 'sharpe_ratio', 'sortino_ratio', 'std_dev_ann_pct',
        'max_drawdown_pct', 'aum_crore', 'expense_ratio_pct'
    ]
    
    # Ensure they are numeric, but do not replace missing values with 0.0! Keep them as NaN (NULL)
    missing_metrics_count = 0
    for col in numeric_cols:
        orig_missing = df_perf[col].isna().sum()
        df_perf[col] = pd.to_numeric(df_perf[col], errors='coerce')
        new_missing = df_perf[col].isna().sum()
        missing_metrics_count += (new_missing - orig_missing)
        
    df_perf['morningstar_rating'] = pd.to_numeric(df_perf['morningstar_rating'], errors='coerce').astype(pd.Int64Dtype())
    
    # Flag negative sharpe_ratio
    df_perf['negative_sharpe_flag'] = (df_perf['sharpe_ratio'] < 0).astype(int)
    # If sharpe_ratio is NaN, set flag to NaN or 0? The requirement says "flag negative sharpe_ratio". Let's set it to 1 if negative, 0 if >= 0 or NaN.
    df_perf.loc[df_perf['sharpe_ratio'].isna(), 'negative_sharpe_flag'] = 0
    
    # Validate expense_ratio_pct range [0.0, 5.0]
    invalid_exp_count = ((df_perf['expense_ratio_pct'] < 0.0) | (df_perf['expense_ratio_pct'] > 5.0)).sum()
    
    perf_cleaned_len = len(df_perf)
    report_lines.append("### 7. Scheme Performance (`clean_scheme_performance.csv`)")
    report_lines.append(f"- **Original Rows**: {orig_perf_len}")
    report_lines.append(f"- **Cleaned Rows**: {perf_cleaned_len}")
    report_lines.append(f"- **Referential Integrity Violations Removed**: {perf_invalid_count} (Invalid AMFI codes: {list(perf_invalid_codes)})")
    report_lines.append(f"- **Negative Sharpe Ratios Flagged**: {df_perf['negative_sharpe_flag'].sum()} schemes flagged")
    report_lines.append(f"- **Expense Ratio Range Violations (>5% or <0%)**: {invalid_exp_count} schemes found")
    report_lines.append(f"- **Preserved NULL Metrics**: Detailed missing financial metrics preserved as NULLs (blank in CSV).")
    report_lines.append("- **Notes**: Retained original metrics, added `negative_sharpe_flag` column.\n")
    
    df_perf.to_csv(os.path.join(processed_dir, "clean_scheme_performance.csv"), index=False)

    # -------------------------------------------------------------
    # 8. Clean Investor Transactions (08_investor_transactions.csv)
    # -------------------------------------------------------------
    trans_path = os.path.join(raw_dir, "08_investor_transactions.csv")
    df_trans = pd.read_csv(trans_path)
    orig_trans_len = len(df_trans)
    
    # Referential integrity check
    trans_invalid_count, trans_invalid_codes, trans_invalid_mask = check_referential_integrity(df_trans, "Investor Transactions")
    df_trans = df_trans[~trans_invalid_mask]
    
    # Standardize transaction_type (coerced to upper case, e.g. SIP, LUMPSUM, REDEMPTION)
    df_trans['transaction_type'] = df_trans['transaction_type'].astype(str).str.strip().str.upper()
    type_mapping = {'SIP': 'SIP', 'LUMPSUM': 'LUMPSUM', 'REDEMPTION': 'REDEMPTION'}
    df_trans['transaction_type'] = df_trans['transaction_type'].map(type_mapping).fillna('SIP')
    
    # Validate amount_inr > 0
    non_positive_amounts = (df_trans['amount_inr'] <= 0).sum()
    df_trans = df_trans[df_trans['amount_inr'] > 0]
    
    # Validate kyc_status values ('Verified', 'Pending')
    df_trans['kyc_status'] = df_trans['kyc_status'].astype(str).str.strip()
    invalid_kyc_mask = ~df_trans['kyc_status'].isin(['Verified', 'Pending'])
    invalid_kyc_count = invalid_kyc_mask.sum()
    # Coerce invalid to 'Pending'
    df_trans.loc[invalid_kyc_mask, 'kyc_status'] = 'Pending'
    
    # Convert transaction_date to datetime
    df_trans['transaction_date'] = pd.to_datetime(df_trans['transaction_date'], errors='coerce').dt.strftime('%Y-%m-%d')
    df_trans = df_trans.dropna(subset=['transaction_date'])
    
    # Other numeric conversions
    df_trans['annual_income_lakh'] = pd.to_numeric(df_trans['annual_income_lakh'], errors='coerce')
    
    trans_cleaned_len = len(df_trans)
    report_lines.append("### 8. Investor Transactions (`clean_investor_transactions.csv`)")
    report_lines.append(f"- **Original Rows**: {orig_trans_len}")
    report_lines.append(f"- **Cleaned Rows**: {trans_cleaned_len}")
    report_lines.append(f"- **Referential Integrity Violations Removed**: {trans_invalid_count} (Invalid AMFI codes: {list(trans_invalid_codes)})")
    report_lines.append(f"- **Negative or Zero Amount Rows Removed**: {non_positive_amounts}")
    report_lines.append(f"- **Coerced Invalid KYC Status to 'Pending'**: {invalid_kyc_count}")
    report_lines.append("- **Notes**: Standardized transaction types to uppercase: `SIP`, `LUMPSUM`, `REDEMPTION`. Validated all transaction amounts and dates.\n")
    
    df_trans.to_csv(os.path.join(processed_dir, "clean_investor_transactions.csv"), index=False)

    # -------------------------------------------------------------
    # 9. Clean Portfolio Holdings (09_portfolio_holdings.csv)
    # -------------------------------------------------------------
    holdings_path = os.path.join(raw_dir, "09_portfolio_holdings.csv")
    df_holdings = pd.read_csv(holdings_path)
    orig_holdings_len = len(df_holdings)
    
    # Referential integrity check
    holdings_invalid_count, holdings_invalid_codes, holdings_invalid_mask = check_referential_integrity(df_holdings, "Portfolio Holdings")
    df_holdings = df_holdings[~holdings_invalid_mask]
    
    df_holdings['stock_symbol'] = df_holdings['stock_symbol'].astype(str).str.strip()
    df_holdings['stock_name'] = df_holdings['stock_name'].astype(str).str.strip()
    df_holdings['sector'] = df_holdings['sector'].astype(str).str.strip()
    
    df_holdings['weight_pct'] = pd.to_numeric(df_holdings['weight_pct'], errors='coerce')
    df_holdings['market_value_cr'] = pd.to_numeric(df_holdings['market_value_cr'], errors='coerce')
    df_holdings['current_price_inr'] = pd.to_numeric(df_holdings['current_price_inr'], errors='coerce')
    df_holdings['portfolio_date'] = pd.to_datetime(df_holdings['portfolio_date'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    df_holdings = df_holdings.dropna(subset=['stock_symbol', 'portfolio_date'])
    
    holdings_cleaned_len = len(df_holdings)
    report_lines.append("### 9. Portfolio Holdings (`clean_portfolio_holdings.csv`)")
    report_lines.append(f"- **Original Rows**: {orig_holdings_len}")
    report_lines.append(f"- **Cleaned Rows**: {holdings_cleaned_len}")
    report_lines.append(f"- **Referential Integrity Violations Removed**: {holdings_invalid_count} (Invalid AMFI codes: {list(holdings_invalid_codes)})")
    report_lines.append("- **Notes**: Structured weights and prices. Filtered out records with missing symbols or dates.\n")
    
    df_holdings.to_csv(os.path.join(processed_dir, "clean_portfolio_holdings.csv"), index=False)

    # -------------------------------------------------------------
    # 10. Clean Benchmark Indices (10_benchmark_indices.csv)
    # -------------------------------------------------------------
    bench_path = os.path.join(raw_dir, "10_benchmark_indices.csv")
    df_bench = pd.read_csv(bench_path)
    orig_bench_len = len(df_bench)
    
    df_bench['index_name'] = df_bench['index_name'].astype(str).str.strip()
    df_bench['date'] = pd.to_datetime(df_bench['date'], errors='coerce').dt.strftime('%Y-%m-%d')
    df_bench = df_bench.dropna(subset=['date', 'index_name'])
    df_bench = df_bench.drop_duplicates(subset=['date', 'index_name'])
    df_bench['close_value'] = pd.to_numeric(df_bench['close_value'], errors='coerce')
    
    bench_cleaned_len = len(df_bench)
    report_lines.append("### 10. Benchmark Indices (`clean_benchmark_indices.csv`)")
    report_lines.append(f"- **Original Rows**: {orig_bench_len}")
    report_lines.append(f"- **Cleaned Rows**: {bench_cleaned_len}")
    report_lines.append(f"- **Duplicates Removed**: {orig_bench_len - bench_cleaned_len}")
    report_lines.append("- **Notes**: Cleaned date values and index names. Ensured unique indexes per date.\n")
    
    df_bench.to_csv(os.path.join(processed_dir, "clean_benchmark_indices.csv"), index=False)

    # Write Cleaning Summary Report
    report_path = os.path.join(processed_dir, "cleaning_report.md")
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("\n".join(report_lines))
        
    print(f"Data cleaning successfully completed! Cleaned datasets saved to {processed_dir}")
    print(f"Cleaning report saved to {report_path}")

if __name__ == "__main__":
    clean_data()
