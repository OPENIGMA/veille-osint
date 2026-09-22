# Veille OSINT — Presse locale & Réseaux sociaux

Site de veille automatisée pour :
1. **Presse locale** : Occitanie, PACA, Corse (flux RSS agrégés et classés par thématique).
2. **Réseaux sociaux** : recherche automatique par thématique sur Reddit et Mastodon (API gratuites), + liens de recherche pré-remplis pour X, Facebook et Instagram (pas d'automatisation possible gratuitement sur ces plateformes).

**100% gratuit** : hébergement GitHub Pages, automatisation GitHub Actions, API Reddit et Mastodon en usage gratuit. Aucune carte bancaire, aucun abonnement.

---

## 1. Structure du projet

```
osint-veille/
├── .github/workflows/main.yml   Workflow unique : fetch + déploiement
├── config/
│   ├── keywords.yaml             Les 42 thématiques + mots-clés associés
│   └── sources_presse.yaml       Les flux RSS presse par région
├── scripts/                      Scripts Python d'agrégation
├── data/                         Données brutes générées (JSON)
├── site/                         Le site statique (HTML/CSS/JS)
│   └── data/                       Copie des données utilisée par le site
└── requirements.txt
```

## 2. Importer ce projet sur GitHub (méthode fiable)

⚠️ **N'utilise pas l'upload web par glisser-déposer** (le bouton "uploading an existing file") : il gère mal les dossiers cachés (`.github`) et les dossiers presque vides (`data/`, `site/data/`), qui finissent par disparaître silencieusement à l'import. Utilise Git en ligne de commande — 10 minutes, et ça marche à tous les coups.

### Étape 1 — Installer Git (si pas déjà fait)

Télécharge et installe : https://git-scm.com/downloads/win — options par défaut, "Suivant" partout.

Vérifie l'installation en ouvrant **PowerShell** ou **l'invite de commande** :
```
git --version
```

### Étape 2 — Créer le dépôt vide sur GitHub

1. Sur github.com, clique **+** → **New repository**.
2. Donne-lui un nom, choisis Public ou Privé.
3. **Ne coche AUCUNE case** ("Add README", ".gitignore", "license") — le dépôt doit être totalement vide.
4. Clique **Create repository**. Reste sur la page qui s'affiche ensuite : elle contient l'URL du dépôt (ex. `https://github.com/TonCompte/ton-depot.git`), qu'il te faudra à l'étape 4.

### Étape 3 — Dézipper l'archive

Dézippe `osint-veille.zip` où tu veux (ex. dans Documents). Tu obtiens un dossier `osint-veille` contenant tous les fichiers du projet.

### Étape 4 — Pousser avec Git

Ouvre PowerShell, déplace-toi dans le dossier dézippé, puis pousse :

```powershell
cd Chemin\Vers\osint-veille
git init
git add .
git commit -m "Initialisation du projet de veille OSINT"
git branch -M main
git remote add origin https://github.com/TonCompte/ton-depot.git
git push -u origin main
```

(Remplace l'URL par celle copiée à l'étape 2. Si c'est ton tout premier usage de Git, il te demandera de te connecter à GitHub via une fenêtre de navigateur — accepte.)

**Vérifie ensuite sur github.com** que TOUS les dossiers sont bien là, y compris `.github` (visible en cliquant dedans) et les sous-dossiers vides de `data/` et `site/data/`.

## 3. Activer GitHub Pages

1. Dans le dépôt : **Settings > Pages**.
2. Sous **"Build and deployment > Source"**, sélectionne **"GitHub Actions"** (pas "Deploy from a branch").
3. Rafraîchis la page pour confirmer que le choix est resté sur "GitHub Actions".

## 4. Vérification critique — permissions du workflow

C'est l'étape la plus souvent oubliée et qui bloque tout silencieusement (aucune erreur claire, juste rien qui se passe) :

1. Va dans **Settings > Actions > General** du dépôt.
2. Descends tout en bas jusqu'à **"Workflow permissions"**.
3. Sélectionne **"Read and write permissions"** (pas l'option "Read repository contents permission" qui est souvent cochée par défaut).
4. Clique **Save**.

Si le dépôt appartient à une **organisation** (comme ici avec OPENIGMA), ce réglage existe aussi au niveau de l'organisation entière (**Organization Settings > Actions > General**) et peut bloquer le dépôt même si le réglage du dépôt est correct — vérifie les deux.

## 5. Déclencher le premier déploiement

Le workflow (`main.yml`) se lance automatiquement à chaque `git push`, donc ton push de l'étape 2 a dû déjà en déclencher un. Pour vérifier ou relancer manuellement :

1. Va dans l'onglet **Actions** du dépôt.
2. Tu dois voir le workflow **"Mise à jour et déploiement"** listé, avec au moins un run.
3. S'il n'y en a aucun : clique sur le workflow dans la liste de gauche, puis sur le bouton **"Run workflow"** (à droite), choisis la branche `main`, et lance-le.
4. Le run prend 1 à 3 minutes. Une fois la coche verte affichée, retourne dans **Settings > Pages** : l'URL de ton site y est indiquée en haut — clique dessus.

**Si le bouton "Run workflow" n'apparaît pas du tout** dans l'onglet Actions pour ce workflow, c'est le signe que GitHub ne l'a pas reconnu comme fichier de workflow valide (problème d'emplacement du fichier, pas de syntaxe) — vérifie qu'il est bien à l'emplacement exact `.github/workflows/main.yml` à la racine du dépôt.

## 6. Configurer les accès gratuits Reddit et Mastodon (facultatif)

Ces deux services nécessitent un jeton d'accès, **gratuit et sans carte bancaire**. Sans eux, le site fonctionne quand même (juste la partie presse + liens manuels réseaux sociaux).

### Reddit (gratuit)

1. Va sur https://www.reddit.com/prefs/apps (connecté à un compte Reddit).
2. Clique **"create another app"** tout en bas.
3. Type **"script"**, donne un nom (ex. "veille-osint"), URL de redirection bidon (ex. `http://localhost:8080`).
4. Récupère le **Client ID** (chaîne courte sous le nom de l'app) et le **Client Secret**.
5. Dans le dépôt GitHub : **Settings > Secrets and variables > Actions > New repository secret**, ajoute :
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`

### Mastodon (gratuit)

1. Crée un compte sur https://mastodon.social (gratuit).
2. **Préférences > Développement > Nouvelle application**, nom au choix, portée `read` cochée.
3. Copie le **jeton d'accès (access token)**.
4. Dans les secrets GitHub du dépôt, ajoute :
   - `MASTODON_ACCESS_TOKEN`

Une fois les secrets ajoutés, relance le workflow manuellement (étape 5) pour qu'il les prenne en compte.

## 7. Personnaliser les thématiques et sources

- **Thématiques et mots-clés** : édite `config/keywords.yaml`. Chaque thématique a un `id` (ne pas changer une fois en prod), un `label` (affiché) et une liste `keywords`.
- **Sources presse** : édite `config/sources_presse.yaml`. Deux types de sources :
  - `type: rss` avec une `url` directe (flux RSS natif) ;
  - `type: gnews` avec juste un `site` (nom de domaine) — utilise le flux RSS gratuit de Google News filtré sur ce domaine, pour les sites sans flux RSS natif fiable.

Après toute modification, il suffit de faire `git add . && git commit -m "..." && git push` — le workflow se relance automatiquement.

## 8. Canaux Telegram (à activer plus tard)

Le module Telegram n'est pas encore implémenté (aucun canal identifié pour l'instant). Quand tu auras une liste de canaux publics à surveiller :
1. Crée un bot Telegram gratuit via [@BotFather](https://t.me/BotFather).
2. Ajoute le bot comme administrateur en lecture sur les canaux à surveiller.
3. Un script `fetch_telegram.py` pourra être ajouté sur ce modèle.

## 9. Limites connues (honnêteté technique)

- **X (Twitter), Facebook, Instagram** : pas d'API de recherche publique gratuite. Le site génère des liens de recherche pré-remplis (page "Réseaux sociaux"), à consulter manuellement.
- **Flux RSS presse** : certains flux changent parfois d'URL. Le script journalise les échecs dans `data/presse/_errors.json`, visible aussi comme bandeau d'alerte sur le site.
- **Limites d'usage gratuites** : Reddit et Mastodon imposent des limites de requêtes sur comptes gratuits ; les scripts respectent des délais entre requêtes pour rester en dessous avec une mise à jour toutes les 3h.

## 10. Si le déploiement ne fonctionne toujours pas

Dans l'ordre de fréquence des causes réelles rencontrées :
1. **Workflow permissions** en lecture seule (section 4 ci-dessus) — la cause la plus fréquente, aucune erreur explicite.
2. **Source Pages** encore sur "Deploy from a branch" au lieu de "GitHub Actions" (section 3).
3. Fichier de workflow pas exactement à `.github/workflows/main.yml` (vérifie l'orthographe et l'emplacement exact sur github.com).
4. Import fait par upload web au lieu de Git, avec des dossiers manquants (section 2) — repars avec la méthode Git si c'est le cas.
