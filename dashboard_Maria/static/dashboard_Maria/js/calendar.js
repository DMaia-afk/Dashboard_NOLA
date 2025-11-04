// Simple year calendar with holidays + per-day notes saved to localStorage
// Calendário anual simples com feriados + notas por dia salvas no localStorage
(function(){
    const calendarEl = document.getElementById('calendar');
    const selectedDayInfo = document.getElementById('selected-day-info');
    const noteText = document.getElementById('note-text');
    const saveBtn = document.getElementById('save-note');
    const clearBtn = document.getElementById('clear-note');
    const yearPrev = document.getElementById('year-prev');
    const yearNext = document.getElementById('year-next');

    let currentYear = new Date().getFullYear();
    let selectedDate = null;
    let currentView = { type: 'overview', year: currentYear };

    // minimal set of Brazilian national holidays (fixed/approx)
    // conjunto mínimo de feriados nacionais brasileiros (fixos/aproximados)
    const holidays = {
        // format YYYY-MM-DD -> name, but we build per-year
        // formato YYYY-MM-DD -> nome, mas construímos por ano
    };

    function buildHolidaysForYear(y){
        const hs = {};
        // Fixed-date holidays
        // Feriados de data fixa
        const fixed = {
            '01-01': 'Confraternização Universal',
            '04-21': 'Tiradentes',
            '05-01': 'Dia do Trabalhador',
            '09-07': 'Independência',
            '10-12': 'Nossa Senhora Aparecida',
            '11-02': 'Finados',
            '11-15': 'Proclamação da República',
            '12-25': 'Natal'
        };
        Object.keys(fixed).forEach(k=> hs[`${y}-${k}`] = fixed[k]);
        // Note: movable holidays (Carnaval, Páscoa) are complex; keep minimal for now
        // Nota: feriados móveis (Carnaval, Páscoa) são complexos; manter mínimo por enquanto
        return hs;
    }

    // Provide a simple in-browser mock API for calendar notes.
    // Fornece uma API mock simples no navegador para notas do calendário.
    // Stored under localStorage keys prefixed with `mock_calendar_notes_`.
    // Armazenado sob chaves localStorage prefixadas com `mock_calendar_notes_`.
    window.calendarNotesMock = window.calendarNotesMock || {
        enabled: true,
        prefix: 'mock_calendar_notes_',
        get(year) {
            try { return JSON.parse(localStorage.getItem(this.prefix + year) || '{}'); } catch (e) { return {}; }
        },
        set(year, notes) {
            try { localStorage.setItem(this.prefix + year, JSON.stringify(notes)); } catch (e) { /* ignore */ }
        },
        clear(year) { try { localStorage.removeItem(this.prefix + year); } catch (e) {} }
    };

    function loadNotes(year){
        if (window.calendarNotesMock && window.calendarNotesMock.enabled) return window.calendarNotesMock.get(year);
        try{ return JSON.parse(localStorage.getItem(`calendar_notes_${year}`) || '{}'); }catch(e){ return {}; }
    }
    function saveNotes(year, notes){
        if (window.calendarNotesMock && window.calendarNotesMock.enabled) return window.calendarNotesMock.set(year, notes);
        try{ localStorage.setItem(`calendar_notes_${year}`, JSON.stringify(notes)); }catch(e){}
    }

    // Render a compact month overview (12 tiles). Clicking a month opens the month detail.
    // Renderizar uma visão geral compacta do mês (12 tiles). Clicar em um mês abre o detalhe do mês.
    function renderYear(y){
        currentView = { type: 'overview', year: y };
        calendarEl.innerHTML = '';
        const headerRow = document.createElement('div');
        headerRow.style.display = 'flex';
        headerRow.style.justifyContent = 'space-between';
        headerRow.style.alignItems = 'center';
        headerRow.style.marginBottom = '8px';
        const title = document.createElement('h2'); title.textContent = y; headerRow.appendChild(title);
        const controls = document.createElement('div'); controls.className = 'calendar-controls'; headerRow.appendChild(controls);
        calendarEl.appendChild(headerRow);

        const notes = loadNotes(y);

        const overview = document.createElement('div'); overview.className = 'months-overview';
        overview.style.display = 'grid';
        overview.style.gridTemplateColumns = 'repeat(4, 1fr)';
        overview.style.gap = '12px';

        for(let m=0;m<12;m++){
            const monthTile = document.createElement('div');
            monthTile.className = 'month-tile';
            monthTile.style.padding = '18px';
            monthTile.style.borderRadius = '12px';
            monthTile.style.background = 'linear-gradient(180deg,#fff,#fbfdff)';
            monthTile.style.boxShadow = '0 8px 20px rgba(2,6,23,0.06)';
            monthTile.style.cursor = 'pointer';
            const monthNameFull = new Date(y, m, 1).toLocaleString('pt-BR', { month: 'long' });
            const label = document.createElement('div'); label.style.fontWeight='800'; label.style.marginBottom='8px'; label.textContent = `${String(m+1).padStart(2,'0')} — ${monthNameFull.charAt(0).toUpperCase()+monthNameFull.slice(1)}`;
            monthTile.appendChild(label);
            // show a small count of notes in that month
            // mostrar uma pequena contagem de notas naquele mês
            const count = Object.keys(notes || {}).filter(d => d.startsWith(`${y}-${String(m+1).padStart(2,'0')}`)).length;
            const meta = document.createElement('div'); meta.style.color='#6b7280'; meta.textContent = `${count} anotação${count !== 1 ? 's' : ''}`;
            monthTile.appendChild(meta);
            monthTile.addEventListener('click', ()=> renderMonthDetail(y, m+1));
            overview.appendChild(monthTile);
        }

        calendarEl.appendChild(overview);
    }

    // Render a single month's detail view (days grid). Includes a back button to months overview.
    // Renderizar a visão de detalhe de um único mês (grade de dias). Inclui um botão voltar para visão geral dos meses.
    function renderMonthDetail(year, month){
        currentView = { type: 'month', year: year, month: month };
        calendarEl.innerHTML = '';
        const headerRow = document.createElement('div');
        headerRow.style.display = 'flex';
        headerRow.style.justifyContent = 'space-between';
        headerRow.style.alignItems = 'center';
        headerRow.style.marginBottom = '8px';
        const title = document.createElement('h2'); title.textContent = `${String(month).padStart(2,'0')} / ${year}`; headerRow.appendChild(title);
        const back = document.createElement('button'); back.className = 'btn-secondary'; back.textContent = '← Voltar';
        back.addEventListener('click', ()=> renderYear(year));
        headerRow.appendChild(back);
        calendarEl.appendChild(headerRow);

        const notes = loadNotes(year);
        const hs = buildHolidaysForYear(year);

        const monthGrid = document.createElement('div'); monthGrid.className = 'month-grid';
        monthGrid.style.gridTemplateColumns = 'repeat(7,1fr)'; monthGrid.style.display = 'grid'; monthGrid.style.gap = '6px';

        // weekday headers
        // cabeçalhos dos dias da semana
        const weekdayNames = ['Dom','Seg','Ter','Qua','Qui','Sex','Sab'];
        weekdayNames.forEach(w => { const h = document.createElement('div'); h.style.fontWeight='700'; h.style.fontSize='0.85rem'; h.style.textAlign='center'; h.style.color='#6b7280'; h.textContent = w; monthGrid.appendChild(h); });

        const first = new Date(year, month-1, 1);
        const startWeekDay = first.getDay();
        const daysInMonth = new Date(year, month, 0).getDate();

        for(let i=0;i<startWeekDay;i++){ const e=document.createElement('div'); monthGrid.appendChild(e); }

        for(let d=1; d<=daysInMonth; d++){
            const dateStr = `${year}-${String(month).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
            const cell = document.createElement('div'); cell.className = 'day-cell'; cell.dataset.date = dateStr;
            const dayNum = document.createElement('div'); dayNum.className = 'day-num'; dayNum.textContent = d; cell.appendChild(dayNum);

            if(hs[dateStr]){
                cell.classList.add('holiday');
                const hspan = document.createElement('div');
                hspan.className = 'holiday-label';
                hspan.textContent = hs[dateStr];
                cell.appendChild(hspan);
            }

            const noteVal = notes[dateStr];
            if(noteVal){ const noteEl = document.createElement('div'); noteEl.className='note yellow'; noteEl.textContent = noteVal.length>120? noteVal.slice(0,117)+'...':noteVal; cell.appendChild(noteEl); }

            cell.addEventListener('click', ()=> selectDate(dateStr));
            monthGrid.appendChild(cell);
        }

        calendarEl.appendChild(monthGrid);
    }

    function selectDate(iso){
        selectedDate = iso;
        selectedDayInfo.textContent = iso;
        const notes = loadNotes(currentYear);
        noteText.value = notes[iso] || '';
        // open day detail screen/modal
        // abrir tela/modal de detalhe do dia
        renderDayDetail(iso);
    }

    // Render a modal/detail screen for a single day (holiday + full annotation editor)
    // Renderizar tela/modal de detalhe para um único dia (feriado + editor de anotação completo)
    function renderDayDetail(iso){
        // iso = YYYY-MM-DD
        // iso = YYYY-MM-DD
        // build modal
        // construir modal
        const existing = document.getElementById('day-detail-modal');
        if(existing) existing.remove();
        const hs = buildHolidaysForYear(currentYear);
        const notes = loadNotes(currentYear);

        const modal = document.createElement('div'); modal.id = 'day-detail-modal'; modal.className = 'day-detail-modal';
        const content = document.createElement('div'); content.className = 'day-detail-content';

        const header = document.createElement('div'); header.className = 'day-detail-header';
        const title = document.createElement('h3'); title.textContent = iso; header.appendChild(title);
        const closeBtn = document.createElement('button'); closeBtn.className = 'btn-secondary'; closeBtn.textContent = 'Fechar';
        closeBtn.addEventListener('click', ()=> { modal.remove(); });
        header.appendChild(closeBtn);
        content.appendChild(header);

        // holiday area
        // área de feriado
        if(hs[iso]){
            const h = document.createElement('div'); h.className = 'day-detail-holiday'; h.textContent = hs[iso]; content.appendChild(h);
        }

        // read-only annotation display
        // exibição de anotação somente leitura
        const editorLabel = document.createElement('h4'); editorLabel.textContent = 'Anotações'; content.appendChild(editorLabel);
        const noteDisplay = document.createElement('div'); noteDisplay.className = 'day-detail-note';
        const noteText = notes[iso] || '';
        noteDisplay.textContent = noteText || 'Nenhuma anotação para este dia.';
        content.appendChild(noteDisplay);

        modal.appendChild(content);
        document.body.appendChild(modal);
        // focus textarea
        // focar textarea
        setTimeout(()=> editor.focus(), 50);
        // close on esc
        // fechar com esc
        const escHandler = (e)=>{ if(e.key === 'Escape'){ modal.remove(); document.removeEventListener('keydown', escHandler); } };
        document.addEventListener('keydown', escHandler);
    }

    saveBtn.addEventListener('click', ()=>{
        if(!selectedDate) return alert('Selecione um dia no calendário');
        const notes = loadNotes(currentYear);
        const v = noteText.value && noteText.value.trim();
        if(v){ notes[selectedDate] = v; } else { delete notes[selectedDate]; }
        saveNotes(currentYear, notes);
        // re-render according to current view: if user was inspecting a month, stay there
        // re-renderizar de acordo com a visão atual: se o usuário estava inspecionando um mês, fique lá
        if(currentView && currentView.type === 'month' && currentView.year === currentYear){
            renderMonthDetail(currentYear, currentView.month);
        } else {
            renderYear(currentYear);
        }
        selectDate(selectedDate);
    });

    clearBtn.addEventListener('click', ()=>{
        if(!selectedDate) return;
        const notes = loadNotes(currentYear);
        delete notes[selectedDate];
        saveNotes(currentYear, notes);
        if(currentView && currentView.type === 'month' && currentView.year === currentYear){
            renderMonthDetail(currentYear, currentView.month);
        } else {
            renderYear(currentYear);
        }
        selectDate(selectedDate);
    });

    yearPrev.addEventListener('click', ()=>{ currentYear--; renderYear(currentYear); selectedDate = null; selectedDayInfo.textContent = 'Nenhum dia selecionado'; noteText.value = ''; });
    yearNext.addEventListener('click', ()=>{ currentYear++; renderYear(currentYear); selectedDate = null; selectedDayInfo.textContent = 'Nenhum dia selecionado'; noteText.value = ''; });

    // initial render
    // renderização inicial
    renderYear(currentYear);
})();
