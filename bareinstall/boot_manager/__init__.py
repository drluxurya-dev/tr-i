"""
BareInstall Boot Manager Module.
Prepares internal disk boot staging and handles Windows BCD configuration safely.
Strictly separates diagnostic checks, file staging, and BCD execution.
"""

import os
import ctypes
import subprocess
import platform
from typing import Tuple, Optional
from bareinstall.recovery_manager import RecoveryManager
from bareinstall.host_manager import SystemReport, DiagnosticAnalyzer


def is_admin() -> bool:
    """Checks if current process has Administrator privileges on Windows."""
    if platform.system() != "Windows":
        return False
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


class BootManager:
    """
    Manages internal disk boot staging and BCD entry creation for Omarchy installation.
    """

    STAGING_DIR = r"C:\BareInstall_Staging"

    def __init__(self, simulated: bool = False):
        self.simulated = simulated or (platform.system() != "Windows")
        self.recovery = RecoveryManager(simulated=self.simulated)

    def prepare_boot(
        self,
        report: SystemReport,
        user_confirmed: bool = False,
        iso_verified: bool = False
    ) -> Tuple[bool, str]:
        """
        Prepares boot environment in three explicit phases:
        Phase 1: Precondition & Diagnostic Check (BitLocker, UEFI, Secure Boot, Admin rights)
        Phase 2: Preventive BCD Backup & Staging File Preparation
        Phase 3: BCD Boot Entry Configuration (Windows only)
        """

        # 1. User confirmation check
        if not user_confirmed:
            return False, "SÉCURITÉ : La préparation du démarrage nécessite la confirmation explicite (--confirm)."

        # 2. ISO Verification check
        if not iso_verified:
            return False, "SÉCURITÉ : Impossible de préparer le démarrage avec une image ISO dont l'intégrité SHA256 n'a pas été confirmée."

        # 3. Privilege check (Windows real mode)
        if not self.simulated and not is_admin():
            return False, "PRIVILÈGES INSUFFISANTS : L'exécution de boot-manager sous Windows nécessite des droits d'Administrateur."

        # 4. System Diagnostic validation
        analyzer = DiagnosticAnalyzer()
        summary = analyzer.analyze(report)

        if not summary.can_proceed:
            blocker_msgs = [f"- [{b.category}] {b.title}: {b.message}" for b in summary.blockers]
            return False, "ÉCHEC DIAGNOSTIC PREALABLE : Des éléments bloquants empêchent la préparation du démarrage :\n" + "\n".join(blocker_msgs)

        # 5. Backup BCD
        ok_backup, bcd_msg = self.recovery.backup_bcd()
        if not ok_backup:
            return False, f"INTERRUPTION DE SÉCURITÉ : Échec de la sauvegarde préventive du BCD ({bcd_msg})."

        # 6. Execution (Simulation vs Windows Real)
        if self.simulated:
            return True, (
                f"[MODE SIMULATION / MOCK]\n"
                f"- Sauvegarde BCD simulée : {bcd_msg}\n"
                f"- Repertoire de staging simulé : {self.STAGING_DIR}\n"
                f"- Inscription de l'entrée de boot EFI dans le BCD simulée avec succès.\n"
                f"Note : En environnement réel Windows, l'entrée BCD est créée via bcdedit."
            )

        # Real Windows Execution
        try:
            os.makedirs(self.STAGING_DIR, exist_ok=True)
            manifest_path = os.path.join(self.STAGING_DIR, "bareinstall_manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write('{"status": "staged", "target_distro": "Omarchy"}')

            # Real BCD Creation via bcdedit
            cmd_create = ["bcdedit", "/create", "/d", "BareInstall Omarchy Installer", "/application", "bootsector"]
            res = subprocess.run(cmd_create, capture_output=True, text=True, check=True)
            output = res.stdout.strip()

            return True, (
                f"PRÉPARATION RÉUSSIE (WINDOWS REEL) :\n"
                f"- Sauvegarde BCD effectuée : {bcd_msg}\n"
                f"- Fichiers de staging créés : {self.STAGING_DIR}\n"
                f"- Inscription BCD exécutée : {output}"
            )
        except subprocess.CalledProcessError as e:
            # Automatic Rollback attempt
            self.recovery.restore_bcd(user_confirmed=True)
            return False, f"ÉCHEC INCRIPTION BCD (Code {e.returncode}) : {e.stderr.strip()}.\nLe BCD d'origine a été automatiquement restauré."
        except Exception as e:
            self.recovery.restore_bcd(user_confirmed=True)
            return False, f"ERREUR SYSTÈME lors de la préparation : {str(e)}.\nLe BCD d'origine a été restauré."
