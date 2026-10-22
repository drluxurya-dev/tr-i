# BareInstall - Rapport d'Avancement et Matrice de Statut

**Projet :** BareInstall
**Auteur :** Équipe BareInstall
**Date de révision :** 22 Octobre 2026

---

## 1. Matrice des Fonctionnalités Implémentées vs Simulées

| Module | Fonctionnalité | Statut |
| :--- | :--- | :--- |
| **`host-manager`** | Collecte matérielle sous Windows (PowerShell/WMI) | **Opérationnel / Réel** (Windows) |
| **`host-manager`** | Mode simulation matériel (MockCollector) | **Opérationnel** (Linux & Test) |
| **`host-manager`** | Détection Secure Boot & BitLocker | **Opérationnel** |
| **`host-manager`** | Analyseur d'éligibilité Omarchy (Distinction Exigences / Recommandations) | **Opérationnel** |
| **`recovery-manager`** | Export / Restauration BCD (`bcdedit /export` et `/import`) | **Opérationnel** (Windows) & Simulable |
| **`boot-manager`** | Préparation répertoire Staging & Sauvegarde BCD | **Opérationnel** |
| **`os-installer`** | Vérification d'intégrité ISO (SHA256) | **Opérationnel** |
| **`distro-omarchy`** | Validation des prérequis officiels Omarchy | **Opérationnel** |
| **`desktop-client` / CLI** | Rapports Terminal, JSON, Markdown, `--prepare-boot`, `--restore-bcd` | **Opérationnel** |

---

## 2. Tests Exécutés

La suite de tests automatisés `pytest` comprend **15 tests unitaires et d'intégration** :
- `tests/test_host_manager.py` (9 tests) :
  - Hardware conforme
  - Bloqueur BitLocker actif
  - Bloqueur BIOS Legacy
  - Bloqueur Secure Boot activé
  - Avertissement RAM faible
  - Avertissement Espace libre restreint
  - Bloqueur MBR
  - Erreurs d'accès BitLocker (securité bloquante)
  - Rendu des rapports Terminal et Markdown
- `tests/test_modules.py` (6 tests) :
  - Sauvegarde/Restauration BCD (RecoveryManager)
  - Refus de préparation sans confirmation utilisateur
  - Préparation de démarrage confirmée
  - Détection ISO absente et taille suspecte (IsoManager)
  - Validation du plugin Omarchy

---

## 3. Limites Restantes & Directives pour le PC Cible

- **Validation Physique Finale :** Le comportement d'amorçage EFI sur le contrôleur eMMC/NVMe spécifique du Pentium Silver doit être validé lors du redémarrage réel sur le PC cible.
- **Sécurité Dual-Boot :** Conformément à la politique d'Omarchy, l'installation conserve le dual-boot Windows dans l'espace libre non alloué.
