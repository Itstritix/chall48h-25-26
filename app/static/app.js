/**
 * app.js — Parkshare Dashboard
 * Logique JS partagée : API, carte Leaflet, graphiques Chart.js, filtres
 */

// ================================================================
// ÉTAT GLOBAL
// ================================================================
let geojsonFull  = null;
let mapInstance  = null;
let mapLayer     = null;
const charts     = {};

// ================================================================
// CHART.JS — CONFIG PAR DÉFAUT
// ================================================================
const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#0d1220',
      borderColor: 'rgba(255,255,255,0.1)',
      borderWidth: 1,
      titleColor: '#e2e8f0',
      bodyColor: '#94a3b8',
      padding: 10,
      cornerRadius: 6,
      titleFont: { family: 'Syne', size: 12, weight: '700' },
      bodyFont:  { family: 'JetBrains Mono', size: 11 }
    }
  },
  scales: {
    x: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: { color: '#475569', font: { family: 'JetBrains Mono', size: 10 } }
    },
    y: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: { color: '#475569', font: { family: 'JetBrains Mono', size: 10 } }
    }
  }
};

// ================================================================
// HELPERS API
// ================================================================

/**
 * Fetch les communes avec filtres optionnels
 * @param {Object} params - { region, score_min, score_max, syndic }
 */
async function fetchCommunes(params = {}) {
  const url = new URL('/api/communes', location.origin);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== '' && v !== null && v !== undefined) url.searchParams.set(k, v);
  });
  const res = await fetch(url);
  return res.json();
}

/**
 * Lit les valeurs courantes des filtres dans le DOM
 */
function getFilters() {
  return {
    region:    document.getElementById('f-region')?.value    || '',
    score_min: document.getElementById('f-score-min')?.value || 0,
    score_max: document.getElementById('f-score-max')?.value || 100,
    syndic:    document.getElementById('f-syndic')?.value    || '',
  };
}

// ================================================================
// FILTRES — INIT & APPLICATION
// ================================================================

/**
 * Charge les valeurs disponibles dans les dropdowns région et syndic
 */
async function initFiltres() {
  const res  = await fetch('/api/filtres');
  const data = await res.json();

  const selR = document.getElementById('f-region');
  if (selR) {
    data.regions.forEach(r => {
      const o = document.createElement('option');
      o.value = r; o.textContent = r;
      selR.appendChild(o);
    });
  }

  const selS = document.getElementById('f-syndic');
  if (selS) {
    data.syndics.slice(0, 50).forEach(s => {
      const o = document.createElement('option');
      o.value = s; o.textContent = s;
      selS.appendChild(o);
    });
  }
}

/**
 * Applique les filtres : met à jour la carte, les KPIs et le Top 20
 */
async function applyFilters() {
  const f = getFilters();

  // Mise à jour KPIs
  const communes = await fetchCommunes(f);
  updateKPIs(communes);

  // Mise à jour carte
  const codes = new Set(communes.map(c => String(c.code_commune)));
  const filtered = {
    type: 'FeatureCollection',
    features: geojsonFull.features.filter(ft => codes.has(String(ft.properties.code_commune)))
  };
  renderMapLayer(filtered);

  // Mise à jour Top 20 avec filtres
  const url = new URL('/api/classement', location.origin);
  Object.entries(f).forEach(([k, v]) => { if (v !== '') url.searchParams.set(k, v); });
  url.searchParams.set('limit', 20);
  const res = await fetch(url);
  renderTop20(await res.json());
}

/**
 * Réinitialise tous les filtres
 */
function resetFilters() {
  const fields = ['f-region', 'f-syndic'];
  fields.forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });

  const min = document.getElementById('f-score-min');
  const max = document.getElementById('f-score-max');
  if (min) min.value = 0;
  if (max) max.value = 100;

  const vMin = document.getElementById('val-min');
  const vMax = document.getElementById('val-max');
  if (vMin) vMin.textContent = '0';
  if (vMax) vMax.textContent = '100';

  fetchCommunes().then(updateKPIs);
  if (geojsonFull) renderMapLayer(geojsonFull);
  initTop20();
}

// ================================================================
// KPI CARDS — MISE À JOUR
// ================================================================

/**
 * Met à jour les 4 cartes KPI selon les données filtrées
 * @param {Array} data - liste des communes
 */
function updateKPIs(data) {
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };

  set('kpi-communes', data.length.toLocaleString('fr-FR'));

  const avg = data.reduce((s, c) => s + (c.score_potentiel || 0), 0) / (data.length || 1);
  set('kpi-score', avg.toFixed(1));

  const copros = data.reduce((s, c) => s + (c.nb_coproprietes || 0), 0);
  set('kpi-copros', copros.toLocaleString('fr-FR'));

  const zones = data.filter(c => (c.score_potentiel || 0) >= 66).length;
  set('kpi-zones', zones.toLocaleString('fr-FR'));
}

// ================================================================
// CARTE LEAFLET
// ================================================================

/**
 * Charge le GeoJSON depuis l'API
 */
async function initGeoJSON() {
  const res   = await fetch('/api/geojson');
  geojsonFull = await res.json();
}

/**
 * Initialise la carte Leaflet avec fond sombre + légende
 */
function initMap() {
  if (!document.getElementById('map')) return;

  mapInstance = L.map('map', {
    center: [46.5, 2.5],
    zoom: 5,
    zoomControl: true,
    attributionControl: false
  });

  // Fond de carte dark (CartoDB Dark Matter)
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 18
  }).addTo(mapInstance);

  renderMapLayer(geojsonFull);
  addMapLegend();
}

/**
 * Retourne la couleur hex selon le score potentiel
 * @param {number} score
 */
function getColor(score) {
  if (score >= 66) return '#c8f542';   // lime — zone prioritaire
  if (score >= 33) return '#f59e0b';   // orange — zone moyenne
  return '#ef4444';                     // rouge — zone faible
}

/**
 * (Re)dessine la couche GeoJSON sur la carte
 * @param {Object} data - FeatureCollection GeoJSON
 */
function renderMapLayer(data) {
  if (!mapInstance || !data) return;
  if (mapLayer) mapInstance.removeLayer(mapLayer);

  mapLayer = L.geoJSON(data, {
    style: feature => ({
      fillColor:   getColor(feature.properties.score_potentiel || 0),
      fillOpacity: 0.55,
      color:       'rgba(255,255,255,0.06)',
      weight:      0.5
    }),
    onEachFeature: (feature, layer) => {
      const p     = feature.properties;
      const score = (p.score_potentiel || 0).toFixed(1);
      const emoji = p.score_potentiel >= 66 ? '🟢' : p.score_potentiel >= 33 ? '🟡' : '🔴';

      // Tooltip hover
      layer.bindTooltip(`
        <div>
          <strong style="font-size:13px">${p.nom_commune || '—'}</strong><br>
          <span style="color:#64748b;font-family:'JetBrains Mono';font-size:10px">
            ${p.departement || ''} · ${p.region || ''}
          </span>
          <hr style="border:none;border-top:1px solid rgba(255,255,255,0.08);margin:8px 0">
          ${emoji} Score : <strong style="color:#c8f542">${score}</strong> / 100<br>
          Copropriétés : <strong>${(p.nb_coproprietes || 0).toLocaleString('fr-FR')}</strong><br>
          Syndic : <strong>${p.syndic_dominant || '—'}</strong><br>
          Part HLM : <strong>${p.part_hlm ? (p.part_hlm * 100).toFixed(1) + '%' : '—'}</strong>
        </div>
      `, { className: 'map-tooltip', sticky: true });

      // Hover highlight
      layer.on('mouseover', function () {
        this.setStyle({ fillOpacity: 0.85, weight: 1.5, color: 'rgba(200,245,66,0.4)' });
      });
      layer.on('mouseout', function () {
        mapLayer.resetStyle(this);
      });
    }
  }).addTo(mapInstance);
}

/**
 * Ajoute la légende des couleurs en bas à droite de la carte
 */
function addMapLegend() {
  const legend = L.control({ position: 'bottomright' });
  legend.onAdd = () => {
    const div = L.DomUtil.create('div');
    div.innerHTML = `
      <div style="background:#0d1220;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:12px 14px;font-family:'Syne',sans-serif;font-size:11px;color:#94a3b8">
        <div style="font-family:'JetBrains Mono';font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#e2e8f0;margin-bottom:8px">Score potentiel</div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px"><span style="width:12px;height:12px;border-radius:2px;background:#c8f542;display:inline-block"></span> Élevé ≥ 66</div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px"><span style="width:12px;height:12px;border-radius:2px;background:#f59e0b;display:inline-block"></span> Moyen 33–65</div>
        <div style="display:flex;align-items:center;gap:8px"><span style="width:12px;height:12px;border-radius:2px;background:#ef4444;display:inline-block"></span> Faible &lt; 33</div>
      </div>`;
    return div;
  };
  legend.addTo(mapInstance);
}

// ================================================================
// TABLE — TOP 20
// ================================================================

/**
 * Charge le Top 20 depuis l'API et l'affiche dans le tableau
 */
async function initTop20() {
  const res  = await fetch('/api/top20');
  const data = await res.json();
  renderTop20(data);
}

/**
 * Injecte les lignes du Top 20 dans le tbody
 * @param {Array} data
 */
function renderTop20(data) {
  const tbody = document.getElementById('tbody-top20');
  if (!tbody) return;

  tbody.innerHTML = data.map(c => {
    const s   = c.score_potentiel;
    const cls = s >= 66 ? 'badge-high' : s >= 33 ? 'badge-mid' : 'badge-low';
    const hlm = c.part_hlm_pct != null ? c.part_hlm_pct + '%' : '—';

    return `<tr>
      <td class="rank-num">#${c.rang}</td>
      <td style="font-weight:700;color:#e2e8f0">${c.nom_commune}</td>
      <td style="font-size:11px;color:#64748b">${c.region}</td>
      <td><span class="badge ${cls}">${(+s).toFixed(1)}</span></td>
      <td style="font-family:'JetBrains Mono';font-size:11px">${(c.nb_coproprietes || 0).toLocaleString('fr-FR')}</td>
      <td style="font-family:'JetBrains Mono';font-size:11px;color:#94a3b8">${hlm}</td>
      <td><span class="chip">${c.syndic_dominant || '—'}</span></td>
    </tr>`;
  }).join('');
}

// ================================================================
// GRAPHIQUES CHART.JS
// ================================================================

/**
 * KPI 1 — Histogramme distribution des scores par tranche
 */
async function initDistrib() {
  const res  = await fetch('/api/graphiques/distribution');
  const data = await res.json();

  if (charts.distrib) charts.distrib.destroy();
  charts.distrib = new Chart(document.getElementById('chart-distrib'), {
    type: 'bar',
    data: {
      labels: data.map(d => `${d.tranche_min}–${d.tranche_max}`),
      datasets: [{
        label: 'Communes',
        data: data.map(d => d.nb_communes),
        backgroundColor: data.map(d =>
          d.tranche_min >= 66 ? 'rgba(200,245,66,0.7)'  :
          d.tranche_min >= 33 ? 'rgba(245,158,11,0.7)'  :
          'rgba(239,68,68,0.5)'
        ),
        borderRadius: 4,
        borderSkipped: false
      }]
    },
    options: { ...CHART_DEFAULTS }
  });
}

/**
 * Agrégat — Score moyen par région (barres horizontales)
 */
async function initStats() {
  const res  = await fetch('/api/stats');
  const data = await res.json();
  const top  = data.slice(0, 12);

  const labels = top.map(r => r.region.length > 18 ? r.region.slice(0, 18) + '…' : r.region);
  const values = top.map(r => r.score_moyen);

  if (charts.regions) charts.regions.destroy();
  charts.regions = new Chart(document.getElementById('chart-regions'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: values.map(v =>
          v >= 66 ? 'rgba(200,245,66,0.7)' :
          v >= 33 ? 'rgba(245,158,11,0.7)' :
          'rgba(239,68,68,0.7)'
        ),
        borderRadius: 4,
        borderSkipped: false
      }]
    },
    options: {
      ...CHART_DEFAULTS,
      indexAxis: 'y',
      scales: {
        x: { ...CHART_DEFAULTS.scales.x, min: 0, max: 100 },
        y: { ...CHART_DEFAULTS.scales.y, ticks: { ...CHART_DEFAULTS.scales.y.ticks, font: { family: 'JetBrains Mono', size: 9 } } }
      }
    }
  });
}

/**
 * KPI 3 — Concentration syndic Top 15 communes
 */
async function initSyndic() {
  const res  = await fetch('/api/graphiques/syndic');
  const data = await res.json();

  const labels = data.map(d => d.nom_commune.length > 14 ? d.nom_commune.slice(0, 14) + '…' : d.nom_commune);
  const values = data.map(d => d.concentration_pct);

  if (charts.syndic) charts.syndic.destroy();
  charts.syndic = new Chart(document.getElementById('chart-syndic'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Concentration syndic (%)',
        data: values,
        backgroundColor: 'rgba(0,212,255,0.6)',
        borderColor: 'rgba(0,212,255,1)',
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: { ...CHART_DEFAULTS }
  });
}

/**
 * KPI 4 — Scatter : Part HLM vs Score potentiel
 */
async function initScatter() {
  const res  = await fetch('/api/graphiques/scatter');
  const data = await res.json();

  if (charts.scatter) charts.scatter.destroy();
  charts.scatter = new Chart(document.getElementById('chart-scatter'), {
    type: 'scatter',
    data: {
      datasets: [
        {
          label: 'Score élevé (≥ 66)',
          data: data.filter(d => d.score_category === 'Élevé').map(d => ({ x: d.part_hlm_pct, y: d.score_potentiel, label: d.nom_commune })),
          backgroundColor: 'rgba(200,245,66,0.5)',
          borderColor:     'rgba(200,245,66,0.8)',
          pointRadius: 4, pointHoverRadius: 6
        },
        {
          label: 'Score moyen (33–65)',
          data: data.filter(d => d.score_category === 'Moyen').map(d => ({ x: d.part_hlm_pct, y: d.score_potentiel, label: d.nom_commune })),
          backgroundColor: 'rgba(245,158,11,0.5)',
          borderColor:     'rgba(245,158,11,0.8)',
          pointRadius: 3, pointHoverRadius: 5
        },
        {
          label: 'Score faible (< 33)',
          data: data.filter(d => d.score_category === 'Faible').map(d => ({ x: d.part_hlm_pct, y: d.score_potentiel, label: d.nom_commune })),
          backgroundColor: 'rgba(239,68,68,0.4)',
          borderColor:     'rgba(239,68,68,0.7)',
          pointRadius: 3, pointHoverRadius: 5
        }
      ]
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: {
          display: true,
          labels: { color: '#94a3b8', font: { family: 'JetBrains Mono', size: 10 }, boxWidth: 10, padding: 16 }
        },
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: {
            label: ctx => {
              const d = ctx.raw;
              return ` ${d.label || '—'} — HLM : ${d.x}% · Score : ${d.y}`;
            }
          }
        }
      },
      scales: {
        x: {
          ...CHART_DEFAULTS.scales.x,
          title: { display: true, text: 'Part logements HLM (%)', color: '#475569', font: { family: 'JetBrains Mono', size: 10 } }
        },
        y: {
          ...CHART_DEFAULTS.scales.y,
          min: 0, max: 100,
          title: { display: true, text: 'Score potentiel', color: '#475569', font: { family: 'JetBrains Mono', size: 10 } }
        }
      }
    }
  });
}

// ================================================================
// NAVIGATION SIDEBAR
// ================================================================

/**
 * Active le lien de navigation cliqué
 * @param {HTMLElement} el
 */
function setActive(el) {
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  el.classList.add('active');
}

// ================================================================
// POINT D'ENTRÉE PRINCIPAL
// ================================================================

/**
 * Initialise tout le dashboard :
 * filtres → GeoJSON → carte → table → graphiques → KPIs → affichage
 */
async function init() {
  await Promise.all([
    initFiltres(),
    initGeoJSON(),
    initTop20(),
    initStats(),
    initDistrib(),
    initSyndic(),
    initScatter()
  ]);

  const communes = await fetchCommunes();
  updateKPIs(communes);

  initMap();

  // Cache le loader après chargement
  setTimeout(() => {
    const loader = document.getElementById('loading');
    if (loader) loader.style.display = 'none';

    // Anime les éléments au chargement
    document.querySelectorAll('.fade').forEach((el, i) => {
      setTimeout(() => el.classList.add('in'), i * 60);
    });
  }, 1600);
}

// ── Scroll reveal pour rapport.html ──
const revealObs = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      revealObs.unobserve(e.target);
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el));

// ── Lancement ──
window.addEventListener('load', init);