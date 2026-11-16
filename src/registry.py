"""
Feature registry: the single source of truth for the 48 features.

Each entry: name -> (group, description, expected_min, expected_max).
The registry drives the range-validation queries and the generated
feature dictionary (docs/feature_dictionary.md).
"""
INF = float("inf")

GROUPS = {
    "g1": "Transactional behaviour",
    "g2": "Balance & product holding",
    "g3": "Channel sentiment",
    "g4": "Geo-behavioural",
    "g5": "Life-stage & demographic",
    "g6": "Network & relationship",
    "g7": "Risk-scoring layer",
}

FEATURES = {
    # G1 ---------------------------------------------------------------
    "g1_txn_cnt_12m": ("g1", "Customer-initiated transactions, last 12 months", 0, INF),
    "g1_txn_cnt_3m": ("g1", "Transactions, last 3 months", 0, INF),
    "g1_txn_value_12m_log": ("g1", "log(1 + inflow + outflow value), 12 months", 0, 40),
    "g1_avg_monthly_txn": ("g1", "Average monthly transactions", 0, INF),
    "g1_txn_trend_3v9": ("g1", "Avg monthly txns last 3m / previous 9m (+1 smoothed)", 0, INF),
    "g1_months_active_12m": ("g1", "Months with at least one transaction", 0, 12),
    "g1_months_since_peak": ("g1", "Months since the busiest month in the window", 1, 12),
    "g1_outflow_inflow_ratio_3m": ("g1", "Outflow / inflow, last 3 months", 0, INF),
    "g1_max_gap_months": ("g1", "Longest run of inactive months", 0, 11),
    "g1_txn_cv": ("g1", "Coefficient of variation of monthly transactions", 0, INF),
    # G2 ---------------------------------------------------------------
    "g2_avg_balance_12m_log": ("g2", "log(1 + average deposit balance), 12 months", 0, 40),
    "g2_balance_trend": ("g2", "Slope of signed-log deposit balance per month", -INF, INF),
    "g2_balance_3m_vs_12m": ("g2", "Avg balance last 3m / avg balance 12m", -INF, INF),
    "g2_min_balance_ratio": ("g2", "Min monthly balance / average balance", -INF, INF),
    "g2_n_accounts": ("g2", "Number of accounts held", 1, 20),
    "g2_n_product_types": ("g2", "Number of distinct product types", 1, 5),
    "g2_has_card": ("g2", "Holds a card product", 0, 1),
    "g2_has_loan": ("g2", "Holds a loan product", 0, 1),
    # G3 ---------------------------------------------------------------
    "g3_channel_success_rate_6m": ("g3", "Digital success rate, 6m, volume-weighted + shrunk (k=20)", 0, 1),
    "g3_failed_txn_3m": ("g3", "Failed digital attempts, last 3 months", 0, INF),
    "g3_digital_share_12m": ("g3", "Share of activity through digital channels", 0, 1),
    "g3_n_channels_used": ("g3", "Distinct digital channels used", 0, 4),
    "g3_digital_trend_3v9": ("g3", "Digital activity last 3m vs previous 9m", 0, INF),
    "g3_css_score": ("g3", "Channel Sentiment Score (0-100, 60/20/20)", 0, 100),
    # G4 ---------------------------------------------------------------
    "g4_n_states_12m": ("g4", "Distinct states with branch / ATM / POS activity", 0, 37),
    "g4_top_state_share": ("g4", "Share of activity in the most-used state", 0, 1),
    "g4_relocated_flag": ("g4", "Most-used state differs from account-opening state", 0, 1),
    "g4_branch_visits_12m": ("g4", "Branch visits, 12 months", 0, INF),
    "g4_atm_share": ("g4", "ATM share of physical activity", 0, 1),
    # G5 ---------------------------------------------------------------
    "g5_age": ("g5", "Age in years", 16, 100),
    "g5_tenure_months": ("g5", "Months since onboarding", 0, 600),
    "g5_new_to_bank": ("g5", "Onboarded in the last 12 months", 0, 1),
    "g5_young_adult": ("g5", "Age under 30", 0, 1),
    "g5_affluent": ("g5", "Affluent segment", 0, 1),
    "g5_months_since_kyc_update": ("g5", "Months since last KYC update", 0, 600),
    # G6 ---------------------------------------------------------------
    "g6_counterparties_12m": ("g6", "Distinct counterparties (summed monthly), 12m", 0, INF),
    "g6_counterparties_trend": ("g6", "Counterparties last 3m vs previous 9m", 0, INF),
    "g6_salary_months_12m": ("g6", "Months with a salary credit", 0, 12),
    "g6_months_since_salary": ("g6", "Months since last salary credit (13 = none)", 1, 13),
    "g6_self_transfer_share_3m": ("g6", "Share of outflow to own accounts at other banks, 3m", 0, 1),
    "g6_self_transfer_share_12m": ("g6", "Share of outflow to own accounts at other banks, 12m", 0, 1),
    # G7 ---------------------------------------------------------------
    "g7_flag_salary_stopped": ("g7", "Regular salary earner with no salary for 2+ months", 0, 1),
    "g7_flag_balance_drain": ("g7", "3m balance < 50% of 12m average", 0, 1),
    "g7_flag_txn_drop": ("g7", "Transaction trend below 0.6", 0, 1),
    "g7_flag_digital_friction": ("g7", "Digital success rate below 80%", 0, 1),
    "g7_flag_funds_leaving": ("g7", "Over 15% of outflow going to own accounts elsewhere", 0, 1),
    "g7_n_risk_flags": ("g7", "Number of risk flags raised (0-5)", 0, 5),
    "g7_early_warning_points": ("g7", "Weighted early-warning points (0-11)", 0, 11),
}

assert len(FEATURES) == 48, len(FEATURES)
