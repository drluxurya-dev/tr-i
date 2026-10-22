# BareInstall - Architecture Système & Conception Modulaire

**Projet :** BareInstall
**Auteur :** Équipe BareInstall
**Version :** 0.1.0

---

## 1. Vue d'Ensemble de l'Architecture

BareInstall est conçu comme un framework modulaire d'installation de systèmes d'exploitation sur matériel bare-metal depuis le disque interne, sans nécessiter de support d'installation externe (clé USB).

Le système repose sur 7 modules logiciels interconnectés mais strictement découplés :

```
+-------------------------------------------------------------------+
|                        desktop-client                             |
|       (Interface CLI / GUI Windows pour l'utilisateur)           |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                        host-manager                               |
|   (Diagnostic matériel, UEFI, BitLocker, Partitions, BCD)         |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                       recovery-manager                            |
|       (Sauvegarde BCD, points de restauration, journalisation)    |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                        boot-manager                               |
|   (Création partition staging FAT32, configuration EFI / GRUB)   |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                       linux-runtime                               |
|   (Environnement Linux d'installation éphémère exécuté au reboot) |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                        os-installer                               |
|     (Moteur d'installation modulaire basé sur des plugins)       |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                      distro-omarchy                               |
|        (Plugin spécifique à la distribution Omarchy)              |
+-------------------------------------------------------------------+
```

---

## 2. Rôle et Spécifications des Modules

### 1. `host-manager` (Implémenté en Phase B - Lecture Seule)
- **Rôle :** Inspection approfondie du système hôte.
- **Fonctionnalités :**
  - Détection du type de firmware (UEFI vs BIOS Legacy).
  - Détection du statut de Secure Boot.
  - Détection du chiffrement de disque (BitLocker / Device Encryption).
  - Détection du processeur (architecture, nombre de cœurs).
  - Détection de la mémoire RAM physique totale et disponible.
  - Détection des disques durs/SSD (capacité réelle, type de media NVMe/SATA/eMMC, table de partition GPT/MBR, espace libre).
  - Analyse de l'état de Windows Fast Startup / Hibernation.
- **Sécurité :** Strictement en lecture seule. N'exécute aucune modification système.

### 2. `recovery-manager`
- **Rôle :** Gestion de la sécurité et de la réversibilité.
- **Fonctionnalités :**
  - Export et sauvegarde du magasin BCD Windows initial.
  - Journalisation détaillée des opérations.
  - Procédure de restauration d'urgence en 1 clic/commande.

### 3. `boot-manager`
- **Rôle :** Préparation de l'amorçage depuis le disque interne.
- **Fonctionnalités :**
  - Redimensionnement sécurisé du volume Windows via l'API VDS.
  - Création de la partition staging FAT32.
  - Déploiement des binaires EFI d'amorce (GRUB2 / Shim).
  - Ajout temporaire d'une entrée de démarrage dans le BCD de Windows.

### 4. `linux-runtime`
- **Rôle :** Environnement d'exécution Linux autonome chargé au redémarrage.
- **Fonctionnalités :**
  - Kernel & RAMDisk légers pré-packagés.
  - Montage de la partition d'installation.
  - Exécution du moteur `os-installer`.

### 5. `os-installer`
- **Rôle :** Moteur modulaire orchestrant l'installation de l'OS cible.
- **Fonctionnalités :**
  - Interface de plugin unifiée (`BaseDistroPlugin`).
  - Gestion du partitionnement cible, du formatage et du chroot.

### 6. `distro-omarchy`
- **Rôle :** Plugin spécifique pour l'installation d'Omarchy.
- **Fonctionnalités :**
  - Validation des prérequis d'Omarchy (x86_64, >=4Go RAM, >=20Go Disque libre, UEFI).
  - Exécution du script/processus d'installation d'Omarchy.

### 7. `desktop-client`
- **Rôle :** Interface utilisateur finale.
- **Fonctionnalités :**
  - Propose un mode CLI avec rapports structurés (Terminal, JSON, Markdown).
  - Présentation claire des avertissements de sécurité et des bloquants.
