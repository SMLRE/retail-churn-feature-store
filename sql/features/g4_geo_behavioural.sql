-- =====================================================================
-- G4  Geo-behavioural (5 features)
-- Uses the Customer Residence Inference idea: where the customer actually
-- transacts vs the state recorded at account opening.
-- =====================================================================
WITH g AS (
    SELECT customer_id, state, SUM(branch_visits) AS bv, SUM(atm_txns) AS atm, SUM(pos_txns) AS pos,
           SUM(branch_visits + atm_txns + pos_txns) AS tot
    FROM geo_monthly WHERE month_idx BETWEEN {s} - 12 AND {s} - 1
    GROUP BY customer_id, state
),
ranked AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY tot DESC, state) AS rn FROM g)
SELECT p.customer_id,
       COUNT(DISTINCT r.state)                                                       AS g4_n_states_12m,
       COALESCE(MAX(CASE WHEN r.rn = 1 THEN r.tot END) * 1.0 / NULLIF(SUM(r.tot), 0), 0) AS g4_top_state_share,
       CASE WHEN MAX(CASE WHEN r.rn = 1 THEN r.state END) <> ANY_VALUE(cm.open_state) THEN 1 ELSE 0 END AS g4_relocated_flag,
       COALESCE(SUM(r.bv), 0)                                                        AS g4_branch_visits_12m,
       COALESCE(SUM(r.atm) * 1.0 / NULLIF(SUM(r.tot), 0), 0)                         AS g4_atm_share
FROM population p
JOIN customer_master cm USING (customer_id)
LEFT JOIN ranked r USING (customer_id)
GROUP BY p.customer_id
