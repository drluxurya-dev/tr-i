"""
BareInstall Host Manager Diagnostic Analyzer.
Evaluates system reports against Omarchy and BareInstall installation requirements.
Generates structured diagnostic results (BLOCKER, WARNING, INFO).
"""

from typing import List
from .models import SystemReport, DiagnosticCheck, DiagnosticSummary


class DiagnosticAnalyzer:
    """
    Analyzes SystemReport objects and assesses compatibility for USB-less Omarchy installation.
    """

    MIN_RAM_GB = 3.5          # Official / BareInstall RAM target (~4GB machine)
    MIN_DISK_FREE_GB = 20.0   # Required free disk space for staging + OS installation
    MIN_DISKS = 1

    def analyze(self, report: SystemReport) -> DiagnosticSummary:
        checks: List[DiagnosticCheck] = []

        # 1. Check Firmware (UEFI vs Legacy)
        if report.firmware.is_uefi:
            checks.append(DiagnosticCheck(
                check_id="FW_UEFI",
                category="Firmware",
                title="Firmware UEFI",
                passed=True,
                severity="INFO",
                message="Le système est démarré en mode UEFI.",
                details=f"Firmware détecté : {report.firmware.firmware_type}"
            ))
        else:
            checks.append(DiagnosticCheck(
                check_id="FW_UEFI",
                category="Firmware",
                title="Firmware UEFI Obligatoire",
                passed=False,
                severity="BLOCKER",
                message="Le système est en mode Legacy BIOS. Omarchy et l'amorçage sans clé USB exigent le mode UEFI.",
                details=f"Type détecté : {report.firmware.firmware_type}"
            ))

        # 2. Check Partition Style (GPT vs MBR)
        system_disk = None
        for d in report.disks:
            for p in d.partitions:
                if p.is_system or p.drive_letter.upper() == "C:":
                    system_disk = d
                    break
            if system_disk:
                break

        if system_disk:
            if system_disk.partition_style.upper() == "GPT":
                checks.append(DiagnosticCheck(
                    check_id="PART_GPT",
                    category="Partitionnement",
                    title="Table de partition GPT",
                    passed=True,
                    severity="INFO",
                    message="Le disque système utilise une table de partition GPT.",
                    details=f"Disque ID: {system_disk.device_id}, Modèle: {system_disk.model}"
                ))
            else:
                checks.append(DiagnosticCheck(
                    check_id="PART_GPT",
                    category="Partitionnement",
                    title="Table de partition GPT requise",
                    passed=False,
                    severity="BLOCKER",
                    message="Le disque système utilise MBR au lieu de GPT.",
                    details=f"Style de partition détecté : {system_disk.partition_style}"
                ))
        else:
            checks.append(DiagnosticCheck(
                check_id="SYS_DISK",
                category="Stockage",
                title="Disque système C: non identifié",
                passed=False,
                severity="WARNING",
                message="Impossible d'identifier avec certitude le disque système C:.",
                details=None
            ))

        # 3. Check BitLocker Encryption
        bitlocker_active = False
        for drive, status in report.security.bitlocker_status.items():
            if "Encrypted" in status or "On" in status:
                bitlocker_active = True
                checks.append(DiagnosticCheck(
                    check_id="SEC_BITLOCKER",
                    category="Sécurité",
                    title="Chiffrement BitLocker Actif",
                    passed=False,
                    severity="BLOCKER",
                    message=f"BitLocker est actif sur la partition {drive}. Les données et le BCD sont chiffrés.",
                    details=f"Statut : {status}. Désactiver/suspendre BitLocker avant toute modification."
                ))
        if not bitlocker_active:
            checks.append(DiagnosticCheck(
                check_id="SEC_BITLOCKER",
                category="Sécurité",
                title="Chiffrement BitLocker Inactif",
                passed=True,
                severity="INFO",
                message="Aucun chiffrement BitLocker bloquant n'a été détecté sur les disques.",
                details=None
            ))

        # 4. Check Secure Boot
        if report.security.secure_boot_enabled is True:
            checks.append(DiagnosticCheck(
                check_id="SEC_BOOT",
                category="Sécurité",
                title="Secure Boot Activé",
                passed=False,
                severity="WARNING",
                message="Secure Boot est activé. Un bootloader signé (Shim/Microsoft CA) sera requis pour le démarrage sans clé USB.",
                details="Il est recommandé de désactiver Secure Boot dans le BIOS UEFI en cas d'échec de signature."
            ))
        elif report.security.secure_boot_enabled is False:
            checks.append(DiagnosticCheck(
                check_id="SEC_BOOT",
                category="Sécurité",
                title="Secure Boot Désactivé",
                passed=True,
                severity="INFO",
                message="Secure Boot est désactivé. L'amorçage de kernels personnalisés ou de GRUB sera facilité.",
                details=None
            ))
        else:
            checks.append(DiagnosticCheck(
                check_id="SEC_BOOT",
                category="Sécurité",
                title="Statut Secure Boot Indéterminé",
                passed=True,
                severity="WARNING",
                message="Impossible d'interroger le statut de Secure Boot (droits insuffisants ou API non supportée).",
                details=None
            ))

        # 5. Check CPU Architecture
        arch = report.cpu.architecture.lower()
        if "64" in arch or "amd64" in arch or "x86_64" in arch:
            checks.append(DiagnosticCheck(
                check_id="CPU_ARCH",
                category="Processeur",
                title="Architecture 64 bits (x86_64)",
                passed=True,
                severity="INFO",
                message="Le processeur supporte l'architecture x86_64 requise par Omarchy.",
                details=f"Processeur : {report.cpu.model}"
            ))
        else:
            checks.append(DiagnosticCheck(
                check_id="CPU_ARCH",
                category="Processeur",
                title="Architecture 64 bits requise",
                passed=False,
                severity="BLOCKER",
                message="Architecture processeur incompatible avec Omarchy (x86_64 requis).",
                details=f"Architecture détectée : {report.cpu.architecture}"
            ))

        # 6. Check Memory (RAM)
        if report.memory.total_ram_gb >= self.MIN_RAM_GB:
            checks.append(DiagnosticCheck(
                check_id="MEM_RAM",
                category="Mémoire",
                title="Mémoire RAM suffisante (>= 4 Go)",
                passed=True,
                severity="INFO",
                message=f"RAM totale : {report.memory.total_ram_gb} Go (Disponible: {report.memory.available_ram_gb} Go).",
                details="Attention : Ne pas utiliser l'option de boot 'toram' lors du chargement de l'image ISO."
            ))
        else:
            checks.append(DiagnosticCheck(
                check_id="MEM_RAM",
                category="Mémoire",
                title="Mémoire RAM insuffisante",
                passed=False,
                severity="BLOCKER",
                message=f"RAM totale détectée ({report.memory.total_ram_gb} Go) inférieure au minimum requis ({self.MIN_RAM_GB} Go).",
                details=f"Disponible : {report.memory.available_ram_gb} Go."
            ))

        # 7. Check Disk Space
        free_space_c = 0.0
        for d in report.disks:
            for p in d.partitions:
                if p.is_system or p.drive_letter.upper() == "C:":
                    free_space_c = p.free_gb
                    break

        if free_space_c >= self.MIN_DISK_FREE_GB:
            checks.append(DiagnosticCheck(
                check_id="DISK_FREE",
                category="Stockage",
                title="Espace disque disponible suffisant",
                passed=True,
                severity="INFO",
                message=f"Espace libre sur C: : {free_space_c} Go (Minimum requis : {self.MIN_DISK_FREE_GB} Go).",
                details="Espace suffisant pour la partition staging FAT32 (4 Go) et l'installation d'Omarchy."
            ))
        else:
            checks.append(DiagnosticCheck(
                check_id="DISK_FREE",
                category="Stockage",
                title="Espace disque libre insuffisant",
                passed=False,
                severity="BLOCKER",
                message=f"Espace libre sur C: ({free_space_c} Go) inférieur à {self.MIN_DISK_FREE_GB} Go.",
                details="Libérer de l'espace disque sous Windows avant de poursuivre."
            ))

        # 8. Fast Startup warning
        if report.security.fast_startup_enabled:
            checks.append(DiagnosticCheck(
                check_id="FAST_STARTUP",
                category="Système",
                title="Démarrage rapide (Fast Startup) activé",
                passed=False,
                severity="WARNING",
                message="Le démarrage rapide Windows est activé. Il peut empêcher l'accès aux partitions depuis Linux.",
                details="Recommandé : Désactiver Fast Startup dans les options d'alimentation de Windows."
            ))

        # Separate checks into categories
        blockers = [c for c in checks if c.severity == "BLOCKER" and not c.passed]
        warnings = [c for c in checks if c.severity == "WARNING" or (not c.passed and c.severity != "BLOCKER")]
        passed = [c for c in checks if c.passed and c.severity == "INFO"]

        can_proceed = (len(blockers) == 0)

        return DiagnosticSummary(
            can_proceed=can_proceed,
            blockers=blockers,
            warnings=warnings,
            passed_checks=passed,
            system_report=report
        )
