#!/usr/bin/env python3
"""
Agrège les flux RSS de presse locale (config/sources_presse.yaml),
les enrichit avec un tag "thématique" détecté par mots-clés
(config/keywords.yaml), et écrit le résultat dans data/presse/latest.json.

100% gratuit : utilise uniquement des flux RSS publics (natifs ou
Google News). Aucune clé API nécessaire.
"""

import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

import urllib.request
import urllib.error
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data" / "presse"
DATA_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (compatible; VeilleOSINT/1.0; "
    "+https://github.com/) RSS-Aggregator"
)
TIMEOUT = 15
MAX_ITEMS_PER_SOURCE = 30


def normalize(text: str) -> str:
    """Minuscule + suppression des accents, pour un matching robuste."""
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


def load_yaml(filename: str) -> dict:
    with open(CONFIG_DIR / filename, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_gnews_url(site: str) -> str:
    """Construit une URL de flux RSS Google News filtrée sur un domaine."""
    query = quote(f"site:{site}")
    return (
        f"https://news.google.com/rss/search?q={query}"
        "&hl=fr&gl=FR&ceid=FR:fr"
    )


def fetch_xml(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def parse_rss_items(xml_bytes: bytes) -> list:
    """Parse un flux RSS 2.0 standard (natif ou Google News) en liste d'items."""
    items = []
    root = ET.fromstring(xml_bytes)
    for item in root.findall(".//item")[:MAX_ITEMS_PER_SOURCE]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = (item.findtext("description") or "").strip()
        # Nettoyage sommaire du HTML dans les descriptions Google News
        description = re.sub(r"<[^>]+>", " ", description)
        description = re.sub(r"\s+", " ", description).strip()
        if title:
            items.append(
                {
                    "title": title,
                    "link": link,
                    "published": pub_date,
                    "summary": description[:400],
                }
            )
    return items


def detect_themes(text: str, themes_config: list) -> list:
    """Retourne la liste des ids de thématiques dont un mot-clé apparaît dans le texte.

    Le matching se fait sur des mots/expressions entiers (limites de mots),
    pas sur de simples sous-chaînes, pour éviter les faux positifs
    (ex. le mot-clé "TER" ne doit pas matcher "centre-ville").
    """
    norm_text = normalize(text)
    matched = []
    for theme in themes_config:
        for kw in theme["keywords"]:
            norm_kw = normalize(kw)
            pattern = r"(?<![a-z0-9])" + re.escape(norm_kw) + r"(?![a-z0-9])"
            if re.search(pattern, norm_text):
                matched.append(theme["id"])
                break
    return matched


def main():
    sources_cfg = load_yaml("sources_presse.yaml")
    keywords_cfg = load_yaml("keywords.yaml")
    themes = keywords_cfg["themes"]

    all_articles = []
    errors = []
    fetched_at = datetime.now(timezone.utc).isoformat()

    for region, sources in sources_cfg.items():
        if region.startswith("_"):
            continue
        for src in sources:
            src_type = src.get("type", "rss")
            url = src["url"] if src_type == "rss" else build_gnews_url(src["site"])
            try:
                xml_bytes = fetch_xml(url)
                items = parse_rss_items(xml_bytes)
                for it in items:
                    theme_ids = detect_themes(
                        it["title"] + " " + it["summary"], themes
                    )
                    all_articles.append(
                        {
                            "region": region,
                            "source_id": src["id"],
                            "source_label": src["label"],
                            "title": it["title"],
                            "link": it["link"],
                            "published": it["published"],
                            "summary": it["summary"],
                            "themes": theme_ids,
                        }
                    )
                print(f"OK  [{region}] {src['label']} — {len(items)} articles")
            except Exception as exc:  # noqa: BLE001
                print(f"ERR [{region}] {src['label']} — {exc}", file=sys.stderr)
                errors.append(
                    {
                        "region": region,
                        "source_id": src["id"],
                        "source_label": src["label"],
                        "url": url,
                        "error": str(exc),
                        "at": fetched_at,
                    }
                )

    output = {
        "fetched_at": fetched_at,
        "count": len(all_articles),
        "articles": all_articles,
    }

    with open(DATA_DIR / "latest.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # On garde une trace des erreurs de la dernière exécution seulement
    with open(DATA_DIR / "_errors.json", "w", encoding="utf-8") as f:
        json.dump({"fetched_at": fetched_at, "errors": errors}, f, ensure_ascii=False, indent=2)

    print(f"\nTotal : {len(all_articles)} articles, {len(errors)} erreurs.")


if __name__ == "__main__":
    main()
