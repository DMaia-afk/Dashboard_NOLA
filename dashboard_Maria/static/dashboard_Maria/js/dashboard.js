// dashboard.js base para os 20 cards do CARD_IDEAS.md
// Enable local mock by default (intercepts /api/dashboard-layout/)
// Habilita mock local por padrão (intercepta /api/dashboard-layout/)
    try { if (typeof enableLocalLayoutMock === 'function') { enableLocalLayoutMock(); /* local mock enabled by default */ } } catch(e) { /* ok if function not yet defined due to load order */ }
// Função utilitária para renderizar cards de lista com paginação
function renderPaginatedListCard(cardId, cardTitle, columns, rows, currentPage, totalPages, onPageChangeFnName) {
    // Build accessible, compact table with pagination controls and consistent classes
    // Construir tabela acessível, compacta com controles de paginação e classes consistentes
    const safeCols = columns.map(c => `<th scope="col">${c}</th>`).join("");
    const safeRows = rows.map(r => `<tr>${r.map(cell => `<td>${cell}</td>`).join("")}</tr>`).join("");
    let html = `<div id="${cardId}" class="widget-card table-card">
        <div class="kpi-title"><span>${cardTitle}</span></div>
        <div class="table-wrapper">
            <table class="compact-table" role="table">
                <thead><tr>${safeCols}</tr></thead>
                <tbody>${safeRows}</tbody>
            </table>
        </div>`;

    // pagination controls (only when there's more than one page)
    // controles de paginação (apenas quando há mais de uma página)
    if (totalPages > 1) {
        html += `<div class='pagination-controls' role="navigation" aria-label="pagination-${cardId}">`;
        html += `<button class="page-btn" onclick='window.${onPageChangeFnName}(${currentPage - 1})' ${currentPage === 1 ? "disabled" : ""} aria-label="Página anterior">‹ Anterior</button>`;
        html += `<span class="page-info">Página ${currentPage} de ${totalPages}</span>`;
        html += `<button class="page-btn" onclick='window.${onPageChangeFnName}(${currentPage + 1})' ${currentPage === totalPages ? "disabled" : ""} aria-label="Próxima página">Próxima ›</button>`;
        html += `</div>`;
    }

    html += `</div>`;
    return html;
}
const CARD_IDS = [
    'card-faturamento-total',
    'card-ticket-medio',
    'card-vendas-por-dia-hora',
    'card-produtos-mais-vendidos',
    'card-produtos-menos-vendidos',
    'card-produtos-mais-customizados',
    'card-itens-complementos-mais-vendidos',
    'card-taxa-cancelamento',
    'card-taxa-desconto',
    'card-performance-entrega-regiao',
    'card-clientes-frequentes',
    'card-clientes-ausentes',
    'card-novos-clientes',
    // 'card-retencao-clientes', // migrado para insights
    'card-lifetime-value',
    'card-performance-por-canal',
    'card-performance-por-loja'
];
const VISIBILITY_KEY = 'dashboard_widget_visibility';
const ORDER_KEY = 'dashboard_widget_order';
const INSIGHTS_ORDER_KEY = 'dashboard_insights_widget_order';
let widgetVisibility = {};

function initDashboard() {
    // Inicialização leve do dashboard:
    // - restaura visibilidade de widgets do localStorage
    // - inicializa sortable se disponível
    // - popula lista de lojas via API
    try {
        // restaura visibilidade
        const raw = localStorage.getItem(VISIBILITY_KEY);
        if (raw) {
            try { widgetVisibility = JSON.parse(raw) || {}; } catch(e) { widgetVisibility = {}; }
        }
        // garante valores padrão para todos os cards
        CARD_IDS.forEach(id => {
            if (typeof widgetVisibility[id] === 'undefined') widgetVisibility[id] = true;
        });
        // tenta inicializar sortable (se implementado)
        if (typeof initSortable === 'function') {
            try { initSortable(); } catch (e) { console.warn('initSortable falhou:', e); }
        }
        if (typeof initSortables === 'function') {
            try { initSortables(); } catch (e) { console.warn('initSortables falhou:', e); }
        }
        // popula datalist de lojas (se existir) usando a API /api/lojas/
        try {
            fetch('/api/lojas/')
                .then(res => res.json())
                .then(data => {
                    if (data && Array.isArray(data.lojas)) {
                        const dl = document.getElementById('lojas-list');
                        if (dl) {
                            dl.innerHTML = data.lojas.map(l => `<option value="${l}">`).join('');
                        }
                    }
                })
                .catch(err => { /* não é crítico */ });
        } catch (e) { /* ignore */ }

        // grava visibilidade atual (pode ser atualizada por UI posteriormente)
        try { localStorage.setItem(VISIBILITY_KEY, JSON.stringify(widgetVisibility)); } catch(e) { }

        // attempt to load server-side saved layout (if user/session saved it).
        // tenta carregar layout salvo no lado do servidor (se usuário/sessão salvou).
        return loadLayoutFromServer();
    } catch (err) {
        console.error('Erro em initDashboard:', err);
        return Promise.resolve();
    }
}

function loadLayoutFromServer() {
    try {
        return fetch('/api/dashboard-layout/', { credentials: 'same-origin' })
            .then(r => {
                if (!r.ok) throw new Error('no-layout');
                return r.json();
            })
            .then(d => {
                if (!d || !d.layout) return;
                const layout = d.layout || {};
                try {
                    if (Array.isArray(layout.order)) {
                        localStorage.setItem(ORDER_KEY, JSON.stringify(layout.order));
                    }
                    if (layout.visibility && typeof layout.visibility === 'object') {
                        widgetVisibility = Object.assign({}, widgetVisibility, layout.visibility);
                        localStorage.setItem(VISIBILITY_KEY, JSON.stringify(widgetVisibility));
                    }
                } catch (e) { /* ignore storage errors */ }
            })
            .catch(e => {
                // fallback: enable a local in-browser mock for the dashboard-layout API
                // fallback: habilita um mock local no navegador para a API dashboard-layout
                try {
                    enableLocalLayoutMock();
                    // Dashboard layout server not available — using local in-browser mock.
                    // Servidor de layout do dashboard não disponível — usando mock local no navegador.
                } catch (ex) {
                    console.warn('Failed to enable local layout mock', ex);
                }
                // load saved mock layout from localStorage if present
                // carrega layout mock salvo do localStorage se presente
                try {
                    const raw = localStorage.getItem('mock_server_dashboard_layout');
                    if (raw) {
                        const d = JSON.parse(raw);
                        const layout = d.layout || {};
                        if (Array.isArray(layout.order)) localStorage.setItem(ORDER_KEY, JSON.stringify(layout.order));
                        if (layout.visibility && typeof layout.visibility === 'object') { widgetVisibility = Object.assign({}, widgetVisibility, layout.visibility); localStorage.setItem(VISIBILITY_KEY, JSON.stringify(widgetVisibility)); }
                    }
                } catch (ee) { /* ignore */ }
            });
    } catch (e) { return Promise.resolve(); }
}

// Installs a lightweight local mock that intercepts fetch calls to
// Instala um mock local leve que intercepta chamadas fetch para
// '/api/dashboard-layout/' and stores/serves layout JSON from localStorage.
function enableLocalLayoutMock() {
    if (window.__dashboard_layout_mock_installed) return;
    const originalFetch = window.fetch.bind(window);
    // store original for possible restore
    // armazena original para possível restauração
    if (!window.__dashboard_layout_original_fetch) window.__dashboard_layout_original_fetch = originalFetch;
    window.fetch = function(input, init) {
        try {
            const url = (typeof input === 'string') ? input : (input && input.url) ? input.url : '';
            const method = (init && init.method) ? init.method.toUpperCase() : 'GET';
            if (url.indexOf('/api/dashboard-layout/') !== -1) {
                // Mock GET
                // Mock GET
                if (method === 'GET') {
                    const raw = localStorage.getItem('mock_server_dashboard_layout');
                    const body = raw ? JSON.parse(raw) : { layout: {} };
                    const res = new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } });
                    return Promise.resolve(res);
                }
                // Mock POST
                // Mock POST
                if (method === 'POST') {
                    try {
                        const reader = (init && init.body) ? init.body : null;
                        // init.body may be a stringified JSON
                        // init.body pode ser um JSON stringificado
                        let payload = {};
                        if (typeof reader === 'string') {
                            payload = JSON.parse(reader || '{}');
                        } else if (reader && typeof reader === 'object') {
                            // attempt to read JSON if it's a plain object
                            payload = reader;
                        }
                        const toStore = { layout: payload.layout || payload };
                        localStorage.setItem('mock_server_dashboard_layout', JSON.stringify(toStore));
                        const res = new Response(JSON.stringify({ status: 'ok', layout: toStore.layout }), { status: 200, headers: { 'Content-Type': 'application/json' } });
                        return Promise.resolve(res);
                    } catch (err) {
                        const res = new Response(JSON.stringify({ error: 'invalid payload' }), { status: 400, headers: { 'Content-Type': 'application/json' } });
                        return Promise.resolve(res);
                    }
                }
            }
        } catch (e) {
            // fall back to original fetch on any error
        }
        return originalFetch(input, init);
    };
    window.__dashboard_layout_mock_installed = true;
}

function disableLocalLayoutMock() {
    try {
        if (window.__dashboard_layout_original_fetch) {
            window.fetch = window.__dashboard_layout_original_fetch;
            delete window.__dashboard_layout_original_fetch;
        }
    delete window.__dashboard_layout_mock_installed;
    // local dashboard-layout mock disabled
    } catch (e) { console.warn('disableLocalLayoutMock failed', e); }
}

function saveLayoutToServer() {
    try {
        const payload = {
            layout: {
                order: (() => { try { return JSON.parse(localStorage.getItem(ORDER_KEY) || '[]'); } catch (e) { return []; } })(),
                visibility: widgetVisibility,
                // include insights order so server/mock has unified state
                insights_order: (() => { try { return JSON.parse(localStorage.getItem(INSIGHTS_ORDER_KEY) || '[]'); } catch (e) { return []; } })()
            }
        };
        fetch('/api/dashboard-layout/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), credentials: 'same-origin' })
            .then(r => { /* fire-and-forget; ignore response */ })
            .catch(e => { /* ignore */ });
    } catch (e) { /* ignore */ }
}

function isMockEnabled() {
    return !!window.__dashboard_layout_mock_installed;
}

function getMockLayoutFromStorage() {
    try { return JSON.parse(localStorage.getItem('mock_server_dashboard_layout') || '{}'); } catch (e) { return {}; }
}

function clearMockLayoutStorage() {
    try { localStorage.removeItem('mock_server_dashboard_layout'); } catch (e) { }
}
// Aplica filtros exclusivos do card de retenção de clientes
function applyRetencaoFilters(event) {
    // Não precisa preventDefault pois não está em um form
    // Só envia loja, mes_inicio e mes_fim exclusivos do card
    // Função migrada para insights.js
}

function applyVisibility(element, isVisible) {
    try {
        if (!element) return;
        element.style.display = isVisible ? '' : 'none';
        // update storage
        widgetVisibility[element.id] = !!isVisible;
        try { localStorage.setItem(VISIBILITY_KEY, JSON.stringify(widgetVisibility)); } catch (e) { }
    } catch (e) { console.warn('applyVisibility failed', e); }
}

function saveOrder() {
    try {
        const grid = document.getElementById('dashboard-grid');
        if (!grid) return;
        const ids = Array.from(grid.querySelectorAll('.widget-card')).map(el => el.id).filter(Boolean);
        try { localStorage.setItem(ORDER_KEY, JSON.stringify(ids)); } catch (e) { console.warn('saveOrder localStorage failed', e); }
        try { saveLayoutToServer(); } catch (e) {}
        return ids;
    } catch (e) { console.warn('saveOrder failed', e); }
}

function saveVisibility() {
    try { localStorage.setItem(VISIBILITY_KEY, JSON.stringify(widgetVisibility)); saveLayoutToServer(); } catch (e) { console.warn('saveVisibility failed', e); }
}

function initSortable() {
    try {
        const grid = document.getElementById('dashboard-grid');
        if (!grid || typeof Sortable === 'undefined') return;
        // create Sortable with a drag handle selector
        if (grid._sortable) return; // already initialized
        grid._sortable = Sortable.create(grid, {
            animation: 150,
            handle: '.card-drag-handle',
            draggable: '.widget-card',
            onEnd: function() {
                saveOrder();
            }
        });
        // restore previous order if present
        try {
            const raw = localStorage.getItem(ORDER_KEY);
            if (raw) {
                const order = JSON.parse(raw);
                // re-order DOM to match saved order
                order.forEach(id => {
                    const el = document.getElementById(id);
                    if (el && grid.contains(el)) grid.appendChild(el);
                });
            }
function initSortables() {
    try {
        if (typeof Sortable === 'undefined') return;
        const grids = [ 'dashboard-grid', 'insights-grid' ];
        grids.forEach(gridId => {
            const grid = document.getElementById(gridId);
            if (!grid) return;
            if (grid._sortable) return; // already initialized
            grid._sortable = Sortable.create(grid, {
                animation: 150,
                handle: '.card-drag-handle',
                draggable: '.widget-card',
                onEnd: function() {
                    if (gridId === 'dashboard-grid') saveOrder(); else saveInsightsOrder();
                }
            });
            // restore previous order if present
            try {
                const raw = localStorage.getItem(gridId === 'dashboard-grid' ? ORDER_KEY : INSIGHTS_ORDER_KEY);
                if (raw) {
                    const order = JSON.parse(raw) || [];
                    order.forEach(id => {
                        const el = document.getElementById(id);
                        if (el && grid.contains(el)) grid.appendChild(el);
                    });
                }
            } catch (e) { /* ignore restore errors */ }
        });
    } catch (e) { console.warn('initSortables failed', e); }
}
        } catch (e) { /* ignore restore errors */ }
    } catch (e) { console.warn('initSortable failed', e); }
}

function removeCard(cardId) {
    try {
        const el = document.getElementById(cardId);
        if (!el) return;
        el.parentElement && el.parentElement.removeChild(el);
        widgetVisibility[cardId] = false;
        saveVisibility();
        saveOrder();
function saveInsightsOrder() {
    try {
        const grid = document.getElementById('insights-grid');
        if (!grid) return;
        const ids = Array.from(grid.querySelectorAll('.widget-card')).map(el => el.id).filter(Boolean);
        try { localStorage.setItem(INSIGHTS_ORDER_KEY, JSON.stringify(ids)); } catch (e) { console.warn('saveInsightsOrder failed', e); }
        try { saveLayoutToServer(); } catch (e) {}
        return ids;
    } catch (e) { console.warn('saveInsightsOrder failed', e); }
}
    } catch (e) { console.warn('removeCard failed', e); }
}

function showCard(cardId) {
    try {
        widgetVisibility[cardId] = true;
        saveVisibility();
        // if card already present do nothing (fetchAndRenderCards can insert missing)
        const grid = document.getElementById('dashboard-grid');
        if (!grid) return;
        const exists = document.getElementById(cardId);
        if (exists) { exists.style.display = ''; return; }
        // find config and render it immediately
        const cfg = CARD_CONFIGS.find(c => c.id === cardId);
        if (!cfg) return;
        // fetch data and render
        fetch(appendQueryParams(cfg.api, globalFilters)).then(r=>r.json()).then(data=>{
            grid.insertAdjacentHTML('beforeend', cfg.render(data));
            attachCardControls(cardId);
            saveOrder();
        }).catch(err=>{
            grid.insertAdjacentHTML('beforeend', cfg.render({}));
            attachCardControls(cardId);
            saveOrder();
        });
    } catch (e) { console.warn('showCard failed', e); }
}

function showAddWidgetModal() {
    try {
        const modal = document.getElementById('add-widget-modal');
        if (!modal) return;
        // build list of available cards (including those hidden)
        const available = CARD_CONFIGS.map(c => ({ id: c.id, name: c.name }));
        // modal content
        let html = `<div class="modal" role="dialog" aria-modal="true" style="background:#fff;padding:18px;border-radius:8px;max-width:720px;margin:40px auto;">`;
        html += `<h3>Adicionar Card</h3>`;
        html += `<p>Escolha cards disponíveis para adicionar ao dashboard.</p>`;
        html += `<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px;max-height:60vh;overflow:auto;padding:6px;">`;
        available.forEach(a => {
            const visible = !!widgetVisibility[a.id];
            html += `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px;border:1px solid #eee;border-radius:6px;background:${visible?'#f6fff6':'#fff'};">`;
            html += `<div style="font-weight:600;color:#333">${a.name}</div>`;
            html += `<div>`;
            if (!visible) html += `<button class="add-widget-btn" data-id="${a.id}" style="padding:6px 10px;border-radius:6px;border:1px solid #1976d2;background:#1976d2;color:#fff;">Adicionar</button>`;
            else html += `<button disabled style="padding:6px 10px;border-radius:6px;border:1px solid #ccc;background:#eee;color:#666;">Adicionado</button>`;
            html += `</div></div>`;
        });
        html += `</div>`;
        html += `<div style="margin-top:12px;text-align:right;"><button id="add-widget-close" class="btn-secondary" style="padding:8px 12px;border-radius:6px;border:1px solid #ccc;background:#fff;">Fechar</button></div>`;
        html += `</div>`;
        modal.innerHTML = html;
        modal.classList.remove('hidden');
        // attach handlers
        modal.querySelectorAll('.add-widget-btn').forEach(b => b.addEventListener('click', ev => {
            const id = b.getAttribute('data-id');
            showCard(id);
            // refresh modal content to reflect change
            setTimeout(() => showAddWidgetModal(), 150);
        }));
        const close = document.getElementById('add-widget-close'); if (close) close.addEventListener('click', hideAddWidgetModal);
    } catch (e) { console.warn('showAddWidgetModal failed', e); }
}

function hideAddWidgetModal() {
    try { const modal = document.getElementById('add-widget-modal'); if (modal) modal.classList.add('hidden'); } catch (e) { }
}

// Adds drag handle and remove button to a card after it is rendered
function attachCardControls(cardId) {
    try {
        const root = document.getElementById(cardId);
        if (!root) return;
        // avoid duplicating controls
        if (root.querySelector('.card-controls')) return;
        root.style.position = root.style.position || 'relative';
        const controls = document.createElement('div');
        controls.className = 'card-controls';
        controls.style.position = 'absolute';
        controls.style.top = '8px';
        controls.style.right = '8px';
        controls.style.display = 'flex';
        controls.style.gap = '6px';

        const handle = document.createElement('button');
        handle.type = 'button';
        handle.className = 'card-drag-handle';
        handle.title = 'Arrastar para mover';
        handle.innerHTML = '☰';
        handle.style.cursor = 'grab';
        handle.style.border = '0';
        handle.style.background = 'transparent';
        handle.style.fontSize = '16px';

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'card-remove-btn';
        removeBtn.title = 'Remover card';
        removeBtn.innerHTML = '✕';
        removeBtn.style.cursor = 'pointer';
        removeBtn.style.border = '0';
        removeBtn.style.background = 'transparent';
        removeBtn.style.fontSize = '16px';
        removeBtn.addEventListener('click', function(ev) {
            ev.preventDefault(); ev.stopPropagation();
            removeCard(cardId);
            // refresh add modal if open
            try { const modal = document.getElementById('add-widget-modal'); if (modal && !modal.classList.contains('hidden')) showAddWidgetModal(); } catch(e){}
        });

        controls.appendChild(handle);
        controls.appendChild(removeBtn);
        root.appendChild(controls);
    } catch (e) { console.warn('attachCardControls failed', e); }
}


// Funções utilitárias para renderização visual
// Small helper to create a colored percent-change badge
function createChangeBadge(pct) {
    if (pct === null || typeof pct === 'undefined' || isNaN(Number(pct))) return '';
    const n = Number(pct);
    const sign = n >= 0 ? '+' : '';
    const colorClass = n >= 0 ? 'kpi-change-positive' : 'kpi-change-negative';
    const text = `${sign}${n.toLocaleString('pt-BR', {maximumFractionDigits:1})}%`;
    return `<span class="kpi-change-badge ${colorClass}" aria-hidden="true">${text}</span>`;
}
        let html = `<div class="modal" role="dialog" aria-modal="true" style="background:#fff;padding:18px;border-radius:8px;max-width:720px;margin:40px auto;">`;
// Render analysis inline inside the card DOM. Keeps a small, collapsible panel inside the card
function renderAnalysisInCard(cardId, analysis) {
    try {
        const root = document.getElementById(cardId);
        if (!root) return;
        // remove existing panel if any
        let panel = root.querySelector('.card-analysis-inline');
        if (!panel) {
            panel = document.createElement('div');
            panel.className = 'card-analysis-inline';
            panel.setAttribute('aria-live', 'polite');
            panel.style.borderTop = '1px solid #eee';
            panel.style.marginTop = '12px';
        // mock controls
        const mockStatus = isMockEnabled() ? 'Ativado' : 'Desativado';
        html += `<hr style="margin-top:12px;margin-bottom:8px;">`;
        html += `<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">`;
        html += `<div style="flex:1">Mock local do servidor: <strong id="mock-status">${mockStatus}</strong></div>`;
        html += `<div style="display:flex;gap:6px">`;
        html += `<button id="toggle-mock-btn" class="btn-secondary" style="padding:6px 10px;border-radius:6px;border:1px solid #1976d2;background:#fff;">${isMockEnabled() ? 'Desativar mock' : 'Ativar mock'}</button>`;
        html += `<button id="view-mock-btn" class="btn-secondary" style="padding:6px 10px;border-radius:6px;border:1px solid #ccc;background:#fff;">Visualizar mock</button>`;
        html += `<button id="clear-mock-btn" class="btn-secondary" style="padding:6px 10px;border-radius:6px;border:1px solid #d32f2f;background:#fff;color:#d32f2f;">Limpar mock</button>`;
        html += `</div></div>`;
        html += `<div style="margin-top:12px;text-align:right;"><button id="add-widget-close" class="btn-secondary" style="padding:8px 12px;border-radius:6px;border:1px solid #ccc;background:#fff;">Fechar</button></div>`;
            panel.style.fontSize = '0.95em';
            panel.style.background = 'linear-gradient(90deg, rgba(255,255,255,0.0), rgba(250,250,250,0.02))';
            root.appendChild(panel);
        }
        const title = analysis.metric_name || analysis.title || '';
        let html = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">`;
        html += `<div style="font-weight:700;color:#333">${title}</div>`;
        html += `<div><button type="button" class="card-analysis-collapse" aria-label="Fechar análise" style="background:transparent;border:0;cursor:pointer;font-size:16px;line-height:1;">×</button></div>`;
        html += `</div>`;
        html += `<div class="card-analysis-body">`;
        if (typeof analysis.current !== 'undefined') html += `<div><strong>Atual:</strong> ${analysis.current}</div>`;
        if (typeof analysis.previous !== 'undefined') html += `<div><strong>Anterior:</strong> ${analysis.previous}</div>`;
        if (typeof analysis.pct_change !== 'undefined' && analysis.pct_change !== null) html += `<div><strong>Variação:</strong> ${createChangeBadge(analysis.pct_change)}</div>`;
        if (analysis.message) html += `<div style="margin-top:6px;color:#444">${analysis.message}</div>`;
        if (analysis.top) html += `<div style="margin-top:8px"><strong>Top:</strong> ${analysis.top.label || analysis.top[0]} — ${analysis.top.value || analysis.top[1]}</div>`;
        if (analysis.bottom) html += `<div style="margin-top:4px"><strong>Menor:</strong> ${analysis.bottom.label || analysis.bottom[0]} — ${analysis.bottom.value || analysis.bottom[1]}</div>`;
        // optional extras: por_canal, buckets
        if (Array.isArray(analysis.por_canal) && analysis.por_canal.length) {
            html += `<div style="margin-top:8px;font-weight:600">Por canal</div>`;
            html += `<div style="max-height:120px;overflow:auto;padding-right:6px;margin-top:6px;">`;
            html += analysis.por_canal.map(c => `<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px dashed #f6f6f6;"><div style="color:#666">${c.canal || c.name}</div><div style="font-weight:600">${(typeof c.pct !== 'undefined' ? c.pct : c.taxa || c.value || c.n_canceladas)}${typeof c.pct !== 'undefined' ? '%' : ''}</div></div>`).join('');
            html += `</div>`;
        }
        if (Array.isArray(analysis.buckets) && analysis.buckets.length) {
            html += `<div style="margin-top:8px;font-weight:600">Buckets</div>`;
            html += `<div style="display:flex;gap:8px;margin-top:6px;flex-wrap:wrap">`;
            html += analysis.buckets.map(b => `<div style="background:#fafafa;border:1px solid #f0f0f0;padding:6px 8px;border-radius:6px;font-size:0.85em;color:#333">${b.label || b.bucket}: <strong>${b.count ?? b.value ?? 0}</strong></div>`).join('');
            html += `</div>`;
        }
        html += `</div>`;
        panel.innerHTML = html;
        const btn = panel.querySelector('.card-analysis-collapse');
        if (btn) btn.addEventListener('click', function() { panel.parentElement && panel.parentElement.removeChild(panel); });
    } catch (e) {
        console.warn('renderAnalysisInCard failed', e);
    }
}

function renderKPICard(id, title, value, subtitle = "", changeHtml = "") {
    return `<div id="${id}" class="widget-card kpi-card">
        <div class="kpi-title"><span>${title}</span></div>
        <div class="kpi-value">${value} ${changeHtml || ''}</div>
        ${subtitle ? `<div class="kpi-subtitle">${subtitle}</div>` : ""}
    </div>`;
}

// Local storage helpers for per-card view mode ('pct' | 'count' | 'money')
function _viewModeKey(cardId) { return `card_view_mode::${cardId}`; }
function getCardViewMode(cardId) {
    try {
        const v = localStorage.getItem(_viewModeKey(cardId));
        if (!v) return 'pct';
        return v;
    } catch (e) { return 'pct'; }
}
function setCardViewMode(cardId, mode) {
    try { localStorage.setItem(_viewModeKey(cardId), mode); } catch (e) { }
}

function formatCurrencyBRL(n) {
    try {
        const num = Number(n) || 0;
        return 'R$ ' + num.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    } catch (e) { return 'R$ 0,00'; }
}

function renderTableCard(id, title, columns, rows) {
    const header = columns.map(c => `<th scope="col">${c}</th>`).join("");
    const body = rows.map(r => `<tr>${r.map(cell => `<td>${cell}</td>`).join("")}</tr>`).join("");
    return `<div id="${id}" class="widget-card table-card">
        <div class="kpi-title"><span>${title}</span></div>
        <div class="table-wrapper">
            <table class="compact-table" role="table">
                <thead><tr>${header}</tr></thead>
                <tbody>${body}</tbody>
            </table>
        </div>
    </div>`;
}

function renderBarChartCard(id, title, labels, data, label) {
    setTimeout(() => {
        const canvas = document.getElementById(`${id}-chart`);
        if (canvas) {
            new Chart(canvas.getContext('2d'), {
                type: 'bar',
                data: { labels: labels, datasets: [{ label: label, data: data, backgroundColor: '#007bff' }] },
                options: { responsive: true, plugins: { legend: { display: false } } }
            });
        }
    }, 100);
    return `<div id="${id}" class="widget-card chart-card">
        <div class="kpi-title"><span>${title}</span></div>
        <canvas id="${id}-chart"></canvas>
    </div>`;
}

function renderLineChartCard(id, title, labels, data, label) {
    setTimeout(() => {
        const canvas = document.getElementById(`${id}-chart`);
        if (canvas) {
            new Chart(canvas.getContext('2d'), {
                type: 'line',
                data: { labels: labels, datasets: [{ label: label, data: data, borderColor: '#007bff', fill: false }] },
                options: { responsive: true, plugins: { legend: { display: false } } }
            });
        }
    }, 100);
    return `<div id="${id}" class="widget-card chart-card">
        <div class="kpi-title"><span>${title}</span></div>
        <canvas id="${id}-chart"></canvas>
    </div>`;
}

function renderAlertCard(id, title, alerts) {
    return `<div id="${id}" class="widget-card alert-card">
        <div class="kpi-title"><span>${title}</span></div>
        <ul>${alerts.map(a => `<li><span class="alert-icon">⚠️</span> ${a.tipo}: ${a.dia} (${a.vendas} vendas)</li>`).join("")}</ul>
    </div>`;
}

const CARD_CONFIGS = [
    {
        id: 'card-faturamento-total',
        name: 'Faturamento Total',
        api: '/api/card-faturamento-total/',
        render: function(data) {
            // Valor total
            let valor = `R$ ${data.valor_total?.toLocaleString('pt-BR', {minimumFractionDigits:2}) || '...'}`;
            const overallPct = (data && (typeof data.pct_change !== 'undefined' ? data.pct_change : (typeof data.pct_diff !== 'undefined' ? data.pct_diff : null)));
            const changeHtml = overallPct !== null && typeof overallPct !== 'undefined' ? createChangeBadge(overallPct) : '';
            // Gráfico mensal
            let meses = (data.faturamento_mensal || []).map(item => {
                if (typeof item.mes === 'string' && item.mes.indexOf('-') > -1) {
                    return item.mes.split('-')[1];
                }
                return item.mes;
            });
            let valores = (data.faturamento_mensal || []).map(item => item.faturamento);
            // embed only the chart area here — the outer KPI card already renders the title/value
            let html = `<div style="margin-top:16px">
                        <canvas id="grafico-faturamento-mensal" height="220"></canvas>
                    </div>`;
            setTimeout(() => {
                if (window.Chart && meses.length) {
                    const canvas = document.getElementById('grafico-faturamento-mensal');
                    if (canvas) {
                        if (window.faturamentoChart && typeof window.faturamentoChart.destroy === 'function') {
                            window.faturamentoChart.destroy();
                        }
                        const ctx = canvas.getContext('2d');
                        window.faturamentoChart = new Chart(ctx, {
                            type: 'line',
                            data: {
                                labels: meses,
                                datasets: [{
                                    label: 'Faturamento por mês',
                                    data: valores,
                                    borderColor: '#1976d2',
                                    backgroundColor: 'rgba(25, 118, 210, 0.1)',
                                    fill: true,
                                    tension: 0.3
                                }]
                            },
                            options: {
                                plugins: { legend: { display: false } },
                                scales: {
                                    x: { autoSkip: false, maxRotation: 0, minRotation: 0 },
                                    y: {
                                        title: { display: true, text: 'Faturamento (R$)' },
                                        beginAtZero: true,
                                        ticks: {
                                            stepSize: 5000000,
                                            callback: function(value) { return 'R$ ' + (value/1000000).toFixed(0) + 'M'; }
                                        }
                                    }
                                }
                            }
                        });
                    }
                }
            }, 100);
            // Card de retenção removido para insights
            return renderKPICard('card-faturamento-total', 'Faturamento Total', valor, `<div style="margin-top:16px">${html}</div>`, changeHtml);
        }
    },
    {
        id: 'card-ticket-medio',
        name: 'Ticket Médio',
        api: '/api/card-ticket-medio/',
        render: function(data) {
            const overall = (data && typeof data.ticket_medio !== 'undefined') ? data.ticket_medio : null;
            const value = overall !== null ? `R$ ${overall.toLocaleString('pt-BR', {minimumFractionDigits:2})}` : '...';
            // render optional overall change badge when backend provides a top-level percent change
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
                    // Mostrar apenas o average principal; manter min/max em tooltip (sem traço inline)
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
                subtitle = `<div style="margin-top:10px;text-align:left;max-height:240px;overflow:auto;padding-right:6px;">${items}</div>`;
            }
            const infoIcon = `<span style="margin-left:8px;cursor:pointer;" title="Ticket por canal: média das vendas apenas desse canal. Ticket geral: média de todas as vendas do período."><span style="display:inline-block;width:18px;height:18px;border-radius:50%;background:#e0e0e0;color:#333;text-align:center;line-height:18px;font-weight:bold;font-size:12px;">i</span></span>`;
            return renderKPICard('card-ticket-medio', `Ticket Médio ${infoIcon}`, value, subtitle, changeHtml);
        }
    },
    {
        id: 'card-vendas-por-dia-hora',
        name: 'Vendas por Dia/Hora',
        api: '/api/card-vendas-por-dia-hora/',
        render: data => renderBarChartCard('card-vendas-por-dia-hora', 'Vendas por Dia/Hora', data.labels || [], data.valores || [], 'Vendas')
    },
    {
        id: 'card-produtos-mais-vendidos',
        name: 'Produtos Mais Vendidos',
        api: '/api/card-produtos-mais-vendidos/',
        render: renderProdutosMaisVendidosCard
    },
    {
        id: 'card-produtos-menos-vendidos',
        name: 'Produtos Menos Vendidos',
        api: '/api/card-produtos-menos-vendidos/',
        render: renderProdutosMenosVendidosCard
    },
    {
        id: 'card-mix-produtos',
        name: 'Mix de Produtos',
        api: '/api/card-mix-produtos/',
        render: renderMixProdutosCard
    },
    {
        id: 'card-produtos-mais-customizados',
        name: 'Produtos Mais Customizados',
        api: '/api/card-produtos-mais-customizados/',
        render: renderProdutosMaisCustomizadosCard
    },
    {
        id: 'card-complementos-mais-adicionados',
        name: 'Complementos Mais Adicionados',
        api: '/api/card-itens-complementos-mais-vendidos/',
        render: renderComplementosMaisAdicionadosCard
    },
    {
        id: 'card-complementos-mais-removidos',
        name: 'Complementos Mais Removidos',
        api: '/api/card-complementos-mais-removidos/',
        render: renderComplementosMaisRemovidosCard
    },
    {
        id: 'card-taxa-cancelamento',
        name: 'Taxa de Cancelamento',
        api: '/api/card-taxa-cancelamento/',
        render: function(data) {
            const overall = (data && typeof data.taxa_cancelamento !== 'undefined') ? data.taxa_cancelamento : 0;
            const overallPct = (data && (typeof data.pct_change !== 'undefined' ? data.pct_change : (typeof data.pct_diff !== 'undefined' ? data.pct_diff : null)));
            const changeHtml = overallPct !== null && typeof overallPct !== 'undefined' ? createChangeBadge(overallPct) : '';
            // render a small toggle to switch view mode. Persisted in localStorage per card.
            const mode = getCardViewMode('card-taxa-cancelamento');
            const toggle = `<div style="margin-top:6px;display:flex;gap:6px;align-items:center;"><div style="font-size:0.85em;color:#666">Ver:</div><button class="view-mode-btn" data-mode="pct" style="padding:4px 8px;border-radius:6px;border:1px solid #e6e6e6;background:${mode==='pct'?'#eee':'transparent'}">%</button><button class="view-mode-btn" data-mode="count" style="padding:4px 8px;border-radius:6px;border:1px solid #e6e6e6;background:${mode==='count'?'#eee':'transparent'}">n</button><button class="view-mode-btn" data-mode="money" style="padding:4px 8px;border-radius:6px;border:1px solid #e6e6e6;background:${mode==='money'?'#eee':'transparent'}">R$</button></div>`;
            let subtitle = `<div id="card-taxa-cancelamento-sub" style="margin-top:8px;text-align:left;max-height:160px;overflow:auto;padding-right:6px;">${toggle}<div class="impact-row" style="margin-top:8px;color:#444;font-size:0.95em;">Carregando impacto monetário...</div></div>`;
            const main = `${overall}%`;
            // after render, schedule a background fetch to obtain detailed data (monetary sums)
            setTimeout(() => {
                try {
                    const filters = getGlobalFilters();
                    const url = appendQueryParams('/api/card-taxa-cancelamento/?detail=1', filters);
                    fetch(url).then(r => r.json()).then(d => {
                        const container = document.getElementById('card-taxa-cancelamento-sub');
                        if (!container) return;
                        // compute monetary impact if backend provided values; fallback to compute from returned structures
                        let lostRevenue = null;
                        if (d && typeof d.cancelled_amount !== 'undefined') {
                            lostRevenue = d.cancelled_amount;
                        } else if (d && Array.isArray(d.top_produtos_em_vendas_canceladas)) {
                            // fallback: sum receita from top products as lower-bound (best-effort)
                            lostRevenue = d.top_produtos_em_vendas_canceladas.reduce((s,x)=>s+Number(x.receita||0),0);
                        }
                        const totalRevenue = (d && typeof d.total_revenue !== 'undefined') ? d.total_revenue : null;
                        let impactHtml = '';
                        if (lostRevenue !== null && totalRevenue !== null) {
                            const pct = totalRevenue ? (lostRevenue/totalRevenue*100.0) : 0;
                            impactHtml = `<div><strong>Perda por cancelamento:</strong> ${formatCurrencyBRL(lostRevenue)} (${pct.toFixed(1)}% do faturamento)</div>`;
                        } else if (lostRevenue !== null) {
                            impactHtml = `<div><strong>Perda por cancelamento:</strong> ${formatCurrencyBRL(lostRevenue)}</div>`;
                        } else {
                            impactHtml = `<div><strong>Perda por cancelamento:</strong> dados não disponíveis</div>`;
                        }
                        container.querySelector('.impact-row').innerHTML = impactHtml;
                        // attach toggle handlers
                        Array.from(container.querySelectorAll('.view-mode-btn')).forEach(b => b.addEventListener('click', ev => {
                            const m = b.getAttribute('data-mode');
                            setCardViewMode('card-taxa-cancelamento', m);
                            // simply rerender the small subtitle to reflect mode selection (keep impact as-is)
                            Array.from(container.querySelectorAll('.view-mode-btn')).forEach(x=>x.style.background = (x.getAttribute('data-mode')===m?'#eee':'transparent'));
                            // update main display depending on mode
                            const root = document.getElementById('card-taxa-cancelamento');
                            if (!root) return;
                            const kpiVal = root.querySelector('.kpi-value');
                            if (!kpiVal) return;
                            if (m === 'pct') kpiVal.innerHTML = `${d.taxa_cancelamento || 0}% ${changeHtml || ''}`;
                            else if (m === 'count') kpiVal.innerHTML = `${d.total_cancelled_count || (d.por_canal ? d.por_canal.reduce((s,x)=>s + (x.n_canceladas||0),0) : '...')} cancel.`;
                            else if (m === 'money') kpiVal.innerHTML = `${lostRevenue !== null ? formatCurrencyBRL(lostRevenue) : 'R$ -'} ${changeHtml || ''}`;
                        }));
                    }).catch(e=>{
                        const container = document.getElementById('card-taxa-cancelamento-sub'); if (container) container.querySelector('.impact-row').innerText = 'Erro ao obter dados detalhados.';
                    });
                } catch(e) { console.warn('fetch detailed cancelamento failed', e); }
            }, 50);

            return renderKPICard('card-taxa-cancelamento', 'Taxa de Cancelamento', main, subtitle, changeHtml);
        }
    },
    {
        id: 'card-taxa-desconto',
        name: 'Taxa de Desconto',
        api: '/api/card-taxa-desconto/',
        render: data => {
            const main = `${data.taxa_desconto || 0}%`;
            const overallPct = (data && (typeof data.pct_change !== 'undefined' ? data.pct_change : (typeof data.pct_diff !== 'undefined' ? data.pct_diff : null)));
            const changeHtml = overallPct !== null && typeof overallPct !== 'undefined' ? createChangeBadge(overallPct) : '';
            const mode = getCardViewMode('card-taxa-desconto');
            const toggle = `<div style="margin-top:6px;display:flex;gap:6px;align-items:center;"><div style="font-size:0.85em;color:#666">Ver:</div><button class="view-mode-btn" data-mode="pct" style="padding:4px 8px;border-radius:6px;border:1px solid #e6e6e6;background:${mode==='pct'?'#eee':'transparent'}">%</button><button class="view-mode-btn" data-mode="count" style="padding:4px 8px;border-radius:6px;border:1px solid #e6e6e6;background:${mode==='count'?'#eee':'transparent'}">n</button><button class="view-mode-btn" data-mode="money" style="padding:4px 8px;border-radius:6px;border:1px solid #e6e6e6;background:${mode==='money'?'#eee':'transparent'}">R$</button></div>`;
            const subtitle = `<div id="card-taxa-desconto-sub" style="margin-top:8px;text-align:left;max-height:160px;overflow:auto;padding-right:6px;">${toggle}<div class="impact-row" style="margin-top:8px;color:#444;font-size:0.95em;">Carregando impacto monetário...</div></div>`;
            setTimeout(() => {
                try {
                    const filters = getGlobalFilters();
                    const url = appendQueryParams('/api/card-taxa-desconto/?detail=1', filters);
                    fetch(url).then(r => r.json()).then(d => {
                        const container = document.getElementById('card-taxa-desconto-sub');
                        if (!container) return;
                        // compute discount monetary impact: sum of discounts
                        let discountSum = null;
                        if (d && typeof d.total_discount_amount !== 'undefined') discountSum = d.total_discount_amount;
                        else if (d && Array.isArray(d.top_produtos_com_desconto)) discountSum = d.top_produtos_com_desconto.reduce((s,x)=>s + Number(x.receita||0),0);
                        const totalRevenue = (d && typeof d.total_revenue !== 'undefined') ? d.total_revenue : null;
                        let impactHtml = '';
                        if (discountSum !== null && totalRevenue !== null) {
                            const pct = totalRevenue ? (discountSum / totalRevenue * 100.0) : 0;
                            impactHtml = `<div><strong>Impacto por descontos:</strong> ${formatCurrencyBRL(discountSum)} (${pct.toFixed(1)}% do faturamento)</div>`;
                        } else if (discountSum !== null) {
                            impactHtml = `<div><strong>Impacto por descontos:</strong> ${formatCurrencyBRL(discountSum)}</div>`;
                        } else {
                            impactHtml = `<div><strong>Impacto por descontos:</strong> dados não disponíveis</div>`;
                        }
                        container.querySelector('.impact-row').innerHTML = impactHtml;
                        Array.from(container.querySelectorAll('.view-mode-btn')).forEach(b => b.addEventListener('click', ev => {
                            const m = b.getAttribute('data-mode');
                            setCardViewMode('card-taxa-desconto', m);
                            Array.from(container.querySelectorAll('.view-mode-btn')).forEach(x=>x.style.background = (x.getAttribute('data-mode')===m?'#eee':'transparent'));
                            const root = document.getElementById('card-taxa-desconto'); if (!root) return; const kpiVal = root.querySelector('.kpi-value'); if (!kpiVal) return;
                            if (m === 'pct') kpiVal.innerHTML = `${d.taxa_desconto || 0}% ${changeHtml || ''}`;
                            else if (m === 'count') kpiVal.innerHTML = `${d.total_discount_count || (d.por_canal ? d.por_canal.reduce((s,x)=>s + (x.n_descontos||0),0) : '...')} descontos`;
                            else if (m === 'money') kpiVal.innerHTML = `${discountSum !== null ? formatCurrencyBRL(discountSum) : 'R$ -'} ${changeHtml || ''}`;
                        }));
                    }).catch(e=>{ const container = document.getElementById('card-taxa-desconto-sub'); if (container) container.querySelector('.impact-row').innerText = 'Erro ao obter dados detalhados.'; });
                } catch(e) { console.warn('fetch detailed desconto failed', e); }
            }, 50);
            return renderKPICard('card-taxa-desconto', 'Taxa de Desconto', main, subtitle, changeHtml);
        }
    },
    {
        id: 'card-performance-entrega-regiao',
        name: 'Performance de Entrega por Região',
        api: '/api/card-performance-entrega-regiao/',
        render: function(data) {
            const columns = ['Cidade', 'Bairro', 'Tempo Médio (min)'];
            const rows = (data.tempo_entrega || []).map(e => [e.cidade, e.bairro, e.tempo_medio_min.toFixed(1)]);
            return renderPaginatedListCard('card-performance-entrega-regiao', 'Performance de Entrega por Região', columns, rows, data.page || 1, data.total || 1, 'changePerformanceEntregaRegiaoPage');
        }
    },
    {
        id: 'card-clientes-frequentes',
        name: 'Clientes Frequentes',
        api: '/api/card-clientes-frequentes/',
        render: renderClientesFrequentesCard
    },
    {
        id: 'card-clientes-ausentes',
        name: 'Clientes Ausentes',
        api: '/api/card-clientes-ausentes/',
        render: function(data) {
            const columns = ['Cliente', 'Última Compra'];
            const rows = (data.clientes_ausentes || []).map(c => [c.cliente, c.ultima_compra]);
            return renderPaginatedListCard('card-clientes-ausentes', 'Clientes Ausentes', columns, rows, data.page || 1, data.total || 1, 'changeClientesAusentesPage');
        }
    },
    {
        id: 'card-novos-clientes',
        name: 'Novos Clientes',
        api: '/api/card-novos-clientes/',
        render: function(data) {
            const columns = ['Cliente', 'Primeira Compra', 'Ticket Médio'];
            const rows = (data.novos_clientes || []).map(c => [c.cliente, c.primeira_compra, `R$ ${c.ticket_medio.toLocaleString('pt-BR', {minimumFractionDigits:2})}`]);
            return renderPaginatedListCard('card-novos-clientes', 'Novos Clientes', columns, rows, data.page || 1, data.total || 1, 'changeNovosClientesPage');
        }
    },
    {
        id: 'card-lifetime-value',
        name: 'Lifetime Value (LTV)',
        api: '/api/card-lifetime-value/',
        render: function(data) {
            const main = `R$ ${data.ltv_medio?.toLocaleString('pt-BR', {minimumFractionDigits:2}) || '...'}`;
            // If backend already returned ltv_por_canal, render it directly; otherwise show a placeholder and let the loader fetch fallback
            let subtitleHtml = `<div id="card-ltv-per-canal" style="margin-top:8px;text-align:left;color:#666;font-size:0.95em;">Carregando valor por canal...</div>`;
            if (data && Array.isArray(data.ltv_por_canal) && data.ltv_por_canal.length) {
                const itemsHtml = data.ltv_por_canal.map(i => `<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px dashed #f0f0f0;"><div style="color:#666">${i.canal}</div><div style="font-weight:600">R$ ${Number(i.ltv).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div></div>`).join('');
                subtitleHtml = `<div id="card-ltv-per-canal" data-filled="true" style="margin-top:8px;text-align:left;color:#666;font-size:0.95em;"><div style="max-height:160px;overflow:auto;padding-right:6px;">${itemsHtml}</div></div>`;
            }
            const overallPctLtv = (data && (typeof data.pct_change !== 'undefined' ? data.pct_change : (typeof data.pct_diff !== 'undefined' ? data.pct_diff : null)));
            const changeHtmlLtv = overallPctLtv !== null && typeof overallPctLtv !== 'undefined' ? createChangeBadge(overallPctLtv) : '';
            return renderKPICard('card-lifetime-value', 'Lifetime Value (LTV)', main, subtitleHtml, changeHtmlLtv);
        }
    },
    {
        id: 'card-performance-por-canal',
        name: 'Performance por Canal',
        api: '/api/card-performance-por-canal/',
        render: data => {
            const columns = ['Canal', 'Faturamento', 'Ticket Médio', 'Vendas'];
            const rows = (data.comparativo_canal || []).map(c => [c.canal, `R$ ${c.faturamento.toLocaleString('pt-BR', {minimumFractionDigits:2})}`, `R$ ${c.ticket_medio.toLocaleString('pt-BR', {minimumFractionDigits:2})}`, c.vendas]);
            return renderTableCard('card-performance-por-canal', 'Performance por Canal', columns, rows);
        }
    },
    {
        id: 'card-performance-por-loja',
        name: 'Performance por Loja',
        api: '/api/card-performance-por-loja/',
        render: function(data) {
            const columns = ['Loja', 'Faturamento', 'Ticket Médio', 'Vendas'];
            const rows = (data.comparativo_loja || []).map(l => [l.loja, `R$ ${l.faturamento.toLocaleString('pt-BR', {minimumFractionDigits:2})}`, `R$ ${l.ticket_medio.toLocaleString('pt-BR', {minimumFractionDigits:2})}`, l.vendas]);
            return renderPaginatedListCard('card-performance-por-loja', 'Performance por Loja', columns, rows, data.page || 1, data.total || 1, 'changePerformancePorLojaPage');
        }
    }
];

// Variável global para filtros
var globalFilters = {};
// Função para obter os filtros globais
function getGlobalFilters() {
    return {
        loja: document.getElementById('filtro-loja').value,
        canal: document.getElementById('filtro-canal').value,
        data_inicio: document.getElementById('filtro-data-inicio').value,
        data_fim: document.getElementById('filtro-data-fim').value
    };
}

// Anexa parâmetros de query a uma URL base, escolhendo ? ou & corretamente
function appendQueryParams(baseUrl, filters) {
    try {
        const params = new URLSearchParams();
        if (!filters) return baseUrl;
        if (filters.loja) params.append('loja', filters.loja);
        if (filters.canal) params.append('canal', filters.canal);
        if (filters.data_inicio) params.append('data_inicio', filters.data_inicio);
        if (filters.data_fim) params.append('data_fim', filters.data_fim);
        const s = params.toString();
        if (!s) return baseUrl;
        return baseUrl + (baseUrl.indexOf('?') === -1 ? '?' : '&') + s;
    } catch (e) {
        return baseUrl;
    }
}

// Handlers de navegação para os novos cards paginados
window.changePerformanceEntregaRegiaoPage = function(page) {
    const filters = globalFilters;
    const url = appendQueryParams(`/api/card-performance-entrega-regiao/?page=${page}`, filters);
    fetch(url)
        .then(res => res.json())
        .then(data => {
            document.getElementById('card-performance-entrega-regiao').outerHTML = CARD_CONFIGS.find(c => c.id === 'card-performance-entrega-regiao').render(data);
        });
};

window.changePerformancePorLojaPage = function(page) {
    const filters = globalFilters;
    const url = appendQueryParams(`/api/card-performance-por-loja/?page=${page}`, filters);
    fetch(url)
        .then(res => res.json())
        .then(data => {
            document.getElementById('card-performance-por-loja').outerHTML = CARD_CONFIGS.find(c => c.id === 'card-performance-por-loja').render(data);
        });
};

// Remove stray code and properly define fetchAndRenderCards function
function fetchAndRenderCards() {
    if (window.isRenderingCards) return;
    window.isRenderingCards = true;

    const grid = document.getElementById('dashboard-grid');
    if (!grid) { window.isRenderingCards = false; return; }
    grid.innerHTML = '';
    // determine order: prefer saved order in localStorage
    let order = [];
    try { const raw = localStorage.getItem(ORDER_KEY); if (raw) order = JSON.parse(raw) || []; } catch(e) { order = []; }
    // create ordered list of card configs to render
    const idToCfg = {};
    CARD_CONFIGS.forEach(c => idToCfg[c.id] = c);
    const orderedConfigs = [];
    // append saved order first
    order.forEach(id => { if (idToCfg[id]) orderedConfigs.push(idToCfg[id]); });
    // append any missing configs (new or never-saved)
    CARD_CONFIGS.forEach(c => { if (!orderedConfigs.find(x => x.id === c.id)) orderedConfigs.push(c); });

    orderedConfigs.forEach(card => {
        // respect visibility settings
        if (typeof widgetVisibility[card.id] !== 'undefined' && !widgetVisibility[card.id]) return;
    // solicitando dados para o card (request realizada abaixo)
        fetch(appendQueryParams(card.api, globalFilters))
            .then(res => res.json())
            .then(data => {
                try {
                    grid.insertAdjacentHTML('beforeend', card.render(data));
                    // attach controls and robot analyzer
                    attachCardControls(card.id);
                    try { if (typeof window.attachRobotButton === 'function') window.attachRobotButton(card.id); } catch(e) { console.warn('attachRobotButton failed', e); }
                } catch (e) { console.warn('render insert failed for', card.id, e); }
            })
            .catch(err => {
                console.error('Erro ao buscar dados do card', card.id, err);
                try { grid.insertAdjacentHTML('beforeend', card.render({})); attachCardControls(card.id); } catch(e) { }
            });
    });
    // INSIGHTS_CARDS are rendered by `insights.js` into the dedicated
    // #insights-grid (or dashboard-grid as fallback). Avoid duplicating
    // that rendering here to keep responsibilities separated.
    // Renderiza o card de retenção fora do loop, sempre por último e fora do formulário global
    const retencaoCard = CARD_CONFIGS.find(c => c.id === 'card-retencao-clientes');
    if (retencaoCard) {
        grid.insertAdjacentHTML('beforeend', retencaoCard.render({ info: 'Selecione os filtros e clique em Filtrar Retenção para visualizar os dados.' }));
        setTimeout(() => {
            const btn = document.getElementById('btn-retencao-filtrar');
            if (btn) {
                btn.addEventListener('click', applyRetencaoFilters);
            }
        }, 0);
    }
    // Após renderizar os cards, carregamos dados complementares do LTV (valor por canal)
    setTimeout(() => {
        if (typeof window.loadLtvPerChannel === 'function') {
            try { window.loadLtvPerChannel(); } catch (e) { console.warn('loadLtvPerChannel failed:', e); }
        }
        // initialize sortable and restore order/controls
        try { initSortable(); } catch (e) { console.warn('initSortable failed after render', e); }
        window.isRenderingCards = false;
    }, 150);
}

// -----------------------------
// Card analyzer (robot) helpers
// -----------------------------
// Utility to safely read cookie (for CSRF token if present)
function _getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
}

window.attachRobotButton = function(cardId) {
    try {
        const root = document.getElementById(cardId);
        if (!root) return;
        // avoid duplicate
        if (root.querySelector('.card-robot-btn')) return;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'card-robot-btn';
        btn.title = 'Analisar este card';
        btn.setAttribute('aria-label', 'Analisar este card');
        btn.innerHTML = '🤖';
        btn.addEventListener('click', function(ev) {
            ev.preventDefault();
            ev.stopPropagation();
            if (typeof window.showCardAnalysis === 'function') {
                window.showCardAnalysis(cardId, btn);
            }
        });
        root.style.position = root.style.position || 'relative';
        root.appendChild(btn);
    } catch (e) {
        console.warn('attachRobotButton error', e);
    }
}

window.closeAnalysisPopover = function() {
    const existing = document.getElementById('analysis-popover-global');
    if (existing && existing.parentElement) existing.parentElement.removeChild(existing);
}

window.showCardAnalysis = function(cardId, anchorEl) {
    try {
        window.closeAnalysisPopover();
        const pop = document.createElement('div');
        pop.id = 'analysis-popover-global';
        pop.className = 'card-analysis-popover';
        pop.innerHTML = `<button class="analysis-close" aria-label="Fechar">×</button><div class="analysis-content">Carregando análise...</div>`;
        document.body.appendChild(pop);
        const closeBtn = pop.querySelector('.analysis-close');
        closeBtn.addEventListener('click', () => window.closeAnalysisPopover());

        // position the popover near the anchor with robust placement
        try {
            // Center the popover in the middle of the card element (card may be larger than the robot button)
            const cardRoot = document.getElementById(cardId) || anchorEl.closest('.widget-card') || anchorEl.parentElement;
            const rect = cardRoot.getBoundingClientRect();
            pop.style.position = 'fixed';
            pop.style.zIndex = 9999;
            // temporarily place at 0,0 so we can measure it with current CSS applied
            pop.style.left = '0px';
            pop.style.top = '0px';
            const popRect = pop.getBoundingClientRect();

            // compute center of card and center popover on that point
            let left = rect.left + (rect.width / 2) - (popRect.width / 2);
            let top = rect.top + (rect.height / 2) - (popRect.height / 2);

            // clamp to viewport with small margins
            const margin = 8;
            if (left < margin) left = margin;
            if (left + popRect.width > window.innerWidth - margin) left = window.innerWidth - popRect.width - margin;
            if (top < margin) top = margin;
            if (top + popRect.height > window.innerHeight - margin) top = window.innerHeight - popRect.height - margin;

            pop.style.left = left + 'px';
            pop.style.top = top + 'px';
        } catch (e) {
            // fallback: center around the anchor button if card root detection fails
            const rect = anchorEl.getBoundingClientRect();
            pop.style.position = 'fixed';
            pop.style.zIndex = 9999;
            pop.style.left = (rect.left + rect.width/2 - pop.offsetWidth/2) + 'px';
            pop.style.top = (rect.top + rect.height/2 - pop.offsetHeight/2) + 'px';
        }

        // prepare payload using global filters when available
        const filters = (typeof getGlobalFilters === 'function') ? getGlobalFilters() : globalFilters || {};
        const basePayload = {
            card_id: cardId,
            loja: filters.loja || null,
            canal: filters.canal || null,
            data_inicio: filters.data_inicio || null,
            data_fim: filters.data_fim || null
        };

        const headers = { 'Content-Type': 'application/json' };
        const csrftoken = _getCookie('csrftoken');
        if (csrftoken) headers['X-CSRFToken'] = csrftoken;

        // If there is a Chart.js chart in the card, prefer chart-analysis endpoint
        try {
            const root = document.getElementById(cardId);
            const canvas = root ? root.querySelector('canvas') : null;
            let chartInstance = null;
            if (canvas && window.Chart) {
                // Chart.js v3+: Chart.getChart(canvas) returns instance
                if (typeof Chart.getChart === 'function') {
                    chartInstance = Chart.getChart(canvas);
                }
                // fallback to common global variable naming conventions (e.g., window.faturamentoChart)
                if (!chartInstance) {
                    const tryName = `${cardId.replace(/-/g, '')}Chart`;
                    if (window[tryName]) chartInstance = window[tryName];
                }
            }

            if (chartInstance && chartInstance.data && Array.isArray(chartInstance.data.labels) && Array.isArray(chartInstance.data.datasets)) {
                // extract labels and first dataset values
                const labels = chartInstance.data.labels.slice();
                const values = (chartInstance.data.datasets[0] && Array.isArray(chartInstance.data.datasets[0].data)) ? chartInstance.data.datasets[0].data.slice() : [];

                // basic date range validation
                if (!basePayload.data_inicio || !basePayload.data_fim) {
                    const content = pop.querySelector('.analysis-content');
                    if (content) content.innerText = 'Por favor, selecione um intervalo de datas (Data início e Data fim) antes de pedir a análise.';
                    return;
                }

                const payload = Object.assign({}, basePayload, { labels: labels, values: values });
                fetch('/api/chart-analysis/', { method: 'POST', headers: headers, body: JSON.stringify(payload), credentials: 'same-origin' })
                    .then(res => res.json())
                    .then(resp => {
                        const content = pop.querySelector('.analysis-content');
                        if (!resp) return content && (content.innerText = 'Nenhuma resposta do servidor.');
                        if (resp.error) return content && (content.innerText = 'Erro: ' + resp.error);
                        const a = resp.analysis || resp;
                        if (!a) return content && (content.innerText = 'Sem análise disponível.');
                        let html = `<div class="analysis-title">${a.title || cardId}</div>`;
                        html += `<div class="analysis-body">`;
                        if (typeof a.mean !== 'undefined') html += `<div><strong>Média:</strong> ${a.mean}</div>`;
                        if (a.top) html += `<div><strong>Top:</strong> ${a.top.label} (${a.top.value})</div>`;
                        if (a.bottom) html += `<div><strong>Menor:</strong> ${a.bottom.label} (${a.bottom.value})</div>`;
                        if (typeof a.diff_abs !== 'undefined') html += `<div><strong>Diferença absoluta:</strong> ${a.diff_abs}</div>`;
                        if (typeof a.diff_pct !== 'undefined') html += `<div><strong>Diferença relativa:</strong> ${a.diff_pct}%</div>`;
                        if (a.message) html += `<div style="margin-top:8px;color:#333">${a.message}</div>`;
                        html += `</div>`;
                        content.innerHTML = html;
                        try { renderAnalysisInCard(cardId, a); } catch(e) { console.warn('inline analysis render failed', e); }
                    }).catch(err => {
                        const content = pop.querySelector('.analysis-content');
                        if (content) content.innerText = 'Erro ao buscar análise de gráfico: ' + (err && err.message ? err.message : err);
                    });
                return;
            }
        } catch (e) {
            console.warn('chart detection/analysis fallback', e);
        }

        // Quick first-vs-last analysis for list/table cards (client-side, no server call)
        try {
            const root = document.getElementById(cardId);
            if (root) {
                // TABLE variant
                const table = root.querySelector('table.compact-table, .table-wrapper table');
                if (table) {
                    let tbody = table.tBodies && table.tBodies.length ? table.tBodies[0] : table.querySelector('tbody');
                    const rows = tbody ? Array.from(tbody.querySelectorAll('tr')) : Array.from(table.querySelectorAll('tr'));
                    if (rows.length >= 1) {
                        const firstCells = Array.from(rows[0].querySelectorAll('td,th'));
                        const lastCells = Array.from(rows[rows.length-1].querySelectorAll('td,th'));
                        function parseCellNumeric(cells) {
                            for (let i = cells.length - 1; i >= 0; i--) {
                                const txt = (cells[i].innerText || '').trim();
                                if (!txt) continue;
                                // normalize pt-BR numbers: remove thousands separators and convert , to .
                                const cleaned = txt.replace(/[^0-9,\-\.]/g, '').replace(/\./g, '').replace(/,/g, '.');
                                const num = Number(cleaned);
                                if (!isNaN(num)) return { num: num, text: txt };
                            }
                            return null;
                        }
                        const firstVal = parseCellNumeric(firstCells);
                        const lastVal = parseCellNumeric(lastCells);
                        const firstLabel = (firstCells[0] && firstCells[0].innerText) ? firstCells[0].innerText.trim() : 'Primeiro';
                        const lastLabel = (lastCells[0] && lastCells[0].innerText) ? lastCells[0].innerText.trim() : 'Último';
                        if (firstVal && lastVal) {
                            const diff_abs = firstVal.num - lastVal.num;
                            const diff_pct = (lastVal.num === 0) ? null : (diff_abs / Math.abs(lastVal.num)) * 100;
                            const content = pop.querySelector('.analysis-content');
                            let html = `<div class="analysis-title">${firstLabel} vs ${lastLabel}</div>`;
                            html += `<div class="analysis-body">`;
                            html += `<div><strong>${firstLabel}:</strong> ${firstVal.text}</div>`;
                            html += `<div><strong>${lastLabel}:</strong> ${lastVal.text}</div>`;
                            html += `<div><strong>Diferença absoluta:</strong> ${diff_abs.toLocaleString('pt-BR', {maximumFractionDigits:2})}</div>`;
                            if (diff_pct !== null) html += `<div><strong>Diferença relativa:</strong> ${diff_pct.toLocaleString('pt-BR', {maximumFractionDigits:1})}%</div>`;
                            html += `</div>`;
                            content.innerHTML = html;
                            return;
                        }
                    }
                }

                // UL/OL variant: try to find numeric values inside list items
                const list = root.querySelector('ul, ol, .retencao-list');
                if (list) {
                    const items = Array.from(list.querySelectorAll('li'));
                    if (items.length >= 1) {
                        function extractNumber(el) {
                            const txt = (el.innerText || '').trim();
                            const cleaned = txt.replace(/[^0-9,\-\.]/g, '').replace(/\./g, '').replace(/,/g, '.');
                            const n = Number(cleaned);
                            return isNaN(n) ? null : { num: n, text: txt };
                        }
                        const first = items[0];
                        const last = items[items.length - 1];
                        const firstNum = extractNumber(first);
                        const lastNum = extractNumber(last);
                        const firstLabel = (first.childNodes && first.childNodes[0] && first.childNodes[0].textContent) ? first.childNodes[0].textContent.trim() : first.innerText.trim();
                        const lastLabel = (last.childNodes && last.childNodes[0] && last.childNodes[0].textContent) ? last.childNodes[0].textContent.trim() : last.innerText.trim();
                        if (firstNum && lastNum) {
                            const diff_abs = firstNum.num - lastNum.num;
                            const diff_pct = (lastNum.num === 0) ? null : (diff_abs / Math.abs(lastNum.num)) * 100;
                            const content = pop.querySelector('.analysis-content');
                            let html = `<div class="analysis-title">${firstLabel} vs ${lastLabel}</div>`;
                            html += `<div class="analysis-body">`;
                            html += `<div><strong>${firstLabel}:</strong> ${firstNum.text}</div>`;
                            html += `<div><strong>${lastLabel}:</strong> ${lastNum.text}</div>`;
                            html += `<div><strong>Diferença absoluta:</strong> ${diff_abs.toLocaleString('pt-BR', {maximumFractionDigits:2})}</div>`;
                            if (diff_pct !== null) html += `<div><strong>Diferença relativa:</strong> ${diff_pct.toLocaleString('pt-BR', {maximumFractionDigits:1})}%</div>`;
                            html += `</div>`;
                            content.innerHTML = html;
                            return;
                        }
                    }
                }
            }
        } catch (e) {
            console.warn('list first/last analysis failed', e);
        }

        // Fallback: card-level analysis endpoint (unchanged behavior)
        // Validate required fields before attempting the POST to avoid 400 responses
        if (!basePayload.data_inicio || !basePayload.data_fim) {
            const content = pop.querySelector('.analysis-content');
            if (content) content.innerText = 'Por favor, selecione um intervalo de datas (Data início e Data fim) antes de pedir a análise.';
            return;
        }

        fetch('/api/card-analysis/', { method: 'POST', headers: headers, body: JSON.stringify(basePayload), credentials: 'same-origin' })
            .then(res => res.json())
            .then(data => {
                const content = pop.querySelector('.analysis-content');
                if (!data) return content && (content.innerText = 'Nenhuma resposta do servidor.');
                if (data.error) return content && (content.innerText = 'Erro: ' + data.error);
                const a = data.analysis || data;
                if (!a) return content && (content.innerText = 'Sem análise disponível.');
                let html = `<div class="analysis-title">${a.metric_name || cardId}</div>`;
                html += `<div class="analysis-body">`;
                html += `<div><strong>Atual:</strong> ${a.current}</div>`;
                html += `<div><strong>Anterior:</strong> ${a.previous}</div>`;
                if (typeof a.pct_change !== 'undefined' && a.pct_change !== null) html += `<div><strong>Variação:</strong> ${a.pct_change}%</div>`;
                if (a.message) html += `<div style="margin-top:8px;color:#333">${a.message}</div>`;
                html += `</div>`;
                content.innerHTML = html;
                try { renderAnalysisInCard(cardId, a); } catch(e) { console.warn('inline analysis render failed', e); }
            }).catch(err => {
                const content = pop.querySelector('.analysis-content');
                if (content) content.innerText = 'Erro ao buscar análise: ' + (err && err.message ? err.message : err);
            });
    } catch (e) {
        console.error('showCardAnalysis error', e);
    }
}

function applyGlobalFilters(event) {
    event.preventDefault();
    globalFilters = getGlobalFilters();
    // Re-render main dashboard cards
    fetchAndRenderCards();
    // Also re-render insights cards (crescimento, produto sazonal, etc.) when present
    // This ensures cards rendered by `insights.js` react to global filter changes.
    try { if (typeof fetchAndRenderInsightsCards === 'function') fetchAndRenderInsightsCards(); } catch(e) { console.warn('re-render insights failed', e); }
}

function applyGlobalFilters(event) {
    event.preventDefault();
    globalFilters = getGlobalFilters();
    // Re-render main dashboard cards
    fetchAndRenderCards();
    // Also update insights cards if the insights renderer is available
    try { if (typeof fetchAndRenderInsightsCards === 'function') fetchAndRenderInsightsCards(); } catch(e) { console.warn('re-render insights failed', e); }
}

// Use addEventListener para evitar sobrescrever outros handlers
window.addEventListener('load', function() {
    try {
    // inicialização do dashboard
    globalFilters = getGlobalFilters();
        if (typeof initDashboard === 'function') {
            // initDashboard may fetch server-side saved layout before rendering
            initDashboard().then(() => {
                fetchAndRenderCards();
            }).catch(() => { fetchAndRenderCards(); });
        } else {
            console.warn('initDashboard is not defined');
            fetchAndRenderCards();
        }
        // Save layout when user closes the tab or navigates away
        try {
            window.addEventListener('beforeunload', function() { try { saveLayoutToServer(); } catch (e) {} });
            document.addEventListener('visibilitychange', function() { if (document.visibilityState === 'hidden') { try { saveLayoutToServer(); } catch (e) {} } });
        } catch (e) { /* ignore */ }
    // inicialização do dashboard finalizada
    } catch (err) {
        console.error('Erro em window.load handler:', err);
    }
});

function renderProdutosMaisVendidosCard(data) {
    const columns = ['Produto', 'Quantidade', 'Receita'];
    const rows = (data.top_produtos || []).map(p => [p.produto, p.quantidade, `R$ ${p.receita.toLocaleString('pt-BR', {minimumFractionDigits:2})}`]);
    if (!rows || rows.length === 0) {
        return `<div id="card-produtos-mais-vendidos" class="widget-card table-card">
            <div class="kpi-title"><span>Produtos Mais Vendidos</span></div>
            <div style="padding:28px;text-align:center;color:#666;font-size:1.05em;">Por favor, aplique um filtro de período (Data início e Data fim) para visualizar resultados.</div>
        </div>`;
    }
    return renderPaginatedListCard('card-produtos-mais-vendidos', 'Produtos Mais Vendidos', columns, rows, data.page, data.total, 'changeProdutosMaisVendidosPage');
}
window.changeProdutosMaisVendidosPage = function(page) {
    const filters = globalFilters;
    const url = appendQueryParams(`/api/card-produtos-mais-vendidos/?page=${page}`, filters);
    fetch(url)
        .then(res => res.json())
        .then(data => {
            document.getElementById('card-produtos-mais-vendidos').outerHTML = renderProdutosMaisVendidosCard(data);
        });
};

function renderProdutosMenosVendidosCard(data) {
    const columns = ['Produto', 'Quantidade', 'Receita'];
    const rows = (data.bottom_produtos || []).map(p => [p.produto, p.quantidade, `R$ ${p.receita.toLocaleString('pt-BR', {minimumFractionDigits:2})}`]);
    if (!rows || rows.length === 0) {
        return `<div id="card-produtos-menos-vendidos" class="widget-card table-card">
            <div class="kpi-title"><span>Produtos Menos Vendidos</span></div>
            <div style="padding:28px;text-align:center;color:#666;font-size:1.05em;">Por favor, aplique um filtro de período (Data início e Data fim) para visualizar resultados.</div>
        </div>`;
    }
    return renderPaginatedListCard('card-produtos-menos-vendidos', 'Produtos Menos Vendidos', columns, rows, data.page, data.total, 'changeProdutosMenosVendidosPage');
}
window.changeProdutosMenosVendidosPage = function(page) {
    const filters = globalFilters;
    const url = appendQueryParams(`/api/card-produtos-menos-vendidos/?page=${page}`, filters);
    fetch(url)
        .then(res => res.json())
        .then(data => {
            document.getElementById('card-produtos-menos-vendidos').outerHTML = renderProdutosMenosVendidosCard(data);
        });
};

function renderProdutosMaisCustomizadosCard(data) {
    // Suporta formatos antigos e o novo retorno { top_customizacoes: [...] }
    let produtos = data.produtos_mais_customizados || data.top_customizacoes || [];
    // Normaliza chaves para compatibilidade: aceita 'customizacoes' ou 'vezes_customizado'
    produtos = produtos.map(p => ({
        produto: p.produto || p.name || p.produto_nome || '',
        customizacoes: (typeof p.customizacoes !== 'undefined') ? p.customizacoes : (typeof p.vezes_customizado !== 'undefined' ? p.vezes_customizado : 0),
        receita: (typeof p.receita !== 'undefined') ? p.receita : (typeof p.revenue !== 'undefined' ? p.revenue : 0)
    })).sort((a, b) => b.customizacoes - a.customizacoes);
    if (produtos.length === 0) {
        return `<div id="card-produtos-mais-customizados" class="widget-card">
            <div class="kpi-title"><span>Produtos Mais Customizados</span></div>
            <div style="padding:28px;text-align:center;color:#666;font-size:1.05em;">Por favor, aplique um filtro de período (Data início e Data fim) para visualizar resultados.</div>
        </div>`;
    }
    let html = `<div id="card-produtos-mais-customizados" class="widget-card">
        <div class="kpi-title"><span>Produtos Mais Customizados</span></div>
        <div style="display:flex;font-weight:600;color:#444;border-bottom:2px solid #eee;padding-bottom:6px;margin-bottom:8px;">
            <div style="flex:2;">Produto</div>
            <div style="flex:1;text-align:right;">Vezes Customizado</div>
        </div>
        <ul style="list-style:none;padding:0;margin:0;">
            ${produtos.map(p => `
                <li style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #eee;">
                    <div style="flex:2;color:#333;">${p.produto}</div>
                    <div style="flex:1;text-align:right;color:#007bff;font-weight:500;">${p.customizacoes}</div>
                </li>
            `).join('')}
        </ul>
    </div>`;
    return html;
}
window.changeProdutosMaisCustomizadosPage = function(page) {
    const filters = globalFilters;
    const url = appendQueryParams(`/api/card-produtos-mais-customizados/?page=${page}`, filters);
    fetch(url)
        .then(res => res.json())
        .then(data => {
            document.getElementById('card-produtos-mais-customizados').outerHTML = renderProdutosMaisCustomizadosCard(data);
        });
};

function renderItensComplementosMaisVendidosCard(data) {
    // Implementação do card de itens/complementos mais vendidos
    const columns = ['Item/Complemento', 'Quantidade'];
    const rows = (data.top_itens_complementos || []).map(i => [i.item, i.quantidade]);
    return renderPaginatedListCard('card-itens-complementos-mais-vendidos', 'Itens/Complementos Mais Vendidos', columns, rows, data.page, data.total, 'changeItensComplementosMaisVendidosPage');
}

// Card Complementos Mais Adicionados
function renderComplementosMaisAdicionadosCard(data) {
    const infoIcon = `<span style="margin-left:8px;cursor:pointer;" title="Card não segue o filtro global por se tratar de uma análise macro"><span style="display:inline-block;width:18px;height:18px;border-radius:50%;background:#e0e0e0;color:#333;text-align:center;line-height:18px;font-weight:bold;font-size:14px;" aria-label="Informação">i</span></span>`;
    const adicionais = data.adicionais || [];
    if (adicionais.length === 0) {
        return `<div id="card-complementos-mais-adicionados" class="widget-card chart-card">
            <div class="kpi-title"><span>Complementos Mais Adicionados</span></div>
            <div style="margin-top:4px; margin-bottom:4px; text-align:left;">${infoIcon}</div>
            <div style="padding:32px;text-align:center;color:#888;font-size:1.1em;">Nenhum dado disponível.</div>
        </div>`;
    }
    const labels = adicionais.map(i => i.adicional);
    const values = adicionais.map(i => i.vezes_utilizado);
    setTimeout(() => {
        const canvas = document.getElementById('card-complementos-mais-adicionados-pie');
        if (canvas) {
            if (window.complementosAdicionadosChart && typeof window.complementosAdicionadosChart.destroy === 'function') {
                window.complementosAdicionadosChart.destroy();
            }
            window.complementosAdicionadosChart = new Chart(canvas.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Vezes utilizados',
                        data: values,
                        backgroundColor: '#007bff',
                        borderRadius: 6,
                        maxBarThickness: 48
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: { padding: { top: 8, bottom: 8, left: 8, right: 8 } },
                    plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
                    scales: {
                        x: {
                            stacked: false,
                            ticks: { autoSkip: true, maxRotation: 45, minRotation: 0 },
                            grid: { display: false }
                        },
                        y: { beginAtZero: true, ticks: { precision: 0 } }
                    },
                    elements: { bar: { barPercentage: 0.7, categoryPercentage: 0.75 } }
                }
            });
        }
    }, 100);
    return `<div id="card-complementos-mais-adicionados" class="widget-card chart-card">
        <div class="kpi-title"><span>Complementos Mais Adicionados</span></div>
        <div style="margin-top:4px; margin-bottom:4px; text-align:left;">${infoIcon}</div>
        <canvas id="card-complementos-mais-adicionados-pie"></canvas>
    </div>`;
}

// Card Complementos Mais Removidos
function renderComplementosMaisRemovidosCard(data) {
    const infoIcon = `<span style="margin-left:8px;cursor:pointer;" title="Card não segue o filtro global por se tratar de uma análise macro"><span style="display:inline-block;width:18px;height:18px;border-radius:50%;background:#e0e0e0;color:#333;text-align:center;line-height:18px;font-weight:bold;font-size:14px;" aria-label="Informação">i</span></span>`;
    const removidos = data.removidos || [];
    if (removidos.length === 0) {
        return `<div id="card-complementos-mais-removidos" class="widget-card chart-card">
            <div class="kpi-title"><span>Complementos Mais Removidos</span></div>
            <div style="margin-top:4px; margin-bottom:4px; text-align:left;">${infoIcon}</div>
            <div style="padding:32px;text-align:center;color:#888;font-size:1.1em;">Nenhum dado disponível.</div>
        </div>`;
    }
    const labels = removidos.map(i => i.complemento_removido);
    const values = removidos.map(i => i.vezes_removido);
    setTimeout(() => {
        const canvas = document.getElementById('card-complementos-mais-removidos-pie');
        if (canvas) {
            if (window.complementosRemovidosChart && typeof window.complementosRemovidosChart.destroy === 'function') {
                window.complementosRemovidosChart.destroy();
            }
            window.complementosRemovidosChart = new Chart(canvas.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Vezes removido',
                        data: values,
                        backgroundColor: '#dc3545',
                        borderRadius: 6,
                        maxBarThickness: 48
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: { padding: { top: 8, bottom: 8, left: 8, right: 8 } },
                    plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
                    scales: {
                        x: { ticks: { autoSkip: true, maxRotation: 45, minRotation: 0 }, grid: { display: false } },
                        y: { beginAtZero: true, ticks: { precision: 0 } }
                    },
                    elements: { bar: { barPercentage: 0.7, categoryPercentage: 0.75 } }
                }
            });
        }
    }, 100);
    return `<div id="card-complementos-mais-removidos" class="widget-card chart-card">
        <div class="kpi-title"><span>Complementos Mais Removidos</span></div>
        <div style="margin-top:4px; margin-bottom:4px; text-align:left;">${infoIcon}</div>
        <canvas id="card-complementos-mais-removidos-pie"></canvas>
    </div>`;
}

window.loadComplementosMaisAdicionadosCard = function() {
    fetch('/api/card-complementos-mais-adicionados/')
        .then(res => res.json())
        .then(data => {
            document.getElementById('card-complementos-mais-adicionados').outerHTML = renderComplementosMaisAdicionadosCard(data);
        });
}

window.loadComplementosMaisRemovidosCard = function() {
    fetch('/api/card-complementos-mais-removidos/')
        .then(res => res.json())
        .then(data => {
            document.getElementById('card-complementos-mais-removidos').outerHTML = renderComplementosMaisRemovidosCard(data);
        });
}
window.changeItensComplementosMaisVendidosPage = function(page) {
    // Card macro, não tem paginação nem filtro global
    fetch('/api/card-itens-complementos-mais-vendidos/')
        .then(res => res.json())
        .then(data => {
            document.getElementById('card-itens-complementos-mais-vendidos').outerHTML = renderItensComplementosMaisVendidosCard(data);
        });
};

function renderClientesAusentesCard(data) {
    // If backend provided an info message (e.g., loja + date range + no data), show it
    if (data && data.info) {
        return `<div id="card-clientes-ausentes" class="widget-card table-card">
            <div class="kpi-title"><span>Clientes Ausentes</span></div>
            <div style="padding:28px;text-align:center;color:#666;font-size:1.05em;">${data.info}</div>
        </div>`;
    }
    const columns = ['Cliente', 'Última Compra'];
    const rows = (data.clientes_ausentes || []).map(c => [c.cliente, c.ultima_compra]);
    if (!rows || rows.length === 0) {
        return `<div id="card-clientes-ausentes" class="widget-card table-card">
            <div class="kpi-title"><span>Clientes Ausentes</span></div>
            <div style="padding:28px;text-align:center;color:#666;font-size:1.05em;">Nenhum cliente ausente encontrado para os filtros informados.</div>
        </div>`;
    }
    return renderPaginatedListCard('card-clientes-ausentes', 'Clientes Ausentes', columns, rows, data.page, data.total, 'changeClientesAusentesPage');
}
window.changeClientesAusentesPage = function(page) {
    const filters = globalFilters;
    const url = appendQueryParams(`/api/card-clientes-ausentes/?page=${page}`, filters);
    fetch(url)
        .then(res => res.json())
        .then(data => {
            document.getElementById('card-clientes-ausentes').outerHTML = renderClientesAusentesCard(data);
        });
};

function renderNovosClientesCard(data) {
    if (data && data.info) {
        return `<div id="card-novos-clientes" class="widget-card table-card">
            <div class="kpi-title"><span>Novos Clientes</span></div>
            <div style="padding:28px;text-align:center;color:#666;font-size:1.05em;">${data.info}</div>
        </div>`;
    }
    const columns = ['Cliente', 'Primeira Compra', 'Ticket Médio'];
    const rows = (data.novos_clientes || []).map(c => [c.cliente, c.primeira_compra, `R$ ${c.ticket_medio.toLocaleString('pt-BR', {minimumFractionDigits:2})}`]);
    if (!rows || rows.length === 0) {
        return `<div id="card-novos-clientes" class="widget-card table-card">
            <div class="kpi-title"><span>Novos Clientes</span></div>
            <div style="padding:28px;text-align:center;color:#666;font-size:1.05em;">Nenhum novo cliente encontrado para os filtros informados.</div>
        </div>`;
    }
    return renderPaginatedListCard('card-novos-clientes', 'Novos Clientes', columns, rows, data.page, data.total, 'changeNovosClientesPage');
}
window.changeNovosClientesPage = function(page) {
    const filters = globalFilters;
    const url = appendQueryParams(`/api/card-novos-clientes/?page=${page}`, filters);
    fetch(url)
        .then(res => res.json())
        .then(data => {
            document.getElementById('card-novos-clientes').outerHTML = renderNovosClientesCard(data);
        });
};

// Carrega e popula o campo "valor por canal" dentro do card LTV
window.loadLtvPerChannel = function() {
    const container = document.getElementById('card-ltv-per-canal');
    if (!container) return;
    // If render already populated the container (backend provided ltv_por_canal), skip fetching
    if (container.dataset && container.dataset.filled === 'true') return;
    const url = appendQueryParams('/api/card-performance-por-canal/', globalFilters);
    fetch(url)
        .then(res => res.json())
        .then(data => {
            const items = data.comparativo_canal || [];
            if (!items || items.length === 0) {
                container.innerHTML = `<div style="color:#666">Nenhum dado por canal disponível para o período selecionado.</div>`;
                return;
            }
            const html = items.map(i => `<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px dashed #f0f0f0;"><div style="color:#666">${i.canal}</div><div style="font-weight:600">R$ ${Number(i.faturamento).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div></div>`).join('');
            container.innerHTML = `<div style="max-height:160px;overflow:auto;padding-right:6px;">${html}</div>`;
        })
        .catch(err => {
            console.warn('Erro ao carregar LTV por canal:', err);
            container.innerHTML = `<div style="color:#666">Não foi possível carregar dados por canal.</div>`;
        });
}

function renderMixProdutosCard(data) {
    const columns = ['Combinação', 'Quantidade'];
    // Backwards/forwards compatibility: prefer `top_combos` (array of {produtos: [], quantidade})
    // but also accept `combos` (array of {combinacao: 'A, B', quantidade})
    let combos = [];
    if (data && Array.isArray(data.top_combos)) combos = data.top_combos;
    else if (data && Array.isArray(data.combos)) combos = data.combos;
    // Normalize each entry to { produtos: [...], quantidade: N }
    const normalized = combos.map(c => {
        if (!c) return { produtos: [], quantidade: 0 };
        if (Array.isArray(c.produtos)) return { produtos: c.produtos, quantidade: Number(c.quantidade || c.qty || c.count || 0) };
        if (typeof c.combinacao === 'string') {
            const produtos = c.combinacao.split(',').map(s => s.trim()).filter(Boolean);
            return { produtos: produtos, quantidade: Number(c.quantidade || c.qty || c.count || 0) };
        }
        // fallback: try to coerce any remaining shapes
        if (typeof c === 'string') return { produtos: [c], quantidade: 0 };
        return { produtos: c.produtos || [], quantidade: Number(c.quantidade || c.qty || c.count || 0) };
    });

    // Determine how many items to display: backend may provide data.max_items or client defaults to 10
    const maxItems = (data && (typeof data.max_items !== 'undefined')) ? Number(data.max_items) : 10;
    const rows = normalized.slice(0, maxItems).map(c => [ (c.produtos || []).join(', '), (c.quantidade || 0) ]);
    if (!rows || rows.length === 0) {
        return `<div id="card-mix-produtos" class="widget-card table-card">
            <div class="kpi-title"><span>Mix de Produtos</span></div>
            <div style="padding:28px;text-align:center;color:#666;font-size:1.05em;">Por favor, aplique um filtro de período (Data início e Data fim) para visualizar resultados.</div>
        </div>`;
    }
    return renderPaginatedListCard('card-mix-produtos', 'Mix de Produtos', columns, rows, data.page, data.total, 'changeMixProdutosPage');
}
window.changeMixProdutosPage = function(page) {
    const filters = globalFilters;
    const url = appendQueryParams(`/api/card-mix-produtos/?page=${page}`, filters);
    fetch(url)
        .then(res => res.json())
        .then(data => {
            document.getElementById('card-mix-produtos').outerHTML = renderMixProdutosCard(data);
        });
};

function renderClientesFrequentesCard(data) {
    const columns = ['Cliente', 'Compras', 'Ticket Médio'];
    const rows = (data.top_clientes || []).map(c => [c.cliente, c.compras, `R$ ${c.ticket_medio.toLocaleString('pt-BR', {minimumFractionDigits:2})}`]);
    return renderPaginatedListCard('card-clientes-frequentes', 'Clientes Frequentes', columns, rows, data.page, data.total, 'changeClientesFrequentesPage');
}
window.changeClientesFrequentesPage = function(page) {
    const filters = globalFilters;
    const url = appendQueryParams(`/api/card-clientes-frequentes/?page=${page}`, filters);
    fetch(url)
        .then(res => res.json())
        .then(data => {
            document.getElementById('card-clientes-frequentes').outerHTML = renderClientesFrequentesCard(data);
        });
};

// arquivo terminado - balanceando chaves faltantes

