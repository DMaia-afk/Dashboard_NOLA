// insights.js - renderização dos cards agregados/anomalias

const INSIGHTS_CARDS = [
    {
        id: 'card-retencao-clientes',
        name: 'Retenção de Clientes',
        api: '/api/card-retencao-clientes/',
        render: function(data) {
            const lojaRetencao = window.retencaoLoja || '';
            const mesInicio = window.retencaoMesInicio || '';
            const mesFim = window.retencaoMesFim || '';
            const filtroForm = `
                <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0;">
                    <label for="retencao-loja" style="flex:0 0 80px;min-width:120px;">Loja:</label>
                    <input id="retencao-loja" list="lojas-list" value="${lojaRetencao}" style="flex:1;padding:6px;border:1px solid #e6e6e6;border-radius:4px;">
                    <label for="retencao-mes-inicio" style="flex:0 0 auto;min-width:120px;">Mês Inicial:</label>
                    <input type="month" id="retencao-mes-inicio" name="mes_inicio" value="${mesInicio}" style="flex:0 0 160px;padding:6px;border:1px solid #e6e6e6;border-radius:4px;">
                    <label for="retencao-mes-fim" style="flex:0 0 auto;min-width:120px;">Mês Final:</label>
                    <input type="month" id="retencao-mes-fim" name="mes_fim" value="${mesFim}" style="flex:0 0 160px;padding:6px;border:1px solid #e6e6e6;border-radius:4px;">
                    <button type="button" id="btn-retencao-filtrar" class="btn-primary" style="flex:0 0 auto;padding:8px 10px;border-radius:6px;margin-left:6px;"><i class="fas fa-filter"></i> Filtrar Retenção</button>
                </div>`;

            if (data && data.info) {
                return `<div id="card-retencao-clientes" class="widget-card kpi-card">
                    <div class="kpi-title"><span>Retenção de Clientes</span></div>
                    ${filtroForm}
                    <div class="kpi-subtitle" style="color:#007bff;padding:16px 0;">${data.info}</div>
                </div>`;
            }

            if (data && data.matriz && Array.isArray(data.matriz) && data.matriz.length > 1) {
                const rows = data.matriz.slice(1);
                let list = `<ul class="retencao-list" style="list-style:none;padding:0;margin:0;">`;
                list += rows.map(r => `
                    <li style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #eee;min-width:0;">
                        <div style="flex:2;min-width:0;font-weight:600;color:#1976d2;word-break:break-word;">${r[0]}</div>
                        <div style="flex:1;min-width:80px;text-align:center;color:#333;">${r[1]}</div>
                        <div style="flex:1;min-width:80px;text-align:center;color:#007bff;">${r[4]}%</div>
                        <div style="flex:1;min-width:120px;text-align:right;color:#888;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${r[2]} coorte / ${r[3]} ativos</div>
                    </li>
                `).join("");
                list += `</ul>`;
                const headerHtml = `<div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;padding:8px 0 4px 0;font-weight:700;color:#444;border-bottom:2px solid #1976d2;">
                    <div style="flex:2;min-width:0;">Loja</div>
                    <div style="flex:1;min-width:80px;text-align:center;">Mês</div>
                    <div style="flex:1;min-width:80px;text-align:center;">Taxa de Retenção (%)</div>
                    <div style="flex:1;min-width:120px;text-align:right;">Coorte / Ativos</div>
                </div>`;
                return `<div id="card-retencao-clientes" class="widget-card table-card">
                        <div class="kpi-title"><span>Retenção de Clientes</span></div>
                        ${filtroForm}
                        <div style="margin-top:8px;max-height:320px;overflow:auto;">${headerHtml}${list}</div>
                    </div>`;
            }

            const total = (data && data.clientes_total) || 0;
            const retidos = (data && data.clientes_retidos) || 0;
            const taxa = (data && data.taxa_retencao) || 0;
            return `<div id="card-retencao-clientes" class="widget-card kpi-card">
                    <div class="kpi-title"><span>Retenção de Clientes</span></div>
                    ${filtroForm}
                    <div class="kpi-subtitle" style="max-width:100%;overflow:hidden;word-break:break-word;">${retidos} de ${total} clientes retornaram (${taxa}%)<br><span style="color:#666;font-size:0.95em;">A taxa considera clientes que compraram mais de uma vez em datas diferentes.</span></div>
                </div>`;
        },
        init: function(root, data) {
            try {
                const datalist = document.getElementById('lojas-list');
                if (datalist && datalist.children.length === 0) {
                    fetch('/api/lojas/')
                        .then(r => r.json())
                        .then(json => {
                            const list = Array.isArray(json) ? json : (json && Array.isArray(json.lojas) ? json.lojas : []);
                            if (Array.isArray(list) && list.length > 0) {
                                datalist.innerHTML = list.map(l => `<option value="${l}"></option>`).join('');
                            }
                        }).catch(() => {});
                }

                const btn = root.querySelector('#btn-retencao-filtrar');
                if (btn) {
                    btn.addEventListener('click', function() {
                        const loja = root.querySelector('#retencao-loja')?.value || '';
                        const mesInicio = root.querySelector('#retencao-mes-inicio')?.value || '';
                        const mesFim = root.querySelector('#retencao-mes-fim')?.value || '';
                        window.retencaoLoja = loja;
                        window.retencaoMesInicio = mesInicio;
                        window.retencaoMesFim = mesFim;

                        const globalFilters = (typeof getGlobalFilters === 'function') ? getGlobalFilters() : {};
                        const merged = Object.assign({}, globalFilters);
                        if (loja) merged.loja = loja;
                        if (mesInicio) merged.mes_inicio = mesInicio;
                        if (mesFim) merged.mes_fim = mesFim;

                        const url = (typeof appendQueryParams === 'function') ? appendQueryParams(this.api, merged) : `${this.api}?${new URLSearchParams(merged).toString()}`;

                        fetch(url)
                            .then(res => res.json())
                            .then(newData => {
                                const parent = root.parentElement;
                                if (!parent) return;
                                parent.insertAdjacentHTML('beforeend', this.render(newData));
                                try { if (typeof window.attachCardControls === 'function') window.attachCardControls(this.id); if (typeof window.initSortables === 'function') window.initSortables(); } catch(e) { }
                                root.remove();
                                const newRoot = document.getElementById(this.id);
                                if (this.init && newRoot) this.init(newRoot, newData);
                            }).catch(() => {
                                const parent = root.parentElement;
                                if (!parent) return;
                                parent.insertAdjacentHTML('beforeend', this.render({}));
                                try { if (typeof window.attachCardControls === 'function') window.attachCardControls(this.id); if (typeof window.initSortables === 'function') window.initSortables(); } catch(e) { }
                                root.remove();
                                const newRoot = document.getElementById(this.id);
                                if (this.init && newRoot) this.init(newRoot, {});
                            });
                    }.bind(this));
                }
            } catch (err) {
                console.error('Erro init retencao:', err);
            }
        }
    },
    {
        id: 'card-anomalias-temporais',
        name: 'Anomalias Temporais',
        api: '/api/card-anomalias-temporais/',
        render: function(data) {
            const alerts = Array.isArray(data.alertas) ? data.alertas : [];
            const pageSize = 5;
            const page = Number(data.page || 1);
            const total = Number(typeof data.total !== 'undefined' ? data.total : alerts.length);

            // Always perform client-side slicing to ensure we show at most `pageSize` items per page.
            const start = (page - 1) * pageSize;
            const pageAlerts = alerts.slice(start, start + pageSize);
            const rows = pageAlerts.map(a => {
                const lojas = a.loja ? (Array.isArray(a.loja) ? a.loja.join(', ') : a.loja) : '';
                const tipo = a.tipo || '';
                const dia = a.dia || '';
                const vendas = (typeof a.vendas !== 'undefined') ? a.vendas : '';
                return [ `${dia} — ${tipo}`, lojas, vendas ];
            });
            return renderPaginatedListCard('card-anomalias-temporais', 'Anomalias Temporais', ['Data / Tipo', 'Loja(s)', 'Vendas'], rows, page, total, 'changeAnomaliasTemporaisPage', pageSize);
        },
        init: function(root, data) {
            // noop for now; pagination buttons call global changeAnomaliasTemporaisPage
        }
    },
    {
    id: 'card-crescimento-loja',
    name: 'Crescimento de Loja',
    api: '/api/card-crescimento-loja/',
    // Backend now returns a richer payload: { monthly: [...], chart: { labels, revenue, sales }, series: { combined_pct } }
    // O backend agora retorna um payload mais rico: { monthly: [...], chart: { labels, revenue, sales }, series: { combined_pct } }
    // Prefer plotting the combined growth series (percent) when available; fall back to revenue series.
    // Prefere plotar a série de crescimento combinado (porcentagem) quando disponível; recai na série de receita.
    render: data => {
        const labels = (data && data.chart && Array.isArray(data.chart.labels)) ? data.chart.labels : (Array.isArray(data.monthly) ? data.monthly.map(m=>m.mes) : []);
        let combined = (data && data.series && Array.isArray(data.series.combined_pct)) ? data.series.combined_pct : null;
        const revenue = (data && data.chart && Array.isArray(data.chart.revenue)) ? data.chart.revenue : (Array.isArray(data.monthly) ? data.monthly.map(m=>m.faturamento) : []);

        // Fallback: if combined missing or all null/undefined, use revenue as fallback so the chart shows something
        // Fallback: se combinado estiver faltando ou todos nulos/indefinidos, use receita como fallback para que o gráfico mostre algo
        const allNull = !combined || combined.length === 0 || combined.every(v => v === null || typeof v === 'undefined');
        if (allNull) {
            combined = revenue || [];
        }

        // If still no usable data, show an informative empty-card message instead of an empty canvas
        // Se ainda não houver dados utilizáveis, mostre uma mensagem informativa de cartão vazio em vez de um canvas vazio
        const usable = Array.isArray(labels) && labels.length > 0 && Array.isArray(combined) && combined.length > 0;
        if (!usable) {
            return `<div id="card-crescimento-loja" class="widget-card chart-card"><div class="kpi-title">Crescimento de Loja</div><div style="color:#666;padding:12px;">Sem dados suficientes para desenhar o gráfico. Ajuste os filtros ou selecione outra loja/período.</div></div>`;
        }

    // Render as column (bar) chart instead of line chart
    // Renderizar como gráfico de coluna (barra) em vez de gráfico de linha
    return renderBarChartCard('card-crescimento-loja', 'Crescimento de Loja', labels, combined, 'Crescimento');
    },
    init: function(root, data) {
        try {
            const canvas = root.querySelector('canvas');
            if (!canvas) return;
            const labels = (data && data.chart && Array.isArray(data.chart.labels)) ? data.chart.labels : (Array.isArray(data.monthly) ? data.monthly.map(m=>m.mes) : []);
            let combined = (data && data.series && Array.isArray(data.series.combined_pct)) ? data.series.combined_pct : null;
            const revenue = (data && data.chart && Array.isArray(data.chart.revenue)) ? data.chart.revenue : (Array.isArray(data.monthly) ? data.monthly.map(m=>m.faturamento) : []);
            const allNull = !combined || combined.length === 0 || combined.every(v => v === null || typeof v === 'undefined');
            if (allNull) combined = revenue || [];

            // If still no data, display placeholder message inside the card
            if (!Array.isArray(labels) || labels.length === 0 || !Array.isArray(combined) || combined.length === 0) {
                const placeholder = root.querySelector('.kpi-title');
                if (placeholder) {
                    placeholder.insertAdjacentHTML('afterend', `<div class="kpi-subtitle" style="color:#666;padding:12px;">Sem dados suficientes para desenhar o gráfico.</div>`);
                }
                return;
            }

            // Ensure combined values are numbers or null (Chart.js needs numeric values)
            try {
                combined = combined.map(v => (v === null || typeof v === 'undefined') ? null : Number(v));
            } catch (e) {
                // keep as-is if map fails
            }

            // Render as bar chart (columns)
            try {
                // Ensure combined values are numeric
                const numeric = combined.map(v => (v === null || typeof v === 'undefined') ? null : Number(v));
                createBarChart(canvas, labels, numeric, 'Crescimento');
            } catch (e) {
                // fallback to line chart if bar creation fails
                try { createLineChart(canvas, labels, combined, 'Crescimento', { datasetOptions: { spanGaps: true, tension: 0.2, pointRadius: 3 } }); } catch (e2) { console.error('init crescimento loja fallback failed', e2); }
            }
        } catch (e) { console.error('init crescimento loja', e); }
    }
    },
    {
        id: 'card-produto-sazonal',
        name: 'Produto Sazonal',
        api: '/api/card-produto-sazonal/',
        render: function(data) {
                // Render Produto Sazonal as a simple list (no chart)
                const analysisMsg = (data && data.analysis && data.analysis.message) ? `<div class="kpi-subtitle" style="color:#333;margin-top:6px;font-size:0.95em;">${data.analysis.message}</div>` : '';
                const listHtml = `<div class="sazonal-list" style="margin-top:8px;"></div>`;
                return `<div id="${this.id}" class="widget-card list-card">
                    <div class="kpi-title">Produto Sazonal</div>
                    ${analysisMsg}
                    ${listHtml}
                </div>`;
            },
            init: function(root, data) {
                try {
                    // Prefer holiday-driven list when present
                    // Prefere lista orientada por feriados quando presente
                    const container = root.querySelector('.sazonal-list');
                    if (!container) return;

                    const holidayList = Array.isArray(data.holiday_top_products) ? data.holiday_top_products : [];
                    const legacyTop = Array.isArray(data.top_products) ? data.top_products : (Array.isArray(data.topProducts) ? data.topProducts : []);
                    // limit the number of items shown (default 10). Backend can override by passing data.max_items
                    // limita o número de itens mostrados (padrão 10). O backend pode substituir passando data.max_items
                    const maxItems = (data && typeof data.max_items !== 'undefined') ? Number(data.max_items) : 10;
                    const listToShow = (holidayList && holidayList.length > 0) ? holidayList : legacyTop;

                    if (!listToShow || listToShow.length === 0) {
                        container.innerHTML = `<div style="color:#666;font-size:0.95em;">Nenhum produto no período selecionado.</div>`;
                        return;
                    }
                    // Apply limit
                    const sliced = listToShow.slice(0, maxItems);

                    const currency = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

                    // Build simple list format: product name | holiday_qty (baseline_qty) | receita_holiday | lift%
                    // Construir formato de lista simples: nome do produto | holiday_qty (baseline_qty) | receita_holiday | lift%
                    const items = sliced.map(item => {
                        // Support both holiday_top_products shape and legacy top_products
                    // Suporta tanto a forma holiday_top_products quanto top_products legado
                        const nome = item.produto || item.produto || item.produto || item.produto;
                        const quantidade_h = item.quantidade_holiday !== undefined ? Number(item.quantidade_holiday) : (item.quantidade !== undefined ? Number(item.quantidade) : 0);
                        const quantidade_b = item.quantidade_baseline !== undefined ? Number(item.quantidade_baseline) : null;
                        const receita_h = item.receita_holiday !== undefined ? Number(item.receita_holiday) : (item.receita !== undefined ? Number(item.receita) : 0);
                        const lift = item.lift_pct !== undefined ? item.lift_pct : null;

                        const liftHtml = (lift === null || typeof lift === 'undefined') ? '' : `<span style="font-weight:700;color:${lift>0? '#1b5e20':'#b71c1c'};margin-left:8px;">${lift>0?'+':''}${Number(lift).toFixed(2)}%</span>`;
                        const baselineHtml = (quantidade_b === null) ? '' : `<span style="color:#777;margin-left:6px;">(baseline ${quantidade_b})</span>`;

                        return `<li style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f0f0f0;align-items:center;">
                                    <div style="flex:1;min-width:0;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;font-weight:600;color:#1976d2;">${nome}</div>
                                    <div style="flex:0 0 220px;text-align:right;color:#333;">${quantidade_h} ${baselineHtml} <span style="margin-left:10px;color:#666;">${currency.format(receita_h)}</span>${liftHtml}</div>
                                </li>`;
                    }).join('');

                    const title = (listToShow === holidayList && holidayList && holidayList.length>0) ? `Produtos em alta no(s) feriado(s) — top ${sliced.length}` : `Top produtos — top ${sliced.length}`;
                    container.innerHTML = `<div style="margin-top:8px;font-weight:700;color:#444;margin-bottom:6px;">${title}</div><ul style="list-style:none;padding:0;margin:0;">${items}</ul>`;

                } catch (e) { console.error('init produto sazonal', e); }
            }
    },
    // 'Ranking Global de Produtos' removed — card deprecated and hidden from insights
    {
    id: 'card-mix-produtos',
    name: 'Mix de Produtos',
    api: '/api/card-mix-produtos/',
        render: data => {
            const columns = ['Combinação', 'Quantidade'];
            const rows = (data.combos || []).map(c => [c.combinacao, c.quantidade]);
            return renderTableCard('card-mix-produtos', 'Mix de Produtos', columns, rows);
        }
    },
    
];

function renderAlertCard(id, title, alerts) {
    // Normalize alerts array
    const list = Array.isArray(alerts) ? alerts : [];
    if (list.length === 0) {
        return `<div id="${id}" class="widget-card alert-card">
            <div class="kpi-title">${title}</div>
            <div style="color:#666;padding:12px 0;font-size:0.95em;">Nenhuma anomalia identificada no período.</div>
        </div>`;
    }

    const itemsHtml = list.map(a => {
        const lojas = a.loja ? (Array.isArray(a.loja) ? a.loja.join(', ') : a.loja) : '';
        const tipoLabel = a.tipo ? a.tipo : '';
        const dia = a.dia ? a.dia : '';
        const vendas = (typeof a.vendas !== 'undefined') ? a.vendas : '';
        return `
            <li style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #eee;min-width:0;">
                <div style="flex:2;min-width:0;font-weight:600;color:#1976d2;word-break:break-word;">${dia} — ${tipoLabel}</div>
                <div style="flex:1;min-width:140px;text-align:center;color:#333;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${lojas}</div>
                <div style="flex:0 0 120px;text-align:right;color:#e65100;">${vendas} vendas</div>
            </li>`;
    }).join('');

    return `<div id="${id}" class="widget-card alert-card">
           <div class="kpi-title">${title}</div>
           <div style="margin-top:8px;max-height:320px;overflow:auto;"><ul style="list-style:none;padding:0;margin:0;">${itemsHtml}</ul></div>
    </div>`;
}

function renderTableCard(id, title, columns, rows) {
    const header = columns.map(c => `<th scope="col">${c}</th>`).join("");
    const body = rows.map(r => `<tr>${r.map(cell => `<td>${cell}</td>`).join("")}</tr>`).join("");
    return `<div id="${id}" class="widget-card table-card">
        <div class="kpi-title">${title}</div>
        <div class="table-wrapper">
            <table class="compact-table" role="table">
                <thead><tr>${header}</tr></thead>
                <tbody>${body}</tbody>
            </table>
        </div>
    </div>`;
}

function renderBarChartCard(id, title, labels, data, label) {
    return `<div id="${id}" class="widget-card chart-card">
        <div class="kpi-title">${title}</div>
        <canvas id="${id}-chart"></canvas>
    </div>`;
}

function renderLineChartCard(id, title, labels, data, label) {
    return `<div id="${id}" class="widget-card chart-card">
        <div class="kpi-title">${title}</div>
        <canvas id="${id}-chart"></canvas>
    </div>`;
}

// helpers para criar charts de forma explícita quando o canvas já está no DOM
function createBarChart(canvas, labels, data, label) {
    try {
        const ctx = canvas.getContext('2d');
        // destroy existing chart instance on this canvas if present (prevents "Canvas is already in use")
        try {
            if (typeof Chart.getChart === 'function') {
                const existing = Chart.getChart(canvas);
                if (existing && typeof existing.destroy === 'function') existing.destroy();
            }
        } catch (e) { /* non-fatal */ }
        new Chart(ctx, {
            type: 'bar',
            data: { labels: labels, datasets: [{ label: label, data: data, backgroundColor: '#007bff' }] },
            options: { responsive: true, plugins: { legend: { display: false } } }
        });
    } catch (e) { console.error('createBarChart', e); }
}

function createLineChart(canvas, labels, data, label, opts) {
    try {
        const ctx = canvas.getContext('2d');
        const options = opts || {};
        const isPercent = options.percent === true;

        const chartOptions = {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {}
        };

        if (isPercent) {
            chartOptions.scales = {
                y: {
                    ticks: {
                        callback: function(value) { return value + '%'; }
                    }
                }
            };
            chartOptions.plugins.tooltip = {
                callbacks: {
                    label: function(context) {
                        const v = context.parsed.y;
                        return (v === null || typeof v === 'undefined') ? 'N/A' : (v + '%');
                    }
                }
            };
        }

        // destroy existing chart instance on this canvas if present
        try {
            if (typeof Chart.getChart === 'function') {
                const existing = Chart.getChart(canvas);
                if (existing && typeof existing.destroy === 'function') existing.destroy();
            }
        } catch (e) { /* non-fatal */ }

        const datasetOpts = Object.assign({ label: label, data: data, borderColor: '#007bff', fill: false }, options.datasetOptions || {});
        new Chart(ctx, {
            type: 'line',
            data: { labels: labels, datasets: [datasetOpts] },
            options: chartOptions
        });
    } catch (e) { console.error('createLineChart', e); }
}

function renderPaginatedListCard(id, title, columns, rows, page, total, onPageChange, pageSize = 5) {
    const header = columns.map(c => `<th scope="col">${c}</th>`).join("");
    const body = rows.map(r => `<tr>${r.map(cell => `<td>${cell}</td>`).join("")}</tr>`).join("");
    // pageSize default is 5 for backward compatibility; pass 6 for anomalies when needed
    let totalPages = Math.max(1, Math.ceil(total / pageSize));
    let pagination = '';
    if (totalPages > 1) {
        pagination = `<div class="pagination-controls" role="navigation" aria-label="pagination-${id}">
            <button class="page-btn" ${page <= 1 ? 'disabled' : ''} onclick="window.${onPageChange}(${page-1})">‹ Anterior</button>
            <span class="page-info">Página ${page} de ${totalPages}</span>
            <button class="page-btn" ${page >= totalPages ? 'disabled' : ''} onclick="window.${onPageChange}(${page+1})">Próxima ›</button>
        </div>`;
    }
    return `<div id="${id}" class="widget-card table-card">
        <div class="kpi-title">${title}</div>
        <div class="table-wrapper">
            <table class="compact-table" role="table">
                <thead><tr>${header}</tr></thead>
                <tbody>${body}</tbody>
            </table>
        </div>
        ${pagination}
    </div>`;
}

// Exemplo para um card de lista paginada
function renderClientesFrequentesCard(data) {
    const columns = ['Cliente', 'Compras', 'Ticket Médio'];
    const rows = (data.top_clientes || []).map(c => [c.cliente, c.compras, `R$ ${c.ticket_medio.toLocaleString('pt-BR', {minimumFractionDigits:2})}`]);
    return renderPaginatedListCard('card-clientes-frequentes', 'Clientes Frequentes', columns, rows, data.page, data.total, 'changeClientesFrequentesPage');
}

window.changeClientesFrequentesPage = function(page) {
    fetch(`/api/card-clientes-frequentes/?page=${page}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('card-clientes-frequentes').outerHTML = renderClientesFrequentesCard(data);
        });
};

window.changeAnomaliasTemporaisPage = function(page) {
    fetch(`/api/card-anomalias-temporais/?page=${page}`)
        .then(res => res.json())
        .then(data => {
            try {
                const cardDef = (window.INSIGHTS_CARDS || []).find(c => c.id === 'card-anomalias-temporais');
                const alerts = Array.isArray(data.alertas) ? data.alertas : [];
                const pageSize = 5;

                // If backend provides explicit pagination (page/total), use cardDef.render directly
                if ((typeof data.page !== 'undefined') && (typeof data.total !== 'undefined')) {
                    if (cardDef) {
                        document.getElementById('card-anomalias-temporais').outerHTML = cardDef.render(data);
                        const newRoot = document.getElementById('card-anomalias-temporais');
                        if (cardDef.init && newRoot) cardDef.init(newRoot, data);
                        return;
                    }
                    // fallback render with provided values
                    document.getElementById('card-anomalias-temporais').outerHTML = renderPaginatedListCard('card-anomalias-temporais', 'Anomalias Temporais', ['Data / Tipo', 'Loja(s)', 'Vendas'], alerts.map(a => [ `${a.dia} — ${a.tipo}`, Array.isArray(a.loja)?a.loja.join(', '):(a.loja||''), a.vendas || '' ]), data.page || 1, data.total || alerts.length, 'changeAnomaliasTemporaisPage', pageSize);
                    return;
                }

                // Backend returned full list without pagination: do client-side paging
                const total = alerts.length;
                const totalPages = Math.max(1, Math.ceil(total / pageSize));
                const currentPage = Math.min(Math.max(1, Number(page || 1)), totalPages);
                const start = (currentPage - 1) * pageSize;
                const pageAlerts = alerts.slice(start, start + pageSize);
                const rows = pageAlerts.map(a => [ `${a.dia} — ${a.tipo}`, Array.isArray(a.loja)?a.loja.join(', '):(a.loja||''), a.vendas || '' ]);
                document.getElementById('card-anomalias-temporais').outerHTML = renderPaginatedListCard('card-anomalias-temporais', 'Anomalias Temporais', ['Data / Tipo', 'Loja(s)', 'Vendas'], rows, currentPage, total, 'changeAnomaliasTemporaisPage', pageSize);

            } catch (e) {
                console.error('changeAnomaliasTemporaisPage error', e);
            }
        }).catch(err => {
            console.error('fetch error for anomalias temporais page', err);
        });
};

async function fetchAndRenderInsightsCards() {
    // Prefer rendering insights into the dashboard grid when available so
    // Prefere renderizar insights na grade do dashboard quando disponível para que
    // insight cards appear on the main dashboard; fall back to the
    // original insights grid when not present.
    const grid = document.getElementById('insights-grid') || document.getElementById('dashboard-grid');
    if (!grid) return;
    // limpar antes de inserir (evita duplicação em reloads)
    grid.innerHTML = '';

    // If the dashboard grid doesn't exist (we're on the legacy insights page),
    // Se a grade do dashboard não existir (estamos na página de insights legado),
    // show a short migration note that points users to the main Dashboard.
    // mostre uma nota curta de migração que direciona os usuários para o Dashboard principal.
    const dashboardExists = !!document.getElementById('dashboard-grid');
    if (!dashboardExists) {
        if (!document.getElementById('insights-migrate-note')) {
            const noteHtml = `
                <div id="insights-migrate-note" class="insights-note" style="margin-bottom:12px;padding:10px;border-left:4px solid #1976d2;background:#f5f8ff;color:#153e75;display:flex;align-items:center;gap:12px;">
                    <div style="flex:1"><strong>Nota:</strong> Os cards de insights foram migrados para o Dashboard principal.</div>
                    <div><a class="btn-primary" href="/">Ver Dashboard</a></div>
                </div>`;
            grid.insertAdjacentHTML('beforebegin', noteHtml);
        }
    }

    // Ensure we have a stable way to append query params to API endpoints.
    // Garanta que temos uma maneira estável de anexar parâmetros de consulta aos endpoints da API.
    // Some pages define `appendQueryParams` globally; if not, provide a small polyfill
    // Algumas páginas definem `appendQueryParams` globalmente; se não, forneça um pequeno polyfill
    // that preserves existing behavior but guarantees selected filters are sent.
    if (typeof appendQueryParams !== 'function') {
        window.appendQueryParams = function(url, params) {
            try {
                if (!params || Object.keys(params).length === 0) return url;
                // Use the page origin to build an absolute URL then return path+search
                const u = new URL(url, window.location.origin);
                Object.keys(params).forEach(k => {
                    const v = params[k];
                    if (v !== null && typeof v !== 'undefined' && String(v) !== '') {
                        u.searchParams.set(k, v);
                    }
                });
                return u.pathname + u.search;
            } catch (e) {
                // Fallback: naive serialization
                try {
                    const qs = new URLSearchParams();
                    Object.keys(params).forEach(k => {
                        const v = params[k];
                        if (v !== null && typeof v !== 'undefined' && String(v) !== '') qs.set(k, v);
                    });
                    return url + (url.indexOf('?') === -1 ? '?' : '&') + qs.toString();
                } catch (e2) {
                    return url;
                }
            }
        };
    }

    // Fetch cards sequentially to avoid bursting the backend with many parallel requests
    // Busque cards sequencialmente para evitar sobrecarregar o backend com muitas solicitações paralelas
    for (const card of INSIGHTS_CARDS) {
        try {
            // Defensive: if any element with this id exists anywhere in the document, skip to avoid duplicates
            // Defensivo: se qualquer elemento com este id existir em qualquer lugar do documento, pule para evitar duplicatas
            if (document.getElementById(card.id)) {
                // já existe um elemento com este id no DOM; pular para evitar duplicação
                continue;
            }
            const filters = (typeof getGlobalFilters === 'function') ? getGlobalFilters() : {};
            // Always build a URL that includes filters: prefer existing appendQueryParams but
            // fall back to our polyfill above (so cards get loja/data filters correctly).
            const url = appendQueryParams(card.api, filters);
            try {
                const res = await fetch(url);
                const data = await res.json();
                grid.insertAdjacentHTML('beforeend', card.render(data));
                try {
                    const root = document.getElementById(card.id);
                    if (card.init && root) card.init(root, data);
                    // After init, ensure there are no duplicate elements with the same id (defensive cleanup)
                    const duplicates = document.querySelectorAll(`#${card.id}`);
                    if (duplicates && duplicates.length > 1) {
                        // keep the first occurrence and remove the rest
                        for (let i = 1; i < duplicates.length; i++) {
                            try { duplicates[i].parentElement && duplicates[i].parentElement.removeChild(duplicates[i]); } catch (e) { /* ignore */ }
                        }
                        console.warn('insights: removed duplicate instances of', card.id);
                    }
                } catch (e) { console.error('init card error', card.id, e); }
                // attach robot button if available (re-use global from dashboard.js)
                // anexe botão de robô se disponível (reutilize global do dashboard.js)
                try { if (typeof window.attachRobotButton === 'function') window.attachRobotButton(card.id); } catch(e) { }
            } catch (err) {
                console.error('fetch error for', card.id, err);
                try {
                    grid.insertAdjacentHTML('beforeend', card.render({}));
                    const root = document.getElementById(card.id);
                    if (card.init && root) card.init(root, {});
                    // defensive dedupe
                    const duplicates = document.querySelectorAll(`#${card.id}`);
                    if (duplicates && duplicates.length > 1) {
                        for (let i = 1; i < duplicates.length; i++) {
                            try { duplicates[i].parentElement && duplicates[i].parentElement.removeChild(duplicates[i]); } catch (e) { /* ignore */ }
                        }
                        console.warn('insights: removed duplicate instances of', card.id);
                    }
                } catch (e) { console.error('render error for', card.id, e); }
            }
        } catch (e) {
            console.error('fetchAndRenderInsightsCards: error building request for', card.id, e);
        }
    }
}

window.addEventListener('load', fetchAndRenderInsightsCards);

// Expose the cards definition to other scripts (dashboard.js expects
// Exponha a definição dos cards para outros scripts (dashboard.js espera
// `window.INSIGHTS_CARDS` when integrating insights into the dashboard).
try { window.INSIGHTS_CARDS = INSIGHTS_CARDS; } catch(e) { /* ignore */ }
