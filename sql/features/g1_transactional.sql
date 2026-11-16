-- =====================================================================
-- G1  Transactional behaviour (10 features)
-- =====================================================================
WITH m AS (   -- customer x month, rolled up across accounts via account_master
    SELECT am.customer_id, t.month_idx,
           SUM(t.txn_cnt) AS cnt, SUM(t.inflow_amt) AS inflow, SUM(t.outflow_amt) AS outflow
    FROM txn_monthly t JOIN account_master am USING (account_id)
    WHERE t.month_idx BETWEEN {s} - 12 AND {s} - 1
    GROUP BY am.customer_id, t.month_idx
),
gaps AS (
    SELECT customer_id, month_idx - LAG(month_idx) OVER (PARTITION BY customer_id ORDER BY month_idx) - 1 AS gap
    FROM m WHERE cnt > 0
)
SELECT p.customer_id,
       COALESCE(SUM(m.cnt), 0)                                                    AS g1_txn_cnt_12m,
       COALESCE(SUM(CASE WHEN m.month_idx >= {s} - 3 THEN m.cnt END), 0)         AS g1_txn_cnt_3m,
       LN(1 + COALESCE(SUM(m.inflow + m.outflow), 0))                             AS g1_txn_value_12m_log,
       COALESCE(SUM(m.cnt), 0) / 12.0                                             AS g1_avg_monthly_txn,
       (COALESCE(SUM(CASE WHEN m.month_idx >= {s} - 3 THEN m.cnt END), 0) / 3.0 + 1)
         / (COALESCE(SUM(CASE WHEN m.month_idx < {s} - 3 THEN m.cnt END), 0) / 9.0 + 1) AS g1_txn_trend_3v9,
       COUNT(DISTINCT CASE WHEN m.cnt > 0 THEN m.month_idx END)                   AS g1_months_active_12m,
       {s} - ARG_MAX(m.month_idx, m.cnt * 1000 + m.month_idx)                     AS g1_months_since_peak,  -- ties -> latest month
       (SUM(CASE WHEN m.month_idx >= {s} - 3 THEN m.outflow END) + 1)
         / (SUM(CASE WHEN m.month_idx >= {s} - 3 THEN m.inflow END) + 1)          AS g1_outflow_inflow_ratio_3m,
       COALESCE((SELECT MAX(gap) FROM gaps g WHERE g.customer_id = p.customer_id), 0) AS g1_max_gap_months,
       STDDEV_SAMP(m.cnt) / (AVG(m.cnt) + 1)                                      AS g1_txn_cv
FROM population p LEFT JOIN m USING (customer_id)
GROUP BY p.customer_id
