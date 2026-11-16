-- =====================================================================
-- G7  Risk-scoring layer (7 features)
-- Interpretable rule flags built ON TOP of groups 1-6, the "early
-- warning" view a retention team can read without a model.
-- =====================================================================
WITH b AS (
    SELECT g1.customer_id,
           CASE WHEN g6.g6_salary_months_12m >= 6 AND g6.g6_months_since_salary >= 2 THEN 1 ELSE 0 END AS f_salary_stopped,
           CASE WHEN g2.g2_balance_3m_vs_12m < 0.5 THEN 1 ELSE 0 END                                     AS f_balance_drain,
           CASE WHEN g1.g1_txn_trend_3v9 < 0.6 THEN 1 ELSE 0 END                                         AS f_txn_drop,
           CASE WHEN g3.g3_channel_success_rate_6m < 0.80 THEN 1 ELSE 0 END                             AS f_digital_friction,
           CASE WHEN g6.g6_self_transfer_share_3m > 0.15 THEN 1 ELSE 0 END                               AS f_funds_leaving
    FROM g1_transactional g1
    JOIN g2_balance_product g2 USING (customer_id)
    JOIN g3_channel_sentiment g3 USING (customer_id)
    JOIN g6_network_relationship g6 USING (customer_id)
)
SELECT customer_id,
       f_salary_stopped   AS g7_flag_salary_stopped,
       f_balance_drain    AS g7_flag_balance_drain,
       f_txn_drop         AS g7_flag_txn_drop,
       f_digital_friction AS g7_flag_digital_friction,
       f_funds_leaving    AS g7_flag_funds_leaving,
       f_salary_stopped + f_balance_drain + f_txn_drop + f_digital_friction + f_funds_leaving AS g7_n_risk_flags,
       3 * f_funds_leaving + 3 * f_salary_stopped + 2 * f_balance_drain + 2 * f_txn_drop + f_digital_friction AS g7_early_warning_points
FROM b
