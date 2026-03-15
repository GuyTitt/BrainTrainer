# 🎮 Puzzle des Couleurs

**Manuel complet — Utilisateur & Développeur**

*Version 1.3 · Avril 2026 · Python 3.10+ · Tkinter · PyYAML · Architecture MVC*

---

## 1. Présentation générale

### 1.1 Qu'est-ce que le Puzzle des Couleurs ?

Le Puzzle des Couleurs est un jeu de réflexion et de logique conçu pour travailler la pensée stratégique et la planification à court terme. Inspiré des casse-tête de tri de pièces (type *Ball Sort Puzzle*), il propose une variante inédite grâce à la règle du **déplacement en bloc**.

Sur un plateau de 5 colonnes et 7 rangées, 25 pions de 5 couleurs différentes sont empilés dans un arrangement initial mélangé. Le joueur doit redistribuer ces pions pour atteindre un état final cible, en un minimum de coups. Contrairement aux versions classiques, l'état final n'impose **pas** nécessairement une couleur unique par colonne : chaque colonne peut contenir plusieurs couleurs différentes, rendant la résolution beaucoup plus riche.

| Caractéristique | Valeur |
|---|---|
| Langage | Python 3.10 ou supérieur |
| Interface graphique | Tkinter (bibliothèque standard Python) |
| Seule dépendance externe | PyYAML (`pip install pyyaml`) |
| Architecture logicielle | MVC + Config centralisée |
| Plateformes | Windows, macOS, Linux |
| Lancement | `python prog\main.py` |
| Configuration | `config.yaml` — modifiable sans toucher au code |

### 1.2 Philosophie de conception

- **Séparation nette des responsabilités** : chaque fichier Python a un rôle unique. Le modèle (`model.py`) ne connaît pas l'interface, la vue (`view.py`) ne connaît pas les règles, le contrôleur (`controller.py`) orchestre sans calcul propre.
- **Zéro paramètre magique dans le code** : toutes les couleurs, tailles, durées, polices et comportements sont dans `config.yaml`. Changer l'apparence ne nécessite d'éditer aucun `.py`.
- **Versionnage intégré** : chaque fichier `.py` porte son numéro de version sur la première et la dernière ligne. L'installateur vérifie l'intégrité avant de déployer.
- **Robustesse** : sauvegarde complète avec historique, undo/redo illimité, détection de fichiers tronqués, validation de configuration au démarrage.

---

## 2. Règles du jeu

### 2.1 Le plateau

Le plateau est une grille de **5 colonnes × 7 rangées**. Chaque colonne peut contenir au maximum 7 pions superposés. Au début, chaque colonne contient exactement **5 pions** (rangées du bas), les 2 rangées supérieures étant libres.

Les colonnes sont numérotées **C1** (gauche) à **C5** (droite). Dans chaque colonne, les pions s'empilent depuis le bas. Le « sommet » désigne toujours le pion le plus haut.

### 2.2 Les pions

25 pions de 5 couleurs : **Rouge (R), Jaune (J), Bleu (B), Vert (V), Orange (O)**. Chaque couleur est représentée par 5 pions. Un pion est accessible uniquement depuis le sommet de sa colonne.

### 2.3 Configuration initiale (défaut)

| Colonne | Contenu (bas → sommet) | Sommet |
|---|---|---|
| C1 | O · V · B · J · R | Rouge |
| C2 | R · O · V · B · J | Jaune |
| C3 | J · R · O · V · B | Bleu |
| C4 | B · J · R · O · V | Vert |
| C5 | V · B · J · R · O | Orange |

### 2.4 État final cible

L'état final définit ce que chaque colonne doit contenir. La victoire est vérifiée par **comptage** (Counter) : l'ordre des pions dans la colonne n'importe pas.

| Colonne | Couleurs requises | Détail |
|---|---|---|
| C1 | 3 Orange + 2 Rouge | Fond bicolore orange/rouge |
| C2 | 3 Jaune  + 2 Bleu  | Fond bicolore jaune/bleu |
| C3 | 3 Vert   + 2 Orange | Fond bicolore vert/orange |
| C4 | 3 Rouge  + 2 Jaune | Fond bicolore rouge/jaune |
| C5 | 3 Bleu   + 2 Vert  | Fond bicolore bleu/vert |

!!! info "Fond coloré"
    Avec `target_alpha: 1.0` (défaut), le fond de chaque colonne utilise exactement les mêmes teintes que les pions correspondants. Il vous indique visuellement quelles couleurs doivent y être rassemblées.

### 2.5 Le déplacement simple

!!! note "Règle du déplacement simple"
    - La colonne **source** doit avoir au moins 1 pion.
    - La colonne **destination** doit avoir au moins 1 case libre.
    - Source et destination doivent être différentes.
    - **Coûte 1 coup.**

**Comment l'exécuter :**

1. Cliquer sur la colonne source (ou le pion du haut). La colonne se surbrille en doré ; les destinations valides apparaissent en vert.
2. Cliquer sur la colonne destination. Le pion glisse avec une animation fluide.
3. Ou bien : **glisser-déposer** le pion de la source vers la destination.

### 2.6 Le déplacement en bloc

La règle du déplacement en bloc est la mécanique centrale et originale de ce puzzle.

!!! tip "Conditions CUMULATIVES du déplacement en bloc"
    ① Les **2 pions au sommet** de la colonne source sont de **la même couleur**.  
    ② La colonne destination dispose d'au moins **2 cases libres**.  
    ③ Le pion au sommet de la destination est de **la même couleur**.  
    → Les 2 pions se déplacent ensemble et coûtent **1 seul coup**.

**Option A — Clic sur le 2e pion :**

1. Cliquer directement sur le **deuxième pion depuis le haut** (pas le sommet, mais celui juste en dessous). Si ce pion forme un couple identique avec le sommet, le mode BLOC s'active immédiatement (contour bleu+blanc).
2. Cliquer sur la colonne destination.

**Option B — Bouton après sélection :**

1. Cliquer d'abord sur la colonne source (sélection simple, contour doré).
2. Cliquer sur le bouton **⣿ Bloc** dans le panneau gauche.
3. Cliquer sur la colonne destination.

**Option C — Glisser-déposer :**

1. Commencer le glisser depuis le **2e pion** d'un couple. Le mode bloc s'active automatiquement.
2. Relâcher sur la colonne destination.

!!! warning "Annuler une sélection"
    Pour annuler la sélection en cours et revenir à l'état neutre :

    - Cliquer sur le bouton **✕ Esc** dans le panneau gauche,
    - ou appuyer sur la touche **Echap** du clavier,
    - ou **cliquer en dehors** de la grille de jeu.

### 2.7 Condition de victoire

La partie est gagnée lorsque chaque colonne contient exactement les couleurs indiquées par son fond coloré, **peu importe l'ordre vertical** des pions. La vérification est faite par `Counter` Python : si la colonne 1 doit contenir 3 Orange et 2 Rouge, il suffit que ces 5 pions y soient présents dans n'importe quel ordre.

Une boîte de félicitations apparaît avec le score. Le bouton **Rejouer** permet de recommencer la même disposition.

### 2.8 Stratégie et conseils

!!! tip "Principes pour progresser"
    - **Comptez les cases libres** : avec seulement 2 cases libres par colonne au départ, chaque case est précieuse. Évitez de gaspiller de l'espace.
    - **Pensez en blocs** : chaque opportunité de déplacer 2 pions pour le prix d'1 est un avantage. Construisez des couples au sommet des colonnes.
    - **Anticipez les blocages** : une colonne pleine est bloquée. Gardez toujours au moins une issue de secours.
    - **Utilisez l'undo librement** : le nombre d'annulations est illimité. Expérimentez sans crainte.
    - **Observez les fonds** : les couleurs de fond indiquent la destination finale de chaque pion.

---

## 3. Interface utilisateur

### 3.1 Vue d'ensemble de la fenêtre

| Zone | Emplacement | Rôle |
|---|---|---|
| Titre | En haut, centré | Nom du jeu |
| Panneau gauche (SpecialPanel) | À gauche de la grille | 5 boutons d'action rapide |
| Grille de jeu (BoardView) | Centre | Plateau interactif, animations |
| Panneau droit (TapePanel) | À droite de la grille | Compteur + ruban historique + 3 boutons |
| Barre de commandes (CommandBar) | En bas | Saisie textuelle des commandes |

### 3.2 La grille de jeu — couches de dessin

La grille repose sur un canvas Tkinter organisé en **7 couches superposées** (de bas en haut) :

| Couche (tag) | Contenu | Rafraîchissement |
|---|---|---|
| `bg` | Fonds colorés des cellules cibles | Une seule fois au démarrage |
| `grid` | Lignes internes + bordure extérieure | Une seule fois au démarrage |
| `bg_tint` | Teintes de surbrillance (doré/vert) | À chaque `refresh()`, **avant** les pions |
| `piece` | Pions (ovales colorés + étiquettes) | À chaque `refresh()`, après `bg_tint` |
| `hl_border` | Contours de surbrillance (sans fill) | À chaque `refresh()`, après `piece` |
| `guide` | Trait pointillé précurseur d'animation | Pendant l'animation uniquement |
| `ghost` | Fantômes semi-transparents (drag) | Pendant le glisser-déposer |

!!! info "Architecture des couches"
    Les teintes de fond (`bg_tint`) sont dessinées **AVANT** les pions. Les contours de surbrillance (`hl_border`) sont dessinés **APRÈS** les pions mais sans remplissage (`fill=''`). Cette architecture garantit que les pions ne peuvent jamais être cachés par les effets visuels.

### 3.3 Retour visuel lors de la sélection

| Indicateur | Signification |
|---|---|
| Contour **doré épais** sur la colonne | Colonne source sélectionnée (mode SIMPLE) |
| Fond légèrement doré | Renforcement visuel de la sélection |
| Contour **vert** sur d'autres colonnes | Destinations valides pour le déplacement |
| Fond légèrement vert | Renforcement visuel des destinations |
| Contour **bleu + contour blanc** intérieur | Mode BLOC actif sur la source |
| Fond plus intense (alpha 0.40) | Mode BLOC actif |

### 3.4 Le panneau gauche — boutons spéciaux

| Bouton | Raccourci | Effet |
|---|---|---|
| **✕ Esc** | `Echap` | Annule toute sélection en cours. Retour à l'état IDLE. |
| **⣿ Bloc** | — | Active/désactive le mode BLOC. Disponible si une colonne est sélectionnée. Bascule entre SIMPLE et BLOC. |
| **↩ Undo** | `Ctrl+Z` | Annule le dernier coup joué. Illimité. |
| **↪ Redo** | `Ctrl+Y` | Rejoue le coup qui vient d'être annulé. |
| **? Aide** | `F1` | Ouvre la fenêtre d'aide intégrée. |

### 3.5 Le panneau droit — ruban historique

- **Compteur de coups** : affiché en grand. Reflète tous les déplacements validés.
- **Ruban des coups joués** : liste numérotée `C1→C2` ou `C1→C2 [B]` pour les blocs. Le dernier coup est en rouge gras.
- **Séparateur + coups annulés** : si des coups ont été annulés (undo), une ligne de séparation puis la liste des redos disponibles (en gris).
- **↺ RAZ** : remet le puzzle à sa configuration initiale. Demande confirmation.
- **💾 Enregistrer** : sauvegarde la partie complète dans un fichier YAML. (`Ctrl+S`)
- **📂 Charger** : charge une partie sauvegardée. (`Ctrl+O`)

### 3.6 La barre de commandes

Saisir une commande et appuyer sur `Entrée`. La barre affiche les messages d'erreur ou de confirmation à droite.

| Commande | Arguments | Effet |
|---|---|---|
| `deplace` | `C1 C2` | Déplacement simple de la colonne C1 vers C2 |
| `bloc` | `C1 C2` | Déplacement en bloc de C1 vers C2 |
| `efface` | — | Undo |
| `rejoue` | — | Redo |
| `raz` | — | Remet le plateau à l'état initial (confirmation) |
| `lire` | `<nom>` | Charge `parties/<nom>.partie.yaml` |
| `enregistre` | `<nom>` | Sauvegarde dans `parties/<nom>.partie.yaml` |
| `init` | `<nom>` | Charge `initialisations/<nom>.init.yaml` |
| `aide` ou `?` | — | Ouvre la fenêtre d'aide |
| `debug` | — | Affiche l'état interne du plateau dans la console |

### 3.7 Raccourcis clavier

| Raccourci | Effet |
|---|---|
| `Ctrl + Z` | Undo — annule le dernier coup |
| `Ctrl + Y` | Redo — rejoue le dernier coup annulé |
| `Ctrl + S` | Sauvegarde la partie |
| `Ctrl + O` | Charge une partie sauvegardée |
| `Echap` | Annule la sélection en cours |
| `F1` | Ouvre la fenêtre d'aide |

---

## 4. Guide du joueur pas à pas

### 4.1 Démarrer une partie

1. Lancer le programme : `python prog\main.py`
2. La fenêtre s'ouvre avec la configuration initiale. Les fonds de colonnes indiquent l'état final à atteindre.
3. Choisir la première colonne source.

### 4.2 Déplacement simple — exemple

Vous voulez déplacer le Rouge (R) du sommet de C1 vers C2.

1. **Clic sur C1** : C1 se surbrille en doré. Les colonnes où R peut aller s'affichent en vert.
2. **Clic sur C2** : R glisse de C1 vers C2 avec animation. Le compteur passe à 1. La ligne `1. C1→C2` apparaît dans le ruban.

### 4.3 Déplacement en bloc — exemple

Vous avez deux Bleus (B) au sommet de C3. La destination C5 a 2 cases libres et un Bleu au sommet.

1. **Clic sur le 2e pion (B) de C3** : mode BLOC activé directement. C3 se surbrille en bleu+blanc. Seules les colonnes acceptant un bloc s'affichent en vert.
2. **Clic sur C5** : les deux B glissent ensemble vers C5. 1 seul coup compté. Le ruban affiche `2. C3→C5 [B]`.

### 4.4 Glisser-déposer

- Maintenir le bouton gauche sur un pion puis glisser vers la destination.
- Un **fantôme semi-transparent** suit le curseur pendant le glisser.
- Si le glisser démarre depuis le **2e pion d'un couple** ET que les conditions du bloc sont remplies, le mode bloc s'active automatiquement (fantôme de 2 pions).
- Relâcher hors de la grille ou sur la même colonne annule le déplacement.

### 4.5 Sauvegarder et reprendre

**Sauvegarder** : cliquer sur 💾 Enregistrer (ou `Ctrl+S`), donner un nom. Le fichier est créé dans `parties/` avec l'extension `.partie.yaml`. Il contient l'état initial, l'état final et l'historique complet de tous les coups.

**Reprendre** : cliquer sur 📂 Charger (ou `Ctrl+O`), sélectionner le fichier. La partie se reconstruit en rejouant l'historique, ce qui garantit la cohérence des piles undo/redo.

### 4.6 Charger une configuration personnalisée

Créer un fichier `.init.yaml` dans `initialisations/`. Voir la [section 7.2](#72-fichier-dinitialisation-inityaml) pour le format.

```bash
# Au démarrage
python prog\main.py --init monpuzzle

# Pendant le jeu (barre de commandes)
init monpuzzle
```

---

## 5. Configuration — config.yaml

### 5.1 Principe général

Tout le comportement visuel et paramétrique du jeu est contrôlé par `prog/config.yaml`. Ce fichier texte peut être ouvert avec n'importe quel éditeur. Les changements prennent effet au prochain lancement.

!!! tip "Règle d'or"
    Ne jamais modifier un fichier `.py` pour changer l'apparence ou le comportement du jeu. Tout ce qui est paramétrable est dans `config.yaml`. Si une section manque dans `config.yaml`, les valeurs par défaut de `config.py` s'appliquent automatiquement.

### 5.2 Section `game` — dimensions du plateau

| Paramètre | Défaut | Description |
|---|---|---|
| `nb_columns` | `5` | Nombre de colonnes |
| `nb_rows` | `7` | Hauteur maximale d'une colonne |
| `nb_rows_initial` | `5` | Pions au départ par colonne. Cases libres = `nb_rows - nb_rows_initial` |
| `nb_colors` | `5` | Nombre de couleurs distinctes |
| `nb_pieces_per_color` | `5` | Pions par couleur. Validation : `nb_colors × nb_pieces_per_color = nb_columns × nb_rows_initial` |

### 5.3 Section `pieces` — apparence des pions

| Paramètre | Défaut | Description |
|---|---|---|
| `colors.R.fill` | `#E63946` | Couleur de remplissage (hex `#RRGGBB`) |
| `colors.R.outline` | `#9B1B24` | Couleur du contour |
| `colors.R.text` | `#FFFFFF` | Couleur de la lettre au centre |
| `radius` | `28` | Rayon du pion en pixels. Doit être `< cell_size / 2` |
| `outline_width` | `2` | Épaisseur du contour |
| `show_label` | `true` | Afficher la lettre initiale |
| `label_font` | `Helvetica` | Police de la lettre |
| `label_font_size` | `13` | Taille de la lettre |
| `label_font_bold` | `true` | Lettre en gras |

### 5.4 Section `grid` — grille et surbrillances

!!! info "Nouveauté v1.2 / v1.3"
    Les paramètres de traits (`inner_v`, `inner_h`, `outer_border`) et la transparence du fond cible (`target_alpha`) sont entièrement configurables.

| Paramètre | Défaut | Description |
|---|---|---|
| `cell_size` | `68` | Taille d'une cellule carrée (pixels) |
| `target_alpha` | `1.0` | Opacité du fond coloré des cibles. `0.0` = fond uni, `1.0` = couleur identique aux pions |
| `empty_cell_color` | `#1E1E2E` | Couleur des cases vides (hors zone cible) |
| `grid_bg` | `#12121F` | Couleur de fond générale du canvas |
| `inner_v_width` | `1` | Épaisseur des traits verticaux séparant les colonnes (`0` = désactivé) |
| `inner_v_color` | `#3A3A3A` | Couleur des séparateurs verticaux |
| `inner_h_width` | `0` | Épaisseur des traits horizontaux entre rangées (`0` = désactivé) |
| `inner_h_color` | `#2A2A2A` | Couleur des séparateurs horizontaux |
| `outer_border_width` | `2` | Épaisseur de la bordure extérieure (`0` = aucune) |
| `outer_border_color` | `#5A5A7A` | Couleur de la bordure extérieure |
| `highlight_color` | `#FFD700` | Couleur du contour de la colonne sélectionnée (doré) |
| `highlight_width` | `3` | Épaisseur du contour de sélection |
| `valid_color` | `#52B788` | Couleur des colonnes destination valides |

### 5.5 Section `animation`

| Paramètre | Défaut | Description |
|---|---|---|
| `enabled` | `true` | Activer les animations (`false` = instantané) |
| `duration_ms` | `300` | Durée d'une animation en millisecondes |
| `fps` | `60` | Images par seconde (30 à 60 recommandé) |
| `easing` | `ease_in_out` | Loi de vitesse : `linear` / `ease_in` / `ease_out` / `ease_in_out` |
| `guide_line.enabled` | `true` | Afficher le trait précurseur pointillé |
| `guide_line.dash` | `[6, 4]` | Motif du pointillé : `[px pleins, px vides]` |

### 5.6 Section `debug`

| Paramètre | Défaut | Description |
|---|---|---|
| `enabled` | `false` | Active toutes les traces debug (aussi activable avec `--debug`) |
| `highlight_valid` | `true` | Colorer en vert les destinations valides |

Quand `debug.enabled: true`, chaque appel de méthode du contrôleur génère une ligne :

```
10:23:45 [DEBUG  ] puzzle.controller: DBG _on_click  état=SRC_SELECTED  src=2  col=4  row=1  is_pair_bot=False
```

### 5.7 Section `logging`

| Paramètre | Défaut | Description |
|---|---|---|
| `level` | `INFO` | Niveau de log : `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `log_to_file` | `true` | Écrire les logs dans un fichier rotatif |
| `log_to_console` | `false` | Écrire aussi sur stdout |
| `max_file_size_kb` | `512` | Taille maximale avant rotation |
| `max_backup_files` | `3` | Nombre de fichiers de sauvegarde |
| `filename` | `puzzle.log` | Nom du fichier dans `paths.log_dir` |

### 5.8 Section `paths`

| Paramètre | Défaut | Description |
|---|---|---|
| `saves_dir` | `./parties` | Dossier de sauvegarde des parties |
| `init_dir` | `./initialisations` | Dossier des configurations initiales |
| `log_dir` | `./logs` | Dossier des fichiers journaux |
| `save_extension` | `.partie.yaml` | Extension ajoutée aux sauvegardes |
| `init_extension` | `.init.yaml` | Extension ajoutée aux initialisations |

---

## 6. Arguments de la ligne de commande

```bash
python prog\main.py [--aide] [--debug] [--check] [--init F] [--partie F]
```

| Argument | Abréviation | Effet |
|---|---|---|
| `--aide` | `-h` | Affiche l'aide console et quitte |
| `--debug` | — | Force le mode debug (surcharge `config.yaml`) |
| `--check` | — | Vérifie que `config.yaml` est valide, affiche les versions et quitte |
| `--init FICHIER` | — | Charge `initialisations/<FICHIER>.init.yaml` au démarrage |
| `--partie FICHIER` | — | Charge `parties/<FICHIER>.partie.yaml` au démarrage |

**Exemples :**

```bash
python prog\main.py                        # démarrage normal
python prog\main.py --debug                # avec traces détaillées
python prog\main.py --init monpuzzle       # charge une config personnalisée
python prog\main.py --partie save_23       # reprend une partie sauvegardée
python prog\main.py --check                # vérifie la config et quitte
```

---

## 7. Formats des fichiers de données

### 7.1 Fichier de partie (`.partie.yaml`)

Ce fichier est créé lors d'une sauvegarde. Il contient tout ce qu'il faut pour reconstituer exactement la partie, y compris les piles undo et redo.

```yaml
meta:
  version: 1                       # version du format
  date: 2026-04-15T14:32:00        # date de sauvegarde (ISO 8601)
  moves: 12                        # nombre de coups joués

initial:                           # état de départ (bas → sommet)
  - [O, V, B, J, R]               # colonne 1
  - [R, O, V, B, J]               # colonne 2
  - [J, R, O, V, B]               # colonne 3
  - [B, J, R, O, V]               # colonne 4
  - [V, B, J, R, O]               # colonne 5

final:                             # état objectif
  - [O, O, O, R, R]
  - [J, J, J, B, B]
  - [V, V, V, O, O]
  - [R, R, R, J, J]
  - [B, B, B, V, V]

current: [[ ... ]]                 # état courant après les coups joués

history:                           # liste de tous les coups
  - {type: simple, from: 1, to: 3}
  - {type: bloc,   from: 3, to: 5}
  - {type: simple, from: 2, to: 1}

current_move: 12
```

### 7.2 Fichier d'initialisation (`.init.yaml`)

Ce fichier permet de créer des puzzles personnalisés. Le placer dans `initialisations/` et le charger avec `--init` ou la commande `init`.

```yaml
# Mon puzzle personnalisé
initial:
  - [O, V, B, J, R]               # colonne 1 : bas → sommet
  - [R, O, V, B, J]
  - [J, R, O, V, B]
  - [B, J, R, O, V]
  - [V, B, J, R, O]

final:
  - [O, O, O, O, O]               # exemple pédagogique : 1 couleur/colonne
  - [R, R, R, R, R]
  - [J, J, J, J, J]
  - [B, B, B, B, B]
  - [V, V, V, V, V]
```

!!! warning "Contraintes obligatoires"
    - Chaque colonne doit contenir exactement `nb_rows_initial` pions (5 par défaut).
    - Le nombre total de pions doit être identique dans `initial` et `final`.
    - Chaque couleur doit apparaître le même nombre de fois dans `initial` et `final`.
    - Les identifiants de couleurs doivent correspondre aux clés de `pieces.colors`.

---

## 8. Programmes source

### 8.1 Organisation des fichiers

```
projet/
├── package/                     ← archive source pour le déploiement
│   ├── installation.py          ← installateur générique (ne change jamais)
│   ├── data_installation_v1.3.py← manifeste de la livraison courante
│   ├── main_v1.2.py             ← fichiers sources versionnés
│   ├── config_v1.1.py
│   ├── model_v1.1.py
│   ├── view_v1.3.py
│   ├── controller_v1.3.py
│   ├── fileio_v1.0.py
│   ├── logger_v1.0.py
│   ├── config.yaml
│   └── exemple.init.yaml
│
└── prog/                        ← dossier d'exécution
    ├── main.py                  ← copies sans numéro de version
    ├── config.py
    ├── model.py
    ├── view.py
    ├── controller.py
    ├── fileio.py
    ├── logger.py
    ├── config.yaml
    ├── parties/                 ← sauvegardes de parties
    ├── initialisations/         ← configurations personnalisées
    └── logs/                    ← fichiers journaux rotatifs
```

### 8.2 Liste des fichiers source

| Fichier | Version | Lignes | Description |
|---|---|---|---|
| `main.py` | 1.2 | 204 | Point d'entrée : arguments CLI, création de la fenêtre Tkinter, instanciation de tous les composants, boucle principale. |
| `config.py` | 1.1 | 224 | Charge `config.yaml`, fusionne avec `DEFAULTS`, expose tous les paramètres par attributs imbriqués (`cfg.grid.cell_size`). |
| `model.py` | 1.1 | 152 | Logique du jeu : colonnes, règles de déplacement, vérification de victoire par `Counter`, piles undo/redo par snapshots. |
| `view.py` | 1.3 | 668 | Tous les composants visuels Tkinter : grille animée, boutons, ruban, saisie, fenêtres de dialogue. |
| `controller.py` | 1.3 | 455 | Machine à 3 états, gestion des clics et du drag & drop, exécution des commandes textuelles. |
| `fileio.py` | 1.0 | 84 | Sérialisation YAML des parties (`save_game`, `load_game`, `load_init`). |
| `logger.py` | 1.0 | 79 | Registre des versions, configuration du `RotatingFileHandler`, bannière de démarrage. |

### 8.3 Rubrique Programme — `main.py`

!!! abstract "Contenu de main.py"
    - `parse_args()` avec tous les arguments (`--aide`, `--debug`, `--check`, `--init`, `--partie`).
    - `DEFAULT_INITIAL` et `DEFAULT_FINAL` (configuration par défaut).
    - `main()` qui crée l'arborescence des objets dans l'ordre : `Config` → `GameState` → fenêtre `Tk` → vues → `GameController`.
    - Bindings raccourcis clavier (`Ctrl+Z`, `F1`, `Echap`, etc.).
    - Rebinding des boutons `TapePanel` sur le contrôleur.
    - `root.mainloop()` en toute fin.

### 8.4 Rubrique Programme — `config.py`

!!! abstract "Contenu de config.py"
    - Dictionnaire `DEFAULTS` avec toutes les valeurs par défaut.
    - Classe `Config` avec `__init__(path)`, `__getattr__`, `get_color()`, `font()`, `str()`.
    - `_deep_merge()` pour fusionner `DEFAULTS` et `config.yaml`.
    - `_to_ns()` pour convertir un `dict` en `SimpleNamespace` imbriqué.
    - `_validate()` pour vérifier la cohérence des dimensions.

### 8.5 Rubrique Programme — `model.py`

!!! abstract "Contenu de model.py"
    - `MoveRecord` (dataclass) : `type`, `src`, `dst`, `label()`, `to_dict()`, `from_dict()`.
    - `GameState` avec les méthodes :
        - Accès : `top()`, `second()`, `height()`, `free()`, `snapshot()`
        - Règles : `can_move()`, `can_bloc()`, `has_bloc_candidate()`, `valid_dests()`
        - Actions : `do_move()`, `undo()`, `redo()`, `reset()`
        - Victoire : `is_won()` — utilise `Counter` (ordre non requis)
        - Debug : `__repr__()` affiche la grille en ASCII

### 8.6 Rubrique Programme — `view.py`

!!! abstract "Contenu de view.py"
    - `BoardView` : canvas principal, 7 couches de dessin, gestion `DRAG_THRESHOLD` (seuil 8 px pour distinguer clic de drag), animations avec easing, ghost drag.
    - `SpecialPanel` : 5 boutons d'action (Esc, Bloc, Undo, Redo, Aide).
    - `TapePanel` : compteur + ruban historique + 3 boutons.
    - `CommandBar` : champ de saisie avec placeholder.
    - `show_win_dialog()` et `show_help_dialog()`.
    - `AIDE_TEXTE` : texte de l'aide intégrée.

### 8.7 Rubrique Programme — `controller.py`

!!! abstract "Contenu de controller.py"
    - `GameController` avec les 3 états (`IDLE` / `SRC_SELECTED` / `BLOC_PENDING`).
    - `_is_pair_bottom(col, row)` : détecte si le clic est sur le 2e pion d'un couple.
    - `_on_click(col, row)`, `_on_drag_start(col, row)`, `_on_drag_end(dst)`.
    - `_select_col()`, `_activate_bloc_mode()`, `_deactivate_bloc_mode()`.
    - `do_undo()`, `do_redo()`, `do_reset()`, `show_aide()`.
    - `do_save()`, `do_load()`, `do_load_init()`.
    - `on_command(text)` : analyse et dispatch des commandes textuelles.
    - `_dbg()` : trace debug conditionnelle (log + console).

### 8.8 Rubrique Programme — `fileio.py`

!!! abstract "Contenu de fileio.py"
    - `save_game(state, path)` : sérialise `GameState` complet en YAML.
    - `load_game(path, cfg)` : désérialise et rejoue l'historique coup par coup.
    - `load_init(path)` : lit `initial` et `final` depuis un `.init.yaml`.
    - `add_extension(path, ext)` : utilitaire d'extension automatique.

### 8.9 Rubrique Programme — `logger.py`

!!! abstract "Contenu de logger.py"
    - `_registry` : dictionnaire `{nom_module → version}`.
    - `register(VERSION)` : appelé par chaque module à son import.
    - `setup(cfg)` : configure `RotatingFileHandler` + `StreamHandler` selon `config.yaml`.
    - `log_banner(logger, app_name)` : affiche la liste des versions au démarrage.
    - `get(name)` : retourne un logger enfant (`puzzle.controller`, `puzzle.view`, etc.).

### 8.10 Convention de versionnage — règles absolues

Chaque fichier `.py` respecte un format strict :

| Position | Contenu obligatoire | Exemple |
|---|---|---|
| **Ligne 1** (absolue) | Commentaire avec nom et version | `# view.py  v1.3` |
| **Ligne 2** (absolue) | `from __future__ import annotations` | `from __future__ import annotations` |
| Variable globale | Tuple (nom, version) | `VERSION = ('view.py', '1.3')` |
| **Toute fin du fichier** | Commentaire de clôture | `# end view.py  v1.3` |
| Au chargement | Appel logger.register | `logger.register(VERSION)` |

!!! danger "Règle impérative"
    - **Incrémenter le numéro de version au moindre changement.** L'installateur compare les versions pour décider si une copie est nécessaire.
    - Un fichier avec `# end` manquant est considéré **tronqué** et n'est **jamais** copié.
    - `from __future__ import annotations` doit impérativement être en **ligne 2** (après le commentaire `#`). En ligne 1, Python lève une `SyntaxError`.

---

## 9. Architecture technique

### 9.1 Schéma général MVC

```
┌─────────────────────────────────────────────────────────────┐
│                       config.yaml                           │
│                           │                                 │
│                    Config (config.py)                       │
│                           │  partagé par tous               │
└─────────────────────────────────────────────────────────────┘

main.py (point d'entrée)
   │
   ├── GameState (model.py)       ← pure logique, pas de Tkinter
   │
   ├── BoardView    ┐
   ├── SpecialPanel │  view.py    ← affichage, pas de règles
   ├── TapePanel    │
   ├── CommandBar   ┘
   │
   └── GameController (controller.py)
          │   coordonne model ↔ vue
          │
          ├── fileio.py   (YAML)
          └── logger.py   (journalisation)
```

### 9.2 Machine à états du contrôleur

```
                    ┌─────────────────────────────────────────┐
                    │                  IDLE                   │
                    │   (aucune sélection active)             │
                    └─────────────────────────────────────────┘
                              │               ▲
              Clic col non vide              Esc / clic hors grille
                              ▼               │
                    ┌─────────────────────────────────────────┐
                    │            SRC_SELECTED                 │
                    │   Contour doré. Destinations vertes.    │
                    └─────────────────────────────────────────┘
              Re-clic 2e pion ↕ ← → Bouton Bloc ou re-clic source
              (couple)         │               │
                              ▼               ▲
                    ┌─────────────────────────────────────────┐
                    │            BLOC_PENDING                 │
                    │   Contour bleu+blanc. Destinations bloc.│
                    └─────────────────────────────────────────┘
```

| État | Transitions possibles |
|---|---|
| **IDLE** | Clic col non vide → `SRC_SELECTED` |
| **SRC_SELECTED** | Clic 2e pion (couple) → `BLOC_PENDING` · Clic destination → coup puis `IDLE` · Esc / clic hors grille → `IDLE` |
| **BLOC_PENDING** | Clic source → `SRC_SELECTED` · Clic destination → coup puis `IDLE` · Esc / clic hors grille → `IDLE` |

### 9.3 Architecture des événements souris (v1.3)

La gestion des événements a été entièrement repensée pour éliminer les interférences entre clic et drag.

| Événement Tkinter | Rôle dans `view.py` | Transmis au contrôleur |
|---|---|---|
| `<ButtonPress-1>` | Mémorise position x, y, col, row | **Rien** (pas de logique jeu) |
| `<B1-Motion>` | Si déplacement > **8 px** : démarre drag, crée fantôme | `drag_start_cb(col, row)` |
| `<ButtonRelease-1>` | Si drag en cours → fin drag · Sinon → clic | `drag_end_cb(dst_col)` · `click_cb(col, row)` |

!!! success "Avantage clé"
    Le contrôleur ne reçoit **jamais** simultanément press+click pour le même événement. La source et la destination ne peuvent plus se confondre. C'est la correction du bug B2 (v1.2) qui causait l'échappement involontaire.

### 9.4 Logique de détection du mode bloc

La sélection du mode bloc est basée sur la **position du clic**, pas sur une détection automatique. Cette règle respecte l'intention du joueur.

| Position du clic | Colonne cliquée | Effet |
|---|---|---|
| Pion du sommet (`row = height-1`) | N'importe laquelle | Sélection **SIMPLE** |
| Zone vide au-dessus | Colonne non vide | Sélection **SIMPLE** du sommet |
| 2e pion (`row = height-2`) + couple | Source | Sélection **BLOC** directement |
| Bouton ⣿ Bloc | N/A | Bascule SIMPLE ↔ BLOC |
| Drag depuis 2e pion d'un couple | Source | Drag **BLOC** automatique |

### 9.5 Bannière de démarrage

Au lancement, chaque module s'auto-enregistre via `logger.register(VERSION)`. La bannière résultante est écrite dans le log :

```
─────────────────────────────────────────────────────
Puzzle des Couleurs — Démarrage
─────────────────────────────────────────────────────
  config.py               v1.1
  controller.py           v1.3
  fileio.py               v1.0
  logger.py               v1.0
  main.py                 v1.2
  model.py                v1.1
  view.py                 v1.3
─────────────────────────────────────────────────────
```

---

## 10. Historique des versions

| Version | Date | Fichiers | Modifications |
|---|---|---|---|
| **v1.0** | Mars 2026 | Tous (initial) | Création : architecture MVC, règles du jeu, `config.yaml` complet, animations, undo/redo illimité, fileio YAML, logger avec registre, système d'installation. |
| **v1.1** | Mars 2026 | main, view, controller, installation, data | Correction bug `from __future__` (devait être ligne 2). Bouton/commande/argument `--aide`. Raccourci `F1`. Traces debug log + console. Retour visuel dès le 1er clic. Installateur générique (lit le projet dans le manifeste, crée `prog/` si absent). |
| **v1.2** | Mars 2026 | config, view, controller, data | Bug B1 : pions plus effacés (bg_tint dessiné AVANT piece, hl_border sans fill). Bug B2 : re-clic même colonne ne fait plus d'escape involontaire. Bug B3 : mode bloc corrigé pour clic/bouton/drag. Nouveaux params grille (inner_v/h/outer_border). `target_alpha=1.0`. `Counter` pour `is_won()`. |
| **v1.3** | Avril 2026 | main, model, view, controller, data | Refonte événements souris (DRAG_THRESHOLD 8 px, séparation stricte clic/drag). Sélection bloc basée sur la position du clic (2e pion). Escape sur clic hors grille. Nouvel état final général (multi-couleurs par colonne). `sorted(final[col])` dans `draw_static_background`. |

---

## Annexe A — Le système d'installation

### A.1 Principe et motivation

Le système d'installation est conçu pour livrer de nouvelles versions sans que le destinataire ait à identifier manuellement quels fichiers ont changé, lesquels supprimer, et dans quel ordre copier.

Il repose sur deux fichiers ayant des rôles complémentaires :

| Fichier | Évolution | Rôle |
|---|---|---|
| `installation.py` | **Ne change jamais** | Moteur générique de déploiement |
| `data_installation_vX.Y.py` | Nouvelle version à chaque livraison | Manifeste décrivant ce qu'il faut faire |

!!! tip "Principe de généricité"
    `installation.py` ne contient **aucune référence au projet**. Il lit tout depuis `data_installation_vX.Y.py` : nom du projet, liste des fichiers, fichiers à supprimer, dossiers à créer. Ce mécanisme permet de réutiliser le même installateur pour n'importe quel projet Python.

### A.2 Utilisation

```bash
# Depuis le dossier package/
python installation.py              # déploiement normal
python installation.py --check      # simulation complète sans aucune copie
python installation.py --force      # force la copie même si versions identiques
python installation.py --aide       # affiche l'aide de l'installateur
```

### A.3 Déroulement d'une installation

1. Parcourt `package/` pour trouver le fichier `data_installation_vX.Y.py` le plus récent.
2. Importe dynamiquement ce manifeste et lit : `PROJET`, `VERSION_PROJET`, `SRC`, `DST`, `FICHIERS`, `SUPPRIMER`, `SOUS_DOSSIERS`.
3. Affiche un en-tête récapitulatif (nom du projet, source, cible, mode).
4. Crée `prog/` et ses sous-dossiers (`parties/`, `logs/`, `initialisations/`) s'ils n'existent pas.
5. Pour chaque fichier dans `FICHIERS` : vérifie l'existence, contrôle le marqueur `# end` (intégrité), compare les numéros de version, copie si nécessaire.
6. Pour chaque fichier dans `SUPPRIMER` : supprime s'il existe (anciens manifestes, anciennes versions).
7. Parcourt `prog/` et signale les fichiers non répertoriés dans `CONNUS` (orphelins suspects).
8. Affiche le bilan : copies effectuées, fichiers à jour, erreurs éventuelles.

### A.4 Vérification d'intégrité

Avant toute copie, chaque fichier source est vérifié :

- **Existence** : le fichier est présent dans le dossier source. Un fichier manquant est signalé `ABSENT`.
- **Marqueur de clôture** : la dernière ligne non vide doit commencer par `# end`. Ce marqueur prouve que le fichier est complet et non tronqué.
- **Comparaison de version** : la version extraite de la première ligne du fichier source est comparée à celle du fichier cible. La copie n'a lieu que si les versions diffèrent, ou si `--force` est spécifié.

```
  OK        config_v1.1.py  ->  prog/config.py    v1.1 -> v1.1  [à jour]
  COPIE     view_v1.3.py    ->  prog/view.py      v1.3 -> v1.2
  TRONQUÉ   model_v1.1.py   ->  prog/model.py               [# end absent !]
  ABSENT    fileio_v1.0.py  ->  prog/fileio.py              [OBLIGATOIRE]
  SIM       controller...   ->  prog/controller.py v1.3->v1.2  [--check]
```

### A.5 Le manifeste `data_installation_vX.Y.py`

```python
# data_installation_v1.3.py  v1.3

from pathlib import Path

PROJET         = "Puzzle des Couleurs"   # nom du projet (affiché dans l'en-tête)
VERSION_PROJET = "1.3"                   # version de cette livraison

_ici = Path(__file__).parent             # dossier package/
SRC  = _ici                              # source des fichiers versionnés
DST  = _ici.parent / "prog"             # destination = dossier prog/

SOUS_DOSSIERS = [                        # dossiers à créer si absents
    DST / "initialisations",
    DST / "parties",
    DST / "logs",
]

FICHIERS = [                             # (nom_source, chemin_cible, obligatoire)
    ("main_v1.2.py",        DST / "main.py",       True),
    ("config_v1.1.py",      DST / "config.py",     True),
    ("view_v1.3.py",        DST / "view.py",       True),
    ("controller_v1.3.py",  DST / "controller.py", True),
    ("model_v1.1.py",       DST / "model.py",      True),
    ("fileio_v1.0.py",      DST / "fileio.py",     True),
    ("logger_v1.0.py",      DST / "logger.py",     True),
    ("config.yaml",         DST / "config.yaml",   True),
    ("exemple.init.yaml",   DST / "initialisations" / "exemple.init.yaml", True),
    ("installation.py",     DST / "installation.py", False),
    ("data_installation_v1.3.py", DST / "data_installation_v1.3.py", False),
]

SUPPRIMER = [                            # fichiers obsolètes à effacer
    DST / "data_installation_v1.2.py",
    DST / "data_installation_v1.1.py",
]

CONNUS      = {Path(c).name for _, c, _ in FICHIERS}
CONNUS     |= {"__init__.py", "lancer.cmd", "lancer.bat"}
IGNORER_EXT = {".pyc", ".pyo", ".log", ".partie.yaml", ".init.yaml"}
IGNORER_DIR = {"__pycache__", "parties", "logs", "initialisations"}
```

### A.6 Le programme `installation.py`

> *Placez ici le contenu du fichier `installation.py` fourni dans le package.*

!!! note "Ce fichier ne doit jamais être modifié"
    `installation.py` est conçu pour être universel et permanent. Tout ce qui est spécifique à un projet appartient exclusivement dans `data_installation_vX.Y.py`.

### A.7 Adapter l'installateur à un autre projet

1. Conserver `installation.py` tel quel (ne jamais le modifier).
2. Créer un nouveau `data_installation_vX.Y.py` en adaptant `PROJET`, `VERSION_PROJET`, `SRC`, `DST`, `FICHIERS`, `SUPPRIMER` et `CONNUS`.
3. Placer les fichiers sources versionnés (`nom_vX.Y.py`) dans `package/`.
4. Chaque fichier source doit respecter la convention (`# nom.py vX.Y` en ligne 1, `# end nom.py vX.Y` en dernière ligne).
5. Lancer `python installation.py --check` pour vérifier sans modifier, puis `python installation.py` pour déployer.

---

*— Fin du manuel — Puzzle des Couleurs · v1.3 · Python / Tkinter / PyYAML*
