# BareInstall - Étude de Faisabilité Technique & Analyse des Risques

**Projet :** BareInstall
**Auteur :** Équipe BareInstall
**Date de révision :** 22 Octobre 2026 (Mise à jour suite aux règles officielles Omarchy)
**Cible :** Démarrage et installation d'Omarchy depuis le disque interne sans support externe (clé USB) sous Windows 10/11.

---

## 1. Contexte & Défi Technique

L'installation classique d'Omarchy repose sur le téléchargement d'un fichier ISO officiel et son écriture sur une clé USB via des outils comme balenaEtcher ou Caligula. En l'absence de clé USB ou de second ordinateur, l'image ISO d'installation d'Omarchy doit être préparée, stockée et démarrée directement depuis le **disque interne** de la machine hôte sous Windows 10/11.

### Caractéristiques du matériel cible
- **Processeur :** Intel Pentium Silver (x86_64, 64 bits).
- **RAM :** 4 Go de RAM physique.
- **Disque interne :** Capacité réelle détectée dynamiquement (~789 Go).
- **Firmware :** UEFI obligatoire.

---

## 2. Exigences Officielles Omarchy vs Recommandations BareInstall

Afin d'éviter tout flou technique, BareInstall distingue strictement les **exigences officielles publiées par Omarchy** (sources : https://omarchy.org/ et https://omarchy.org/manual/getting-started/) des **recommandations et seuils internes à BareInstall** :

### A. Exigences Officielles Omarchy (Sources Vérifiées le 22/10/2026)
1. **Désactivation de BitLocker :** *"note that you’ll need to turn off BitLocker in Windows first"*. BitLocker doit être impérativement désactivé dans Windows avant tout dual-boot ou repartitionnement.
2. **Désactivation de Secure Boot et/ou TPM :** *"You must turn off Secure Boot and/or TPM in the BIOS. You have to turn these off to be able to install Omarchy. They’re Microsoft security schemes..."*.
3. **Firmware UEFI :** L'installation d'Omarchy requiert un firmware UEFI moderne.
4. **Architecture CPU :** x86_64 (64 bits).
5. **Clavier :** Clavier filaire ou dongle 2.4 GHz requis lors du premier boot (les claviers Bluetooth ne sont pas supportés pour la saisie du mot de passe de chiffrement LUKS au démarrage).

### B. Recommandations & Seuils BareInstall
1. **Espace disque libre recommandation :** Au moins 15 à 20 Go d'espace libre sur la partition Windows C: pour pouvoir extraire l'ISO et créer une partition/espace non alloué pour le dual-boot.
2. **RAM (4 Go) :** Le Pentium Silver disposant de 4 Go de RAM, BareInstall interdit l'utilisation du paramètre de boot `toram` (qui tenterait de charger l'intégralité du filesystem squashfs de l'ISO en RAM) sous peine de provoqu un échec OOM (Out Of Memory).

---

## 3. Analyse des Méthodes de Démarrage Sans Clé USB

### Contrainte Majeure : Limite FAT32 de 4 GiB
Une partition système de préparation formatée en FAT32 possède une **limite stricte de taille de fichier individuel de 4 GiB (4 294 967 295 octets)**. Si le fichier ISO d'Omarchy ou le fichier `filesystem.squashfs` dépasse 4 GiB, il ne peut pas être stocké directement sur une partition FAT32.

### Méthode 1 : Extraction du Contenu ISO sur Partition de Staging FAT32 + GRUB2 EFI (Recommandée)
- **Fonctionnement :**
  1. Extraction des fichiers du noyau (`/arch/boot/x86_64/vmlinuz-linux`), du RAMDisk (`initramfs-linux.img`), et des fichiers squashfs de l'ISO d'Omarchy dans une partition staging dédiée formatée en FAT32 ou NTFS.
  2. Si l'image squashfs est inférieure à 4 GiB, la partition FAT32 convient. Si elle dépasse 4 GiB, l'utilisation d'une partition NTFS avec le pilote GRUB2 NTFS EFI est requise.
  3. Ajout d'une entrée UEFI dans le BCD de Windows via `bcdedit` pointant vers GRUB2 EFI.
- **Avantages :** Méthode fiable, n'altère pas les fichiers système de Windows.
- **Risque :** Un mauvais paramétrage du BCD peut rendre le menu de boot Windows déroutant, mais est réparable via `bcdedit`.

### Méthode 2 : Chargement ISO direct via Loopback GRUB2 EFI depuis NTFS
- **Fonctionnement :** Stockage du fichier `.iso` d'Omarchy directement sur la partition C: (NTFS) et amorçage par GRUB2 via la commande `loopback`.
- **Obstacle :** Si BitLocker est activé ou si Fast Startup n'a pas été désactivé, GRUB2 EFI ne pourra pas lire le fichier ISO sur la partition NTFS.

---

## 4. Stratégie de Sécurité & Non-Destruction

1. **Conservation de Windows par Défaut :** BareInstall privilégie exclusivement l'installation dual-boot dans l'espace libre ou la préparation d'un environnement de staging. **Aucun formatage automatique du disque entier n'est exécuté par défaut.**
2. **Avertissement et Confirmation Explicite :** Toute action modifiant le BCD ou réduisant le volume exige une validation explicite.
3. **Restauration BCD :** Avant toute modification du BCD, BareInstall réalise un export de sauvegarde du magasin BCD initial (`bcdedit /export C:\BareInstall_BCD_Backup.bcd`).
