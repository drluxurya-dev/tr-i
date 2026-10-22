"""
BareInstall Boot Manager Module.
Prepares internal disk boot entry for Linux installation environment.
Strictly checks prerequisites before applying any changes.
"""

import os
import subprocess
import platform
from typing import Tuple, Optional
from bareinstall.recovery_manager import RecoveryManager
from bareinstall.host_manager import SystemReport, DiagnosticAnalyzer


class BootManager:
    """
    Manages non-USB internal disk boot preparation for Omarchy installation.
    """

    STAGING_DIR = r"C:\BareInstall_Staging"

    def __init__(self, simulated: bool = False):
        self.simulated = simulated or (platform.system() != "Windows")
        self.recovery = RecoveryManager(simulated=self.simulated)

    def prepare_boot(self, report: SystemReport, user_confirmed: bool = False) -> Tuple[bool, str]:
        """
        Validates safety conditions, backs up BCD, and prepares boot staging.
        Refuses to modify system if user_confirmed is False.
        """
        # 1. User confirmation safety check
        if not user_confirmed:
            return False, "SÉCURITÉ : La préparation du démarrage nécessite une confirmation utilisateur explicite."

        # 2. Analyze system report
        analyzer = DiagnosticAnalyzer()
        summary = analyzer.analyze(report)

        if not summary.can_proceed:
            blocker_msgs = [f"- {b.title}: {b.message}" for b in summary.blockers]
            return False, f"Impossible de préparer le démarrage. Des éléments bloquants subsistent :\n" + "\n".join(blocker_msgs)

        # 3. Backup BCD
        ok, bcd_msg = self.recovery.backup_bcd()
        if not ok:
            return False, f"Interruption de sécurité : Échec de la sauvegarde BCD préventive ({bcd_msg})."

        # 4. Prepare Staging
        if self.simulated:
            return True, f"Préparation de démarrage [MOCK] effectuée avec succès.\n- {bcd_msg}\n- Repertoire de staging simulé créé : {self.STAGING_DIR}\n- Entrée de boot UEFI BareInstall configurée."

        try:
            os.makedirs(self.STAGING_DIR, exist_ok=True)
            # Create a README manifest in staging
            manifest_path = os.path.join(self.STAGING_DIR, "bareinstall_manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write('{"status": "prepared", "target_distro": "Omarchy"}')

            return True, f"Préparation réussie. Sauvegarde BCD effectuée ({bcd_msg}) et dossier de staging créé ({self.STAGING_DIR})."
        except Exception as e:
            return False, f"Erreur lors de la création du répertoire de staging : {str(e)}"
