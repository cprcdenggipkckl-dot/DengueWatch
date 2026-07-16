<!DOCTYPE html>
<html>
<head>
    <title>Dengue Timeline Map</title>
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; display: flex; height: 100vh; overflow: hidden; }
        #sidebar { width: 320px; padding: 20px; background-color: #f8f9fa; border-right: 1px solid #dee2e6; overflow-y: auto; box-sizing: border-box; }
        #map-container { flex-grow: 1; position: relative; }
        #map { width: 100%; height: 100%; transition: opacity 0.4s ease-in-out; }
        .control-group { margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #e9ecef; }
        label { display: block; font-weight: bold; margin-bottom: 5px; font-size: 13px; }
        select { width: 100%; padding: 5px; font-size: 13px; box-sizing: border-box; }
        select[multiple] { height: 100px; }
        .help-text { font-size: 11px; color: #6c757d; margin-top: 5px; line-height: 1.4; }
        h3 { margin-top: 0; font-size: 18px; border-bottom: 2px solid #ccc; padding-bottom: 5px; }
        
        .slider-container { display: flex; align-items: center; gap: 8px; margin-top: 5px; }
        #play-btn { padding: 5px 10px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 3px; font-size: 12px; font-weight: bold; }
        #play-btn:hover { background: #0056b3; }
        #slider-val { width: 45px; text-align: center; font-weight: bold; font-size: 13px; background: #e9ecef; border-radius: 3px; padding: 3px; }
        
        #map-overlay {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(255, 255, 255, 0.4);
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s ease-in-out;
            z-index: 10;
        }
    </style>
</head>
<body>
    <div id="sidebar">
        <h3>Filter & Visualisasi</h3>

        <div class="control-group" style="background: #eef2f5; padding: 10px; border-radius: 5px; border: 1px solid #cdd4db;">
            <label>Animasi / Timeline Epid</label>
            <div class="slider-container">
                <button id="play-btn" onclick="togglePlay()">▶ Play</button>
                <input type="range" id="epid-slider" min="0" max="100" value="0" style="flex-grow: 1;" oninput="onSliderInput()">
                <span id="slider-val">Semua</span>
            </div>
            <div class="help-text">Gunakan slider untuk melihat pergerakan kes.</div>
        </div>

        <div class="control-group">
            <label>Jenis Peta (Basemap)</label>
            <select id="map-style" onchange="updateMap()">
                <option value="carto-positron" selected>Carto Positron (Peta Cerah - Default)</option>
                <option value="open-street-map">OpenStreetMap (Terperinci)</option>
                <option value="carto-darkmatter">Carto Darkmatter (Peta Gelap)</option>
            </select>
        </div>
        
        <div class="control-group">
            <label>Visual Mode</label>
            <select id="visual-mode" onchange="updateMap()">
                <option value="heatmap">Heat Map</option>
                <option value="dots">Kes Individu (Dots sahaja)</option>
                <option value="dots_200">Dots + 200m Radius Geografi (Tepat)</option>
                <option value="dots_400">Dots + 400m Radius Geografi (Tepat)</option>
                <option value="dots_both">Dots + 200m & 400m Radius (Tepat)</option>
            </select>
        </div>
        
        <div class="control-group">
            <label>Epid Minggu (Daftar) <span style="font-weight:normal;">(Pelbagai)</span></label>
            <select id="epid" multiple onchange="onEpidDropdownChange()">
                <option value="Semua" selected>-- Semua Minggu --</option>
                __EPID__
            </select>
        </div>

        <div class="control-group">
            <label>Pelaksana</label>
            <select id="pelaksana" onchange="updateMap()">
                <option value="Semua">Semua</option>
                __PELAKSANA__
            </select>
        </div>

        <div class="control-group">
            <label>Wabak Status</label>
            <select id="wabak" onchange="updateMap()">
                <option value="Semua">Semua</option>
                __WABAK__
            </select>
        </div>

        <div class="control-group">
            <label>Kewarganegaraan</label>
            <select id="warga" onchange="updateMap()">
                <option value="Semua">Semua</option>
                __WARGA__
            </select>
        </div>
    </div>
    
    <div id="map-container">
        <div id="map"></div>
        <div id="map-overlay"></div>
    </div>

    <script>
        const rawData = __DATA__;
        let mapInitialized = false;
        let timer = null;

        const epidWeeksRaw = [...new Set(rawData.map(d => parseFloat(d.epid_daftar)))]
            .filter(n => !isNaN(n))
            .sort((a, b) => a - b);
        
        const epidWeeks = epidWeeksRaw.map(n => Math.floor(n) === n ? String(Math.floor(n)) : String(n));

        const slider = document.getElementById('epid-slider');
        const sliderValDisplay = document.getElementById('slider-val');
        slider.min = 0;
        slider.max = epidWeeks.length;
        slider.value = 0;

        function onSliderInput() {
            const val = parseInt(slider.value, 10);
            const epidSelect = document.getElementById('epid');
            
            if (val === 0) {
                sliderValDisplay.innerText = "Semua";
                for(let i=0; i < epidSelect.options.length; i++) {
                    epidSelect.options[i].selected = (epidSelect.options[i].value === 'Semua');
                }
            } else {
                const week = epidWeeks[val - 1];
                sliderValDisplay.innerText = "M" + week;
                for(let i=0; i < epidSelect.options.length; i++) {
                    epidSelect.options[i].selected = (epidSelect.options[i].value === week);
                }
            }
            updateMapWithFade();
        }

        function onEpidDropdownChange() {
            const selected = getSelectedValues('epid');
            
            if (selected.length === 1 && selected[0] !== 'Semua') {
                const idx = epidWeeks.indexOf(selected[0]);
                if (idx !== -1) {
                    slider.value = idx + 1;
                    sliderValDisplay.innerText = "M" + selected[0];
                }
            } else {
                slider.value = 0;
                sliderValDisplay.innerText = "Semua";
                if (timer) {
                    clearInterval(timer);
                    timer = null;
                    document.getElementById('play-btn').innerText = "▶ Play";
                }
            }
            updateMapWithFade();
        }

        function togglePlay() {
            const btn = document.getElementById('play-btn');
            if (timer) {
                clearInterval(timer);
                timer = null;
                btn.innerText = "▶ Play";
            } else {
                btn.innerText = "⏸ Pause";
                if (parseInt(slider.value, 10) === parseInt(slider.max, 10) || parseInt(slider.value, 10) === 0) {
                    slider.value = 1;
                }
                
                onSliderInput();
                
                timer = setInterval(() => {
                    let v = parseInt(slider.value, 10);
                    if (v < parseInt(slider.max, 10)) {
                        slider.value = v + 1;
                        onSliderInput();
                    } else {
                        clearInterval(timer);
                        timer = null;
                        btn.innerText = "▶ Play";
                    }
                }, 1200); 
            }
        }

        function getSelectedValues(selectId) {
            const select = document.getElementById(selectId);
            const values = [];
            for (let i = 0; i < select.options.length; i++) {
                if (select.options[i].selected) {
                    values.push(select.options[i].value);
                }
            }
            return values;
        }

        function updateMapWithFade() {
            if (!mapInitialized) {
                updateMap();
                return;
            }
            const overlay = document.getElementById('map-overlay');
            const mapStyle = document.getElementById('map-style').value;
            overlay.style.background = (mapStyle === 'carto-darkmatter') ? 'rgba(20, 20, 20, 0.5)' : 'rgba(255, 255, 255, 0.5)';
            overlay.style.opacity = 1;
            setTimeout(() => {
                updateMap();
                setTimeout(() => { overlay.style.opacity = 0; }, 100);
            }, 250);
        }

        // GENERATE TRUE GEOGRAPHICAL GEOJSON CIRCLES
        function createGeoJsonCircles(data, radiusInMeters) {
            const features = data.map(d => {
                const earthRadius = 6378137; // in meters
                const points = 32;
                const coords = [];
                for (let i = 0; i <= points; i++) {
                    const angle = (i * 360 / points) * (Math.PI / 180);
                    const dLat = (radiusInMeters / earthRadius) * (180 / Math.PI);
                    const dLon = (radiusInMeters / (earthRadius * Math.cos(Math.PI * d.lat / 180))) * (180 / Math.PI);
                    coords.push([d.lon + dLon * Math.cos(angle), d.lat + dLat * Math.sin(angle)]);
                }
                return {
                    type: "Feature",
                    geometry: { type: "Polygon", coordinates: [coords] }
                };
            });
            return { type: "FeatureCollection", features: features };
        }

        function updateMap() {
            const visualMode = document.getElementById('visual-mode').value;
            const mapStyle = document.getElementById('map-style').value;
            const pelaksana = document.getElementById('pelaksana').value;
            const wabak = document.getElementById('wabak').value;
            const warga = document.getElementById('warga').value;
            
            let activeEpids = null;
            const sliderVal = parseInt(slider.value, 10);
            let titleText = "Analisis Kelajuan & Ekspansi";

            if (sliderVal === 0) {
                activeEpids = getSelectedValues('epid');
                if (activeEpids.includes('Semua') || activeEpids.length === 0) {
                    activeEpids = null; 
                    titleText += " (Semua Minggu)";
                } else {
                    titleText += ` (Minggu: ${activeEpids.join(', ')})`;
                }
            } else {
                const week = epidWeeks[sliderVal - 1];
                activeEpids = [ week ];
                titleText += ` (Transisi: M${week})`;
            }

            const filteredData = rawData.filter(d => {
                if (pelaksana !== 'Semua' && d.pelaksana !== pelaksana) return false;
                if (wabak !== 'Semua' && d.wabak !== wabak) return false;
                if (warga !== 'Semua' && d.warga !== warga) return false;
                if (activeEpids !== null && !activeEpids.includes(d.epid_daftar)) return false;
                return true;
            });

            const lats = filteredData.map(d => d.lat);
            const lons = filteredData.map(d => d.lon);
            const lats_j = filteredData.map(d => d.lat_j);
            const lons_j = filteredData.map(d => d.lon_j);
            const customdata = filteredData.map(d => [d.lokaliti, d.jenis, d.epid_daftar, d.wabak, d.warga, d.pelaksana]);
            
            const hovertemplate = 
                "<b>Lokaliti:</b> %{customdata[0]}<br>" +
                "<b>Jenis Kes:</b> %{customdata[1]}<br>" +
                "<b>Epid Minggu:</b> %{customdata[2]}<br>" +
                "<b>Wabak Status:</b> %{customdata[3]}<br>" +
                "<b>Kewarganegaraan:</b> %{customdata[4]}<br>" +
                "<b>Pelaksana:</b> %{customdata[5]}<br>" +
                "<extra></extra>";

            const traces = [];

            // 1. Heatmap Trace
            traces.push({
                type: 'densitymapbox',
                lat: lats, lon: lons, z: Array(lats.length).fill(1),
                radius: 18, customdata: customdata, hovertemplate: hovertemplate,
                name: 'Heatmap', visible: visualMode === 'heatmap'
            });

            // 2. Individual Dots Trace
            let dotColor = mapStyle === 'carto-darkmatter' ? 'rgba(255, 255, 255, 0.8)' : 'rgba(20, 20, 20, 0.7)';
            let dotLine = mapStyle === 'carto-darkmatter' ? 'black' : 'white';

            traces.push({
                type: 'scattermapbox', mode: 'markers',
                lat: lats_j, lon: lons_j,
                marker: { size: 8, color: dotColor, line: {color: dotLine, width: 1} },
                customdata: customdata, hovertemplate: hovertemplate,
                name: 'Kes Individu', 
                visible: visualMode !== 'heatmap'
            });

            // CREATE TRUE GEOGRAPHICAL MAPBOX LAYERS FOR RADII
            const layers = [];
            
            if (visualMode === 'dots_400' || visualMode === 'dots_both') {
                const geoJson400 = createGeoJsonCircles(filteredData, 400);
                layers.push({
                    sourcetype: 'geojson',
                    source: geoJson400,
                    type: 'fill',
                    color: 'rgba(135, 206, 250, 0.15)' // Light blue fill
                });
                layers.push({
                    sourcetype: 'geojson',
                    source: geoJson400,
                    type: 'line',
                    color: 'rgba(135, 206, 250, 0.8)', // Solid blue border
                    line: {width: 1}
                });
            }

            if (visualMode === 'dots_200' || visualMode === 'dots_both') {
                const geoJson200 = createGeoJsonCircles(filteredData, 200);
                layers.push({
                    sourcetype: 'geojson',
                    source: geoJson200,
                    type: 'fill',
                    color: 'rgba(255, 69, 0, 0.2)' // Orange fill
                });
                layers.push({
                    sourcetype: 'geojson',
                    source: geoJson200,
                    type: 'line',
                    color: 'rgba(255, 69, 0, 0.8)', // Solid orange border
                    line: {width: 1}
                });
            }

            const layout = {
                title: titleText,
                transition: {duration: 500, easing: 'cubic-in-out'},
                mapbox: {
                    style: mapStyle, 
                    center: {lat: 3.13, lon: 101.71},
                    zoom: 12.5,
                    layers: layers  // Adding the True Geo-Scale Layers here
                },
                margin: {r: 0, t: 40, l: 0, b: 0},
                showlegend: false,
                uirevision: 'true'  
            };

            if (!mapInitialized) {
                Plotly.newPlot('map', traces, layout);
                mapInitialized = true;
            } else {
                Plotly.react('map', traces, layout);
            }
        }

        updateMap();
    </script>
</body>
</html>
