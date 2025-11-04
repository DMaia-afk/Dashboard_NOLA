// Lightweight map page logic. Uses Leaflet (loaded in template).
// Lógica leve da página do mapa. Usa Leaflet (carregado no template).
// The script will try to fetch /api/recent-sales/ (if you implement it)
// O script tentará buscar /api/recent-sales/ (se você implementar)
// and otherwise runs a local simulation of sale events for development.
// e caso contrário executa uma simulação local de eventos de vendas para desenvolvimento.

(function(){
    const mapEl = document.getElementById('map');
    const simulateCheckbox = document.getElementById('realtime-sim');
    const clearBtn = document.getElementById('clear-markers');

    const map = L.map(mapEl).setView([-14.2350, -51.9253], 4);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    const markersLayer = L.layerGroup().addTo(map);

    // Example city coordinates to bias the simulation
    // Coordenadas de cidades de exemplo para influenciar a simulação
    const cities = [
        { name: 'São Paulo', lat: -23.55052, lon: -46.633308 },
        { name: 'Rio de Janeiro', lat: -22.906847, lon: -43.172897 },
        { name: 'Belo Horizonte', lat: -19.9245, lon: -43.9352 },
        { name: 'Brasília', lat: -15.826691, lon: -47.921820 },
        { name: 'Salvador', lat: -12.977749, lon: -38.501630 },
        { name: 'Fortaleza', lat: -3.71722, lon: -38.5434 },
    ];

    function randomOffset(coord, spreadKm){
        // convert approximate km to degrees (very rough)
        // converter km aproximado para graus (muito aproximado)
        const deg = spreadKm / 111;
        return coord + (Math.random() - 0.5) * deg * 2;
    }

    function addSaleMarker(lat, lon, info){
        const c = L.circleMarker([lat, lon], { radius: 7, color: '#d32f2f', fillColor: '#ff7043', fillOpacity: 0.9 });
        c.bindPopup(info || 'Venda');
        markersLayer.addLayer(c);
        // small pulse effect: open popup then close
        // pequeno efeito de pulso: abrir popup então fechar
        c.openPopup();
        setTimeout(()=>{ try{ c.closePopup(); }catch(e){} }, 1200);
    }

    let simInterval = null;

    function startSimulation(){
        if(simInterval) return;
        simInterval = setInterval(()=>{
            // generate 1-4 events each tick
            // gerar 1-4 eventos a cada tick
            const n = 1 + Math.floor(Math.random()*3);
            for(let i=0;i<n;i++){
                const city = cities[Math.floor(Math.random()*cities.length)];
                const lat = randomOffset(city.lat, 20);
                const lon = randomOffset(city.lon, 30);
                const amount = (Math.random()*120).toFixed(2);
                addSaleMarker(lat, lon, `${city.name} — R$ ${amount}`);
            }
        }, 2500);
    }
    function stopSimulation(){
        if(simInterval){ clearInterval(simInterval); simInterval = null; }
    }

    clearBtn.addEventListener('click', ()=>{ markersLayer.clearLayers(); });
    simulateCheckbox.addEventListener('change', ()=>{
        if(simulateCheckbox.checked) startSimulation(); else stopSimulation();
    });

    // Try to fetch real recent sales endpoint, otherwise fallback to simulation
// Tente buscar endpoint real de vendas recentes, caso contrário fallback para simulação
    function fetchRecentSalesAndPlot(){
        // If your backend provides /api/recent-sales/ returning [{lat,lng,amount,city}] you can wire it here
// Se seu backend fornecer /api/recent-sales/ retornando [{lat,lng,amount,city}] você pode conectá-lo aqui
        fetch('/api/recent-sales/')
            .then(r=>{
                if(!r.ok) throw new Error('no endpoint');
                return r.json();
            })
            .then(data=>{
                markersLayer.clearLayers();
                if(Array.isArray(data)){
                    data.forEach(s=>{
                        addSaleMarker(s.lat || s.latitude, s.lng || s.longitude || s.lon, `${s.city || ''} — R$ ${s.amount || s.value || ''}`);
                    });
                } else if(data && Array.isArray(data.sales)){
                    data.sales.forEach(s=> addSaleMarker(s.lat, s.lng, s.info));
                }
            })
            .catch(()=>{
                // endpoint /api/recent-sales/ não disponível — usando simulação local
                if(simulateCheckbox.checked) startSimulation();
            });
    }

    // Initial behaviour
// Comportamento inicial
    fetchRecentSalesAndPlot();

    // Provide an optional manual refresh every 30s (if using real endpoint)
// Fornece uma atualização manual opcional a cada 30s (se usando endpoint real)
    setInterval(()=>{
        if(!simulateCheckbox.checked) fetchRecentSalesAndPlot();
    }, 30000);

})();
