-- Analytical SQL Queries for Bluestock Mutual Fund Analytics
-- Powered by SQLite Star Schema

-- ====================================================================
-- Query 1: Top 5 Funds by AUM
-- Rationale: Identifies the largest schemes by assets under management.
-- ====================================================================
SELECT 
    f.amfi_code, 
    f.scheme_name, 
    f.fund_house, 
    p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.aum_crore IS NOT NULL
ORDER BY p.aum_crore DESC
LIMIT 5;


-- ====================================================================
-- Query 2: Average NAV Per Month
-- Rationale: Provides monthly historical averages for fund pricing,
-- grouped by scheme to see general upward/downward trends.
-- ====================================================================
SELECT 
    f.scheme_name, 
    d.year, 
    d.month, 
    d.month_name, 
    ROUND(AVG(n.nav), 4) AS avg_nav
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
JOIN dim_date d ON n.nav_date = d.date
GROUP BY f.amfi_code, d.year, d.month
ORDER BY f.scheme_name, d.year, d.month
LIMIT 50; -- Limit output for readability


-- ====================================================================
-- Query 3: SIP Inflow Year-Over-Year (YoY) Growth
-- Rationale: Tracks industry-wide SIP flow patterns and shows the YoY progress.
-- ====================================================================
SELECT 
    month_date, 
    sip_inflow_crore, 
    active_sip_accounts_crore, 
    sip_aum_lakh_crore, 
    yoy_growth_pct
FROM monthly_sip_inflows
ORDER BY month_date;


-- ====================================================================
-- Query 4: Transactions by State
-- Rationale: Identifies geographical density of mutual fund transactions
-- by counting total transactions and summing investment volume.
-- ====================================================================
SELECT 
    state, 
    COUNT(*) AS total_transactions, 
    ROUND(SUM(amount_inr), 2) AS total_amount_inr, 
    ROUND(AVG(amount_inr), 2) AS avg_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;


-- ====================================================================
-- Query 5: Funds with Expense Ratio < 1%
-- Rationale: Locates low-cost investment options (often index/direct funds).
-- ====================================================================
SELECT 
    amfi_code, 
    scheme_name, 
    fund_house, 
    category, 
    plan, 
    expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0 AND expense_ratio_pct IS NOT NULL
ORDER BY expense_ratio_pct ASC;


-- ====================================================================
-- Query 6: Top Performing Funds (Ranked by 3-Year Return)
-- Rationale: Ranks the top 10 best-performing funds based on 3-year performance.
-- ====================================================================
SELECT 
    f.amfi_code, 
    f.scheme_name, 
    f.fund_house, 
    p.return_3yr_pct, 
    p.return_5yr_pct, 
    p.morningstar_rating,
    p.risk_grade
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.return_3yr_pct IS NOT NULL
ORDER BY p.return_3yr_pct DESC
LIMIT 10;


-- ====================================================================
-- Query 7: Average Investment Amount by Age Group
-- Rationale: Reveals investment behaviour across different age demographics.
-- ====================================================================
SELECT 
    age_group, 
    COUNT(*) AS transaction_count, 
    ROUND(SUM(amount_inr), 2) AS total_amount_inr, 
    ROUND(AVG(amount_inr), 2) AS avg_amount_inr
FROM fact_transactions
GROUP BY age_group
ORDER BY age_group;


-- ====================================================================
-- Query 8: Redemption Analysis (By City Tier)
-- Rationale: Examines redemptions to analyze the cash outflow behavior
-- across Metro/T30 vs Tier-2/B30 cities.
-- ====================================================================
SELECT 
    city_tier, 
    COUNT(*) AS redemption_count, 
    ROUND(SUM(amount_inr), 2) AS total_redemption_inr, 
    ROUND(AVG(amount_inr), 2) AS avg_redemption_inr
FROM fact_transactions
WHERE transaction_type = 'REDEMPTION'
GROUP BY city_tier;


-- ====================================================================
-- Query 9: Risk Category Distribution of Funds
-- Rationale: Checks the distribution of fund risk levels and their 
-- corresponding average expense ratios.
-- ====================================================================
SELECT 
    risk_category, 
    COUNT(*) AS scheme_count, 
    ROUND(AVG(expense_ratio_pct), 3) AS avg_expense_ratio_pct
FROM dim_fund
WHERE risk_category IS NOT NULL
GROUP BY risk_category
ORDER BY scheme_count DESC;


-- ====================================================================
-- Query 10: Fund House Comparison
-- Rationale: Compares Asset Management Companies (AMCs) by total AUM,
-- average 3-year performance, and average expense ratios.
-- ====================================================================
SELECT 
    f.fund_house, 
    COUNT(DISTINCT f.amfi_code) AS total_schemes, 
    ROUND(SUM(p.aum_crore), 2) AS aggregated_schemes_aum_crore, 
    ROUND(AVG(p.return_3yr_pct), 2) AS avg_3yr_return_pct, 
    ROUND(AVG(p.expense_ratio_pct), 3) AS avg_expense_ratio_pct
FROM dim_fund f
JOIN fact_performance p ON f.amfi_code = p.amfi_code
GROUP BY f.fund_house
ORDER BY aggregated_schemes_aum_crore DESC;
