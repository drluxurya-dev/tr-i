"""
BareInstall OS Installer & ISO Integrity Verification Module.
Handles strict cryptographic verification (SHA256) of Omarchy ISO images against official release checksums.
"""

import os
import hashlib
from typing import Tuple, Optional


class IsoManager:
    """
    Handles cryptographic SHA256 verification of Omarchy ISO images.
    """

    @staticmethod
    def calculate_sha256(filepath: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Computes the SHA256 hash of a local file in 64KB chunks.
        Returns (sha256_hex, error_message).
        """
        if not os.path.exists(filepath):
            return None, f"Fichier ISO introuvable : {filepath}"

        if not os.path.isfile(filepath):
            return None, f"Le chemin spécifié n'est pas un fichier : {filepath}"

        hasher = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest(), None
        except PermissionError:
            return None, f"Erreur de permission : Impossible de lire le fichier {filepath}"
        except Exception as e:
            return None, f"Erreur lors de la lecture du fichier ISO : {str(e)}"

    @staticmethod
    def verify_iso(filepath: str, expected_sha256: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Verifies an ISO image file against an official SHA256 checksum.
        Returns (is_verified, message, actual_sha256).

        Strict rules:
        - If expected_sha256 is missing, the ISO is flagged as UNVERIFIED (never declared valid).
        - No arbitrary file size heuristics are used to claim validity.
        """
        actual_sha256, err = IsoManager.calculate_sha256(filepath)
        if err or not actual_sha256:
            return False, f"Échec de calcul SHA256 : {err}", None

        if not expected_sha256 or not expected_sha256.strip():
            return False, (
                f"INTEGRITÉ NON CONFIRMÉE : Aucune empreinte SHA256 officielle fournie pour la vérification.\n"
                f"Fichier : {filepath}\n"
                f"Empreinte calculée : {actual_sha256}\n"
                f"Veuillez fournir l'empreinte SHA256 officielle d'Omarchy (--expected-sha256)."
            ), actual_sha256

        clean_expected = expected_sha256.strip().lower()
        clean_actual = actual_sha256.strip().lower()

        if clean_actual == clean_expected:
            return True, (
                f"VÉRIFICATION RÉUSSIE : L'empreinte SHA256 de l'image ISO correspond exactement à la référence officielle.\n"
                f"SHA256 : {clean_actual}"
            ), clean_actual
        else:
            return False, (
                f"ÉCHEC CRITIQUE DE VÉRIFICATION ISO : Empreinte SHA256 INCORRECTE ou fichier corrompu.\n"
                f"Attendu : {clean_expected}\n"
                f"Calculé : {clean_actual}"
            ), clean_actual


class BaseInstallerPlugin:
    """Base interface for distribution-specific installation plugins."""

    def name(self) -> str:
        raise NotImplementedError()

    def validate_requirements(self) -> Tuple[bool, str]:
        raise NotImplementedError()
