-- =====================================================================
-- G3  Channel sentiment (6 features)
-- Reuses the Channel Sentiment Score logic: volume-weighted success rate
-- with Bayesian shrinkage, plus a simple composite CSS-style score.
-- =====================================================================
WITH c AS (
    SELECT customer_id, month_idx, channel, attempts, successes
    FROM channel_monthly WHERE month_idx BETWEEN {s} - 12 AND {s} - 1
),
prior AS (SELECT SUM(successes) * 1.0 / SUM(attempts) AS r FROM c WHERE month_idx >= {s} - 6),
agg AS (
    SELECT customer_id,
           SUM(CASE WHEN month_idx >= {s} - 6 THEN successes END)            AS suc6,
           SUM(CASE WHEN month_idx >= {s} - 6 THEN attempts END)             AS att6,
           SUM(CASE WHEN month_idx >= {s} - 3 THEN attempts - successes END) AS failed3,
           COUNT(DISTINCT channel)                                           AS n_channels,
           SUM(CASE WHEN month_idx >= {s} - 3 THEN successes END) / 3.0      AS dig3,
           SUM(CASE WHEN month_idx <  {s} - 3 THEN successes END) / 9.0      AS dig9,
           SUM(successes)                                                    AS dig12
    FROM c GROUP BY customer_id
),
g1 AS (SELECT customer_id, g1_txn_cnt_12m, g1_txn_trend_3v9 FROM g1_transactional),
g2 AS (SELECT customer_id, g2_balance_trend FROM g2_balance_product)
SELECT p.customer_id,
       (COALESCE(a.suc6, 0) + 20 * pr.r) / (COALESCE(a.att6, 0) + 20)               AS g3_channel_success_rate_6m,
       COALESCE(a.failed3, 0)                                                       AS g3_failed_txn_3m,
       COALESCE(a.dig12, 0) / (COALESCE(a.dig12, 0) + g1.g1_txn_cnt_12m + 1)        AS g3_digital_share_12m,
       COALESCE(a.n_channels, 0)                                                    AS g3_n_channels_used,
       (COALESCE(a.dig3, 0) + 1) / (COALESCE(a.dig9, 0) + 1)                        AS g3_digital_trend_3v9,
       -- composite CSS-style score: percentile ranks, 60/20/20
       ROUND(100 * (0.6 * PERCENT_RANK() OVER (ORDER BY (COALESCE(a.suc6, 0) + 20 * pr.r) / (COALESCE(a.att6, 0) + 20))
                  + 0.2 * PERCENT_RANK() OVER (ORDER BY COALESCE(g2.g2_balance_trend, 0))
                  + 0.2 * PERCENT_RANK() OVER (ORDER BY g1.g1_txn_trend_3v9)), 1)  AS g3_css_score
FROM population p
CROSS JOIN prior pr
LEFT JOIN agg a USING (customer_id)
JOIN g1 USING (customer_id)
JOIN g2 USING (customer_id)
