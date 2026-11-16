-- =====================================================================
-- G6  Network & relationship (6 features)
-- Salary credits anchor a relationship; transfers to the customer's OWN
-- accounts at other banks are the classic "moving house" signal.
-- =====================================================================
WITH t AS (
    SELECT am.customer_id, t.month_idx,
           SUM(t.distinct_counterparties) AS cps, MAX(t.salary_credit) AS sal,
           SUM(t.inflow_amt) AS inflow, SUM(t.outflow_amt) AS outflow, SUM(t.self_transfer_out_amt) AS self_out
    FROM txn_monthly t JOIN account_master am USING (account_id)
    WHERE t.month_idx BETWEEN {s} - 12 AND {s} - 1
    GROUP BY am.customer_id, t.month_idx
)
SELECT p.customer_id,
       COALESCE(SUM(t.cps), 0)                                                         AS g6_counterparties_12m,
       (COALESCE(SUM(CASE WHEN t.month_idx >= {s} - 3 THEN t.cps END), 0) / 3.0 + 1)
         / (COALESCE(SUM(CASE WHEN t.month_idx < {s} - 3 THEN t.cps END), 0) / 9.0 + 1) AS g6_counterparties_trend,
       COALESCE(SUM(t.sal), 0)                                                         AS g6_salary_months_12m,
       COALESCE({s} - MAX(CASE WHEN t.sal = 1 THEN t.month_idx END), 13)               AS g6_months_since_salary,
       COALESCE(SUM(CASE WHEN t.month_idx >= {s} - 3 THEN t.self_out END)
                / NULLIF(SUM(CASE WHEN t.month_idx >= {s} - 3 THEN t.outflow END), 0), 0) AS g6_self_transfer_share_3m,
       COALESCE(SUM(t.self_out) / NULLIF(SUM(t.outflow), 0), 0)                        AS g6_self_transfer_share_12m
FROM population p LEFT JOIN t USING (customer_id)
GROUP BY p.customer_id
