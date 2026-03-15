# installation.py  v1.1
"""
installation.py — Installateur générique.
────────────────────────────────────────────────────────────────────────────
Ce fichier NE CHANGE JAMAIS. Seul data_installation_vX.Y.py évolue.

Fonctionnement :
  1. Trouve le data_installation_vX.Y.py le plus récent dans package/.
  2. L'importe dynamiquement (PROJET, FICHIERS, SUPPRIMER, CONNUS…).
  3. Crée prog/ (et ses sous-dossiers) si absents.
  4. Déploie : copie si version différente, signale les fichiers inconnus,
     supprime les anciens fichiers listés dans SUPPRIMER.
  5. Bilan + code de sortie 0 (succès) ou 1 (erreurs bloquantes).

Usage :
  python installation.py             déploiement normal
  python installation.py --check     simulation sans copie
  python installation.py --force     force la copie même si à jour
  python installation.py --aide      cette aide
v1.1 : création automatique de prog/ si absent, description générique.
"""
VERSION = ('installation.py', '1.1')

import sys
import re
import shutil
import importlib.util
import argparse
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _version_tuple(nom: str) -> tuple:
    """Extrait (major, minor) depuis 'data_installation_v1.23.py'."""
    m = re.search(r'v(\d+)[._](\d+)', nom)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def trouver_dernier_manifeste(dossier: Path) -> Path:
    """Retourne le fichier data_installation_vX.Y.py le plus récent."""
    candidats = sorted(
        dossier.glob('data_installation_v*.py'),
        key=lambda p: _version_tuple(p.name),
        reverse=True)
    if not candidats:
        raise FileNotFoundError(
            f"Aucun data_installation_vX.Y.py trouvé dans {dossier}")
    return candidats[0]


def charger_manifeste(chemin: Path):
    """Importe dynamiquement le manifeste et retourne le module."""
    spec   = importlib.util.spec_from_file_location('_manifeste', chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extraire_version(chemin: Path) -> str:
    """
    Extrait la version depuis :
      - la première ligne  # nom.py  vX.Y
      - ou VERSION = ('nom', 'X.Y')
    """
    try:
        lignes = chemin.read_text(encoding='utf-8', errors='ignore').splitlines()
        if lignes:
            m = re.search(r'\bv(\d+[\.\d]*)', lignes[0])
            if m:
                return m.group(1)
        contenu = '\n'.join(lignes)
        m = re.search(r"VERSION\s*=\s*\([^,]+,\s*[\"']([^\"']+)[\"']", contenu)
        if m:
            return m.group(1)
    except Exception:
        pass
    return '?'


def verifier_integrite(chemin: Path) -> bool:
    """
    Contrôle que la dernière ligne non-vide commence par '# end '
    (marqueur de fichier complet, non tronqué).
    """
    try:
        lignes = chemin.read_text(encoding='utf-8', errors='ignore').splitlines()
        for ligne in reversed(lignes):
            s = ligne.strip()
            if s:
                return s.startswith('# end ')
        return False
    except Exception:
        return False


def _rel(chemin: Path, racine: Path) -> Path:
    try:    return chemin.relative_to(racine)
    except: return chemin


def _afficher(statut: str, src_nom, dst_rel, v_src='', v_dst='', note=''):
    s_src = str(src_nom)[:36].ljust(36)
    s_dst = str(dst_rel)[:30].ljust(30)
    v_col = f"  v{v_src} -> v{v_dst}" if (v_src or v_dst) else ''
    n_col = f"  [{note}]"              if note              else ''
    print(f"  {statut:<8}  {s_src}  ->  {s_dst}{v_col}{n_col}")


# ─────────────────────────────────────────────────────────────────────────────
#  Déploiement
# ─────────────────────────────────────────────────────────────────────────────
def deployer(manifeste, args) -> int:
    """Déploie selon le manifeste. Retourne le nombre d'erreurs."""
    SRC    = manifeste.SRC
    DST    = manifeste.DST
    racine = DST.parent

    erreurs = copies = a_jour = 0

    # Vérification / création du dossier source
    if not SRC.exists():
        print(f"  ERREUR  Dossier source introuvable : {SRC}")
        return 1

    # Création du dossier cible et de ses sous-dossiers si absents
    if not DST.exists():
        if not args.check:
            DST.mkdir(parents=True, exist_ok=True)
            print(f"  CRÉÉ    Dossier cible créé : {DST}")
        else:
            print(f"  [SIM]   Dossier cible à créer : {DST}")

    for sd in getattr(manifeste, 'SOUS_DOSSIERS', []):
        if not sd.exists():
            if not args.check:
                sd.mkdir(parents=True, exist_ok=True)
                print(f"  CRÉÉ    Sous-dossier : {_rel(sd, racine)}")
            else:
                print(f"  [SIM]   Sous-dossier à créer : {_rel(sd, racine)}")

    # ── Copie des fichiers ────────────────────────────────────────────────────
    print()
    print("  DÉPLOIEMENT")
    print()

    for nom_src, chemin_dst, obligatoire in manifeste.FICHIERS:
        chemin_src = SRC / nom_src

        if not chemin_src.exists():
            note = "OBLIGATOIRE" if obligatoire else "optionnel"
            _afficher("ABSENT", nom_src, _rel(chemin_dst, racine), note=note)
            if obligatoire:
                erreurs += 1
            continue

        # Vérification d'intégrité pour les .py
        if chemin_src.suffix == '.py' and not verifier_integrite(chemin_src):
            _afficher("TRONQUÉ", nom_src, _rel(chemin_dst, racine),
                      note="marqueur '# end' absent — fichier incomplet !")
            erreurs += 1
            continue

        v_src = extraire_version(chemin_src)
        v_dst = extraire_version(chemin_dst) if chemin_dst.exists() else '\u2014'

        if not args.force and v_src == v_dst and chemin_dst.exists():
            _afficher("OK", nom_src, _rel(chemin_dst, racine), v_src, v_dst, "à jour")
            a_jour += 1
        else:
            if not args.check:
                chemin_dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(chemin_src), str(chemin_dst))
            action = "SIM" if args.check else "COPIE"
            _afficher(action, nom_src, _rel(chemin_dst, racine), v_src, v_dst)
            copies += 1

    # ── Suppressions ─────────────────────────────────────────────────────────
    supprimer = getattr(manifeste, 'SUPPRIMER', [])
    if supprimer:
        print()
        print("  SUPPRESSIONS")
        print()
        for chemin in supprimer:
            if chemin.exists():
                if not args.check:
                    chemin.unlink()
                action = "SIM" if args.check else "SUPPRIMÉ"
                print(f"  {action:<8}  {_rel(chemin, racine)}")
            else:
                print(f"  ABSENT    {_rel(chemin, racine)}  (déjà supprimé)")

    # ── Fichiers non répertoriés ──────────────────────────────────────────────
    connus      = getattr(manifeste, 'CONNUS',      set())
    ignorer_ext = getattr(manifeste, 'IGNORER_EXT', {'.pyc', '.pyo'})
    ignorer_dir = getattr(manifeste, 'IGNORER_DIR', {'__pycache__'})
    inconnus    = []

    if DST.exists():
        for f in DST.iterdir():
            if f.is_dir() and f.name in ignorer_dir:
                continue
            if f.is_dir():
                continue
            if f.suffix in ignorer_ext:
                continue
            if f.name not in connus:
                inconnus.append(f)

    if inconnus:
        print()
        print("  FICHIERS NON RÉPERTORIÉS (à vérifier manuellement)")
        print()
        for f in sorted(inconnus):
            v  = extraire_version(f)
            ok = "✓ complet" if verifier_integrite(f) else "✗ incomplet"
            print(f"  ??        {f.name:<42}  v{v}  {ok}")
    else:
        print()
        print("  Aucun fichier non répertorié dans prog/")

    # ── Bilan ─────────────────────────────────────────────────────────────────
    print()
    print("=" * 72)
    mode = "  [SIMULATION — aucune modification]" if args.check else ""
    if erreurs:
        print(f"  ATTENTION : {erreurs} erreur(s) — voir ABSENT/TRONQUÉ ci-dessus{mode}")
    else:
        print(f"  OK : {copies} copie(s)   {a_jour} déjà à jour"
              f"   {len(inconnus)} non répertorié(s){mode}")
    print("=" * 72)
    print()
    return erreurs


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # Trouver le manifeste en premier pour avoir le nom du projet
    ici = Path(__file__).parent
    try:
        manifeste_path = trouver_dernier_manifeste(ici)
        manifeste      = charger_manifeste(manifeste_path)
        nom_projet     = getattr(manifeste, 'PROJET', '(projet inconnu)')
        ver_projet     = getattr(manifeste, 'VERSION_PROJET', '?')
    except FileNotFoundError:
        manifeste      = None
        nom_projet     = '(projet inconnu)'
        ver_projet     = '?'
        manifeste_path = None

    parser = argparse.ArgumentParser(
        prog='installation.py',
        description=f'Installateur générique — {nom_projet} v{ver_projet}',
        add_help=False)
    parser.add_argument('--aide', '-h', '--help', action='store_true',
                        help='Affiche cette aide et quitte')
    parser.add_argument('--check', action='store_true',
                        help='Simulation sans modification')
    parser.add_argument('--force', action='store_true',
                        help='Force la copie même si versions identiques')
    parser.add_argument('--manifeste', default=None,
                        help='Chemin explicite vers data_installation_vX.Y.py')
    args = parser.parse_args()

    if args.aide:
        parser.print_help()
        sys.exit(0)

    # Surcharge manifeste si passé en argument
    if args.manifeste:
        manifeste_path = Path(args.manifeste)
        manifeste      = charger_manifeste(manifeste_path)
        nom_projet     = getattr(manifeste, 'PROJET', '(projet inconnu)')
        ver_projet     = getattr(manifeste, 'VERSION_PROJET', '?')

    if manifeste is None:
        print(f"\n  ERREUR : aucun data_installation_vX.Y.py trouvé dans {ici}")
        sys.exit(1)

    # ── En-tête ───────────────────────────────────────────────────────────────
    print()
    print("=" * 72)
    print(f"  installation.py  v{VERSION[1]}"
          f"   —   {nom_projet}  v{ver_projet}")
    print(f"  Manifeste : {manifeste_path.name}")
    print(f"  Source    : {manifeste.SRC}")
    print(f"  Cible     : {manifeste.DST}")
    if args.check: print("  MODE      : SIMULATION (--check)")
    if args.force: print("  MODE      : FORCE (--force)")
    print("=" * 72)

    erreurs = deployer(manifeste, args)
    sys.exit(1 if erreurs else 0)


if __name__ == '__main__':
    main()

# end installation.py  v1.1
