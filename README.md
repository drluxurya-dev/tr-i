# BareInstall

**BareInstall** est un outil open source permettant d'installer des systèmes d'exploitation (prioritairement **Omarchy**) sur un PC sans clé USB ni support externe, en préparant un environnement d'installation démarrable directement depuis le disque dur interne sous Windows 10/11.

---

## 🎯 Objectifs du Projet

1. **Axe principal :** Préparer et amorcer l'installation de la distribution **Omarchy** sans support d'installation USB ou externe.
2. **Compatibilité cible :** Windows 10/11 64-bit sur Intel Pentium Silver, 4 Go de RAM, disque interne SSD/NVMe/SATA/eMMC (~789 Go).
3. **Sécurité absolue :**
   - **Lecture seule :** La première phase du projet est strictement en lecture seule. Aucune modification du disque, des partitions ou du magasin BCD n'est entreprise sans diagnostic explicite.
   - **Détection des bloqueurs :** Détection préalable de BitLocker, Secure Boot, Fast Startup, de la mémoire RAM et du style de partitionnement (UEFI / GPT).

---

## 📂 Architecture du Projet

```
.
├── docs/
│   ├── FEASIBILITY_STUDY.md   # Étude de faisabilité, risques & méthodes de boot
│   └── ARCHITECTURE.md        # Architecture logicielle modulaire (7 modules)
├── bareinstall/
│   ├── __init__.py
│   ├── cli.py                 # Interface CLI (Terminal, JSON, Markdown)
│   └── host_manager/          # Module de diagnostic en lecture seule
│       ├── __init__.py
│       ├── models.py          # Dataclasses (SystemReport, DiagnosticSummary)
│       ├── collector.py       # Collecteur Windows PowerShell/WMI & Mock Linux
│       └── analyzer.py        # Analyseur des règles d'éligibilité Omarchy
└── tests/
    └── test_host_manager.py   # Suite de tests pytest pour scénarios limites
```

---

## 🚀 Utilisation & Exécution

### 1. Diagnostic Système (Lecture Seule)

Pour exécuter le diagnostic en lecture seule sous Windows :

```bash
python -m bareinstall.cli
```

#### Exécution en mode simulation (Mock)
Sur Linux ou pour tester sans matériel Windows réel :

```bash
python3 -m bareinstall.cli --simulate
```

#### Exportation des Rapports
Vous pouvez exporter le rapport de diagnostic aux formats JSON et Markdown :

```bash
python3 -m bareinstall.cli --simulate --json-out rapport.json --md-out rapport.md
```

---

## 🧪 Tests Automatisés

La suite de tests est développée avec `pytest` et couvre l'ensemble des cas de figure matériel (BitLocker actif, RAM insuffisante, BIOS Legacy, Secure Boot activé, MBR vs GPT) :

```bash
PYTHONPATH=. pytest
```

---

## 📚 Sources Officielles & Documentation
- **Omarchy Website :** [https://omarchy.org/](https://omarchy.org/)
- **Omarchy Repository :** [https://github.com/basecamp/omarchy](https://github.com/basecamp/omarchy)
- **Étude de faisabilité technique :** Voir [docs/FEASIBILITY_STUDY.md](docs/FEASIBILITY_STUDY.md)
- **Architecture complète :** Voir [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
