# BareInstall - Étude de Faisabilité Technique & Analyse des Risques

**Projet :** BareInstall
**Auteur :** Équipe BareInstall
**Date de révision :** Octobre 2026
**Cible :** Démarrage et installation d'Omarchy (et autres distributions Linux) depuis le disque interne sans support externe (clé USB) sous Windows 10/11.

---

## 1. Contexte & Défi Technique

L'installation classique d'un système Linux nécessite l'utilisation d'une clé USB d'installation (Live USB). Dans le cas où **aucune clé USB ni support externe n'est disponible**, l'environnement d'installation doit être préparé, stocké et amorcé directement depuis le **disque interne** de la machine cible hôte (Windows 10/11).

### Caractéristiques de la machine cible
- **OS Initial :** Windows 10 / 11 64-bit
- **Processeur :** Intel Pentium Silver (x86_64)
- **RAM :** 4 Go
- **Disque interne :** ~789 Go (détection dynamique nécessaire : eMMC, NVMe, SATA SSD ou HDD)
- **Firmware :** UEFI (Secure Boot potentiellement activé)

---

## 2. Analyse des Méthodes de Démarrage depuis le Disque Interne

Plusieurs méthodes permettent d'amorcer un environnement Linux depuis un disque dur interne hébergeant Windows :

### Méthode A : Partition de Staging FAT32 + GRUB2 EFI (Recommandée)
- **Principe :** Réduire la partition Windows C: (via VDS / `diskpart`), créer une petite partition FAT32 (~4-8 Go) nommée `BAREINSTALL_STAGING`. Y extraire le noyau Linux (`vmlinuz`), l'image initiale (`initramfs.img`) et le système de fichiers (`filesystem.squashfs`) de l'ISO Omarchy / Arch.
- **Inscripter l'entrée UEFI :** Ajouter une entrée dans le magasin BCD de Windows (`bcdedit`) ou directement dans le gestionnaire NVRAM UEFI (`efibootmgr` / BCD) pointant vers un binaire EFI bootloader (`grubx64.efi` ou `systemd-boot`).
- **Avantages :**
  - Ne dépend pas de la lecture NTFS sous UEFI.
  - Compatible avec la plupart des firmwares UEFI.
  - La partition est isolée et réutilisable.
- **Inconvénients / Obstacles :**
  - Nécessite de pouvoir réduire la partition C: sans corrompre les données.
  - Nécessite la gestion des signatures Secure Boot.

### Méthode B : Amorçage Loopback ISO depuis NTFS via GRUB2 EFI
- **Principe :** Placer le fichier ISO d'Omarchy directement sur la partition C: (NTFS) et configurer un bootloader UEFI (GRUB2 compilé avec support NTFS) pour charger le fichier ISO via le module `loopback`.
- **Avantages :** Aucune repartitionnement préalable n'est nécessaire.
- **Inconvénients / Obstacles :**
  - Le pilote NTFS du firmware UEFI ou de GRUB2 est parfois instable ou indisponible sur certains firmwares.
  - Si BitLocker est activé sur C:, le bootloader ne pourra pas lire le fichier ISO depuis NTFS au démarrage.

### Méthode C : WinPE / WIM Modification (Déconseillée)
- **Principe :** Remplacer l'environnement de récupération Windows (WinRE) par un environnement Linux ou WinPE personnalisé.
- **Inconvénients :** Risque très élevé de rendre la récupération de Windows inutilisable.

---

## 3. Obstacles Techniques Majeurs et Scénarios d'Échec

| Obstacle | Impact | Solution / Stratégie BareInstall |
| :--- | :--- | :--- |
| **Secure Boot activé** | Le firmware UEFI refuse de charger un binaire EFI non signé par Microsoft (ex: GRUB2 non signé). | Détecter l'état de Secure Boot. Utiliser Shim signé par la clé "Microsoft Corporation UEFI CA" ou guider l'utilisateur pour désactiver Secure Boot dans le BIOS. |
| **Chiffrement BitLocker / Device Encryption** | Le disque C: est chiffré. Linux ne peut pas être amorcé ni lire les données sans la clé de récupération à 48 chiffres. | **Avertissement bloquant.** BareInstall détecte BitLocker et exige la suspension du chiffrement ou la sauvegarde de la clé avant toute opération de repartitionnement. |
| **Démarrage rapide (Fast Startup) & Hibernation** | Windows laisse les partitions NTFS dans un état "incomplet/dirty", empêchant le montage en écriture sous Linux. | Détecter si Fast Startup est activé (`HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Session Manager\Power`) et recommander sa désactivation. |
| **Contrainte RAM (4 Go)** | Charger l'intégralité de l'ISO en mémoire RAM (`toram`) échouera par manque de mémoire (OOM) car l'ISO fait ~2-3 Go et la RAM totale est de 4 Go. | Booter en montant le système de fichiers `squashfs` directement depuis le disque (`img_loop=` ou mount point de la partition staging FAT32) plutôt que de copier l'ISO en RAM. |
| **Firmware BIOS Legacy (Non-UEFI)** | Incompatible avec les méthodes d'amorçage EFI modernes requises par Omarchy. | Détecter le mode de firmware via `bcdedit` / `Get-FirmwareType`. Exiger un environnement UEFI. |

---

## 4. Analyse Spécifique d'Omarchy

- **Distribution de base :** Omarchy (projet officiel : https://omarchy.org / https://github.com/basecamp/omarchy).
- **Architecture requise :** x86_64.
- **Prérequis officiels Omarchy :**
  - Processeur x86_64.
  - RAM : 4 Go recommandé au minimum pour faire tourner l'environnement de bureau moderne (Hyprland / Wayland stack).
  - Espace disque : 20 Go d'espace libre recommandé.
  - Firmware : UEFI obligatoire.
- **Faisabilité sur Intel Pentium Silver / 4 Go RAM / 789 Go Disque :**
  - **Processeur Intel Pentium Silver :** Architecture 64 bits compatible x86_64.
  - **RAM 4 Go :** Suffisante pour le fonctionnement basique d'Omarchy et l'installateur, mais nécessite d'éviter l'option `toram` lors du boot du live installer.
  - **Disque 789 Go :** Espace amplement suffisant pour héberger Windows et Omarchy en dual-boot ou pour une réinstallation complète.

---

## 5. Recommandations & Conclusion de Faisabilité

L'installation d'Omarchy sans clé USB sur la machine cible est **techniquement faisable**, sous réserve de respecter strictement la séquence sécurisée suivante :

1. **Phase de Diagnostic (Lecture Seule) :** Vérifier UEFI, Secure Boot, BitLocker, Fast Startup, la RAM (4 Go) et l'espace disque disponible.
2. **Préparation Staging :** Créer une partition FAT32 dédiée de 4 Go sur le disque interne si BitLocker est désactivé et l'espace suffisant.
3. **Configuration du Bootloader :** Déployer GRUB2/Shim dans l'ESP ou la partition staging et ajouter l'entrée dans le BCD de Windows.
4. **Validation de Récupération :** Garantir un mécanisme de restauration de la configuration BCD initiale de Windows en cas de problème.
