-- =====================================================================
-- 08  Graded target structure
-- ---------------------------------------------------------------------
--   churn_flag          dormant 90+ days: no customer transactions in the
--                       3 months after the snapshot ({s} .. {s}+2)
--   early_warning_flag  activity collapses (< 20% of the 12m monthly average)
--                       in the first ~45-60 days ({s}, {s}+1), an earlier and
--                       softer label for proactive outreach
--   surv_months/event   months until the first full 3-month silence within
--                       a 12-month follow-up (survival label)
-- =====================================================================
WITH m AS (
    SELECT am.customer_id, t.month_idx, SUM(t.txn_cnt) AS cnt
    FROM txn_monthly t JOIN account_master am USING (account_id)
    WHERE t.month_idx BETWEEN {s} - 12 AND {s} + 11
    GROUP BY am.customer_id, t.month_idx
),
grid AS (
    SELECT p.customer_id, g.month_idx
    FROM population p CROSS JOIN (SELECT UNNEST(range({s} - 12, {s} + 12)) AS month_idx) g
),
d AS (
    SELECT g.customer_id, g.month_idx, COALESCE(m.cnt, 0) AS cnt
    FROM grid g LEFT JOIN m USING (customer_id, month_idx)
),
roll AS (
    SELECT *, SUM(cnt) OVER (PARTITION BY customer_id ORDER BY month_idx ROWS BETWEEN CURRENT ROW AND 2 FOLLOWING) AS next3,
              COUNT(*) OVER (PARTITION BY customer_id ORDER BY month_idx ROWS BETWEEN CURRENT ROW AND 2 FOLLOWING) AS n3
    FROM d
)
SELECT customer_id,
       CASE WHEN SUM(CASE WHEN month_idx BETWEEN {s} AND {s} + 2 THEN cnt END) = 0 THEN 1 ELSE 0 END AS churn_flag,
       CASE WHEN SUM(CASE WHEN month_idx BETWEEN {s} AND {s} + 1 THEN cnt END) / 2.0
                 < 0.2 * AVG(CASE WHEN month_idx < {s} THEN cnt END) THEN 1 ELSE 0 END          AS early_warning_flag,
       COALESCE(MIN(CASE WHEN month_idx >= {s} AND n3 = 3 AND next3 = 0 THEN month_idx END) - {s} + 1, 12) AS surv_months,
       CASE WHEN MIN(CASE WHEN month_idx >= {s} AND n3 = 3 AND next3 = 0 THEN month_idx END) IS NOT NULL THEN 1 ELSE 0 END AS surv_event
FROM roll
GROUP BY customer_id
