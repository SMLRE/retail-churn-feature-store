# Feature dictionary

Generated from `src/registry.py`. 48 features in 7 groups, computed over a 12-month observation window.

## G1 · Transactional behaviour (10)

| Feature | Description | Expected range |
|---|---|---|
| `g1_txn_cnt_12m` | Customer-initiated transactions, last 12 months | 0 – ∞ |
| `g1_txn_cnt_3m` | Transactions, last 3 months | 0 – ∞ |
| `g1_txn_value_12m_log` | log(1 + inflow + outflow value), 12 months | 0 – 40 |
| `g1_avg_monthly_txn` | Average monthly transactions | 0 – ∞ |
| `g1_txn_trend_3v9` | Avg monthly txns last 3m / previous 9m (+1 smoothed) | 0 – ∞ |
| `g1_months_active_12m` | Months with at least one transaction | 0 – 12 |
| `g1_months_since_peak` | Months since the busiest month in the window | 1 – 12 |
| `g1_outflow_inflow_ratio_3m` | Outflow / inflow, last 3 months | 0 – ∞ |
| `g1_max_gap_months` | Longest run of inactive months | 0 – 11 |
| `g1_txn_cv` | Coefficient of variation of monthly transactions | 0 – ∞ |

## G2 · Balance & product holding (8)

| Feature | Description | Expected range |
|---|---|---|
| `g2_avg_balance_12m_log` | log(1 + average deposit balance), 12 months | 0 – 40 |
| `g2_balance_trend` | Slope of signed-log deposit balance per month | −∞ – ∞ |
| `g2_balance_3m_vs_12m` | Avg balance last 3m / avg balance 12m | −∞ – ∞ |
| `g2_min_balance_ratio` | Min monthly balance / average balance | −∞ – ∞ |
| `g2_n_accounts` | Number of accounts held | 1 – 20 |
| `g2_n_product_types` | Number of distinct product types | 1 – 5 |
| `g2_has_card` | Holds a card product | 0 – 1 |
| `g2_has_loan` | Holds a loan product | 0 – 1 |

## G3 · Channel sentiment (6)

| Feature | Description | Expected range |
|---|---|---|
| `g3_channel_success_rate_6m` | Digital success rate, 6m, volume-weighted + shrunk (k=20) | 0 – 1 |
| `g3_failed_txn_3m` | Failed digital attempts, last 3 months | 0 – ∞ |
| `g3_digital_share_12m` | Share of activity through digital channels | 0 – 1 |
| `g3_n_channels_used` | Distinct digital channels used | 0 – 4 |
| `g3_digital_trend_3v9` | Digital activity last 3m vs previous 9m | 0 – ∞ |
| `g3_css_score` | Channel Sentiment Score (0-100, 60/20/20) | 0 – 100 |

## G4 · Geo-behavioural (5)

| Feature | Description | Expected range |
|---|---|---|
| `g4_n_states_12m` | Distinct states with branch / ATM / POS activity | 0 – 37 |
| `g4_top_state_share` | Share of activity in the most-used state | 0 – 1 |
| `g4_relocated_flag` | Most-used state differs from account-opening state | 0 – 1 |
| `g4_branch_visits_12m` | Branch visits, 12 months | 0 – ∞ |
| `g4_atm_share` | ATM share of physical activity | 0 – 1 |

## G5 · Life-stage & demographic (6)

| Feature | Description | Expected range |
|---|---|---|
| `g5_age` | Age in years | 16 – 100 |
| `g5_tenure_months` | Months since onboarding | 0 – 600 |
| `g5_new_to_bank` | Onboarded in the last 12 months | 0 – 1 |
| `g5_young_adult` | Age under 30 | 0 – 1 |
| `g5_affluent` | Affluent segment | 0 – 1 |
| `g5_months_since_kyc_update` | Months since last KYC update | 0 – 600 |

## G6 · Network & relationship (6)

| Feature | Description | Expected range |
|---|---|---|
| `g6_counterparties_12m` | Distinct counterparties (summed monthly), 12m | 0 – ∞ |
| `g6_counterparties_trend` | Counterparties last 3m vs previous 9m | 0 – ∞ |
| `g6_salary_months_12m` | Months with a salary credit | 0 – 12 |
| `g6_months_since_salary` | Months since last salary credit (13 = none) | 1 – 13 |
| `g6_self_transfer_share_3m` | Share of outflow to own accounts at other banks, 3m | 0 – 1 |
| `g6_self_transfer_share_12m` | Share of outflow to own accounts at other banks, 12m | 0 – 1 |

## G7 · Risk-scoring layer (7)

| Feature | Description | Expected range |
|---|---|---|
| `g7_flag_salary_stopped` | Regular salary earner with no salary for 2+ months | 0 – 1 |
| `g7_flag_balance_drain` | 3m balance < 50% of 12m average | 0 – 1 |
| `g7_flag_txn_drop` | Transaction trend below 0.6 | 0 – 1 |
| `g7_flag_digital_friction` | Digital success rate below 80% | 0 – 1 |
| `g7_flag_funds_leaving` | Over 15% of outflow going to own accounts elsewhere | 0 – 1 |
| `g7_n_risk_flags` | Number of risk flags raised (0-5) | 0 – 5 |
| `g7_early_warning_points` | Weighted early-warning points (0-11) | 0 – 11 |
