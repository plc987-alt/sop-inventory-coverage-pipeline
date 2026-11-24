import pandas as pd
import numpy as np
from pathlib import Path

def gerar_bases_sinteticas():
    np.random.seed(42)
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # 1. Cadastro de Materiais (estilo MARA)
    n_skus = 200
    categorias = ["Transformadores", "Cabos Isolados", "Chaves Seccionadoras", "Postes", "Medidores"]
    regionais = ["Campinas", "Ribeirão Preto", "Santos", "Caxias do Sul", "Santa Maria"]

    df_materiais = pd.DataFrame({
        "sku_id": [f"MAT-{10000 + i}" for i in range(n_skus)],
        "descricao": [f"Material Elétrico Tipo {i+1}" for i in range(n_skus)],
        "categoria": np.random.choice(categorias, n_skus),
        "custo_unitario": np.round(np.random.uniform(45.0, 4500.0, n_skus), 2),
        "lead_time_dias": np.random.choice([15, 30, 45, 60, 90], n_skus)
    })

    # 2. Posição de Estoque Atual por Depósito (estilo MARD)
    # E001 = Depósito Principal | Y001 / Z001 = Depósitos Auxiliares/Veiculares
    depositos = ["E001", "Y001", "Z001"]
    registros_estoque = []

    for sku in df_materiais["sku_id"]:
        regional = np.random.choice(regionais)
        for dep in depositos:
            qtd_livre = np.random.randint(0, 120) if dep == "E001" else np.random.randint(0, 25)
            qtd_transito = np.random.randint(0, 60) if dep == "E001" else 0
            registros_estoque.append({
                "sku_id": sku,
                "regional": regional,
                "deposito": dep,
                "estoque_livre": qtd_livre,
                "estoque_transito": qtd_transito
            })

    df_estoque = pd.DataFrame(registros_estoque)

    # 3. Histórico de Consumo Mensal (últimos 12 meses)
    meses = pd.date_range(end="2026-10-01", periods=12, freq="MS")
    registros_consumo = []

    for sku in df_materiais["sku_id"]:
        consumo_base = np.random.randint(10, 80)
        for mes in meses:
            variacao = np.random.uniform(0.7, 1.35)
            registros_consumo.append({
                "sku_id": sku,
                "mes_referencia": mes.strftime("%Y-%m-%d"),
                "quantidade_consumida": int(consumo_base * variacao)
            })

    df_consumo = pd.DataFrame(registros_consumo)

    # Salva os arquivos brutos
    df_materiais.to_csv(raw_dir / "materiais_sap.csv", index=False)
    df_estoque.to_csv(raw_dir / "estoque_depositos.csv", index=False)
    df_consumo.to_csv(raw_dir / "historico_consumo.csv", index=False)
    print("✅ Bases sintéticas geradas com sucesso em data/raw/")

if __name__ == "__main__":
    gerar_bases_sinteticas()