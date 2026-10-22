"""
BareInstall Command Line Interface (CLI).
Provides terminal output, JSON output, and Markdown report export for Phase B diagnostics.
STRICTLY READ-ONLY.
"""

import sys
import os
import argparse
import json
from dataclasses import asdict
from typing import Optional

from bareinstall.host_manager import get_collector, DiagnosticAnalyzer, DiagnosticSummary, SystemReport


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
        lines.append(" La machine respecte les prérequis pour une préparation d'installation.")
    else:
        lines.append(" STATUS GLOBAL : INCOMPATIBLE / BLOQUÉ [✗]")
        lines.append(" Des obstacles critiques empêchent la poursuite des opérations.")

    lines.append("----------------------------------------------------------------")

    if summary.blockers:
        lines.append("\n[!] ÉLÉMENTS BLOQUANTS (BLOCKERS) :")
        for b in summary.blockers:
            lines.append(f"  ❌ [{b.category}] {b.title}")
            lines.append(f"     Message : {b.message}")
            if b.details:
                lines.append(f"     Détails : {b.details}")

    if summary.warnings:
        lines.append("\n[?] AVERTISSEMENTS (WARNINGS) :")
        for w in summary.warnings:
            lines.append(f"  ⚠️ [{w.category}] {w.title}")
            lines.append(f"     Message : {w.message}")
            if w.details:
                lines.append(f"     Détails : {w.details}")

    if summary.passed_checks:
        lines.append("\n[✓] VERIFICATIONS CONCLUANTES :")
        for p in summary.passed_checks:
            lines.append(f"  ✓ [{p.category}] {p.title}: {p.message}")

    lines.append("================================================================")
    lines.append(" Note : Ce diagnostic est strictement en LECTURE SEULE.")
    lines.append(" Aucune modification n'a été effectuée sur vos disques ou le BCD.")
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
            lines.append(f"- **[{b.category}] {b.title}**")
            lines.append(f"  - *Message :* {b.message}")
            if b.details:
                lines.append(f"  - *Détails :* {b.details}")

    if summary.warnings:
        lines.append("### ⚠️ Avertissements")
        for w in summary.warnings:
            lines.append(f"- **[{w.category}] {w.title}**")
            lines.append(f"  - *Message :* {w.message}")
            if w.details:
                lines.append(f"  - *Détails :* {w.details}")

    if summary.passed_checks:
        lines.append("### ✓ Vérifications Validées")
        for p in summary.passed_checks:
            lines.append(f"- **[{p.category}] {p.title} :** {p.message}")

    lines.append("")
    lines.append("---")
    lines.append("*Rapport généré automatiquement en lecture seule par BareInstall.*")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="BareInstall Host Diagnostic Tool - Diagnostic en lecture seule pour installation sans clé USB."
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
        "--quiet",
        action="store_true",
        help="Ne pas afficher le rapport dans la console."
    )

    args = parser.parse_args()

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

    sys.exit(0 if summary.can_proceed else 1)


if __name__ == "__main__":
    main()
