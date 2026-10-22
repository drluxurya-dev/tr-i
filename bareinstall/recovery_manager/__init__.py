"""
BareInstall Recovery Manager Module.
Provides BCD backup verification, safe restoration, emergency rollback, and diagnostic logs.
"""

import os
import ctypes
import subprocess
import platform
import shutil
from typing import Tuple, Optional


def is_admin() -> bool:
    """Checks if current process has Administrator privileges on Windows."""
    if platform.system() != "Windows":
        return False
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


class RecoveryManager:
    """
    Manages BCD backups, BCD restorations, and safety rollbacks.
    Validates backup existence, size, readability, and admin rights before restoring.
    """

    DEFAULT_BACKUP_PATH = r"C:\BareInstall_BCD_Backup.bcd"
    MIN_BCD_SIZE_BYTES = 16384  # A valid BCD backup file is at least 16KB

    def __init__(self, backup_path: Optional[str] = None, simulated: Optional[bool] = None):
        self.backup_path = backup_path or self.DEFAULT_BACKUP_PATH
        if simulated is None:
            self.simulated = (platform.system() != "Windows")
        else:
            self.simulated = simulated

    def backup_bcd(self) -> Tuple[bool, str]:
        """Export Windows BCD to backup file."""
        if self.simulated:
            return True, f"[MOCK] BCD exporté avec succès vers {self.backup_path}"

        if not is_admin() and platform.system() == "Windows":
            return False, "PRIVILÈGES INSUFFISANTS : L'export BCD sous Windows nécessite des droits d'Administrateur."

        try:
            cmd = ["bcdedit", "/export", self.backup_path]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if not os.path.exists(self.backup_path):
                return False, f"ÉCHEC VERIFICATION : Le fichier BCD exporté est introuvable à l'emplacement {self.backup_path}"

            size = os.path.getsize(self.backup_path)
            if size < self.MIN_BCD_SIZE_BYTES:
                return False, f"ÉCHEC VERIFICATION : Le fichier BCD exporté est corrompu ou incomplet (Taille: {size} octets)."

            return True, f"Sauvegarde BCD réussie ({size} octets) : {self.backup_path}"
        except subprocess.CalledProcessError as e:
            return False, f"Échec de l'export BCD (Exit {e.returncode}) : {e.stderr.strip()}"
        except Exception as e:
            return False, f"Erreur lors de la sauvegarde BCD : {str(e)}"

    def verify_backup_file(self) -> Tuple[bool, str]:
        """Validates that a BCD backup file exists, is readable, and appears valid."""
        if self.simulated:
            return True, f"[MOCK] Fichier de sauvegarde BCD valide : {self.backup_path}"

        if not os.path.exists(self.backup_path):
            return False, f"SAUVEGARDE INTROUVABLE : Aucun fichier de sauvegarde BCD à l'emplacement {self.backup_path}"

        if not os.path.isfile(self.backup_path):
            return False, f"CHEMIN INVALIDE : {self.backup_path} n'est pas un fichier."

        try:
            size = os.path.getsize(self.backup_path)
            if size < self.MIN_BCD_SIZE_BYTES:
                return False, f"SAUVEGARDE CORROMPUE : La taille du fichier BCD ({size} octets) est inférieure au minimum requis ({self.MIN_BCD_SIZE_BYTES} octets)."

            with open(self.backup_path, "rb") as f:
                header = f.read(16)
                if not header:
                    return False, "SAUVEGARDE CORROMPUE : Impossible de lire l'en-tête du fichier BCD."

            return True, f"Fichier de sauvegarde BCD vérifié ({size} octets, lisible)."
        except PermissionError:
            return False, f"ACCÈS REFUSÉ : Droits insuffisants pour lire {self.backup_path}"
        except Exception as e:
            return False, f"ERREUR LECTURE SAUVEGARDE : {str(e)}"

    def restore_bcd(self, user_confirmed: bool = False) -> Tuple[bool, str]:
        """
        Imports Windows BCD from backup file.
        Requires explicit user confirmation (--confirm) and admin rights on real Windows.
        """
        if self.simulated:
            return True, f"[MOCK] BCD restauré avec succès depuis {self.backup_path}"

        if not user_confirmed:
            return False, "CONFIRMATION REQUISE : La restauration du BCD modifie le démarrage Windows et exige --confirm."

        if not is_admin() and platform.system() == "Windows":
            return False, "PRIVILÈGES INSUFFISANTS : La restauration BCD sous Windows nécessite des droits d'Administrateur."

        ok_ver, msg_ver = self.verify_backup_file()
        if not ok_ver:
            return False, f"INTERRUPTION DE SÉCURITÉ : La restauration a été annulée car le fichier de sauvegarde est invalide :\n{msg_ver}"

        try:
            cmd = ["bcdedit", "/import", self.backup_path]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, f"Restauration BCD réussie depuis {self.backup_path}"
        except subprocess.CalledProcessError as e:
            return False, f"Échec de l'import BCD (Exit {e.returncode}) : {e.stderr.strip()}"
        except Exception as e:
            return False, f"Erreur lors de la restauration BCD : {str(e)}"

    def cleanup_staging(self, staging_dir: str = r"C:\BareInstall_Staging", user_confirmed: bool = False) -> Tuple[bool, str]:
        """Clean up staging directory safely."""
        if self.simulated:
            return True, f"[MOCK] Dossier de staging {staging_dir} nettoyé."

        if not user_confirmed:
            return False, "CONFIRMATION REQUISE : La suppression du dossier de staging exige --confirm."

        clean_path = os.path.abspath(staging_dir)
        protected_paths = ["C:\\", "C:\\WINDOWS", "C:\\PROGRAM FILES", "C:\\USERS"]
        if clean_path.upper() in protected_paths:
            return False, f"REFUS DE SÉCURITÉ : Impossible de supprimer un répertoire système critique : {clean_path}"

        try:
            if os.path.exists(clean_path):
                shutil.rmtree(clean_path)
                return True, f"Dossier de staging {clean_path} supprimé avec succès."
            return True, f"Dossier de staging {clean_path} non présent."
        except Exception as e:
            return False, f"Erreur lors de la suppression du staging : {str(e)}"
