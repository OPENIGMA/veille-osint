#!/usr/bin/env python3
"""
Génère, pour chaque thématique, des liens de recherche pré-remplis
vers X, Facebook et Instagram.

Ces plateformes n'offrent pas d'API de recherche publique gratuite
et libre (contrairement à Reddit/Mastodon) : on ne peut donc pas
automatiser la récupération de résultats. On génère à la place des
URLs de recherche prêtes à cliquer, que l'utilisateur ouvre
manuellement dans son navigateur (recherche déjà connecté à son
propre compte).

Écrit le résultat dans data/manual_links.json (pas de sous-dossier
dédié : ce fichier est statique et ne change que si keywords.yaml
change).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_yaml(filename: str) -> dict:
    with open(CONFIG_DIR / filename, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_links(keywords: list) -> dict:
    query = " ".join(keywords)
    q = quote(query)
    return {
        "x": f"https://x.com/search?q={q}&src=typed_query&f=live",
        "facebook": f"https://www.facebook.com/search/posts/?q={q}",
        "instagram_hashtag": (
            f"https://www.instagram.com/explore/tags/{quote(keywords[0].replace(' ', ''))}/"
            if keywords
            else "https://www.instagram.com/"
        ),
    }


def main():
    keywords_cfg = load_yaml("keywords.yaml")
    themes = keywords_cfg["themes"]

    themes_links = {}
    for theme in themes:
        themes_links[theme["id"]] = {
            "label": theme["label"],
            "keywords": theme["keywords"],
            "links": build_links(theme["keywords"]),
        }

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "themes": themes_links,
    }

    with open(DATA_DIR / "manual_links.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Liens manuels générés pour {len(themes_links)} thématiques.")


if __name__ == "__main__":
    main()
