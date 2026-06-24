import os
import sqlite3
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

def load_data():
    db_name = "bluestock_mf.db"
    base_dir = r"d:\bluestock_mf_capstone"
    processed_dir = os.path.join(base_dir, "data", "processed")
    db_path = os.path.join(base_dir, db_name)
    schema_path = os.path.join(base_dir, "schema.sql")
    
    # Check if cleaned datasets exist
    if not os.path.exists(processed_dir):
        raise FileNotFoundError(f"Processed data directory not found at: {processed_dir}. Run data_cleaning.py first.")
    
    print("--- Initializing SQLite Database ---")
    # Delete database if exists to ensure clean run
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("Removed existing database file to ensure a clean run.")
        except Exception as e:
            print(f"Could not remove existing database: {e}")
            
    # Connect and execute DDL script
    print(f"Creating database schema from {schema_path}...")
    try:
        conn = sqlite3.connect(db_path)
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_ddl = f.read()
        conn.executescript(schema_ddl)
        conn.commit()
        conn.close()
        print("Schema successfully created.")
    except Exception as e:
        print(f"Error during schema initialization: {e}")
        return
    
    # Initialize SQLAlchemy engine
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Dictionary to map CSV names to database tables and their custom loader/renaming logic
    # Format: { 'csv_name': ('table_name', transform_func) }
    datasets = {}
    
    # 1. Fund Master
    datasets["clean_fund_master.csv"] = ("dim_fund", lambda df: df)
    
    # 2. NAV History
    def transform_nav(df):
        df = df.rename(columns={'date': 'nav_date'})
        return df
    datasets["clean_nav_history.csv"] = ("fact_nav", transform_nav)
    
    # 3. Scheme Performance
    datasets["clean_scheme_performance.csv"] = ("fact_performance", lambda df: df)
    
    # 4. Investor Transactions
    datasets["clean_investor_transactions.csv"] = ("fact_transactions", lambda df: df)
    
    # 5. AUM by Fund House
    datasets["clean_aum_by_fund_house.csv"] = ("fact_aum", lambda df: df)
    
    # 6. Portfolio Holdings
    datasets["clean_portfolio_holdings.csv"] = ("portfolio_holdings", lambda df: df)
    
    # 7. Monthly SIP Inflows
    def transform_sip(df):
        # Convert month format YYYY-MM to YYYY-MM-01
        df['month_date'] = df['month'] + "-01"
        df = df.drop(columns=['month'])
        return df
    datasets["clean_monthly_sip_inflows.csv"] = ("monthly_sip_inflows", transform_sip)
    
    # 8. Category Inflows
    def transform_cat(df):
        df['month_date'] = df['month'] + "-01"
        df = df.drop(columns=['month'])
        return df
    datasets["clean_category_inflows.csv"] = ("category_inflows", transform_cat)
    
    # 9. Industry Folio Count
    def transform_folio(df):
        df['month_date'] = df['month'] + "-01"
        df = df.drop(columns=['month'])
        return df
    datasets["clean_industry_folio_count.csv"] = ("industry_folio_count", transform_folio)
    
    # 10. Benchmark Indices
    datasets["clean_benchmark_indices.csv"] = ("benchmark_indices", lambda df: df)
    
    # We will collect dates across all datasets to construct dim_date
    collected_dates = set()
    
    loaded_counts = {}
    csv_counts = {}
    
    # Load all tables
    print("\n--- Loading Cleaned Datasets ---")
    for csv_file, (table_name, transform_fn) in datasets.items():
        csv_path = os.path.join(processed_dir, csv_file)
        if not os.path.exists(csv_path):
            print(f"Warning: Cleaned file {csv_file} not found. Skipping table {table_name}.")
            continue
            
        try:
            # Read CSV, preserving empty fields as NaN
            df = pd.read_csv(csv_path, keep_default_na=True)
            csv_counts[table_name] = len(df)
            
            # Apply transformations
            df = transform_fn(df)
            
            # Extract dates for dim_date
            for date_col in ['nav_date', 'transaction_date', 'date', 'portfolio_date', 'month_date']:
                if date_col in df.columns:
                    collected_dates.update(df[date_col].dropna().unique())
            
            # Write to SQLite
            df.to_sql(table_name, engine, if_exists='append', index=False)
            loaded_counts[table_name] = len(df)
            print(f"Loaded {len(df)} rows into {table_name} (from {csv_file}).")
            
        except Exception as e:
            print(f"Error loading {csv_file} into {table_name}: {e}")
            
    # Generate and load dim_date
    print("\n--- Generating Date Dimension (dim_date) ---")
    if collected_dates:
        try:
            # Convert list of date strings (both YYYY-MM-DD and YYYY-MM-DD dates)
            # Ensure they are valid date formats
            valid_dates = []
            for d in collected_dates:
                # check if d resembles YYYY-MM-DD
                if len(str(d)) == 10 and str(d)[4] == '-' and str(d)[7] == '-':
                    valid_dates.append(str(d))
            
            df_dates = pd.DataFrame(sorted(list(set(valid_dates))), columns=['date'])
            df_dates['parsed'] = pd.to_datetime(df_dates['date'])
            
            df_dates['year'] = df_dates['parsed'].dt.year
            df_dates['quarter'] = df_dates['parsed'].dt.quarter
            df_dates['month'] = df_dates['parsed'].dt.month
            df_dates['day'] = df_dates['parsed'].dt.day
            df_dates['day_of_week'] = df_dates['parsed'].dt.dayofweek # 0 is Monday, 6 is Sunday
            df_dates['is_weekend'] = df_dates['day_of_week'].isin([5, 6]).astype(int)
            df_dates['month_name'] = df_dates['parsed'].dt.strftime('%B')
            
            # Drop parsed datetime column
            df_dates = df_dates.drop(columns=['parsed'])
            
            df_dates.to_sql("dim_date", engine, if_exists='append', index=False)
            print(f"Generated and loaded {len(df_dates)} unique dates into dim_date.")
            loaded_counts["dim_date"] = len(df_dates)
            csv_counts["dim_date"] = len(df_dates)
            
        except Exception as e:
            print(f"Error generating dim_date: {e}")
    else:
        print("No dates found across datasets to populate dim_date!")
        
    # Validation Summary
    print("\n--- Validation Summary ---")
    validation_passed = True
    print(f"{'Table Name':<25} | {'CSV Rows':<10} | {'Loaded Rows':<10} | {'Status':<10}")
    print("-" * 65)
    for table_name, loaded_cnt in loaded_counts.items():
        csv_cnt = csv_counts.get(table_name, 0)
        status = "PASS" if csv_cnt == loaded_cnt else "FAIL"
        if status == "FAIL":
            validation_passed = False
        print(f"{table_name:<25} | {csv_cnt:<10} | {loaded_cnt:<10} | {status:<10}")
        
    # Check foreign key constraints
    # In SQLite, PRAGMA foreign_key_check returns violations
    print("\nVerifying foreign key constraints...")
    try:
        with engine.connect() as connection:
            result = connection.execute(text("PRAGMA foreign_key_check"))
            violations = result.all()
            if violations:
                print(f"Warning: Found {len(violations)} foreign key violations in the database:")
                for violation in violations:
                    print(f"  Table: {violation[0]}, Rowid: {violation[1]}, Target Table: {violation[2]}, FK index: {violation[3]}")
                validation_passed = False
            else:
                print("All foreign key references validated successfully. No orphans found.")
    except Exception as e:
        print(f"Error checking foreign keys: {e}")
        validation_passed = False
        
    if validation_passed:
        print("\nLoad completed successfully! Database is healthy and ready for queries.")
    else:
        print("\nLoad completed with validation warnings. Please check the logs.")

if __name__ == "__main__":
    load_data()
