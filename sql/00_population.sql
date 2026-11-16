-- =====================================================================
-- 00  Scoring population: customers with a customer-initiated transaction
--     in the month before the snapshot. Customers already drifting into
--     silence are a reactivation problem, not a retention one. Including
--     them would also make the model look better than it is, because it
--     would just be "predicting" silence that has already started.
--     All feature groups use the 12 months before {s}: months {s}-12 .. {s}-1
-- =====================================================================
SELECT DISTINCT am.customer_id
FROM txn_monthly t
JOIN account_master am USING (account_id)
WHERE t.month_idx = {s} - 1
  AND t.txn_cnt > 0
