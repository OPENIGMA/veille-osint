// ---------------------------------------------------------
// Page "Presse locale" : filtres région + thématique + recherche
// texte libre, rendu de la liste d'articles depuis
// data/presse/latest.json
// ---------------------------------------------------------

let state = {
  articles: [],
  activeRegions: new Set(),
  activeThemes: new Set(),
  searchQuery: '',
  themeLabels: {}, // id -> label, construit dynamiquement depuis les données
};

function normalizeText(str) {
  return (str || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, ''); // retire les accents
}

function buildRegionFilters() {
  const container = document.getElementById('region-filters');
  container.innerHTML = '';
  REGIONS.forEach(region => {
    const count = state.articles.filter(a => a.region === region.id).length;
    const label = document.createElement('label');
    label.className = 'filter-item';
    label.innerHTML = `
      <input type="checkbox" value="${region.id}" checked>
      ${escapeHtml(region.label)}
      <span class="count">${count}</span>
    `;
    label.querySelector('input').addEventListener('change', onRegionToggle);
    container.appendChild(label);
    state.activeRegions.add(region.id);
  });
}

function buildThemeFilters(themeCounts) {
  const container = document.getElementById('theme-filters');
  container.innerHTML = '';

  const sortedThemes = Object.entries(themeCounts)
    .filter(([, count]) => count > 0)
    .sort((a, b) => b[1] - a[1]);

  if (sortedThemes.length === 0) {
    container.innerHTML = '<div class="empty-state">Aucune thématique détectée</div>';
    return;
  }

  sortedThemes.forEach(([themeId, count]) => {
    const label = document.createElement('label');
    label.className = 'filter-item';
    label.dataset.themeLabel = (state.themeLabels[themeId] || themeId).toLowerCase();
    label.innerHTML = `
      <input type="checkbox" value="${themeId}">
      ${escapeHtml(state.themeLabels[themeId] || themeId)}
      <span class="count">${count}</span>
    `;
    label.querySelector('input').addEventListener('change', onThemeToggle);
    container.appendChild(label);
  });
}

function onRegionToggle(e) {
  const val = e.target.value;
  if (e.target.checked) state.activeRegions.add(val);
  else state.activeRegions.delete(val);
  render();
}

function onThemeToggle(e) {
  const val = e.target.value;
  if (e.target.checked) state.activeThemes.add(val);
  else state.activeThemes.delete(val);
  render();
}

function renderActiveFilters() {
  const container = document.getElementById('active-filters');
  container.innerHTML = '';

  state.activeThemes.forEach(themeId => {
    const chip = document.createElement('span');
    chip.className = 'active-filter-chip';
    chip.innerHTML = `${escapeHtml(state.themeLabels[themeId] || themeId)} <button aria-label="Retirer le filtre">×</button>`;
    chip.querySelector('button').addEventListener('click', () => {
      state.activeThemes.delete(themeId);
      document.querySelectorAll(`#theme-filters input[value="${themeId}"]`).forEach(cb => cb.checked = false);
      render();
    });
    container.appendChild(chip);
  });

  if (state.searchQuery.trim()) {
    const chip = document.createElement('span');
    chip.className = 'active-filter-chip';
    chip.innerHTML = `Recherche : "${escapeHtml(state.searchQuery)}" <button aria-label="Effacer la recherche">×</button>`;
    chip.querySelector('button').addEventListener('click', () => {
      state.searchQuery = '';
      document.getElementById('article-search').value = '';
      render();
    });
    container.appendChild(chip);
  }
}

function getFilteredArticles() {
  const q = normalizeText(state.searchQuery);
  return state.articles.filter(a => {
    if (!state.activeRegions.has(a.region)) return false;
    if (state.activeThemes.size > 0) {
      const hasTheme = a.themes.some(t => state.activeThemes.has(t));
      if (!hasTheme) return false;
    }
    if (q) {
      const haystack = normalizeText(a.title + ' ' + a.summary + ' ' + a.source_label);
      if (!haystack.includes(q)) return false;
    }
    return true;
  });
}

function renderArticleList(articles) {
  const container = document.getElementById('article-list');

  if (articles.length === 0) {
    container.innerHTML = '<div class="empty-state">Aucun article ne correspond aux filtres sélectionnés.</div>';
    return;
  }

  const sorted = [...articles].sort((a, b) => {
    const da = new Date(a.published).getTime() || 0;
    const db = new Date(b.published).getTime() || 0;
    return db - da;
  });

  container.innerHTML = sorted.map(a => `
    <div class="article-row">
      <div class="article-region">${escapeHtml(a.region)}</div>
      <div class="article-source">${escapeHtml(a.source_label)}</div>
      <div>
        <a class="article-title" href="${escapeHtml(a.link)}" target="_blank" rel="noopener">${escapeHtml(a.title)}</a>
        ${a.summary ? `<p class="article-summary">${escapeHtml(a.summary)}</p>` : ''}
        <div class="article-meta">
          <span class="article-date">${formatDate(a.published)}</span>
          ${a.themes.map(t => `<span class="theme-tag">${escapeHtml(state.themeLabels[t] || t)}</span>`).join('')}
        </div>
      </div>
    </div>
  `).join('');
}

function render() {
  const filtered = getFilteredArticles();
  document.getElementById('stat-filtered').textContent = filtered.length;
  renderActiveFilters();
  renderArticleList(filtered);
}

function setupThemeSearch() {
  const input = document.getElementById('theme-search');
  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    document.querySelectorAll('#theme-filters .filter-item').forEach(item => {
      const match = !q || item.dataset.themeLabel.includes(q);
      item.style.display = match ? '' : 'none';
    });
  });
}

function setupArticleSearch() {
  const input = document.getElementById('article-search');
  let debounceTimer;
  input.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      state.searchQuery = input.value;
      render();
    }, 150);
  });
}

async function init() {
  try {
    const [presseData, manualLinksData] = await Promise.all([
      fetchJSON(DATA_URLS.presse),
      fetchJSON(DATA_URLS.manualLinks).catch(() => null),
    ]);

    if (manualLinksData) {
      Object.entries(manualLinksData.themes).forEach(([id, t]) => {
        state.themeLabels[id] = t.label;
      });
    }

    state.articles = presseData.articles || [];
    document.getElementById('stat-total').textContent = state.articles.length;
    document.getElementById('last-update').textContent =
      'Dernière mise à jour : ' + formatDate(presseData.fetched_at);

    const themeCounts = {};
    state.articles.forEach(a => {
      a.themes.forEach(t => {
        themeCounts[t] = (themeCounts[t] || 0) + 1;
        if (!state.themeLabels[t]) state.themeLabels[t] = t;
      });
    });

    buildRegionFilters();
    buildThemeFilters(themeCounts);
    setupThemeSearch();
    setupArticleSearch();

    try {
      const errors = await fetchJSON(DATA_URLS.presseErrors);
      if (errors.errors && errors.errors.length > 0) {
        const banner = document.getElementById('error-banner');
        banner.hidden = false;
        banner.textContent = `${errors.errors.length} flux presse n'ont pas pu être récupérés lors de la dernière mise à jour (voir data/presse/_errors.json).`;
      }
    } catch (_) { /* pas critique */ }

    render();
  } catch (err) {
    document.getElementById('article-list').innerHTML =
      `<div class="empty-state">Impossible de charger les données presse.<br>${escapeHtml(err.message)}<br><br>Astuce : les fichiers /data doivent être générés par les scripts Python (voir README) et copiés dans /site/data avant publication.</div>`;
  }
}

init();
