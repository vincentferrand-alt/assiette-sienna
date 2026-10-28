# L'assiette de Sienna — mise en ligne et base de produits

## Contenu du dossier
- `index.html` : l'application (un seul fichier).
- `construire_base_off.py` : fabrique `produits-off.json` à partir de l'export officiel d'Open Food Facts.
- `.github/workflows/maj-base-off.yml` : refait ce fichier automatiquement sur GitHub (1er du mois, ou à la demande).

## Pourquoi un fichier ?
Open Food Facts limite son service en ligne à 10 recherches par minute et à 15 fiches produit par minute.
Il demande de télécharger son export pour récupérer beaucoup de produits. L'appli charge donc un seul fichier
(`produits-off.json`) avec seulement : code-barres, nom, marque, glucides pour 100 g, poids d'une unité, type d'aliment.

## Option A — automatique avec GitHub Pages (recommandé)
1. Crée un dépôt GitHub public (https://github.com/new).
2. Settings → Pages → Build and deployment → Source : « GitHub Actions ».
3. Envoie index.html, construire_base_off.py et LISEZMOI.md (Add file → Upload files).
4. Crée le fichier .github/workflows/maj-base-off.yml (Add file → Create new file) et colle son contenu.
   Le premier passage démarre tout seul (20 à 40 min) : il fabrique produits-off.json et publie le site.
5. Ensuite : onglet Actions → « Base Open Food Facts et site » → « Run workflow » pour mettre à jour à la demande ;
   c'est aussi refait automatiquement le 1er de chaque mois.
6. Dans l'appli : ⚙️ Ma base → « 🔄 Charger / mettre à jour depuis le site ».

## Option B — à la main sur un ordinateur
1. Installe Python 3 si besoin.
2. Dans ce dossier : `python3 construire_base_off.py`
   (le script télécharge l'export d'environ 0,9 Go ; ou `--source fichier.csv.gz` si tu l'as déjà téléchargé depuis
   https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz).
3. Mets `produits-off.json` à côté de `index.html` sur ton hébergement, puis « 🔄 Charger » dans l'appli.
   Sans hébergement : « 📂 Importer le fichier » dans ⚙️ Ma base.

Par défaut, le fichier garde les 200 000 produits vendus en France les plus scannés (`--max` pour changer).

Données : Open Food Facts, licence Open Database License (ODbL).
