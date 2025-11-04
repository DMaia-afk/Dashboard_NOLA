// Adiciona Chart.js via CDN para gráficos
// Inclua no <head> do seu home.html:
// <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

// dashboard.js - cards analíticos com visualização recomendada
// ...existing code...

// helper to create small change badge
// auxiliar para criar pequeno badge de mudança
function createChangeBadge(pct) {
    if (pct === null || typeof pct === 'undefined' || isNaN(Number(pct))) return '';
    const n = Number(pct);
    const sign = n >= 0 ? '+' : '';
    const colorClass = n >= 0 ? 'kpi-change-positive' : 'kpi-change-negative';
    const text = `${sign}${n.toLocaleString('pt-BR', {maximumFractionDigits:1})}%`;
    return `<span class="kpi-change-badge ${colorClass}" aria-hidden="true">${text}</span>`;
}

function renderKPICard(id, title, value, subtitle = "", changeHtml = "") {
    return `<div id="${id}" class="widget-card kpi-card">
        <h2>${title}</h2>
        <div class="kpi-value">${value} ${changeHtml || ''}</div>
        ${subtitle ? `<div class="kpi-subtitle">${subtitle}</div>` : ""}
    </div>`;
}

function renderTableCard(id, title, columns, rows) {
    const header = columns.map(c => `<th scope="col">${c}</th>`).join("");
    const body = rows.map(r => `<tr>${r.map(cell => `<td>${cell}</td>`).join("")}</tr>`).join("");
    return `<div id="${id}" class="widget-card table-card">
        <h2>${title}</h2>
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
        <h2>${title}</h2>
        <canvas id="${id}-chart"></canvas>
        <script>
        new Chart(document.getElementById('${id}-chart').getContext('2d'), {
            type: 'bar',
            data: { labels: ${JSON.stringify(labels)}, datasets: [{ label: '${label}', data: ${JSON.stringify(data)}, backgroundColor: '#007bff' }] },
            options: { responsive: true, plugins: { legend: { display: false } } }
        });
        </script>
    </div>`;
}

function renderLineChartCard(id, title, labels, data, label) {
    return `<div id="${id}" class="widget-card chart-card">
        <h2>${title}</h2>
        <canvas id="${id}-chart"></canvas>
        <script>
        new Chart(document.getElementById('${id}-chart').getContext('2d'), {
            type: 'line',
            data: { labels: ${JSON.stringify(labels)}, datasets: [{ label: '${label}', data: ${JSON.stringify(data)}, borderColor: '#007bff', fill: false }] },
            options: { responsive: true, plugins: { legend: { display: false } } }
        });
        </script>
    </div>`;
}

// Exemplo para os 3 primeiros cards
const CARD_CONFIGS = [
    {
        id: 'card-faturamento-total',
        name: 'Faturamento Total',
        api: '/api/card-faturamento-total/',
        render: data => {
            const valor = `R$ ${data.valor_total?.toLocaleString('pt-BR', {minimumFractionDigits:2}) || '...'}`;
            const overallPct = (data && (typeof data.pct_change !== 'undefined' ? data.pct_change : (typeof data.pct_diff !== 'undefined' ? data.pct_diff : null)));
            const changeHtml = overallPct !== null && typeof overallPct !== 'undefined' ? createChangeBadge(overallPct) : '';
            return renderKPICard('card-faturamento-total', 'Faturamento Total', valor, '', changeHtml);
        }
    },
    {
        id: 'card-ticket-medio',
        name: 'Ticket Médio',
        api: '/api/card-ticket-medio/',
        render: function(data) {
            const overall = (data && typeof data.ticket_medio !== 'undefined') ? data.ticket_medio : null;
            const value = overall !== null ? `R$ ${Number(overall).toLocaleString('pt-BR', {minimumFractionDigits:2})}` : '...';
            // optional overall percent change
            // mudança percentual geral opcional
            const overallPct = (data && (typeof data.pct_change !== 'undefined' ? data.pct_change : (typeof data.pct_diff !== 'undefined' ? data.pct_diff : (typeof data.delta_pct !== 'undefined' ? data.delta_pct : null))));
            const changeHtml = overallPct !== null && typeof overallPct !== 'undefined' ? createChangeBadge(overallPct) : '';
            let subtitle = '';
            if (data && Array.isArray(data.por_canal) && data.por_canal.length) {
                const totalVendas = (typeof data.total_vendas !== 'undefined' && data.total_vendas !== null) ? data.total_vendas : data.por_canal.reduce((s, x) => s + (x.vendas || 0), 0);
                const items = data.por_canal.map(c => {
                    const avg = (typeof c.ticket_medio !== 'undefined' && c.ticket_medio !== null) ? c.ticket_medio : 0;
                    const vendas = (typeof c.vendas !== 'undefined' && c.vendas !== null) ? c.vendas : 0;
                    const minTicket = (typeof c.min_ticket !== 'undefined' && c.min_ticket !== null) ? c.min_ticket : null;
                    const maxTicket = (typeof c.max_ticket !== 'undefined' && c.max_ticket !== null) ? c.max_ticket : null;
                    const share = (typeof c.share_percent !== 'undefined') ? c.share_percent : (totalVendas ? (vendas / totalVendas * 100.0) : 0);
                    const pctDiff = (typeof c.pct_diff_vs_overall !== 'undefined') ? c.pct_diff_vs_overall : 0;
                    const low = !!c.low_volume;
                    const avgFormatted = `R$ ${Number(avg).toLocaleString('pt-BR', {minimumFractionDigits:2})}`;
                    let avgText = avgFormatted;
                    let tooltipAttr = '';
                    if (minTicket !== null && maxTicket !== null && minTicket > 0) {
                        const rangeText = `R$ ${Number(minTicket).toLocaleString('pt-BR', {maximumFractionDigits:0})} – R$ ${Number(maxTicket).toLocaleString('pt-BR', {maximumFractionDigits:0})}`;
                        tooltipAttr = ` title="Intervalo observado: ${rangeText}"`;
                    }
                    const vendasText = `${Number(vendas).toLocaleString('pt-BR')} vendas`;
                    const shareText = `${Number(share).toLocaleString('pt-BR', {maximumFractionDigits:1})}%`;
                    const pctText = `${pctDiff >= 0 ? '+' : ''}${Number(pctDiff).toLocaleString('pt-BR', {maximumFractionDigits:1})}%`;
                    const pctColor = pctDiff >= 0 ? '#2e7d32' : '#d32f2f';
                    const opacity = low ? 0.6 : 1.0;
                    const badge = createChangeBadge(pctDiff);
                    return `<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f0f0f0;opacity:${opacity};">
                                <div style="color:#666"${tooltipAttr}>${c.canal}<div style="font-size:0.85em;color:#999">${shareText} do total</div></div>
                                <div style="text-align:right;">
                                    <div style="font-weight:600">${avgText} <span style="color:#888;font-weight:400;margin-left:8px;font-size:0.9em">${vendasText}</span></div>
                                    <div style="font-size:0.85em;margin-top:6px">${badge} <span class="cell-secondary" style="margin-left:8px;font-size:0.85em">vs geral</span></div>
                                </div>
                            </div>`;
                }).join('');
                subtitle = `<div style="margin-top:8px;text-align:left;color:#666;font-size:0.95em;max-height:240px;overflow:auto;padding-right:6px;">${items}</div>`;
            }
            const infoIcon = `<span style="margin-left:8px;cursor:pointer;" title="Ticket por canal: média das vendas apenas do canal. Ticket geral: média de todas as vendas do período."><span style="display:inline-block;width:18px;height:18px;border-radius:50%;background:#e0e0e0;color:#333;text-align:center;line-height:18px;font-weight:bold;font-size:12px;">i</span></span>`;
            return renderKPICard('card-ticket-medio', `Ticket Médio ${infoIcon}`, value, subtitle, changeHtml);
        }
    },
    {
        id: 'card-vendas-por-dia-hora',
        name: 'Vendas por Dia/Hora',
        api: '/api/card-vendas-por-dia-hora/',
        render: data => {
            const labels = data.heatmap?.map(h => `${['Dom','Seg','Ter','Qua','Qui','Sex','Sab'][h.dia_semana]} ${h.hora}h`) || [];
            const vendas = data.heatmap?.map(h => h.vendas) || [];
            return renderBarChartCard('card-vendas-por-dia-hora', 'Vendas por Dia/Hora', labels, vendas, 'Vendas');
        }
    },
    // Caso eu precise -> continuar para os demais cards, usando renderTableCard, renderBarChartCard, renderLineChartCard, etc conforme recomendado...
];


