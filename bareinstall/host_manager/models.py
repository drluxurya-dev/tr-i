"""
BareInstall Host Manager Data Models.
Defines structured data classes for system diagnostic information.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CpuInfo:
    model: str
    architecture: str
    cores: int
    logical_processors: int


@dataclass
class MemoryInfo:
    total_ram_gb: float
    available_ram_gb: float
    status: str = "OK"  # "OK", "UNKNOWN", "ERROR"


@dataclass
class DiskPartition:
    drive_letter: str
    filesystem: str
    total_gb: float
    free_gb: float
    is_system: bool


@dataclass
class DiskInfo:
    device_id: str
    model: str
    size_gb: float
    media_type: str  # e.g., NVMe, SSD, HDD, eMMC, Unknown
    bus_type: str
    partition_style: str  # GPT, MBR, or Unknown
    partitions: List[DiskPartition] = field(default_factory=list)


@dataclass
class SecurityInfo:
    secure_boot_enabled: Optional[bool]  # True, False, None if query failed
    bitlocker_status: Dict[str, str] = field(default_factory=dict)  # Drive letter -> status
    fast_startup_enabled: Optional[bool] = None
    query_errors: List[str] = field(default_factory=list)


@dataclass
class FirmwareInfo:
    firmware_type: str  # UEFI, Legacy, or Unknown
    is_uefi: bool
    status: str = "OK"  # "OK", "UNKNOWN", "ERROR"


@dataclass
class SystemReport:
    os_name: str
    os_version: str
    is_windows: bool
    firmware: FirmwareInfo
    cpu: CpuInfo
    memory: MemoryInfo
    disks: List[DiskInfo]
    security: SecurityInfo
    is_simulated: bool = False
    raw_errors: List[str] = field(default_factory=list)


@dataclass
class DiagnosticCheck:
    check_id: str
    category: str
    title: str
    passed: bool
    severity: str  # "BLOCKER", "WARNING", "INFO"
    source: str    # "OFFICIAL_OMARCHY", "BAREINSTALL_RECOMMENDATION", "SYSTEM_SAFETY"
    message: str
    details: Optional[str] = None


@dataclass
class DiagnosticSummary:
    can_proceed: bool
    blockers: List[DiagnosticCheck] = field(default_factory=list)
    warnings: List[DiagnosticCheck] = field(default_factory=list)
    passed_checks: List[DiagnosticCheck] = field(default_factory=list)
    raw_errors: List[str] = field(default_factory=list)
    system_report: Optional[SystemReport] = None
