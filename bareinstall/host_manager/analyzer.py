"""
BareInstall Host Manager Diagnostic Analyzer.
Evaluates system reports against Omarchy official requirements and BareInstall safety thresholds.
Strictly distinguishes official requirements from BareInstall recommendations.
Never assumes unknown status equals compatibility.
"""

from typing import List
from .models import SystemReport, DiagnosticCheck, DiagnosticSummary


class DiagnosticAnalyzer:
    """
    Analyzes SystemReport objects and assesses compatibility for USB-less Omarchy installation.
    """

    # Official / BareInstall Thresholds
    BAREINSTALL_RECOMMENDED_RAM_GB = 3.5  # BareInstall recommendation for target machine (~4GB RAM)
    BAREINSTALL_MIN_FREE_DISK_GB = 15.0   # BareInstall recommendation for ISO staging + dual-boot allocation

    def analyze(self, report: SystemReport) -> DiagnosticSummary:
        checks: List[DiagnosticCheck] = []
        raw_errors: List[str] = list(report.raw_errors) + list(report.security.query_errors)

        # 1. Firmware Check (Official Requirement: UEFI Mandatory)
        if report.firmware.status == "UNKNOWN" or not report.firmware.firmware_type:
            checks.append(DiagnosticCheck(
                check_id="FW_UEFI",
                category="Firmware",
                title="Firmware Indéterminé",
                passed=False,
                severity="BLOCKER",
                source="OFFICIAL_OMARCHY",
                message="Impossible de vérifier si le système est en mode UEFI. Omarchy exige le mode UEFI.",
                details="Le type de firmware n'a pas pu être interrogé par le système."
            ))
        elif report.firmware.is_uefi:
            checks.append(DiagnosticCheck(
                check_id="FW_UEFI",
                category="Firmware",
                title="Firmware UEFI",
                passed=True,
                severity="INFO",
                source="OFFICIAL_OMARCHY",
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
                source="OFFICIAL_OMARCHY",
                message="Le système est en mode Legacy BIOS. Omarchy et l'amorçage sans clé USB exigent le mode UEFI.",
                details=f"Type détecté : {report.firmware.firmware_type}"
            ))

        # 2. CPU Architecture Check (Official Requirement: x86_64)
        arch = report.cpu.architecture.lower()
        if not arch or arch == "unknown":
            checks.append(DiagnosticCheck(
                check_id="CPU_ARCH",
                category="Processeur",
                title="Architecture CPU Indéterminée",
                passed=False,
                severity="BLOCKER",
                source="OFFICIAL_OMARCHY",
                message="Impossible de déterminer l'architecture du processeur. Omarchy nécessite un processeur 64 bits (x86_64).",
                details=None
            ))
        elif "64" in arch or "amd64" in arch or "x86_64" in arch:
            checks.append(DiagnosticCheck(
                check_id="CPU_ARCH",
                category="Processeur",
                title="Architecture 64 bits (x86_64)",
                passed=True,
                severity="INFO",
                source="OFFICIAL_OMARCHY",
                message="Le processeur supporte l'architecture 64 bits requise par Omarchy.",
                details=f"Processeur : {report.cpu.model}"
            ))
        else:
            checks.append(DiagnosticCheck(
                check_id="CPU_ARCH",
                category="Processeur",
                title="Architecture 64 bits requise",
                passed=False,
                severity="BLOCKER",
                source="OFFICIAL_OMARCHY",
                message="Architecture processeur incompatible avec Omarchy (x86_64 requis).",
                details=f"Architecture détectée : {report.cpu.architecture}"
            ))

        # 3. Partition Style Check (GPT vs MBR)
        system_disk = None
        for d in report.disks:
            for p in d.partitions:
                if p.is_system or p.drive_letter.upper() == "C:":
                    system_disk = d
                    break
            if system_disk:
                break

        if not report.disks:
            checks.append(DiagnosticCheck(
                check_id="DISKS_DETECTED",
                category="Stockage",
                title="Aucun Disque Détecté",
                passed=False,
                severity="BLOCKER",
                source="SYSTEM_SAFETY",
                message="Aucun disque physique ou logique n'a pu être identifié par le système.",
                details="Vérifiez les autorisations administratives ou les pilotes de stockage."
            ))
        elif system_disk:
            part_style = system_disk.partition_style.upper()
            if part_style == "GPT":
                checks.append(DiagnosticCheck(
                    check_id="PART_GPT",
                    category="Partitionnement",
                    title="Table de partition GPT",
                    passed=True,
                    severity="INFO",
                    source="SYSTEM_SAFETY",
                    message="Le disque système utilise une table de partition GPT.",
                    details=f"Disque ID: {system_disk.device_id}, Modèle: {system_disk.model}"
                ))
            elif part_style == "MBR":
                checks.append(DiagnosticCheck(
                    check_id="PART_GPT",
                    category="Partitionnement",
                    title="Table de partition GPT requise",
                    passed=False,
                    severity="BLOCKER",
                    source="SYSTEM_SAFETY",
                    message="Le disque système utilise MBR au lieu de GPT.",
                    details="L'amorçage EFI moderne de BareInstall nécessite une table GPT."
                ))
            else:
                checks.append(DiagnosticCheck(
                    check_id="PART_GPT",
                    category="Partitionnement",
                    title="Style de partition inconnu",
                    passed=False,
                    severity="BLOCKER",
                    source="SYSTEM_SAFETY",
                    message="Impossible de déterminer si le disque utilise GPT ou MBR.",
                    details=f"Style détecté : {system_disk.partition_style}"
                ))
        else:
            checks.append(DiagnosticCheck(
                check_id="SYS_DISK",
                category="Stockage",
                title="Disque système C: non identifié",
                passed=False,
                severity="WARNING",
                source="SYSTEM_SAFETY",
                message="Impossible d'identifier la partition système C: sur les disques détectés.",
                details=None
            ))

        # 4. BitLocker Check (Official Requirement: Must be turned off)
        if not report.security.bitlocker_status:
            if report.security.query_errors:
                checks.append(DiagnosticCheck(
                    check_id="SEC_BITLOCKER",
                    category="Sécurité",
                    title="Statut BitLocker Indéterminé",
                    passed=False,
                    severity="BLOCKER",
                    source="OFFICIAL_OMARCHY",
                    message="Impossible d'interroger le statut de BitLocker. Omarchy exige l'extinction de BitLocker.",
                    details="Par sécurité, la préparation du démarrage est bloquée tant que le statut de BitLocker est inconnu."
                ))
            else:
                checks.append(DiagnosticCheck(
                    check_id="SEC_BITLOCKER",
                    category="Sécurité",
                    title="Chiffrement BitLocker Inactif",
                    passed=True,
                    severity="INFO",
                    source="OFFICIAL_OMARCHY",
                    message="Aucun volume chiffré BitLocker n'a été détecté sur le système.",
                    details=None
                ))
        else:
            bitlocker_active = False
            for drive, status in report.security.bitlocker_status.items():
                if any(k in status for k in ["Encrypted", "On", "Locked", "Encrypting"]):
                    bitlocker_active = True
                    checks.append(DiagnosticCheck(
                        check_id="SEC_BITLOCKER",
                        category="Sécurité",
                        title="Chiffrement BitLocker Actif",
                        passed=False,
                        severity="BLOCKER",
                        source="OFFICIAL_OMARCHY",
                        message=f"BitLocker est actif sur la partition {drive}. Omarchy exige que BitLocker soit désactivé.",
                        details=f"Statut : {status}. Désactiver BitLocker dans le panneau de configuration Windows."
                    ))
            if not bitlocker_active:
                checks.append(DiagnosticCheck(
                    check_id="SEC_BITLOCKER",
                    category="Sécurité",
                    title="Chiffrement BitLocker Inactif",
                    passed=True,
                    severity="INFO",
                    source="OFFICIAL_OMARCHY",
                    message="BitLocker est présent mais inactif/déverrouillé sur les volumes.",
                    details=None
                ))

        # 5. Secure Boot Check (Official Requirement: Must be disabled in BIOS)
        if report.security.secure_boot_enabled is True:
            checks.append(DiagnosticCheck(
                check_id="SEC_BOOT",
                category="Sécurité",
                title="Secure Boot Activé",
                passed=False,
                severity="BLOCKER",
                source="OFFICIAL_OMARCHY",
                message="Secure Boot est activé. La documentation officielle d'Omarchy exige de désactiver Secure Boot et/or TPM dans le BIOS.",
                details="Redémarrer dans le BIOS UEFI et désactiver Secure Boot avant de poursuivre."
            ))
        elif report.security.secure_boot_enabled is False:
            checks.append(DiagnosticCheck(
                check_id="SEC_BOOT",
                category="Sécurité",
                title="Secure Boot Désactivé",
                passed=True,
                severity="INFO",
                source="OFFICIAL_OMARCHY",
                message="Secure Boot est désactivé conformément à la documentation officielle d'Omarchy.",
                details=None
            ))
        else:
            checks.append(DiagnosticCheck(
                check_id="SEC_BOOT",
                category="Sécurité",
                title="Statut Secure Boot Indéterminé",
                passed=False,
                severity="WARNING",
                source="OFFICIAL_OMARCHY",
                message="Impossible de vérifier l'état de Secure Boot. Assurez-vous qu'il est désactivé dans le BIOS.",
                details=None
            ))

        # 6. Memory Check (BareInstall Recommendation for 4GB target machine)
        if report.memory.status != "OK" or report.memory.total_ram_gb <= 0:
            checks.append(DiagnosticCheck(
                check_id="MEM_RAM",
                category="Mémoire",
                title="Mémoire RAM Indéterminée",
                passed=False,
                severity="WARNING",
                source="BAREINSTALL_RECOMMENDATION",
                message="Impossible de vérifier la quantité de mémoire RAM du système.",
                details=None
            ))
        elif report.memory.total_ram_gb >= self.BAREINSTALL_RECOMMENDED_RAM_GB:
            checks.append(DiagnosticCheck(
                check_id="MEM_RAM",
                category="Mémoire",
                title="Mémoire RAM (>= 3.5 Go)",
                passed=True,
                severity="INFO",
                source="BAREINSTALL_RECOMMENDATION",
                message=f"RAM totale : {report.memory.total_ram_gb} Go (Disponible: {report.memory.available_ram_gb} Go).",
                details="Recommandation BareInstall : Ne pas utiliser l'option 'toram' au boot sur une machine de 4 Go."
            ))
        else:
            checks.append(DiagnosticCheck(
                check_id="MEM_RAM",
                category="Mémoire",
                title="RAM faible (< 3.5 Go)",
                passed=False,
                severity="WARNING",
                source="BAREINSTALL_RECOMMENDATION",
                message=f"RAM détectée ({report.memory.total_ram_gb} Go). Omarchy Hyprland/Wayland peut présenter de la latence.",
                details=f"RAM disponible : {report.memory.available_ram_gb} Go."
            ))

        # 7. Free Disk Space Check (BareInstall Recommendation for ISO Staging + Free space)
        free_space_c = 0.0
        if system_disk:
            for p in system_disk.partitions:
                if p.is_system or p.drive_letter.upper() == "C:":
                    free_space_c = p.free_gb
                    break

        if free_space_c >= self.BAREINSTALL_MIN_FREE_DISK_GB:
            checks.append(DiagnosticCheck(
                check_id="DISK_FREE",
                category="Stockage",
                title="Espace disque disponible",
                passed=True,
                severity="INFO",
                source="BAREINSTALL_RECOMMENDATION",
                message=f"Espace libre sur C: : {free_space_c} Go (Seuil recommandé : {self.BAREINSTALL_MIN_FREE_DISK_GB} Go).",
                details="Espace suffisant pour la préparation de l'image ISO d'Omarchy et l'espace libre dual-boot."
            ))
        else:
            checks.append(DiagnosticCheck(
                check_id="DISK_FREE",
                category="Stockage",
                title="Espace disque restreint",
                passed=False,
                severity="WARNING",
                source="BAREINSTALL_RECOMMENDATION",
                message=f"Espace libre sur C: ({free_space_c} Go) inférieur à {self.BAREINSTALL_MIN_FREE_DISK_GB} Go.",
                details="Un espace insuffisant risque de bloquer la décompression de l'ISO d'Omarchy."
            ))

        # 8. Fast Startup Check
        if report.security.fast_startup_enabled:
            checks.append(DiagnosticCheck(
                check_id="FAST_STARTUP",
                category="Système",
                title="Démarrage rapide (Fast Startup) activé",
                passed=False,
                severity="WARNING",
                source="BAREINSTALL_RECOMMENDATION",
                message="Le démarrage rapide Windows est activé. Il laisse la partition NTFS dans un état verrouillé.",
                details="Recommandation : Désactiver Fast Startup dans les options d'alimentation de Windows."
            ))

        blockers = [c for c in checks if c.severity == "BLOCKER" and not c.passed]
        warnings = [c for c in checks if c.severity == "WARNING" or (not c.passed and c.severity != "BLOCKER")]
        passed = [c for c in checks if c.passed and c.severity == "INFO"]

        can_proceed = (len(blockers) == 0)

        return DiagnosticSummary(
            can_proceed=can_proceed,
            blockers=blockers,
            warnings=warnings,
            passed_checks=passed,
            raw_errors=raw_errors,
            system_report=report
        )
