#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Construit produits-off.json pour « L'assiette de Sienna ».

Source : export officiel d'Open Food Facts (CSV, séparateur tabulation, ~0,9 Go compressé)
  https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz
Licence des données : Open Database License (ODbL) — source à citer : Open Food Facts.

On ne garde QUE : code-barres, nom, marque, glucides pour 100 g, poids d'une unité
(calculé à partir de la portion indiquée sur le paquet), nom de l'unité, type d'aliment.
Seulement les produits vendus en France, avec un nom et des glucides renseignés.

Utilisation :
  python3 construire_base_off.py                      (télécharge l'export, ~0,9 Go)
  python3 construire_base_off.py --source fichier.csv.gz   (export déjà téléchargé)
  python3 construire_base_off.py --max 300000          (garder plus de produits)
Aucune bibliothèque à installer (Python 3.8 ou plus).
"""
import argparse, datetime, gzip, heapq, io, json, re, sys, time, urllib.request

URL = "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz"
UA = "LassietteDeSienna/1.0 (usage personnel, base glucides)"
EXCLUS = re.compile(r"^(g|gr|grs|grammes?|ml|cl|dl|kg|l|oz|mg)\.?$")


def f(x):
    try:
        v = float(str(x).replace(",", ".").strip())
        return v if v == v else None  # écarte NaN
    except (TypeError, ValueError):
        return None


def singulier(w):
    if len(w) > 3 and w[-1] in "sx" and not w.endswith(("ss", "us")):
        return w[:-1]
    return w


def unite(taille, quantite):
    """'1 biscuit (17 g)' -> (17.0,'biscuit') ; '2 biscuits (37,5 g)' -> (18.8,'biscuit') ; '30 g' -> (30.0,'portion')"""
    q = f(quantite)
    txt = (taille or "").strip()
    lab, n = "portion", 1.0
    m = re.match(r"^\s*(\d+(?:[.,]\d+)?)\s*([^\d()/=,;]+?)\s*(?:\(|/|=|$|d[e']\s*\d)", txt)
    if m:
        w = m.group(2).strip().lower()
        cnt = f(m.group(1))
        if w and len(w) < 25 and not EXCLUS.match(w) and cnt and cnt > 0:
            lab = w if cnt == 1 else singulier(w)
            n = cnt
    if not q or q <= 0:
        m2 = re.search(r"(\d+(?:[.,]\d+)?)\s*(g|gr|ml)\b", txt, re.I)
        if m2:
            q = f(m2.group(1))
    if not q or q <= 0 or q > 1500:
        return 0, ""
    per = round(q / n, 1)
    return (per, lab) if per >= 1 else (0, "")


def ouvrir(source):
    if source.startswith("http"):
        req = urllib.request.Request(source, headers={"User-Agent": UA})
        brut = urllib.request.urlopen(req, timeout=300)
    else:
        brut = open(source, "rb")
    if source.endswith(".gz"):
        brut = gzip.GzipFile(fileobj=brut)
    return io.TextIOWrapper(brut, encoding="utf-8", errors="replace", newline="\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default=URL, help="URL ou chemin de l'export CSV (.csv ou .csv.gz)")
    ap.add_argument("--out", default="produits-off.json")
    ap.add_argument("--max", type=int, default=200000, help="nombre maximum de produits (les plus scannés)")
    ap.add_argument("--pays", default="en:france")
    a = ap.parse_args()

    t0 = time.time()
    fh = ouvrir(a.source)
    entete = fh.readline().rstrip("\n").split("\t")
    col = {nom: i for i, nom in enumerate(entete)}
    for obligatoire in ("code", "product_name", "countries_tags", "carbohydrates_100g"):
        if obligatoire not in col:
            sys.exit("Colonne manquante dans l'export : %s" % obligatoire)
    opt = lambda nom: col.get(nom)
    i_code, i_nom, i_pays, i_glu = col["code"], col["product_name"], col["countries_tags"], col["carbohydrates_100g"]
    i_nomfr, i_marque = opt("product_name_fr"), opt("brands")
    i_taille, i_qte = opt("serving_size"), opt("serving_quantity")
    i_scans, i_compl, i_type = opt("unique_scans_n"), opt("completeness"), opt("pnns_groups_2")
    manquantes = [n for n in ("brands", "serving_size", "serving_quantity", "unique_scans_n", "pnns_groups_2") if n not in col]
    if manquantes:
        print("Attention, colonnes absentes (ignorées) :", ", ".join(manquantes))

    ncol = len(entete)
    pays = a.pays
    tas, seq = [], 0
    vus = lus = mal_formes = 0
    for ligne in fh:
        lus += 1
        if pays not in ligne:  # filtre rapide avant de découper la ligne
            continue
        champs = ligne.rstrip("\n").split("\t")
        if len(champs) != ncol:
            mal_formes += 1
            continue
        if pays not in champs[i_pays].split(","):
            continue
        glu = f(champs[i_glu])
        if glu is None or glu < 0 or glu > 100:
            continue
        nom = (champs[i_nomfr].strip() if i_nomfr is not None else "") or champs[i_nom].strip()
        code = champs[i_code].strip()
        if not nom or not code:
            continue
        vus += 1
        marque = champs[i_marque].split(",")[0].strip() if i_marque is not None else ""
        per, lab = unite(champs[i_taille] if i_taille is not None else "", champs[i_qte] if i_qte is not None else "")
        typ = champs[i_type].strip() if i_type is not None else ""
        scans = f(champs[i_scans]) if i_scans is not None else None
        compl = f(champs[i_compl]) if i_compl is not None else None
        score = ((scans or 0), (compl or 0))
        rec = (code, nom[:90], marque[:40], round(glu, 1), per, lab, typ)
        seq += 1
        item = (score, seq, rec)
        if len(tas) < a.max:
            heapq.heappush(tas, item)
        elif item > tas[0]:
            heapq.heapreplace(tas, item)
        if lus % 500000 == 0:
            print("  %d lignes lues, %d produits France retenus…" % (lus, vus), flush=True)

    produits = [r for _, _, r in sorted(tas, reverse=True)]
    types = sorted({r[6] for r in produits if r[6] and r[6].lower() != "unknown"})
    idx = {t: i for i, t in enumerate(types)}
    p = [[r[0], r[1], r[2], r[3], r[4], r[5], idx.get(r[6], -1)] for r in produits]
    sortie = {
        "v": 2,
        "date": datetime.date.today().isoformat(),
        "source": "Open Food Facts — Open Database License (ODbL)",
        "champs": ["code", "nom", "marque", "glucides_100g", "poids_unite_g", "unite", "type"],
        "cats": types,
        "p": p,
    }
    with open(a.out, "w", encoding="utf-8") as out:
        json.dump(sortie, out, ensure_ascii=False, separators=(",", ":"))
    avec_unite = sum(1 for r in p if r[4] > 0)
    print("Terminé en %.0f s : %d lignes lues, %d produits France avec glucides, %d gardés (%d avec poids d'unité), %d lignes mal formées."
          % (time.time() - t0, lus, vus, len(p), avec_unite, mal_formes))
    print("Fichier écrit :", a.out)


if __name__ == "__main__":
    main()
