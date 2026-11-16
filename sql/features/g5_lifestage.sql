-- =====================================================================
-- G5  Life-stage & demographic (6 features)
-- Snapshot month {s} corresponds to calendar year 2025 in the synthetic data.
-- =====================================================================
SELECT p.customer_id,
       2025 - cm.birth_year                                                   AS g5_age,
       {s} - cm.onboard_month_idx                                             AS g5_tenure_months,
       CASE WHEN {s} - cm.onboard_month_idx < 12 THEN 1 ELSE 0 END            AS g5_new_to_bank,
       CASE WHEN 2025 - cm.birth_year < 30 THEN 1 ELSE 0 END                  AS g5_young_adult,
       CASE WHEN cm.segment = 'AFFLUENT' THEN 1 ELSE 0 END                    AS g5_affluent,
       {s} - cm.kyc_update_month_idx                                          AS g5_months_since_kyc_update
FROM population p
JOIN customer_master cm USING (customer_id)
