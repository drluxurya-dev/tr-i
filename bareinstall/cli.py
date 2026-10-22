"""
BareInstall Command Line Interface (CLI).
Provides terminal output, JSON output, Markdown report export, boot preparation, ISO verification, and BCD recovery.
STRICTLY SAFE & READ-ONLY BY DEFAULT.
"""

import sys
import os
import argparse
import json
from dataclasses import asdict
from typing import Optional

from bareinstall.host_manager import get_collector, DiagnosticAnalyzer, DiagnosticSummary, SystemReport
from bareinstall.boot_manager import BootManager
from bareinstall.recovery_manager import RecoveryManager
from bareinstall.os_installer import IsoManager
from bareinstall.distro_omarchy import OmarchyPlugin


def render_terminal_summary(summary: DiagnosticSummary) -> str:
    lines = []
    lines.append("================================================================")
    lines.append("               BAREINSTALL - RAPPORT DE DIAGNOSTIC              ")
    lines.append("================================================================")

    rep = summary.system_report
    if rep:
        sim_suffix = " (MODE SIMULATION / MOCK)" if rep.is_simulated else ""
        lines.append(f"OS : {rep.os_name} {rep.os_version}{sim_suffix}")
        lines.append(f"Firmware : {rep.firmware.firmware_type} (UEFI: {rep.firmware.is_uefi})")
        lines.append(f"Processeur : {rep.cpu.model} ({rep.cpu.architecture}, {rep.cpu.cores} cœurs)")
        lines.append(f"RAM Totale : {rep.memory.total_ram_gb} Go | Disponible : {rep.memory.available_ram_gb} Go")
        lines.append("Disques détectés :")
        for d in rep.disks:
            lines.append(f"  - Disque #{d.device_id}: {d.model} ({d.size_gb} Go, {d.media_type}/{d.bus_type}, {d.partition_style})")
            for p in d.partitions:
                sys_tag = " [Système C:]" if p.is_system else ""
                lines.append(f"      Part {p.drive_letter} {p.filesystem} ({p.free_gb} Go libres / {p.total_gb} Go){sys_tag}")
    lines.append("----------------------------------------------------------------")

    if summary.can_proceed:
        lines.append(" STATUS GLOBAL : COMPATIBLE [✓]")
        lines.append(" La machine respecte l'ensemble des prérequis d'installation.")
    else:
        lines.append(" STATUS GLOBAL : INCOMPATIBLE / BLOQUÉ [✗]")
        lines.append(" Des obstacles critiques empêchent la poursuite des opérations.")

    lines.append("----------------------------------------------------------------")

    if summary.blockers:
        lines.append("\n[!] ÉLÉMENTS BLOQUANTS (BLOCKERS) :")
        for b in summary.blockers:
            lines.append(f"  ❌ [{b.category}] {b.title} ({b.source})")
            lines.append(f"     Message : {b.message}")
            if b.details:
                lines.append(f"     Détails : {b.details}")

    if summary.warnings:
        lines.append("\n[?] AVERTISSEMENTS (WARNINGS) :")
        for w in summary.warnings:
            lines.append(f"  ⚠️ [{w.category}] {w.title} ({w.source})")
            lines.append(f"     Message : {w.message}")
            if w.details:
                lines.append(f"     Détails : {w.details}")

    if summary.passed_checks:
        lines.append("\n[✓] VÉRIFICATIONS CONCLUANTES :")
        for p in summary.passed_checks:
            lines.append(f"  ✓ [{p.category}] {p.title}: {p.message}")

    if summary.raw_errors:
        lines.append("\n[ERR] ERREURS RENCONTRÉES LORS DU DIAGNOSTIC :")
        for err in summary.raw_errors:
            lines.append(f"  • {err}")

    lines.append("================================================================")
    lines.append(" Note : Ce diagnostic par défaut est strictement en LECTURE SEULE.")
    lines.append("================================================================")
    return "\n".join(lines)


def render_markdown_report(summary: DiagnosticSummary) -> str:
    lines = []
    lines.append("# BareInstall - Rapport de Diagnostic Système")
    lines.append("")
    rep = summary.system_report
    if rep:
        sim = " *(Mode Simulation / Mock)*" if rep.is_simulated else ""
        lines.append(f"**Système d'exploitation :** {rep.os_name} {rep.os_version}{sim}")
        lines.append(f"- **Firmware :** {rep.firmware.firmware_type}")
        lines.append(f"- **Processeur :** {rep.cpu.model} ({rep.cpu.architecture})")
        lines.append(f"- **RAM Totale :** {rep.memory.total_ram_gb} Go (Disponible: {rep.memory.available_ram_gb} Go)")
        lines.append("")
        lines.append("### Stockage")
        for d in rep.disks:
            lines.append(f"- **Disque #{d.device_id} :** {d.model} ({d.size_gb} Go - {d.media_type}/{d.bus_type} - {d.partition_style})")
            for p in d.partitions:
                sys_tag = " *(Partition Système)*" if p.is_system else ""
                lines.append(f"  - Partition `{p.drive_letter}` ({p.filesystem}) : {p.free_gb} Go libres sur {p.total_gb} Go{sys_tag}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Évaluation de Compatibilité Omarchy")
    lines.append("")
    if summary.can_proceed:
        lines.append("> **Résultat : COMPATIBLE**  ")
        lines.append("> Le système cible satisfait l'ensemble des conditions minimales.")
    else:
        lines.append("> **Résultat : INCOMPATIBLE / BLOQUÉ**  ")
        lines.append("> Des corrections préalables sont indispensables avant de pouvoir installer Omarchy.")

    lines.append("")
    if summary.blockers:
        lines.append("### ❌ Éléments Bloquants")
        for b in summary.blockers:
            lines.append(f"- **[{b.category}] {b.title}** (`{b.source}`)")
            lines.append(f"  - *Message :* {b.message}")
            if b.details:
                lines.append(f"  - *Détails :* {b.details}")

    if summary.warnings:
        lines.append("### ⚠️ Avertissements")
        for w in summary.warnings:
            lines.append(f"- **[{w.category}] {w.title}** (`{w.source}`)")
            lines.append(f"  - *Message :* {w.message}")
            if w.details:
                lines.append(f"  - *Détails :* {w.details}")

    if summary.passed_checks:
        lines.append("### ✓ Vérifications Validées")
        for p in summary.passed_checks:
            lines.append(f"- **[{p.category}] {p.title} :** {p.message}")

    if summary.raw_errors:
        lines.append("### 🛑 Erreurs de Diagnostic")
        for err in summary.raw_errors:
            lines.append(f"- `{err}`")

    lines.append("")
    lines.append("---")
    lines.append("*Rapport généré automatiquement en lecture seule par BareInstall.*")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="BareInstall CLI - Outil complet de diagnostic, préparation de boot et récupération pour Omarchy."
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Exécuter en mode simulation (mock) sans interroger le matériel Windows réel."
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default=None,
        help="Chemin de fichier pour exporter le rapport au format JSON."
    )
    parser.add_argument(
        "--md-out",
        type=str,
        default=None,
        help="Chemin de fichier pour exporter le rapport au format Markdown."
    )
    parser.add_argument(
        "--prepare-boot",
        action="store_true",
        help="Préparer le démarrage interne et sauvegarder le BCD (Nécessite --confirm)."
    )
    parser.add_argument(
        "--restore-bcd",
        action="store_true",
        help="Restaurer le BCD Windows depuis la sauvegarde d'urgence."
    )
    parser.add_argument(
        "--verify-iso",
        type=str,
        default=None,
        help="Vérifier l'intégrité (SHA256) d'un fichier ISO Omarchy local."
    )
    parser.add_argument(
        "--expected-sha256",
        type=str,
        default=None,
        help="Empreinte SHA256 attendue pour la vérification ISO."
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirmer explicitement l'exécution d'une opération modifiant le système."
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Ne pas afficher le rapport de diagnostic dans la console."
    )

    args = parser.parse_args()

    # Mode 1: Restore BCD
    if args.restore_bcd:
        rec = RecoveryManager(simulated=args.simulate)
        ok, msg = rec.restore_bcd()
        print(f"[{'✓' if ok else '❌'}] Restauration BCD : {msg}")
        sys.exit(0 if ok else 1)

    # Mode 2: Verify ISO
    if args.verify_iso:
        ok, msg = IsoManager.verify_iso(args.verify_iso, expected_sha256=args.expected_sha256)
        print(f"[{'✓' if ok else '❌'}] Intégrité ISO : {msg}")
        sys.exit(0 if ok else 1)

    # Mode 3: Diagnostic Standard
    collector = get_collector(simulated=args.simulate)
    report = collector.collect()
    analyzer = DiagnosticAnalyzer()
    summary = analyzer.analyze(report)

    if not args.quiet:
        print(render_terminal_summary(summary))

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(asdict(summary), f, indent=2, ensure_ascii=False)
        print(f"\nRapport JSON exporté avec succès dans : {args.json_out}")

    if args.md_out:
        with open(args.md_out, "w", encoding="utf-8") as f:
            f.write(render_markdown_report(summary))
        print(f"Rapport Markdown exporté avec succès dans : {args.md_out}")

    # Mode 4: Prepare Boot (if requested)
    if args.prepare_boot:
        bm = BootManager(simulated=args.simulate)
        ok, msg = bm.prepare_boot(report, user_confirmed=args.confirm)
        print("\n----------------------------------------------------------------")
        print(f"[{'✓' if ok else '❌'}] Préparation du Démarrage Interne :")
        print(f"Message : {msg}")
        print("----------------------------------------------------------------")
        sys.exit(0 if ok else 1)

    sys.exit(0 if summary.can_proceed else 1)


if __name__ == "__main__":
    main()
