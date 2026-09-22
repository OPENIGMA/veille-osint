// ---------------------------------------------------------
// Page "Réseaux sociaux" : agrège Reddit + Mastodon (auto) et
// affiche les liens de recherche manuels (X / Facebook / Instagram)
// ---------------------------------------------------------

let socialState = {
  reddit: {},
  mastodon: {},
  manualLinks: {},
  activeSources: new Set(['reddit', 'mastodon', 'manual']),
  activeThemes: new Set(),
  themeLabels: {},
  allThemeIds: [],
};

function buildThemeFilters() {
  const container = document.getElementById('theme-filters');
  container.innerHTML = '';

  socialState.allThemeIds.forEach(themeId => {
    const label = document.createElement('label');
    label.className = 'filter-item';
    const themeLabel = socialState.themeLabels[themeId] || themeId;
    label.dataset.themeLabel = themeLabel.toLowerCase();
    label.innerHTML = `
      <input type="checkbox" value="${themeId}">
      ${escapeHtml(themeLabel)}
    `;
    label.querySelector('input').addEventListener('change', (e) => {
      if (e.target.checked) socialState.activeThemes.add(themeId);
      else socialState.activeThemes.delete(themeId);
      render();
    });
    container.appendChild(label);
  });
}

function setupSourceToggles() {
  document.querySelectorAll('.source-toggle').forEach(cb => {
    cb.addEventListener('change', (e) => {
      if (e.target.checked) socialState.activeSources.add(e.target.value);
      else socialState.activeSources.delete(e.target.value);
      render();
    });
  });
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

function renderActiveFilters() {
  const container = document.getElementById('active-filters');
  container.innerHTML = '';
  socialState.activeThemes.forEach(themeId => {
    const chip = document.createElement('span');
    chip.className = 'active-filter-chip';
    chip.innerHTML = `${escapeHtml(socialState.themeLabels[themeId] || themeId)} <button aria-label="Retirer le filtre">×</button>`;
    chip.querySelector('button').addEventListener('click', () => {
      socialState.activeThemes.delete(themeId);
      document.querySelectorAll(`#theme-filters input[value="${themeId}"]`).forEach(cb => cb.checked = false);
      render();
    });
    container.appendChild(chip);
  });
}

function themeVisible(themeId) {
  return socialState.activeThemes.size === 0 || socialState.activeThemes.has(themeId);
}

function renderRedditSection(themeId) {
  const data = socialState.reddit[themeId];
  if (!data || !data.results || data.results.length === 0) return '';
  const items = data.results.map(r => `
    <div class="social-item">
      <div class="social-item-meta">
        <span>${escapeHtml(r.subreddit || '')}</span>
        <span>${formatDate(r.created_utc ? new Date(r.created_utc * 1000).toISOString() : null)}</span>
        <span>↑ ${r.score ?? 0} · 💬 ${r.num_comments ?? 0}</span>
      </div>
      <a href="${escapeHtml(r.url)}" target="_blank" rel="noopener">${escapeHtml(r.title)}</a>
    </div>
  `).join('');
  return `<div class="social-theme-block">
    <div class="social-theme-header">Reddit <span class="count">${data.results.length}</span></div>
    ${items}
  </div>`;
}

function renderMastodonSection(themeId) {
  const data = socialState.mastodon[themeId];
  if (!data || !data.results || data.results.length === 0) return '';
  const items = data.results.map(r => `
    <div class="social-item">
      <div class="social-item-meta">
        <span>@${escapeHtml(r.author || '')}</span>
        <span>${formatDate(r.created_at)}</span>
        <span>🔁 ${r.reblogs_count ?? 0} · ★ ${r.favourites_count ?? 0}</span>
      </div>
      <a href="${escapeHtml(r.url)}" target="_blank" rel="noopener">${escapeHtml(r.content_excerpt)}</a>
    </div>
  `).join('');
  return `<div class="social-theme-block">
    <div class="social-theme-header">Mastodon <span class="count">${data.results.length}</span></div>
    ${items}
  </div>`;
}

function renderManualSection(themeId) {
  const data = socialState.manualLinks[themeId];
  if (!data) return '';
  return `<div class="social-theme-block">
    <div class="social-theme-header">Liens de recherche manuels</div>
    <div class="manual-links-row">
      <a class="manual-link-btn" href="${escapeHtml(data.links.x)}" target="_blank" rel="noopener">Rechercher sur X ↗</a>
      <a class="manual-link-btn" href="${escapeHtml(data.links.facebook)}" target="_blank" rel="noopener">Rechercher sur Facebook ↗</a>
      <a class="manual-link-btn" href="${escapeHtml(data.links.instagram_hashtag)}" target="_blank" rel="noopener">Voir le hashtag Instagram ↗</a>
    </div>
  </div>`;
}

function render() {
  renderActiveFilters();
  const container = document.getElementById('social-content');

  const visibleThemeIds = socialState.allThemeIds.filter(themeVisible);

  if (visibleThemeIds.length === 0) {
    container.innerHTML = '<div class="empty-state">Aucune thématique ne correspond aux filtres sélectionnés.</div>';
    return;
  }

  let html = '';
  visibleThemeIds.forEach(themeId => {
    const label = socialState.themeLabels[themeId] || themeId;
    let sectionHtml = '';
    if (socialState.activeSources.has('reddit')) sectionHtml += renderRedditSection(themeId);
    if (socialState.activeSources.has('mastodon')) sectionHtml += renderMastodonSection(themeId);
    if (socialState.activeSources.has('manual')) sectionHtml += renderManualSection(themeId);

    if (sectionHtml) {
      html += `<div class="social-section">
        <h2 class="social-section-title">${escapeHtml(label)}</h2>
        ${sectionHtml}
      </div>`;
    }
  });

  container.innerHTML = html || '<div class="empty-state">Aucun résultat pour les filtres sélectionnés.</div>';
}

async function init() {
  try {
    const [redditData, mastodonData, manualLinksData] = await Promise.all([
      fetchJSON(DATA_URLS.reddit).catch(() => ({ results_by_theme: {} })),
      fetchJSON(DATA_URLS.mastodon).catch(() => ({ results_by_theme: {} })),
      fetchJSON(DATA_URLS.manualLinks),
    ]);

    socialState.reddit = redditData.results_by_theme || {};
    socialState.mastodon = mastodonData.results_by_theme || {};
    socialState.manualLinks = manualLinksData.themes || {};

    socialState.allThemeIds = Object.keys(socialState.manualLinks);
    socialState.allThemeIds.forEach(id => {
      socialState.themeLabels[id] = socialState.manualLinks[id].label;
    });

    const lastUpdates = [redditData.fetched_at, mastodonData.fetched_at].filter(Boolean);
    if (lastUpdates.length) {
      const mostRecent = lastUpdates.sort().reverse()[0];
      document.getElementById('last-update').textContent = 'Dernière mise à jour : ' + formatDate(mostRecent);
    }

    buildThemeFilters();
    setupSourceToggles();
    setupThemeSearch();
    render();
  } catch (err) {
    document.getElementById('social-content').innerHTML =
      `<div class="empty-state">Impossible de charger les données.<br>${escapeHtml(err.message)}</div>`;
  }
}

init();
