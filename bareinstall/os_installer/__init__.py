"""
BareInstall OS Installer & ISO Manager Module.
Handles ISO integrity verification (SHA256) and installation strategy validation.
"""

import os
import hashlib
from typing import Tuple, Optional


class IsoManager:
    """
    Handles cryptographic verification of Omarchy ISO images.
    """

    @staticmethod
    def calculate_sha256(filepath: str) -> str:
        """Computes the SHA256 hash of a local file."""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def verify_iso(filepath: str, expected_sha256: Optional[str] = None) -> Tuple[bool, str]:
        """
        Verifies that an ISO file exists and matches the expected SHA256 sum.
        """
        if not os.path.exists(filepath):
            return False, f"Fichier ISO introuvable : {filepath}"

        file_size_gb = round(os.path.getsize(filepath) / (1024**3), 2)
        if file_size_gb < 1.0:
            return False, f"Fichier ISO suspect : Taille trop faible ({file_size_gb} Go)."

        actual_sha256 = IsoManager.calculate_sha256(filepath)

        if expected_sha256:
            if actual_sha256.lower() == expected_sha256.lower():
                return True, f"ISO Omarchy vérifiée avec succès (SHA256 valide : {actual_sha256[:12]}...)."
            else:
                return False, f"ÉCHEC DE VÉRIFICATION ISO : SHA256 invalide.\nAttendu : {expected_sha256}\nCalculé : {actual_sha256}"

        return True, f"ISO présente ({file_size_gb} Go) - SHA256 : {actual_sha256}"


class BaseInstallerPlugin:
    """Base interface for distribution-specific installation plugins."""

    def name(self) -> str:
        raise NotImplementedError()

    def validate_requirements(self) -> Tuple[bool, str]:
        raise NotImplementedError()
