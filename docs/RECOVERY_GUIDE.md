# BareInstall - Guide de Récupération & Sécurité Démarrage

**Projet :** BareInstall
**Auteur :** Équipe BareInstall
**Version :** 0.2.0

---

## 1. Principe de Sécurité & Non-Destruction

BareInstall est conçu pour garantir qu'aucune opération irréversible ne se produise sans la confirmation explicite de l'utilisateur. En cas de dysfonctionnement lors de la préparation du démarrage ou de la modification de la configuration UEFI/BCD, ce guide fournit l'ensemble des procédures de diagnostic et de restauration.

---

## 2. Sauvegarde Automatique du BCD Windows

Avant toute modification de la configuration de démarrage sous Windows, BareInstall exécute automatiquement la commande de sauvegarde du Magasin de Données de Configuration de Démarrage (BCD) :

```cmd
bcdedit /export C:\BareInstall_BCD_Backup.bcd
```

Ce fichier de sauvegarde permet de restaurer l'état exact du BCD Windows à tout moment.

---

## 3. Restauration Manuelle du BCD Windows (Sans Second Ordinateur)

### Scénario A : Windows démarre normalement
Si vous pouvez accéder à votre session Windows 10/11 :

1. Ouvrez l'invite de commandes (cmd.exe) ou PowerShell **en tant qu'administrateur**.
2. Exécutez la commande de restauration de BareInstall :
   ```cmd
   python -m bareinstall.cli --restore-bcd
   ```
   ou directement via la commande Windows native :
   ```cmd
   bcdedit /import C:\BareInstall_BCD_Backup.bcd
   ```
3. Redémarrez le système.

### Scénario B : Windows ne démarre pas directement (Accès aux options de récupération WinRE)
Si le PC redémarre en boucle ou affiche un écran d'erreur au démarrage :

1. Laissez Windows tenter de démarrer deux fois d'affilée pour déclencher l'écran automatique **Environnement de récupération Windows (WinRE)**.
2. Naviguez dans : **Dépannage** > **Options avancées** > **Invite de commandes**.
3. Dans l'invite de commandes WinRE, identifiez la lettre du lecteur Windows (généralement `C:` ou `D:`) :
   ```cmd
   dir C:\BareInstall_BCD_Backup.bcd
   ```
4. Restaurez la sauvegarde BCD :
   ```cmd
   bcdedit /import C:\BareInstall_BCD_Backup.bcd
   ```
5. Redémarrez le PC.

---

## 4. Nettoyage de la Partition de Staging

Si une partition ou un dossier de staging `C:\BareInstall_Staging` a été créé pour héberger les fichiers d'installation :

1. Supprimez l'entrée de boot BareInstall dans le BCD :
   ```cmd
   bcdedit /delete {GUID_BAREINSTALL} /f
   ```
2. Supprimez le dossier de staging :
   ```cmd
   rmdir /s /q C:\BareInstall_Staging
   ```

---

## 5. Précautions BitLocker & Clé de Récupération

- Si BitLocker était activé avant l'utilisation de BareInstall, assurez-vous de disposer de la **clé de récupération à 48 chiffres** (disponible sur votre compte Microsoft à l'adresse https://account.microsoft.com/devices/recoverykey).
- Ne tentez jamais de réorganiser les partitions avec BitLocker actif sans l'avoir au préalable désactivé ou suspendu.
