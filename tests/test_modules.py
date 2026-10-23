"""
Pytest Test Suite for BareInstall Modules:
- boot_manager
- recovery_manager
- os_installer (IsoManager)
- distro_omarchy

Includes explicit assertions verifying mock isolation (ensuring no real system files/commands are touched during unit tests).
"""

import os
import tempfile
import pytest
from bareinstall.host_manager import MockCollector
from bareinstall.boot_manager import BootManager
from bareinstall.recovery_manager import RecoveryManager
from bareinstall.os_installer import IsoManager
from bareinstall.distro_omarchy import OmarchyPlugin


def test_mock_isolation_guarantee():
    """Verify that MockCollector and simulated managers run in strict isolation."""
    rec = RecoveryManager(simulated=True)
    assert rec.simulated is True

    bm = BootManager(simulated=True)
    assert bm.simulated is True

    test_path = "/tmp/fake_bareinstall_test_backup.bcd"
    rec_test = RecoveryManager(backup_path=test_path, simulated=True)
    ok, msg = rec_test.backup_bcd()
    assert ok is True
    assert "[MOCK]" in msg
    assert not os.path.exists(test_path)


def test_recovery_manager_verify_backup_validation():
    """Test verification of BCD backup file existence and size."""
    rec_mock = RecoveryManager(simulated=True)
    ok, msg = rec_mock.verify_backup_file()
    assert ok is True

    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        f.write(b"Too small")
        small_path = f.name

    try:
        rec_real = RecoveryManager(backup_path=small_path, simulated=False)
        ok_ver, msg_ver = rec_real.verify_backup_file()
        assert ok_ver is False
        assert "CORROMPUE" in msg_ver
    finally:
        if os.path.exists(small_path):
            os.remove(small_path)


def test_recovery_manager_restore_unconfirmed():
    """Test that BCD restoration fails without explicit user confirmation."""
    rec = RecoveryManager(simulated=False)
    ok, msg = rec.restore_bcd(user_confirmed=False)
    assert ok is False
    assert "CONFIRMATION REQUISE" in msg


def test_boot_manager_unconfirmed_safety():
    bm = BootManager(simulated=True)
    collector = MockCollector()
    report = collector.collect()

    ok, msg = bm.prepare_boot(report, user_confirmed=False, iso_verified=True)
    assert ok is False
    assert "SÉCURITÉ" in msg


def test_boot_manager_unverified_iso_safety():
    bm = BootManager(simulated=True)
    collector = MockCollector()
    report = collector.collect()

    ok, msg = bm.prepare_boot(report, user_confirmed=True, iso_verified=False)
    assert ok is False
    assert "SHA256" in msg


def test_boot_manager_confirmed_and_verified():
    bm = BootManager(simulated=True)
    collector = MockCollector()
    report = collector.collect()

    ok, msg = bm.prepare_boot(report, user_confirmed=True, iso_verified=True)
    assert ok is True
    assert "EXPÉRIMENTALE" in msg or "SIMULÉE" in msg


def test_iso_manager_missing_file():
    ok, msg, hash_val = IsoManager.verify_iso("non_existent_file.iso")
    assert ok is False
    assert "introuvable" in msg
    assert hash_val is None


def test_iso_manager_unverified_missing_expected_sha256():
    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        f.write(b"Dummy ISO File Content For Testing SHA256")
        temp_path = f.name

    try:
        ok, msg, actual_hash = IsoManager.verify_iso(temp_path, expected_sha256=None)
        assert ok is False
        assert "INTEGRITÉ NON CONFIRMÉE" in msg
        assert actual_hash is not None
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_iso_manager_verified_exact_sha256():
    test_content = b"Exact Match ISO Content"
    import hashlib
    expected_hash = hashlib.sha256(test_content).hexdigest()

    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        f.write(test_content)
        temp_path = f.name

    try:
        ok, msg, actual_hash = IsoManager.verify_iso(temp_path, expected_sha256=expected_hash)
        assert ok is True
        assert "VÉRIFICATION RÉUSSIE" in msg
        assert actual_hash == expected_hash
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
