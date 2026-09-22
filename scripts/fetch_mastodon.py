#!/usr/bin/env python3
"""
Recherche sur Mastodon par thématique, via l'API publique de recherche
(gratuite, sans clé API pour la recherche de hashtags/statuts publics
sur une instance donnée).

NB : l'API de recherche "v2/search" nécessite un token d'accès
utilisateur sur la plupart des instances (même pour du contenu public),
mais celui-ci est GRATUIT à générer (Préférences > Développement sur
n'importe quel compte Mastodon, y compris un compte créé spécialement
pour la veille). Voir README pour la procédure.

Écrit le résultat dans data/mastodon/latest.json.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import urllib.request
import urllib.parse
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data" / "mastodon"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Instance(s) Mastodon interrogée(s). mastodon.social est la plus grande
# instance généraliste ; tu peux en ajouter d'autres (ex. piaille.fr,
# mamot.fr) en dupliquant la logique dans main().
INSTANCE = os.environ.get("MASTODON_INSTANCE", "mastodon.social")
ACCESS_TOKEN = os.environ.get("MASTODON_ACCESS_TOKEN")

MAX_RESULTS_PER_THEME = 15


def load_yaml(filename: str) -> dict:
    with open(CONFIG_DIR / filename, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def search_theme(query: str) -> list:
    params = urllib.parse.urlencode(
        {"q": query, "type": "statuses", "limit": MAX_RESULTS_PER_THEME}
    )
    url = f"https://{INSTANCE}/api/v2/search?{params}"
    req = urllib.request.Request(url)
    if ACCESS_TOKEN:
        req.add_header("Authorization", f"Bearer {ACCESS_TOKEN}")

    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read())

    results = []
    for status in payload.get("statuses", []):
        account = status.get("account", {})
        content = status.get("content", "")
        # nettoyage sommaire du HTML mastodon
        import re

        content = re.sub(r"<[^>]+>", " ", content)
        content = re.sub(r"\s+", " ", content).strip()
        results.append(
            {
                "author": account.get("acct"),
                "content_excerpt": content[:300],
                "url": status.get("url"),
                "created_at": status.get("created_at"),
                "reblogs_count": status.get("reblogs_count"),
                "favourites_count": status.get("favourites_count"),
            }
        )
    return results


def main():
    if not ACCESS_TOKEN:
        print(
            "MASTODON_ACCESS_TOKEN manquant — voir README pour générer un "
            "token gratuit depuis un compte Mastodon (Préférences > "
            "Développement > Nouvelle application).",
            file=sys.stderr,
        )
        empty = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "count": 0,
            "results_by_theme": {},
            "note": "Token Mastodon non configuré.",
        }
        with open(DATA_DIR / "latest.json", "w", encoding="utf-8") as f:
            json.dump(empty, f, ensure_ascii=False, indent=2)
        return

    keywords_cfg = load_yaml("keywords.yaml")
    themes = keywords_cfg["themes"]

    results_by_theme = {}
    total = 0

    for theme in themes:
        # Mastodon ne supporte pas bien les requêtes booléennes complexes :
        # on interroge mot-clé par mot-clé et on fusionne, dédoublonné par URL.
        seen_urls = set()
        merged = []
        for kw in theme["keywords"]:
            try:
                results = search_theme(kw)
                for r in results:
                    if r["url"] and r["url"] not in seen_urls:
                        seen_urls.add(r["url"])
                        merged.append(r)
                time.sleep(1)
            except Exception as exc:  # noqa: BLE001
                print(f"ERR {theme['label']} / '{kw}' — {exc}", file=sys.stderr)

        results_by_theme[theme["id"]] = {
            "label": theme["label"],
            "results": merged[:MAX_RESULTS_PER_THEME],
        }
        total += len(merged)
        print(f"OK  {theme['label']} — {len(merged)} résultats")

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": total,
        "instance": INSTANCE,
        "results_by_theme": results_by_theme,
    }

    with open(DATA_DIR / "latest.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nTotal : {total} résultats Mastodon.")


if __name__ == "__main__":
    main()
