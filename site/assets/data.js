// ---------------------------------------------------------
// Chargement des données produites par les scripts Python
// (GitHub Actions les régénère périodiquement dans /data)
// ---------------------------------------------------------

const DATA_URLS = {
  presse: 'data/presse/latest.json',
  reddit: 'data/reddit/latest.json',
  mastodon: 'data/mastodon/latest.json',
  manualLinks: 'data/manual_links.json',
  presseErrors: 'data/presse/_errors.json',
};

// Les thématiques et régions sont dupliquées ici en JS (au lieu de parser
// le YAML côté client) pour éviter une dépendance JS supplémentaire.
// Cette liste DOIT rester synchronisée avec config/keywords.yaml.
// (Elle est régénérée automatiquement par scripts/build_manual_links.py
// via data/manual_links.json, qui sert de source de vérité pour les
// labels de thématiques affichés dans l'UI.)

const REGIONS = [
  { id: 'occitanie', label: 'Occitanie' },
  { id: 'paca', label: 'PACA' },
  { id: 'corse', label: 'Corse' },
];

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Échec du chargement : ${url} (${res.status})`);
  return res.json();
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}
