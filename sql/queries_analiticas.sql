-- Cálculo de Ranking de Criticidade de Ruptura por Regional usando CTE e Window Functions
WITH consumo_recente AS (
    SELECT
        sku_id,
        AVG(quantidade_consumida) AS cmm_6m
    FROM historico_consumo
    WHERE mes_referencia >= CURRENT_DATE - INTERVAL '6 months'
    GROUP BY sku_id
),
posicao_consolidada AS (
    SELECT
        e.regional,
        e.sku_id,
        m.categoria,
        m.custo_unitario,
        SUM(e.estoque_livre + e.estoque_transito) AS estoque_total,
        COALESCE(c.cmm_6m, 0) AS cmm_6m
    FROM estoque_depositos e
    INNER JOIN materiais_sap m ON e.sku_id = m.sku_id
    LEFT JOIN consumo_recente c ON e.sku_id = c.sku_id
    GROUP BY e.regional, e.sku_id, m.categoria, m.custo_unitario, c.cmm_6m
)
SELECT
    regional,
    sku_id,
    categoria,
    estoque_total,
    ROUND(cmm_6m, 2) AS consumo_medio_mensal,
    ROUND(estoque_total / NULLIF(cmm_6m, 0), 2) AS cobertura_meses,
    RANK() OVER (
        PARTITION BY regional
        ORDER BY (estoque_total / NULLIF(cmm_6m, 0)) ASC
    ) AS ranking_risco_ruptura
FROM posicao_consolidada
WHERE cmm_6m > 0;