import pandas as pd
import numpy as np
from pathlib import Path

def executar_pipeline():
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    gold_dir = Path("data/gold")

    # 1. Ingestão
    df_mat = pd.read_csv(raw_dir / "materiais_sap.csv")
    df_est = pd.read_csv(raw_dir / "estoque_depositos.csv")
    df_cons = pd.read_csv(raw_dir / "historico_consumo.csv")

    # 2. Consolidação Multi-Depósito (Agrega depósitos Y/Z no principal por SKU e Regional)
    df_est["tipo_deposito"] = np.where(
        df_est["deposito"].str.startswith("E"), "Principal", "Auxiliar/Veicular"
    )

    df_est_consolidado = (
        df_est.groupby(["sku_id", "regional"], as_index=False)
        .agg(
            estoque_livre_total=("estoque_livre", "sum"),
            estoque_transito_total=("estoque_transito", "sum"),
            saldo_auxiliar=("estoque_livre", lambda x: x[df_est.loc[x.index, "tipo_deposito"] == "Auxiliar/Veicular"].sum())
        )
    )
    df_est_consolidado["estoque_disponivel_geral"] = (
        df_est_consolidado["estoque_livre_total"] + df_est_consolidado["estoque_transito_total"]
    )

    # 3. Cálculo do Consumo Médio Mensal (CMM - Janela móvel dos últimos 6 meses)
    df_cons["mes_referencia"] = pd.to_datetime(df_cons["mes_referencia"])
    data_corte = df_cons["mes_referencia"].max() - pd.DateOffset(months=5)

    df_cmm = (
        df_cons[df_cons["mes_referencia"] >= data_corte]
        .groupby("sku_id", as_index=False)
        .agg(cmm_6m=("quantidade_consumida", "mean"))
    )
    df_cmm["cmm_6m"] = df_cmm["cmm_6m"].round(2)

    # 4. Cruzamento e Cálculo de KPIs de S&OP (Camada Silver)
    df_silver = (
        df_est_consolidado
        .merge(df_mat, on="sku_id", how="left")
        .merge(df_cmm, on="sku_id", how="left")
    )

    df_silver["cobertura_meses"] = np.where(
        df_silver["cmm_6m"] > 0,
        (df_silver["estoque_disponivel_geral"] / df_silver["cmm_6m"]).round(2),
        0
    )
    df_silver["valor_estoque_total"] = (
        df_silver["estoque_disponivel_geral"] * df_silver["custo_unitario"]
    ).round(2)

    # Classificação de Criticidade (Meta de referência = 2.0 meses)
    condicoes = [
        df_silver["cobertura_meses"] < 1.0,
        (df_silver["cobertura_meses"] >= 1.0) & (df_silver["cobertura_meses"] < 2.0),
        (df_silver["cobertura_meses"] >= 2.0) & (df_silver["cobertura_meses"] <= 3.0),
        df_silver["cobertura_meses"] > 3.0
    ]
    status_labels = ["1. Crítico (Ruptura Iminente)", "2. Atenção (< Meta 2M)", "3. Saudável (Na Meta)", "4. Excesso (> 3M)"]
    df_silver["status_cobertura"] = np.select(condicoes, status_labels, default="Sem Consumo")

    df_silver.to_parquet(processed_dir / "estoque_analitico_silver.parquet", index=False)

    # 5. Camada Gold (Tabelas Fato e Dimensão prontas para Power BI)
    df_silver.to_csv(gold_dir / "fato_cobertura_estoque.csv", index=False, sep=";", decimal=",")
    df_mat.to_csv(gold_dir / "dim_materiais.csv", index=False, sep=";", decimal=",")

    print("✅ Pipeline concluído! Resumo executivo:")
    print(df_silver["status_cobertura"].value_counts())

if __name__ == "__main__":
    executar_pipeline()