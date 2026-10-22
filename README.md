# BareInstall

**BareInstall** est un outil open source en Python permettant de préparer et d'installer des systèmes d'exploitation (prioritairement **Omarchy**) sur un PC sans clé USB ni support externe, depuis le disque interne sous Windows 10/11.

---

## 🎯 Objectifs & Principes de Sécurité

1. **Priorité Omarchy :** Préparation de l'installation officielle d'Omarchy conformément à sa documentation officielle.
2. **Conservation de Windows :** Installation dual-boot sur l'espace libre par défaut. Aucune suppression de partition ni formatage de disque entier n'est effectué automatiquement.
3. **Vérification Cryptographique ISO Stricte :** Les images ISO doivent être validées via leur empreinte SHA256 officielle (`--expected-sha256`).
4. **Sauvegarde & Restauration BCD :** Toute modification de démarrage sous Windows exige une sauvegarde préalable du BCD et des privilèges administrateur.

---

## 📂 Structure du Dépôt

```
.
├── docs/
│   ├── FEASIBILITY_STUDY.md   # Étude de faisabilité & contraintes EFI/FAT32
│   ├── ARCHITECTURE.md        # Architecture logicielle modulaire (7 modules)
│   ├── RECOVERY_GUIDE.md      # Guide de restauration d'urgence BCD
│   └── STATUS_REPORT.md       # Matrice de statut & fonctionnalités réelles vs simulées
├── bareinstall/
│   ├── __init__.py
│   ├── cli.py                 # Interface CLI (Diagnostic, Boot, Verification ISO, Recovery)
│   ├── host_manager/          # Module de diagnostic en lecture seule
│   ├── boot_manager/          # Préparation du démarrage interne & BCD
│   ├── recovery_manager/      # Sauvegarde, vérification et restauration du BCD
│   ├── os_installer/          # Vérification SHA256 ISO & gestionnaire d'installateur
│   └── distro_omarchy/        # Plugin de validation des prérequis Omarchy
└── tests/
    ├── test_host_manager.py   # Suite de tests du diagnostic matériel
    └── test_modules.py        # Suite de tests d'isolation, BCD, ISO SHA256 & boot
```

---

## 🚀 Utilisation & Commandes CLI

### 1. Diagnostic Système (Lecture Seule)
Sous Windows (Invite de commandes / PowerShell administrateur) :
```cmd
python -m bareinstall.cli
```

Sur Linux ou en mode simulation (Mock) :
```bash
python3 -m bareinstall.cli --simulate
```

#### Exporter les Rapports (JSON / Markdown)
```bash
python3 -m bareinstall.cli --simulate --json-out rapport.json --md-out rapport.md
```

### 2. Vérification d'Intégrité de l'ISO Omarchy (SHA256)
```bash
python3 -m bareinstall.cli --verify-iso /chemin/vers/omarchy.iso --expected-sha256 <EMPREINTE_OFFICIELLE_SHA256>
```

### 3. Préparation du Démarrage Interne (Windows / Simulation)
La préparation du démarrage requiert une confirmation explicite (`--confirm`) et une ISO vérifiée :
```cmd
python -m bareinstall.cli --prepare-boot --verify-iso C:\omarchy.iso --expected-sha256 <SHA256> --confirm
```

### 4. Restauration d'Urgence du BCD Windows
En cas de besoin de restauration du chargeur de démarrage d'origine :
```cmd
python -m bareinstall.cli --restore-bcd --confirm
```

---

## 🧪 Exécution des Tests Automatisés

```bash
PYTHONPATH=. pytest
```

---

## 📚 Documentation Complète
- **Étude de faisabilité :** [docs/FEASIBILITY_STUDY.md](docs/FEASIBILITY_STUDY.md)
- **Architecture logicielle :** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Guide de récupération :** [docs/RECOVERY_GUIDE.md](docs/RECOVERY_GUIDE.md)
- **Matrice de statut :** [docs/STATUS_REPORT.md](docs/STATUS_REPORT.md)
