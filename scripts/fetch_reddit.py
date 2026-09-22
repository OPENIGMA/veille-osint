#!/usr/bin/env python3
"""
Recherche sur Reddit par thématique, via l'API officielle Reddit
(gratuite, usage "script app" — https://www.reddit.com/prefs/apps).

Nécessite 3 secrets (gratuits à créer, aucune carte bancaire) :
  REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
fournis en variables d'environnement (voir README + workflow GitHub Actions).

Écrit le résultat dans data/reddit/latest.json.
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
DATA_DIR = ROOT / "data" / "reddit"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")
USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "veille-osint-script/1.0")

MAX_RESULTS_PER_THEME = 15
SEARCH_TIME_WINDOW = "week"  # hour, day, week, month, year, all


def load_yaml(filename: str) -> dict:
    with open(CONFIG_DIR / filename, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_access_token() -> str:
    """Authentification OAuth2 "client credentials" — gratuite, sans compte utilisateur."""
    auth = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=data,
        method="POST",
    )
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    import base64

    b64_creds = base64.b64encode(credentials.encode()).decode()
    req.add_header("Authorization", f"Basic {b64_creds}")
    req.add_header("User-Agent", USER_AGENT)

    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read())
        return payload["access_token"]


def search_theme(token: str, query: str) -> list:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "sort": "new",
            "t": SEARCH_TIME_WINDOW,
            "limit": MAX_RESULTS_PER_THEME,
        }
    )
    url = f"https://oauth.reddit.com/search?{params}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"bearer {token}")
    req.add_header("User-Agent", USER_AGENT)

    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read())

    results = []
    for child in payload.get("data", {}).get("children", []):
        d = child.get("data", {})
        results.append(
            {
                "title": d.get("title"),
                "subreddit": d.get("subreddit_name_prefixed"),
                "url": f"https://reddit.com{d.get('permalink', '')}",
                "created_utc": d.get("created_utc"),
                "score": d.get("score"),
                "num_comments": d.get("num_comments"),
                "selftext_excerpt": (d.get("selftext") or "")[:300],
            }
        )
    return results


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print(
            "REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET manquants — "
            "voir README pour créer une app Reddit gratuite (type 'script').",
            file=sys.stderr,
        )
        # On écrit quand même un fichier vide pour ne pas casser le site
        empty = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "count": 0,
            "results_by_theme": {},
            "note": "Identifiants Reddit non configurés.",
        }
        with open(DATA_DIR / "latest.json", "w", encoding="utf-8") as f:
            json.dump(empty, f, ensure_ascii=False, indent=2)
        return

    keywords_cfg = load_yaml("keywords.yaml")
    themes = keywords_cfg["themes"]

    token = get_access_token()
    results_by_theme = {}
    total = 0

    for theme in themes:
        # On regroupe les mots-clés d'une thématique en une seule requête OR
        query = " OR ".join(f'"{kw}"' for kw in theme["keywords"])
        try:
            results = search_theme(token, query)
            results_by_theme[theme["id"]] = {
                "label": theme["label"],
                "results": results,
            }
            total += len(results)
            print(f"OK  {theme['label']} — {len(results)} résultats")
        except Exception as exc:  # noqa: BLE001
            print(f"ERR {theme['label']} — {exc}", file=sys.stderr)
            results_by_theme[theme["id"]] = {
                "label": theme["label"],
                "results": [],
                "error": str(exc),
            }
        time.sleep(1)  # ménage l'API, reste bien sous les limites gratuites

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": total,
        "results_by_theme": results_by_theme,
    }

    with open(DATA_DIR / "latest.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nTotal : {total} résultats Reddit.")


if __name__ == "__main__":
    main()
