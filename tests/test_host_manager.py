"""
Pytest Test Suite for BareInstall Host Manager and Diagnostic Analyzer.
Tests edge cases: BitLocker, low RAM, low Disk Space, Legacy BIOS, MBR partition, Secure Boot enabled.
"""

import pytest
import json
from bareinstall.host_manager import (
    MockCollector, DiagnosticAnalyzer, SystemReport
)
from bareinstall.cli import render_terminal_summary, render_markdown_report


def test_perfect_hardware_scenario():
    """Test a machine that satisfies all requirements."""
    scenario = {
        "firmware_type": "UEFI",
        "cpu_arch": "x86_64",
        "total_ram_gb": 4.0,
        "avail_ram_gb": 2.5,
        "disk_size_gb": 789.0,
        "sys_free_gb": 150.0,
        "bitlocker_enabled": False,
        "secure_boot_enabled": False,
        "fast_startup_enabled": False,
        "partition_style": "GPT",
    }
    collector = MockCollector(scenario)
    report = collector.collect()
    analyzer = DiagnosticAnalyzer()
    summary = analyzer.analyze(report)

    assert summary.can_proceed is True
    assert len(summary.blockers) == 0


def test_bitlocker_blocker_scenario():
    """Test BitLocker active on system drive."""
    scenario = {
        "firmware_type": "UEFI",
        "cpu_arch": "x86_64",
        "total_ram_gb": 4.0,
        "sys_free_gb": 100.0,
        "bitlocker_enabled": True,
    }
    collector = MockCollector(scenario)
    report = collector.collect()
    analyzer = DiagnosticAnalyzer()
    summary = analyzer.analyze(report)

    assert summary.can_proceed is False
    assert any(b.check_id == "SEC_BITLOCKER" for b in summary.blockers)


def test_legacy_bios_blocker_scenario():
    """Test Legacy BIOS firmware (non-UEFI)."""
    scenario = {
        "firmware_type": "Legacy",
        "cpu_arch": "x86_64",
        "total_ram_gb": 4.0,
        "sys_free_gb": 100.0,
    }
    collector = MockCollector(scenario)
    report = collector.collect()
    analyzer = DiagnosticAnalyzer()
    summary = analyzer.analyze(report)

    assert summary.can_proceed is False
    assert any(b.check_id == "FW_UEFI" for b in summary.blockers)


def test_insufficient_ram_blocker_scenario():
    """Test RAM less than 3.5GB."""
    scenario = {
        "firmware_type": "UEFI",
        "cpu_arch": "x86_64",
        "total_ram_gb": 2.0,
        "sys_free_gb": 100.0,
    }
    collector = MockCollector(scenario)
    report = collector.collect()
    analyzer = DiagnosticAnalyzer()
    summary = analyzer.analyze(report)

    assert summary.can_proceed is False
    assert any(b.check_id == "MEM_RAM" for b in summary.blockers)


def test_insufficient_disk_space_blocker_scenario():
    """Test Free Disk Space less than 20GB."""
    scenario = {
        "firmware_type": "UEFI",
        "cpu_arch": "x86_64",
        "total_ram_gb": 4.0,
        "sys_free_gb": 5.0,  # Only 5GB free
    }
    collector = MockCollector(scenario)
    report = collector.collect()
    analyzer = DiagnosticAnalyzer()
    summary = analyzer.analyze(report)

    assert summary.can_proceed is False
    assert any(b.check_id == "DISK_FREE" for b in summary.blockers)


def test_mbr_partition_blocker_scenario():
    """Test MBR partition style instead of GPT."""
    scenario = {
        "firmware_type": "UEFI",
        "cpu_arch": "x86_64",
        "total_ram_gb": 4.0,
        "sys_free_gb": 100.0,
        "partition_style": "MBR",
    }
    collector = MockCollector(scenario)
    report = collector.collect()
    analyzer = DiagnosticAnalyzer()
    summary = analyzer.analyze(report)

    assert summary.can_proceed is False
    assert any(b.check_id == "PART_GPT" for b in summary.blockers)


def test_secure_boot_warning_scenario():
    """Test Secure Boot enabled produces a warning, not a blocker."""
    scenario = {
        "firmware_type": "UEFI",
        "cpu_arch": "x86_64",
        "total_ram_gb": 4.0,
        "sys_free_gb": 100.0,
        "secure_boot_enabled": True,
    }
    collector = MockCollector(scenario)
    report = collector.collect()
    analyzer = DiagnosticAnalyzer()
    summary = analyzer.analyze(report)

    # Secure Boot enabled is a WARNING, so can_proceed is still True
    assert summary.can_proceed is True
    assert any(w.check_id == "SEC_BOOT" for w in summary.warnings)


def test_reports_formatting():
    """Test rendering of terminal and markdown reports."""
    scenario = {
        "firmware_type": "UEFI",
        "cpu_arch": "x86_64",
        "total_ram_gb": 4.0,
        "sys_free_gb": 50.0,
    }
    collector = MockCollector(scenario)
    report = collector.collect()
    analyzer = DiagnosticAnalyzer()
    summary = analyzer.analyze(report)

    term = render_terminal_summary(summary)
    md = render_markdown_report(summary)

    assert "BAREINSTALL - RAPPORT DE DIAGNOSTIC" in term
    assert "# BareInstall - Rapport de Diagnostic Système" in md
