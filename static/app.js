document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Map
    const map = L.map('map', { zoomControl: false }).setView([20.5937, 78.9629], 4);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }).addTo(map);

    const tacticalIcon = L.divIcon({
        className: 'tactical-marker',
        html: `<div style="width:12px;height:12px;background:#ff0055;border-radius:50%;border:2px solid #fff;box-shadow:0 0 10px #ff0055;"></div>`,
        iconSize: [12, 12]
    });

    // 2. Initialize Cytoscape
    const cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': '#00ffcc',
                    'label': 'data(id)',
                    'color': '#fff',
                    'font-size': '10px',
                    'text-valign': 'bottom',
                    'text-margin-y': 5
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': 'rgba(0, 255, 204, 0.3)',
                    'target-arrow-color': 'rgba(0, 255, 204, 0.3)',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier'
                }
            }
        ],
        layout: {
            name: 'cose',
            padding: 50,
            animate: true
        }
    });

    const consoleOut = document.getElementById('console-output');
    function log(msg) {
        const li = document.createElement('li');
        li.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
        consoleOut.appendChild(li);
        consoleOut.scrollTop = consoleOut.scrollHeight;
    }

    async function fetchData() {
        try {
            log("Initiating network sweep...");
            
            const statsRes = await fetch('/api/stats');
            const stats = await statsRes.json();
            document.getElementById('stat-entities').innerText = stats.entities_count;
            document.getElementById('stat-towers').innerText = stats.towers_count;
            log(`Found ${stats.entities_count} entities.`);

            const towersRes = await fetch('/api/towers');
            const towers = await towersRes.json();
            map.eachLayer(layer => { if (layer instanceof L.Marker) map.removeLayer(layer) });
            towers.forEach(t => {
                if (t.lat && t.lon) {
                    L.marker([t.lat, t.lon], { icon: tacticalIcon }).addTo(map)
                     .bindPopup(`<b>Cell:</b> ${t.cell_id}<br/><b>Network:</b> ${t.radio}`);
                }
            });
            if(towers.length > 0) {
                map.fitBounds(towers.map(t => [t.lat, t.lon]), { padding: [50, 50] });
            }
            log(`Plotted ${towers.length} spatial nodes.`);

            const graphRes = await fetch('/api/graph');
            const graphElements = await graphRes.json();
            cy.elements().remove();
            cy.add(graphElements);
            cy.layout({ name: 'cose', animate: true, random: false }).run();
            log(`Graph core synchronized.`);

        } catch (err) {
            log(`Error: ${err.message}`);
        }
    }

    document.getElementById('btn-search').addEventListener('click', async () => {
        const num = document.getElementById('phone-input').value.trim();
        if (!num) return;
        
        log(`Tracing entity: ${num}...`);
        try {
            const res = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ number: num })
            });
            const data = await res.json();
            
            if (res.ok) {
                log(`IDENTIFIED: ${data.carrier} | ${data.location} | +${data.country_code}`);
                // Refresh map/graph to show new entity
                fetchData();
            } else {
                log(`Trace failed: ${data.detail}`);
            }
        } catch (err) {
            log(`Trace error: ${err.message}`);
        }
    });

    document.getElementById('btn-refresh').addEventListener('click', fetchData);
    fetchData();
});
