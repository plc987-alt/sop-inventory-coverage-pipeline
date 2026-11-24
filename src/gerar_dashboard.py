import json
import pandas as pd
from pathlib import Path

def gerar_dashboard_html():
    silver_path = Path("data/processed/estoque_analitico_silver.parquet")
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(silver_path)

    # Coordenadas reais das regionais do projeto
    coordenadas_regionais = {
        "Campinas": {"lat": -22.9099, "lng": -47.0626, "uf": "SP"},
        "Ribeirão Preto": {"lat": -21.1704, "lng": -47.8103, "uf": "SP"},
        "Santos": {"lat": -23.9608, "lng": -46.3336, "uf": "SP"},
        "Caxias do Sul": {"lat": -29.1678, "lng": -51.1794, "uf": "RS"},
        "Santa Maria": {"lat": -29.6842, "lng": -53.8069, "uf": "RS"},
    }

    # Agrupamento geográfico para o mapa
    df_mapa = (
        df.groupby("regional", as_index=False)
        .agg(
            valor_total=("valor_estoque_total", "sum"),
            estoque_pecas=("estoque_disponivel_geral", "sum"),
            cobertura_media=("cobertura_meses", "mean"),
            itens_criticos=("status_cobertura", lambda x: (x.str.startswith("1.")).sum()),
            total_skus=("sku_id", "count")
        )
    )
    df_mapa["lat"] = df_mapa["regional"].map(lambda r: coordenadas_regionais.get(r, {}).get("lat", -23.55))
    df_mapa["lng"] = df_mapa["regional"].map(lambda r: coordenadas_regionais.get(r, {}).get("lng", -46.63))
    df_mapa["uf"] = df_mapa["regional"].map(lambda r: coordenadas_regionais.get(r, {}).get("uf", ""))

    dados_json = df.to_json(orient="records", force_ascii=False)
    mapa_json = df_mapa.to_json(orient="records", force_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S&OP Executive Analytics & Demand Simulator</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        :root {{
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --border: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --danger: #ef4444;
            --warning: #f59e0b;
            --success: #10b981;
            --info: #8b5cf6;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }}
        body {{ background: var(--bg-dark); color: var(--text-main); padding-bottom: 40px; }}
        header {{
            background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
            border-bottom: 1px solid var(--border);
            padding: 20px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }}
        header h1 {{ font-size: 1.35rem; font-weight: 600; color: var(--text-main); }}
        header p {{ font-size: 0.85rem; color: var(--text-muted); margin-top: 4px; }}
        .nav-tabs {{ display: flex; gap: 10px; }}
        .tab-btn {{
            background: var(--bg-card);
            color: var(--text-muted);
            border: 1px solid var(--border);
            padding: 10px 18px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.2s;
        }}
        .tab-btn:hover {{ border-color: var(--accent); color: var(--text-main); }}
        .tab-btn.active {{ background: var(--accent); color: #0f172a; border-color: var(--accent); }}
        .container {{ max-width: 1400px; margin: 24px auto; padding: 0 24px; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        /* Filtros e KPIs */
        .filters {{ display: flex; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }}
        select, input[type="number"], input[type="range"] {{
            background: var(--bg-card);
            color: var(--text-main);
            border: 1px solid var(--border);
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.9rem;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .kpi-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 18px;
        }}
        .kpi-title {{ font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }}
        .kpi-value {{ font-size: 1.7rem; font-weight: 700; margin-top: 8px; }}
        .kpi-sub {{ font-size: 0.8rem; color: var(--text-muted); margin-top: 6px; }}

        /* Grid de Gráficos e Tabelas */
        .charts-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }}
        @media (max-width: 900px) {{ .charts-grid {{ grid-template-columns: 1fr; }} }}
        .panel {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
        }}
        .panel h3 {{ font-size: 1rem; margin-bottom: 16px; color: var(--accent); }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
        th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ color: var(--text-muted); font-weight: 600; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }}
        .b-critico {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; }}
        .b-atencao {{ background: rgba(245, 158, 11, 0.2); color: #fcd34d; }}
        .b-saudavel {{ background: rgba(16, 185, 129, 0.2); color: #6ee7b7; }}
        .b-excesso {{ background: rgba(139, 92, 246, 0.2); color: #c4b5fd; }}

        /* Mapa */
        #map {{ height: 520px; width: 100%; border-radius: 10px; border: 1px solid var(--border); }}

        /* Simulador */
        .sim-grid {{ display: grid; grid-template-columns: 380px 1fr; gap: 24px; }}
        @media (max-width: 960px) {{ .sim-grid {{ grid-template-columns: 1fr; }} }}
        .form-group {{ margin-bottom: 16px; }}
        .form-group label {{ display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 6px; }}
        .form-group label span {{ color: var(--accent); font-weight: 700; }}
        .form-group input, .form-group select {{ width: 100%; }}
        .formula-box {{
            background: #0f172a;
            border-left: 3px solid var(--accent);
            padding: 12px;
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 16px;
            line-height: 1.5;
        }}
    </style>
</head>
<body>

<header>
    <div>
        <h1>📊 S&OP & Inventory Intelligence Dashboard</h1>
        <p>Pipeline Automatizado (SAP MM/S4HANA → Python/Parquet → Executive Analytics) | Autor: Peterson de Lima Cardoso</p>
    </div>
    <div class="nav-tabs">
        <button class="tab-btn active" onclick="openTab('gerencial', this)">1. Visão Gerencial</button>
        <button class="tab-btn" onclick="openTab('mapa-tab', this)">2. Mapa de Distribuição</button>
        <button class="tab-btn" onclick="openTab('simulador', this)">3. Simulador Matemático</button>
    </div>
</header>

<div class="container">

    <!-- ABA 1: GERENCIAL -->
    <div id="gerencial" class="tab-content active">
        <div class="filters">
            <select id="filtroRegional" onchange="atualizarGerencial()">
                <option value="TODAS">Todas as Regionais (SP & RS)</option>
            </select>
            <select id="filtroCategoria" onchange="atualizarGerencial()">
                <option value="TODAS">Todas as Categorias de Material</option>
            </select>
        </div>

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-title">Capital Imobilizado</div>
                <div class="kpi-value" id="kpiValor">R$ 0</div>
                <div class="kpi-sub">Depósitos Principais (E) + Auxiliares (Y/Z)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Cobertura Média Geral</div>
                <div class="kpi-value" id="kpiCobertura">0.0 m</div>
                <div class="kpi-sub">Meta Operacional S&OP: 2.0 meses</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Risco de Ruptura (< 1M)</div>
                <div class="kpi-value" style="color: var(--danger);" id="kpiCriticos">0</div>
                <div class="kpi-sub">SKUs exigindo compra emergencial</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Sobre-estoque (> 3M)</div>
                <div class="kpi-value" style="color: var(--info);" id="kpiExcesso">0</div>
                <div class="kpi-sub">Oportunidade de remanejamento</div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="panel">
                <h3>Distribuição de SKUs por Status de Cobertura</h3>
                <canvas id="chartStatus" height="140"></canvas>
            </div>
            <div class="panel">
                <h3>Valor em Estoque por Categoria (R$)</h3>
                <canvas id="chartCategoria" height="140"></canvas>
            </div>
        </div>

        <div class="panel">
            <h3>Top 12 Itens Mais Críticos (Menor Cobertura vs. Lead-Time)</h3>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>SKU</th>
                            <th>Categoria</th>
                            <th>Regional</th>
                            <th>Estoque Disp.</th>
                            <th>CMM (6m)</th>
                            <th>Lead-Time</th>
                            <th>Cobertura</th>
                            <th>Status S&OP</th>
                        </tr>
                    </thead>
                    <tbody id="tabelaCriticos"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- ABA 2: MAPA INTERATIVO -->
    <div id="mapa-tab" class="tab-content">
        <div class="charts-grid" style="grid-template-columns: 2fr 1fr;">
            <div class="panel">
                <h3>Distribuição Geográfica de Estoques e Criticidade (SP & RS)</h3>
                <div id="map"></div>
            </div>
            <div class="panel">
                <h3>Consolidado por Polo Logístico</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Regional</th>
                            <th>Capital</th>
                            <th>Cob. Média</th>
                            <th>Críticos</th>
                        </tr>
                    </thead>
                    <tbody id="tabelaMapa"></tbody>
                </table>
                <div class="formula-box">
                    <strong>Regra de Consolidação Aplicada:</strong><br>
                    Os saldos dos depósitos satélites e veiculares (<code>Y001</code> e <code>Z001</code>) são agregados automaticamente ao centro principal (<code>E001</code>) de cada regional antes do cálculo de autonomia.
                </div>
            </div>
        </div>
    </div>

    <!-- ABA 3: SIMULADOR MATEMÁTICO -->
    <div id="simulador" class="tab-content">
        <div class="sim-grid">
            <div class="panel">
                <h3>Parâmetros do Modelo de Reabastecimento</h3>
                <div class="form-group">
                    <label>Selecionar SKU da Base SAP:</label>
                    <select id="simSku" onchange="carregarSkuSimulador()"></select>
                </div>
                <div class="form-group">
                    <label>Consumo Médio Mensal Base (un): <span id="lblCmm">50</span></label>
                    <input type="number" id="simCmm" value="50" min="1" oninput="rodarSimulacao()">
                </div>
                <div class="form-group">
                    <label>Estoque Atual Disponível (un): <span id="lblEst">80</span></label>
                    <input type="number" id="simEst" value="80" min="0" oninput="rodarSimulacao()">
                </div>
                <div class="form-group">
                    <label>Meta de Cobertura Desejada (meses): <span id="lblMeta">2.0 m</span></label>
                    <input type="range" id="simMeta" min="0.5" max="6.0" step="0.5" value="2.0" oninput="rodarSimulacao()">
                </div>
                <div class="form-group">
                    <label>Lead-Time de Fornecimento (dias): <span id="lblLt">45 dias</span></label>
                    <input type="range" id="simLt" min="5" max="150" step="5" value="45" oninput="rodarSimulacao()">
                </div>
                <div class="form-group">
                    <label>Variação Projetada de Demanda (%): <span id="lblVar">+10%</span></label>
                    <input type="range" id="simVar" min="-40" max="100" step="5" value="10" oninput="rodarSimulacao()">
                </div>
                <div class="form-group">
                    <label>Nível de Serviço Desejado (Fator Z):</label>
                    <select id="simZ" onchange="rodarSimulacao()">
                        <option value="1.28">90% (Z = 1.28 - Baixa Criticidade)</option>
                        <option value="1.65" selected>95% (Z = 1.65 - Padrão Operacional)</option>
                        <option value="2.33">99% (Z = 2.33 - Infraestrutura Crítica)</option>
                    </select>
                </div>
            </div>

            <div>
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-title">Estoque de Segurança (ES)</div>
                        <div class="kpi-value" id="resEs">0 un</div>
                        <div class="kpi-sub">Buffer contra variabilidade e lead-time</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-title">Ponto de Pedido (ROP)</div>
                        <div class="kpi-value" style="color: var(--warning);" id="resRop">0 un</div>
                        <div class="kpi-sub">Gatilho mínimo para emissão de RC/PO</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-title">Necessidade Líquida Compra</div>
                        <div class="kpi-value" style="color: var(--accent);" id="resCompra">0 un</div>
                        <div class="kpi-sub" id="resCustoCompra">Investimento estimado: R$ 0</div>
                    </div>
                </div>

                <div class="panel">
                    <h3>Projeção de Saldo e Ponto de Ruptura (Horizonte 6 Meses)</h3>
                    <canvas id="chartSimulador" height="125"></canvas>
                    <div class="formula-box" id="diagnosticoSim"></div>
                </div>
            </div>
        </div>
    </div>

</div>

<script>
    const rawData = {dados_json};
    const mapData = {mapa_json};
    let chartStatus, chartCategoria, chartSimulador, mapInstance;

    function formatBRL(v) {{
        return v.toLocaleString('pt-BR', {{ style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }});
    }}

    function openTab(tabId, btn) {{
        document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
        btn.classList.add('active');
        if (tabId === 'mapa-tab') {{
            setTimeout(() => {{
                if (!mapInstance) initMap();
                else mapInstance.invalidateSize();
            }}, 100);
        }}
    }}

    // Inicializar Filtros e Select de SKUs
    function initControls() {{
        const regionais = [...new Set(rawData.map(d => d.regional))].sort();
        const categorias = [...new Set(rawData.map(d => d.categoria))].sort();

        const selReg = document.getElementById('filtroRegional');
        regionais.forEach(r => selReg.innerHTML += `<option value="${{r}}">${{r}}</option>`);

        const selCat = document.getElementById('filtroCategoria');
        categorias.forEach(c => selCat.innerHTML += `<option value="${{c}}">${{c}}</option>`);

        const selSku = document.getElementById('simSku');
        rawData.slice(0, 60).forEach((item, idx) => {{
            selSku.innerHTML += `<option value="${{idx}}">${{item.sku_id}} | ${{item.categoria}} (${{item.regional}})</option>`;
        }});
    }}

    function atualizarGerencial() {{
        const reg = document.getElementById('filtroRegional').value;
        const cat = document.getElementById('filtroCategoria').value;

        const filtrado = rawData.filter(d =>
            (reg === 'TODAS' || d.regional === reg) &&
            (cat === 'TODAS' || d.categoria === cat)
        );

        const totalValor = filtrado.reduce((acc, d) => acc + d.valor_estoque_total, 0);
        const cobMedia = filtrado.length ? (filtrado.reduce((acc, d) => acc + d.cobertura_meses, 0) / filtrado.length) : 0;
        const criticos = filtrado.filter(d => d.status_cobertura.startsWith('1.')).length;
        const excesso = filtrado.filter(d => d.status_cobertura.startsWith('4.')).length;

        document.getElementById('kpiValor').innerText = formatBRL(totalValor);
        document.getElementById('kpiCobertura').innerText = cobMedia.toFixed(2) + ' meses';
        document.getElementById('kpiCriticos').innerText = criticos + ' SKUs';
        document.getElementById('kpiExcesso').innerText = excesso + ' SKUs';

        // Gráfico 1: Status
        const statusLabels = ['1. Crítico (Ruptura Iminente)', '2. Atenção (< Meta 2M)', '3. Saudável (Na Meta)', '4. Excesso (> 3M)'];
        const statusCounts = statusLabels.map(s => filtrado.filter(d => d.status_cobertura === s).length);

        if (chartStatus) chartStatus.destroy();
        chartStatus = new Chart(document.getElementById('chartStatus'), {{
            type: 'doughnut',
            data: {{
                labels: ['Crítico (<1M)', 'Atenção (1-2M)', 'Saudável (2-3M)', 'Excesso (>3M)'],
                datasets: [{{ data: statusCounts, backgroundColor: ['#ef4444', '#f59e0b', '#10b981', '#8b5cf6'], borderWidth: 0 }}]
            }},
            options: {{ plugins: {{ legend: {{ position: 'right', labels: {{ color: '#f8fafc' }} }} }} }}
        }});

        // Gráfico 2: Valor por Categoria
        const cats = [...new Set(filtrado.map(d => d.categoria))];
        const catVals = cats.map(c => filtrado.filter(d => d.categoria === c).reduce((a, b) => a + b.valor_estoque_total, 0));

        if (chartCategoria) chartCategoria.destroy();
        chartCategoria = new Chart(document.getElementById('chartCategoria'), {{
            type: 'bar',
            data: {{
                labels: cats,
                datasets: [{{ label: 'Valor em Estoque (R$)', data: catVals, backgroundColor: '#38bdf8', borderRadius: 6 }}]
            }},
            options: {{
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }},
                    y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }} }}
                }}
            }}
        }});

        // Tabela Top 12 Críticos
        const topCriticos = [...filtrado].sort((a, b) => a.cobertura_meses - b.cobertura_meses).slice(0, 12);
        const tbody = document.getElementById('tabelaCriticos');
        tbody.innerHTML = '';
        topCriticos.forEach(item => {{
            let badgeClass = 'b-saudavel';
            if (item.status_cobertura.startsWith('1.')) badgeClass = 'b-critico';
            else if (item.status_cobertura.startsWith('2.')) badgeClass = 'b-atencao';
            else if (item.status_cobertura.startsWith('4.')) badgeClass = 'b-excesso';

            tbody.innerHTML += `<tr>
                <td><strong>${{item.sku_id}}</strong></td>
                <td>${{item.categoria}}</td>
                <td>${{item.regional}}</td>
                <td>${{item.estoque_disponivel_geral}} un</td>
                <td>${{item.cmm_6m}} un/mês</td>
                <td>${{item.lead_time_dias}} dias</td>
                <td><strong>${{item.cobertura_meses}} m</strong></td>
                <td><span class="badge ${{badgeClass}}">${{item.status_cobertura}}</span></td>
            </tr>`;
        }});
    }}

    // Aba 2: Mapa Interativo
    function initMap() {{
        mapInstance = L.map('map').setView([-25.8, -49.5], 5);
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '© OpenStreetMap © CARTO'
        }}).addTo(mapInstance);

        const tbodyMapa = document.getElementById('tabelaMapa');
        tbodyMapa.innerHTML = '';

        mapData.forEach(loc => {{
            const cor = loc.itens_criticos > 10 ? '#ef4444' : '#38bdf8';
            L.circleMarker([loc.lat, loc.lng], {{
                radius: Math.max(12, Math.sqrt(loc.valor_total) / 75),
                fillColor: cor,
                color: '#ffffff',
                weight: 1.5,
                opacity: 1,
                fillOpacity: 0.75
            }}).addTo(mapInstance).bindPopup(`
                <div style="color:#0f172a; min-width:180px;">
                    <strong>Regional ${{loc.regional}} (${{loc.uf}})</strong><br><hr style="margin:4px 0;">
                    Capital Alocado: <b>${{formatBRL(loc.valor_total)}}</b><br>
                    Volume Total: <b>${{loc.estoque_pecas}} un</b><br>
                    Cobertura Média: <b>${{loc.cobertura_media.toFixed(2)}} meses</b><br>
                    SKUs Críticos: <b style="color:#dc2626;">${{loc.itens_criticos}}</b>
                </div>
            `);

            tbodyMapa.innerHTML += `<tr>
                <td><strong>${{loc.regional}}</strong> (${{loc.uf}})</td>
                <td>${{formatBRL(loc.valor_total)}}</td>
                <td>${{loc.cobertura_media.toFixed(2)}} m</td>
                <td style="color:var(--danger); font-weight:bold;">${{loc.itens_criticos}}</td>
            </tr>`;
        }});
    }}

    // Aba 3: Simulador Matemático
    let custoAtualSku = 850;
    function carregarSkuSimulador() {{
        const idx = document.getElementById('simSku').value;
        const item = rawData[idx];
        document.getElementById('simCmm').value = Math.round(item.cmm_6m);
        document.getElementById('simEst').value = item.estoque_disponivel_geral;
        document.getElementById('simLt').value = item.lead_time_dias;
        custoAtualSku = item.custo_unitario;
        rodarSimulacao();
    }}

    function rodarSimulacao() {{
        const cmmBase = parseFloat(document.getElementById('simCmm').value) || 1;
        const estAtual = parseFloat(document.getElementById('simEst').value) || 0;
        const metaMeses = parseFloat(document.getElementById('simMeta').value);
        const ltDias = parseFloat(document.getElementById('simLt').value);
        const varPct = parseFloat(document.getElementById('simVar').value);
        const zScore = parseFloat(document.getElementById('simZ').value);

        document.getElementById('lblCmm').innerText = cmmBase;
        document.getElementById('lblEst').innerText = estAtual;
        document.getElementById('lblMeta').innerText = metaMeses.toFixed(1) + ' m';
        document.getElementById('lblLt').innerText = ltDias + ' dias';
        document.getElementById('lblVar').innerText = (varPct >= 0 ? '+' : '') + varPct + '%';

        // Modelos Matemáticos de Engenharia de Produção / Supply Chain
        const cmmProjetado = cmmBase * (1 + varPct / 100);
        const desvioPadraoMensal = cmmProjetado * 0.22; // Coeficiente de variação empírico (22%)
        const ltMeses = ltDias / 30.0;

        // Estoque de Segurança: ES = Z * sigma_d * sqrt(LT)
        const estoqueSeguranca = Math.ceil(zScore * desvioPadraoMensal * Math.sqrt(ltMeses));
        // Ponto de Pedido: ROP = (Demanda * LT) + ES
        const pontoPedido = Math.ceil((cmmProjetado * ltMeses) + estoqueSeguranca);
        // Estoque Alvo: (Demanda * Meta_Cobertura) + ES
        const estoqueAlvo = Math.ceil((cmmProjetado * metaMeses) + estoqueSeguranca);
        // Necessidade Líquida de Compra
        const necessidadeCompra = Math.max(0, estoqueAlvo - estAtual);

        document.getElementById('resEs').innerText = estoqueSeguranca + ' un';
        document.getElementById('resRop').innerText = pontoPedido + ' un';
        document.getElementById('resCompra').innerText = necessidadeCompra + ' un';
        document.getElementById('resCustoCompra').innerText = 'Investimento estimado: ' + formatBRL(necessidadeCompra * custoAtualSku);

        // Projeção de Consumo sem Reabastecimento vs. Com Reabastecimento no Lead-Time
        const mesesLabels = ['Atual', 'Mês 1', 'Mês 2', 'Mês 3', 'Mês 4', 'Mês 5', 'Mês 6'];
        const serieSemCompra = [];
        const serieComCompra = [];
        const mesChegadaPedido = Math.max(1, Math.round(ltMeses));

        for (let m = 0; m <= 6; m++) {{
            const saldoSem = Math.max(0, Math.round(estAtual - (cmmProjetado * m)));
            serieSemCompra.push(saldoSem);

            let saldoCom = estAtual - (cmmProjetado * m);
            if (m >= mesChegadaPedido) saldoCom += necessidadeCompra;
            serieComCompra.push(Math.max(0, Math.round(saldoCom)));
        }}

        if (chartSimulador) chartSimulador.destroy();
        chartSimulador = new Chart(document.getElementById('chartSimulador'), {{
            type: 'line',
            data: {{
                labels: mesesLabels,
                datasets: [
                    {{
                        label: 'Saldo Sem Reposição (Inércia)',
                        data: serieSemCompra,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.3,
                        fill: true
                    }},
                    {{
                        label: 'Saldo Com Reposição no Lead-Time',
                        data: serieComCompra,
                        borderColor: '#10b981',
                        tension: 0.3,
                        borderWidth: 3
                    }},
                    {{
                        label: 'Ponto de Pedido (ROP)',
                        data: Array(7).fill(pontoPedido),
                        borderColor: '#f59e0b',
                        borderDash: [6, 6],
                        pointRadius: 0
                    }}
                ]
            }},
            options: {{
                scales: {{
                    x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }} }},
                    y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }} }}
                }},
                plugins: {{ legend: {{ labels: {{ color: '#f8fafc' }} }} }}
            }}
        }});

        const autonomiaAtual = (estAtual / cmmProjetado).toFixed(2);
        const statusGatilho = estAtual <= pontoPedido
            ? '⚠️ <strong>GATILHO ACIONADO:</strong> O estoque atual já está igual ou abaixo do Ponto de Pedido (ROP). Emitir Requisição de Compra imediatamente.'
            : '✅ <strong>POSIÇÃO CONTROLADA:</strong> O saldo atual cobre o consumo durante o lead-time sem atingir o Estoque de Segurança.';

        document.getElementById('diagnosticoSim').innerHTML = `
            <strong>Memória de Cálculo S&OP:</strong> Demanda Ajustada = <code>${{cmmProjetado.toFixed(1)}} un/mês</code> | Autonomia Real = <code>${{autonomiaAtual}} meses</code> | Estoque Alvo = <code>${{estoqueAlvo}} un</code>.<br>
            ${{statusGatilho}}
        `;
    }}

    initControls();
    atualizarGerencial();
    carregarSkuSimulador();
</script>
</body>
</html>
"""

    output_file = docs_dir / "index.html"
    output_file.write_text(html_content, encoding="utf-8")
    print(f"✅ Dashboard HTML interativo gerado com sucesso em: {output_file}")

if __name__ == "__main__":
    gerar_dashboard_html()