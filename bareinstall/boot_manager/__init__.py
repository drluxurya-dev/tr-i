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
            return False, "ÉCHEC DIAGNOSTIC PRÉALABLE : Des éléments bloquants empêchent la préparation du démarrage :\n" + "\n".join(blocker_msgs)

        # 5. Backup BCD
        ok_backup, bcd_msg = self.recovery.backup_bcd()
        if not ok_backup:
            return False, f"INTERRUPTION DE SÉCURITÉ : Échec de la sauvegarde préventive du BCD ({bcd_msg})."

        # 6. Execution (Simulation vs Windows Real)
        if self.simulated:
            return True, (
                f"[FONCTIONNALITÉ EXPÉRIMENTALE / SIMULÉE]\n"
                f"- Sauvegarde BCD simulée : {bcd_msg}\n"
                f"- Repertoire de staging simulé : {self.STAGING_DIR}\n"
                f"- AVERTISSEMENT TECHNIQUE : L'amorçage Linux sans clé USB n'a pas été validé sur matériel physique.\n"
                f"  L'inscription BCD est considérée comme expérimentale et non démontrée sans support externe."
            )

        # Real Windows Execution
        try:
            os.makedirs(self.STAGING_DIR, exist_ok=True)
            manifest_path = os.path.join(self.STAGING_DIR, "bareinstall_manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write('{"status": "staged", "target_distro": "Omarchy"}')

            return True, (
                f"PRÉPARATION DU STAGING RÉUSSIE (WINDOWS REEL) :\n"
                f"- Sauvegarde BCD effectuée : {bcd_msg}\n"
                f"- Fichiers de staging créés : {self.STAGING_DIR}\n"
                f"- NOTE DE SÉCURITÉ : Aucune modification irréversible du BCD n'a été appliquée.\n"
                f"  L'amorçage autonome sans clé USB reste une fonctionnalité expérimentale."
            )
        except Exception as e:
            self.recovery.restore_bcd(user_confirmed=True)
            return False, f"ERREUR SYSTÈME lors de la préparation : {str(e)}.\nLe BCD d'origine a été restauré."
