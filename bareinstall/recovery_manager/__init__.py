"""
BareInstall Recovery Manager Module.
Provides BCD backup, restoration, emergency rollback, and diagnostic logs.
"""

import os
import subprocess
import platform
import shutil
from typing import Tuple, Optional


class RecoveryManager:
    """
    Manages BCD backups, BCD restorations, and safety rollbacks.
    """

    DEFAULT_BACKUP_PATH = r"C:\BareInstall_BCD_Backup.bcd"

    def __init__(self, backup_path: Optional[str] = None, simulated: bool = False):
        self.backup_path = backup_path or self.DEFAULT_BACKUP_PATH
        self.simulated = simulated or (platform.system() != "Windows")

    def backup_bcd(self) -> Tuple[bool, str]:
        """Export Windows BCD to backup file."""
        if self.simulated:
            return True, f"[MOCK] BCD exporté avec succès vers {self.backup_path}"

        try:
            cmd = ["bcdedit", "/export", self.backup_path]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, f"Sauvegarde BCD réussie : {self.backup_path}"
        except subprocess.CalledProcessError as e:
            return False, f"Échec de l'export BCD (Exit {e.returncode}) : {e.stderr.strip()}"
        except Exception as e:
            return False, f"Erreur lors de la sauvegarde BCD : {str(e)}"

    def restore_bcd(self) -> Tuple[bool, str]:
        """Import Windows BCD from backup file."""
        if self.simulated:
            return True, f"[MOCK] BCD restauré avec succès depuis {self.backup_path}"

        if not os.path.exists(self.backup_path):
            return False, f"Fichier de sauvegarde introuvable : {self.backup_path}"

        try:
            cmd = ["bcdedit", "/import", self.backup_path]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, f"Restauration BCD réussie depuis {self.backup_path}"
        except subprocess.CalledProcessError as e:
            return False, f"Échec de l'import BCD (Exit {e.returncode}) : {e.stderr.strip()}"
        except Exception as e:
            return False, f"Erreur lors de la restauration BCD : {str(e)}"

    def cleanup_staging(self, staging_dir: str = r"C:\BareInstall_Staging") -> Tuple[bool, str]:
        """Clean up staging directory."""
        if self.simulated:
            return True, f"[MOCK] Dossier de staging {staging_dir} nettoyé."

        try:
            if os.path.exists(staging_dir):
                shutil.rmtree(staging_dir)
                return True, f"Dossier de staging {staging_dir} supprimé avec succès."
            return True, f"Dossier de staging {staging_dir} non présent."
        except Exception as e:
            return False, f"Erreur lors de la suppression du staging : {str(e)}"
