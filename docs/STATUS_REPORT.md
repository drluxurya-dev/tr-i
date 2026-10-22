# BareInstall - Rapport d'Avancement et Matrice de Statut

**Projet :** BareInstall
**Auteur :** Équipe BareInstall
**Date de révision :** 22 Octobre 2026 (Version 0.3.0)

---

## 1. Matrice des Fonctionnalités Implémentées, Simulées et Limites

| Module | Fonctionnalité | Statut Réel | Mode Simulation / Cloud |
| :--- | :--- | :--- | :--- |
| **`host-manager`** | Collecte matérielle Windows (PowerShell/WMI/Get-Disk) | **Opérationnel sur Windows** | Simulable via `MockCollector` |
| **`host-manager`** | Détection Secure Boot, BitLocker & Fast Startup | **Opérationnel sur Windows** | Interrogation sécurisée (sans accès aveugle) |
| **`host-manager`** | Analyseur d'éligibilité Omarchy | **Opérationnel** | Sépare Exigences Officielles & Recommandations |
| **`os-installer`** | Vérification d'intégrité ISO SHA256 (`IsoManager`) | **Opérationnel** | Exige une empreinte SHA256 officielle (Pas de feinte par taille) |
| **`boot-manager`** | Diagnostic préalable & Staging | **Opérationnel** | Création répertoire Staging `C:\BareInstall_Staging` |
| **`boot-manager`** | Modification BCD / Inscription UEFI | **Opérationnel sur Windows Admin** | Inscription BCD exécutée sous Windows avec privilèges |
| **`recovery-manager`**| Export BCD & Restauration sécurisée | **Opérationnel sur Windows Admin** | Validation d'en-tête/taille du fichier avant import BCD |
| **`distro-omarchy`** | Validation des exigences Omarchy | **Opérationnel** | Conforme aux spécifications officielles DHH / Omarchy |

---

## 2. Distinction Claire des Environnements de Test

- **Environnement Sandbox / Cloud (Linux) :** Les fonctions de modification système (BCD, disques, partitions) sont isolées par les drapeaux `simulated=True` et testées avec des Mocks stricts pour garantir l'absence de toute modification du système hôte.
- **Environnement Machine Cible (Windows 10/11) :** Les commandes natives `bcdedit`, PowerShell, WMI et le contrôle d'accès administrateur (`IsUserAnAdmin`) s'exécutent directement.

---

## 3. Matrice des Tests Automatisés (`pytest`)

La suite comprend **19 tests automatisés** :
- **`tests/test_host_manager.py` (9 tests) :**
  - Validation du matériel conforme.
  - Bloqueur BitLocker actif.
  - Bloqueur BIOS Legacy.
  - Bloqueur Secure Boot activé.
  - Avertissement RAM restreinte (< 3.5 Go).
  - Avertissement Espace disque libre restreint (< 15 Go).
  - Bloqueur table MBR.
  - Traitement sécurisé des erreurs d'accès BitLocker (bloquant par précaution).
  - Rendu des rapports Terminal et Markdown.

- **`tests/test_modules.py` (10 tests) :**
  - Test de garantie d'isolation du Mock (aucune écriture réelle sur disque).
  - Test de validation d'intégrité de fichier de sauvegarde BCD (rejet des fichiers < 16KB).
  - Refus de restauration BCD sans confirmation `--confirm`.
  - Refus de préparation du démarrage sans confirmation `--confirm`.
  - Refus de préparation du démarrage avec ISO non vérifiée SHA256.
  - Préparation du démarrage confirmée et ISO vérifiée.
  - ISO introuvable.
  - Empreinte SHA256 absente (déclarée non confirmée).
  - Empreinte SHA256 exacte (déclarée vérifiée).
  - Validation des prérequis du plugin Omarchy.
