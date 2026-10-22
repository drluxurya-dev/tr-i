"""
Pytest Test Suite for BareInstall Modules:
- boot_manager
- recovery_manager
- os_installer (IsoManager)
- distro_omarchy
"""

import os
import tempfile
import pytest
from bareinstall.host_manager import MockCollector
from bareinstall.boot_manager import BootManager
from bareinstall.recovery_manager import RecoveryManager
from bareinstall.os_installer import IsoManager
from bareinstall.distro_omarchy import OmarchyPlugin


def test_recovery_manager_mock():
    rec = RecoveryManager(simulated=True)
    ok_backup, msg_backup = rec.backup_bcd()
    assert ok_backup is True
    assert "[MOCK]" in msg_backup

    ok_restore, msg_restore = rec.restore_bcd()
    assert ok_restore is True
    assert "[MOCK]" in msg_restore

    ok_clean, msg_clean = rec.cleanup_staging()
    assert ok_clean is True


def test_boot_manager_unconfirmed_safety():
    bm = BootManager(simulated=True)
    collector = MockCollector()
    report = collector.collect()

    # Should refuse if user_confirmed is False
    ok, msg = bm.prepare_boot(report, user_confirmed=False)
    assert ok is False
    assert "SÉCURITÉ" in msg


def test_boot_manager_confirmed():
    bm = BootManager(simulated=True)
    collector = MockCollector()
    report = collector.collect()

    ok, msg = bm.prepare_boot(report, user_confirmed=True)
    assert ok is True
    assert "Préparation" in msg or "MOCK" in msg


def test_iso_manager_missing_file():
    ok, msg = IsoManager.verify_iso("non_existent_file.iso")
    assert ok is False
    assert "introuvable" in msg


def test_iso_manager_valid_and_checksum():
    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        # Write dummy data > 1GB representation or test data
        dummy_content = b"Omarchy ISO Dummy Data " * 100000
        f.write(dummy_content)
        temp_path = f.name

    try:
        # Mock file size check override or use normal file
        ok, msg = IsoManager.verify_iso(temp_path)
        # File is small so it flags size
        assert ok is False
        assert "Taille trop faible" in msg
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_omarchy_plugin():
    plugin = OmarchyPlugin()
    assert plugin.name() == "Omarchy Linux"

    collector = MockCollector()
    report = collector.collect()
    ok, msg = plugin.validate_requirements(report)
    assert ok is True
    assert "satisfaites" in msg
