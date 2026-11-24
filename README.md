# 📦 Pipeline Automatizado de Cobertura de Estoque e Validação de Demanda (S&OP)

Dashboard: https://plc987-alt.github.io/sop-inventory-coverage-pipeline/

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data_Processing-150458?logo=pandas&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-Analytics-orange?logo=postgresql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-Executive_Dashboard-F2C811?logo=powerbi&logoColor=black)

## 🎯 Contexto e Problema de Negócio
Em operações de grande escala apoiadas por ERPs corporativos (como **SAP MM/S4HANA**), o cálculo de cobertura de estoque e a validação de necessidades de materiais costumam depender de extrações manuais e planilhas descentralizadas. Esse processo gera:
* Lentidão na consolidação de saldos entre depósitos principais e depósitos satélites/veiculares;
* Risco de ruptura por falta de cruzamento dinâmico entre **estoque disponível, pedidos em trânsito (lead-time) e consumo médio projetado**;
* Baixa rastreabilidade das premissas de planejamento nos ciclos de **S&OP / S&OE**.

## 💡 Solução Desenvolvida
Este projeto implementa um pipeline automatizado em **Python e SQL** que simula a extração de tabelas transacionais de estoque e consumo (inspirado nas estruturas `MARD`, `MARA` e histórico de consumo do SAP), aplica regras de negócio de planejamento e disponibiliza uma camada analítica pronta para consumo no **Power BI**.

### Principais Funcionalidades
1. **Geração de Dados Sintéticos:** Criação de bases simuladas de materiais, saldos por depósito e histórico de 12 meses de consumo.
2. **Consolidação Multi-Depósito:** Agregação inteligente de saldos operacionais (incorporando depósitos auxiliares/veiculares `Y/Z` aos depósitos principais `E` por regional).
3. **Motor de Cálculo de Cobertura:**
   * Cálculo de Consumo Médio Mensal (CMM) ajustado por janela móvel dos últimos 6 meses;
   * Projeção de meses de cobertura (`Estoque Disponível Geral / CMM`);
   * Classificação automática de criticidade (`Crítico`, `Atenção (< Meta 2M)`, `Saudável (Na Meta)`, `Excesso (> 3M)`).
4. **Camada de Saída (Gold):** Exportação estruturada em formato colunar (`.parquet`) e tabelas relacionais (`.csv`) prontas para visualização executiva no Power BI.

## 🏗️ Arquitetura do Projeto

```text
├── data/
│   ├── raw/                   # Dados brutos simulados (extrações ERP e histórico de consumo)
│   ├── processed/             # Dados tratados e cruzados em formato Parquet (camada Silver)
│   └── gold/                  # Tabelas fato e dimensão prontas para Power BI (camada Gold)
├── sql/
│   └── queries_analiticas.sql # Consultas com CTEs e Window Functions para ranking de ruptura
├── src/
│   ├── gerar_dados.py         # Gerador de bases sintéticas inspiradas no SAP
│   └── pipeline.py            # Orquestrador principal do fluxo ETL e regras de S&OP
├── .gitignore                 # Arquivos ignorados no versionamento
├── requirements.txt           # Dependências do projeto
└── README.md                  # Documentação técnica
