"""
BareInstall Plugin for Omarchy Linux Distribution.
Follows official Omarchy installation guidelines (dual-boot free space preference).
"""

from typing import Tuple
from bareinstall.os_installer import BaseInstallerPlugin
from bareinstall.host_manager import SystemReport, DiagnosticAnalyzer


class OmarchyPlugin(BaseInstallerPlugin):
    """
    Plugin integrating official Omarchy installer prerequisites.
    """

    def name(self) -> str:
        return "Omarchy Linux"

    def validate_requirements(self, report: SystemReport) -> Tuple[bool, str]:
        """
        Validates official Omarchy installation conditions:
        - UEFI Firmware
        - BitLocker Disabled
        - Secure Boot Disabled
        - x86_64 CPU Architecture
        """
        analyzer = DiagnosticAnalyzer()
        summary = analyzer.analyze(report)

        if not summary.can_proceed:
            blockers = [f"- {b.title}: {b.message}" for b in summary.blockers]
            return False, "Conditions d'installation Omarchy non satisfaites :\n" + "\n".join(blockers)

        return True, "Ensemble des conditions requises pour Omarchy satisfaites (UEFI, BitLocker désactivé, Secure Boot désactivé, x86_64)."
