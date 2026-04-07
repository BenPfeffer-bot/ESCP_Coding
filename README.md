# Yield Curve Bootstrapper & Swap Pricer

#projet #python #taux #quantitative-finance #trading-desk #complété

## Objectif

Construire un **outil complet de desk de trading taux** en Python : de la récupération des données live jusqu'au dashboard interactif, en passant par le bootstrapping de la courbe zéro-coupon, le pricing de swaps vanille et le calcul des sensibilités.

**Application desk** : c'est littéralement l'outil de base d'un junior trader taux — fetch les yields, construire la courbe, pricer les swaps, calculer le risque, afficher un dashboard.

## État final : PROJET COMPLET 

Tous les modules sont implémentés, testés avec des données live, et documentés. Le dashboard Streamlit est fonctionnel.

```
rates_project/
├── app/                          # Dashboard Streamlit multipage
│   ├── streamlit_app.py
│   ├── state.py
│   ├── pages/
│   │   ├── 1_📈_Curves.py
│   │   ├── 2_💰_Pricer.py
│   │   ├── 3_📊_Risk.py
│   │   └── 4_📜_History.py
│   └── components/
│       ├── sidebar.py
│       ├── data_loader.py
│       └── metric_cards.py
│
├── src/
│   ├── api/
│   │   └── data_feed.py          # yfinance + FRED + cache SQLite
│   ├── curves/
│   │   ├── bootstrapper.py       # Bootstrap ZC curve
│   │   └── interpolation.py      # Linear & Cubic spline interpolation
│   ├── instruments/
│   │   └── vanilla_swaps.py      # IRS pricer
│   ├── risks/
│   │   └── sensitivities.py      # DV01, convexity, KR-DV01
│   ├── plots/                    # Visualization
│   │   ├── theme.py
│   │   ├── curves.py             # Plots matplotlib
│   │   ├── risks.py
│   │   ├── history.py
│   │   └── plotly_backend/       # Plots Plotly interactifs
│   │       ├── theme.py
│   │       ├── curves.py
│   │       ├── risks.py
│   │       └── history.py
│   ├── utils/
│   │   ├── cache.py              # Cache SQLite des snapshots
│   │   └── helper.py             # Helper reprice() partagé
│   └── tests/                    # Tests visuels + validation
│       ├── test_cache.py
│       ├── test_plots_curves.py
│       ├── test_plots_risk.py
│       └── test_plots_plotly_all.py
│      
├── scripts/
│   └── daily_fetch.py    
│
├── settings/
│   ├── paths.py                  # Chemins du projet
│   ├── config.py                 # Constantes API, tickers, séries FRED
│   └── logs.py                   # Logger factory
│
├── db/
│   └── cache/
│       └── yields.db             # SQLite : snapshots des yields
│
├── plots/
│   ├── plotly/                  # HTML des plots
│   └── output/                  # PNG
│
└── logs/
```

---

## Pipeline end-to-end

```
┌─────────────────────────────────────────────────────────┐
│  Market data (yfinance + FRED)                          │
│  4 tickers CBOE + 6 séries FRED → 10 points de courbe   │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│  Cache SQLite (db/cache/yields.db)                      │
│  Évite les appels API redondants. Historique persistent │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│  Bootstrapper (Module 1)                                │
│  Extraction des discount factors Z(0, T)                │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│  Interpolator (Module 2)                                │
│  Cubic spline sur les zero rates                        │
│  → Z(0, T), y(T), f(T1, T2) pour tout T                │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│  Swap Pricer (Module 3)                                 │
│  NPV, par rate, PV fixed/float leg                      │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│  Risk Engine (Module 4)                                 │
│  DV01, convexity, KR-DV01 par bump & reprice            │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│  Visualization (Module 5)                               │
│  Plots matplotlib (exports) + Plotly (interactif)       │
│  Dashboard Streamlit multipage (4 pages)                │
└─────────────────────────────────────────────────────────┘
```


## Résultats validés sur données live

### Courbe US Treasury (avril 2026)

Pipeline complet exécuté sur données réelles yfinance + FRED :

```
0.25Y : 3.630% (yfinance)
0.50Y : 3.730% (FRED)
1.00Y : 3.720% (FRED)
2.00Y : 3.840% (FRED)
3.00Y : 3.880% (FRED)
5.00Y : 3.974% (yfinance)
7.00Y : 4.170% (FRED)
10.0Y : 4.331% (yfinance)
20.0Y : 4.910% (FRED)
30.0Y : 4.902% (yfinance)
```

**Lecture macro** : courbe upward-sloping globalement, avec une légère **inversion sur le long-end** (30Y < 20Y) — signal d'anticipation de baisses de taux à long terme.

### Swap 5Y receiver 10M€ at-par

Tous les tests du Module 4 passent avec les valeurs attendues :

| Métrique | Valeur | Check |
|----------|--------|-------|
| NPV at-par | €0.00 | ✅ (exact) |
| DV01 parallèle | 4,424.34 €/bp | ✅ (duration implicite ~4.42) |
| Convexité dollar | 2.55 €/bp² | ✅ (positive) |
| Sum KR-DV01 | 4,424.34 €/bp | ✅ |
| Diff vs parallèle | 1.56e-04 € | ✅ (0.0000035%) |

### KR-DV01 ladder

98.3% du risque concentré sur le 5Y comme attendu, avec de petites oscillations signées sur les buckets voisins (comportement classique d'une cubic spline).

---

## Notes Obsidian du projet

| Note | Contenu |
|------|---------|
| [[Module 1 - Bootstrapper]] | Théorie + code + tests |
| [[Module 2 - Interpolation]] | Théorie + code + tests + diagnostic yfinance |
| [[Module 3 - Swap Pricer]] | Théorie + code + tests + pattern d'écart bootstrap/pricer |
| [[Module 4 - Risk Analytics]] | Théorie + code + tests + analyse cubic spline oscillations |
| [[Module 5 - Visualization]] | Plots matplotlib + Plotly + charte graphique |
| [[Dashboard Streamlit]] | Architecture multipage + composants |
| [[Cache SQLite]] | Schéma + intégration + leçon pollution tests |
| [[Data Feed - yfinance API]] | Référence yfinance + tickers CBOE |
| [[Data Feed - FRED API]] | Référence FRED + séries Treasury CMT |
| [[fetch_snapshot - Implémentation]] | Best practices debug + logging |
| [[Données Live Mars 2026]] | Snapshot des valeurs de marché observées |

---

## Lancement

### Tests du pipeline

```bash
# Test du cache SQLite
python -m src.tests.test_cache

# Tests des plots matplotlib (exports PNG)
python -m src.tests.test_plots_curves
python -m src.tests.test_plots_risk

# Tests des plots Plotly (exports HTML)
python -m src.tests.test_plots_plotly_all

# Test du data feed en standalone
python -m src.api.data_feed
```

### Dashboard Streamlit

```bash
streamlit run app/streamlit_app.py
```

Ouvre automatiquement `http://localhost:8501`.

---

## Formules clés — Résumé

### Bootstrapping
$$Z(0, T_{j+1}) = \frac{1 - r_s(T_{j+1}) \cdot \sum_{i=1}^{j} \tau_i \cdot Z(0, T_i)}{1 + r_s(T_{j+1}) \cdot \tau_{j+1}}$$

### Taux zéro-coupon (continu)
$$y(T) = -\frac{\ln Z(0, T)}{T}$$

### Taux forward
$$f(T_1, T_2) = -\frac{\ln(Z(0, T_2) / Z(0, T_1))}{T_2 - T_1}$$

### Pricing swap (convention A)
$$PV_{\text{fixe}} = c \sum_i \tau_i Z_i + Z_N \qquad PV_{\text{float}} = 1$$

$$\text{NPV}_{\text{receiver}} = N \cdot (PV_{\text{fixe}} - 1)$$

### Par rate
$$c^* = \frac{1 - Z(0, T_N)}{\sum_{i=1}^{n} \tau_i \cdot Z(0, T_i)}$$

### DV01 (différence symétrique)
$$\text{DV01} = \frac{V(r - 1\text{bp}) - V(r + 1\text{bp})}{2}$$

### Convexité dollar
$$C_\$ = V(r - 1\text{bp}) + V(r + 1\text{bp}) - 2 V(r)$$

---

## Stack technique

**Langages & frameworks**
- Python 3.11+
- Streamlit (dashboard multipage)

**Data & numerical**
- numpy, scipy (interpolation)
- pandas (tables et exports)
- yfinance, fredapi (data feed)

**Visualization**
- matplotlib (exports statiques)
- plotly (interactivité dashboard)

**Persistence**
- SQLite (cache des snapshots)

**Infrastructure**
- dotenv (gestion des secrets)
- logging (tracing propre)
- ruff (linting)

---

## Sources pédagogiques

- **Didier Marteau** — Options (pour le framework Greeks utilisé implicitement)
- **John Hull** — Options, Futures, and Other Derivatives (Ch.4, Ch.7)
- **Paul Wilmott** — Quantitative Finance (Ch.14, Ch.15)
- **Siddhartha Jha** — Interest Rate Markets (Ch.5, Ch.8) — **référence principale** pour le projet
- **Hagan & West** (2006) — Interpolation methods for curve construction
