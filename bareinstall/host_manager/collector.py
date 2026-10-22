"""
BareInstall Host Manager System Collector.
Gathers hardware, firmware, partition, and security information from Windows or Mock environments.
STRICTLY READ-ONLY: Never modifies system settings, disk partitions, registry, or bootloader.
"""

import sys
import os
import json
import subprocess
import platform
from typing import Dict, Any, List, Optional
from .models import (
    SystemReport, FirmwareInfo, CpuInfo, MemoryInfo,
    DiskInfo, DiskPartition, SecurityInfo
)


class BaseCollector:
    """Base interface for system data collectors."""
    def collect(self) -> SystemReport:
        raise NotImplementedError()


class WindowsCollector(BaseCollector):
    """
    Native Windows Collector using PowerShell, WMI, and System APIs.
    All operations are strictly read-only.
    """

    def _run_powershell_json(self, command: str) -> Any:
        """Helper to run a PowerShell command and parse JSON output."""
        try:
            full_cmd = [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                f"{command} | ConvertTo-Json -Depth 5"
            ]
            res = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=15
            )
            if not res.stdout.strip():
                return None
            return json.loads(res.stdout)
        except Exception as e:
            return None

    def _get_firmware_info(self) -> FirmwareInfo:
        # Check firmware via PowerShell / Get-FirmwareType or BCD
        is_uefi = False
        fw_type = "Unknown"
        try:
            # Check PE / Windows firmware env
            ps_cmd = "$env:firmware_type"
            output = self._run_powershell_json(ps_cmd)
            if isinstance(output, str):
                fw_type = output.strip()
                if fw_type.upper() == "UEFI":
                    is_uefi = True

            if fw_type == "Unknown":
                # Try Get-ComputerInfo
                comp_info = self._run_powershell_json("(Get-ComputerInfo).BiosFirmwareType")
                if comp_info and isinstance(comp_info, str):
                    fw_type = comp_info.strip()
                    if fw_type.upper() == "UEFI":
                        is_uefi = True
        except Exception:
            pass

        return FirmwareInfo(firmware_type=fw_type, is_uefi=is_uefi)

    def _get_cpu_info(self) -> CpuInfo:
        model = platform.processor() or "Unknown CPU"
        architecture = platform.machine() or "x86_64"
        cores = os.cpu_count() or 1
        logical_processors = cores

        try:
            cpu_data = self._run_powershell_json("Get-CimInstance Win32_Processor | Select-Object Name, Architecture, NumberOfCores, NumberOfLogicalProcessors")
            if isinstance(cpu_data, list) and len(cpu_data) > 0:
                cpu_data = cpu_data[0]
            if isinstance(cpu_data, dict):
                model = cpu_data.get("Name", model)
                cores = cpu_data.get("NumberOfCores", cores)
                logical_processors = cpu_data.get("NumberOfLogicalProcessors", logical_processors)
        except Exception:
            pass

        return CpuInfo(
            model=model,
            architecture=architecture,
            cores=cores,
            logical_processors=logical_processors
        )

    def _get_memory_info(self) -> MemoryInfo:
        total_ram_gb = 0.0
        avail_ram_gb = 0.0
        try:
            mem_data = self._run_powershell_json("Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory")
            if isinstance(mem_data, dict):
                tot_kb = mem_data.get("TotalVisibleMemorySize", 0)
                free_kb = mem_data.get("FreePhysicalMemory", 0)
                total_ram_gb = round(tot_kb / (1024 * 1024), 2)
                avail_ram_gb = round(free_kb / (1024 * 1024), 2)
        except Exception:
            pass

        return MemoryInfo(total_ram_gb=total_ram_gb, available_ram_gb=avail_ram_gb)

    def _get_disks_info(self) -> List[DiskInfo]:
        disks: List[DiskInfo] = []
        try:
            physical_disks = self._run_powershell_json("Get-PhysicalDisk | Select-Object DeviceId, FriendlyName, Size, MediaType, BusType")
            if isinstance(physical_disks, dict):
                physical_disks = [physical_disks]

            p_disk_map = {}
            if isinstance(physical_disks, list):
                for pd in physical_disks:
                    dev_id = str(pd.get("DeviceId", ""))
                    p_disk_map[dev_id] = pd

            disk_partitions_data = self._run_powershell_json("Get-Disk | Select-Object Number, FriendlyName, Size, PartitionStyle, BusType")
            if isinstance(disk_partitions_data, dict):
                disk_partitions_data = [disk_partitions_data]

            volumes_data = self._run_powershell_json("Get-Volume | Select-Object DriveLetter, FileSystem, Size, SizeRemaining")
            vol_map = {}
            if isinstance(volumes_data, list):
                for v in volumes_data:
                    dl = v.get("DriveLetter")
                    if dl:
                        vol_map[str(dl).upper()] = v
            elif isinstance(volumes_data, dict) and volumes_data.get("DriveLetter"):
                vol_map[str(volumes_data.get("DriveLetter")).upper()] = volumes_data

            if isinstance(disk_partitions_data, list):
                for d in disk_partitions_data:
                    num_str = str(d.get("Number", ""))
                    pd_info = p_disk_map.get(num_str, {})
                    media_type = pd_info.get("MediaType", "Unknown") if pd_info else "Unknown"
                    bus_type = str(d.get("BusType", pd_info.get("BusType", "Unknown")))
                    size_bytes = d.get("Size", 0) or 0
                    size_gb = round(size_bytes / (1024**3), 2)
                    part_style = str(d.get("PartitionStyle", "Unknown"))

                    # Fetch partitions for this disk
                    parts: List[DiskPartition] = []
                    parts_ps = self._run_powershell_json(f"Get-Partition -DiskNumber {num_str} | Select-Object DriveLetter, AccessPaths, DriveType, Size")
                    if isinstance(parts_ps, dict):
                        parts_ps = [parts_ps]
                    if isinstance(parts_ps, list):
                        for p in parts_ps:
                            dl = p.get("DriveLetter")
                            dl_str = f"{dl}:" if dl else ""
                            v_info = vol_map.get(str(dl).upper(), {}) if dl else {}
                            tot_gb = round((v_info.get("Size", 0) or 0) / (1024**3), 2)
                            free_gb = round((v_info.get("SizeRemaining", 0) or 0) / (1024**3), 2)
                            fs = str(v_info.get("FileSystem", "Unknown"))
                            is_sys = (str(dl).upper() == "C")

                            if dl_str or tot_gb > 0:
                                parts.append(DiskPartition(
                                    drive_letter=dl_str,
                                    filesystem=fs,
                                    total_gb=tot_gb,
                                    free_gb=free_gb,
                                    is_system=is_sys
                                ))

                    disks.append(DiskInfo(
                        device_id=num_str,
                        model=str(d.get("FriendlyName", "Generic Disk")),
                        size_gb=size_gb,
                        media_type=str(media_type),
                        bus_type=bus_type,
                        partition_style=part_style,
                        partitions=parts
                    ))
        except Exception:
            pass

        return disks

    def _get_security_info(self) -> SecurityInfo:
        secure_boot = None
        bitlocker_status = {}
        fast_startup = None

        # Check Secure Boot
        try:
            sb_res = self._run_powershell_json("Confirm-SecureBootUEFI")
            if isinstance(sb_res, bool):
                secure_boot = sb_res
        except Exception:
            secure_boot = None

        # Check BitLocker
        try:
            bl_res = self._run_powershell_json("Get-BitLockerVolume | Select-Object MountPoint, ProtectionStatus, VolumeStatus")
            if isinstance(bl_res, dict):
                bl_res = [bl_res]
            if isinstance(bl_res, list):
                for bl in bl_res:
                    mp = str(bl.get("MountPoint", ""))
                    status = str(bl.get("VolumeStatus", "Unknown"))
                    prot = str(bl.get("ProtectionStatus", "Unknown"))
                    if mp:
                        bitlocker_status[mp] = f"{status} (Protection: {prot})"
        except Exception:
            pass

        # Check Fast Startup Registry
        try:
            reg_res = self._run_powershell_json("(Get-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power').HiberbootEnabled")
            if isinstance(reg_res, int):
                fast_startup = (reg_res == 1)
        except Exception:
            pass

        return SecurityInfo(
            secure_boot_enabled=secure_boot,
            bitlocker_status=bitlocker_status,
            fast_startup_enabled=fast_startup
        )

    def collect(self) -> SystemReport:
        errors = []
        fw = self._get_firmware_info()
        cpu = self._get_cpu_info()
        mem = self._get_memory_info()
        disks = self._get_disks_info()
        sec = self._get_security_info()

        return SystemReport(
            os_name="Windows",
            os_version=platform.version(),
            is_windows=True,
            firmware=fw,
            cpu=cpu,
            memory=mem,
            disks=disks,
            security=sec,
            is_simulated=False,
            raw_errors=errors
        )


class MockCollector(BaseCollector):
    """
    Mock Collector for Linux dev environments and Pytest simulation scenarios.
    Configurable via preset scenarios.
    """

    def __init__(self, scenario_config: Optional[Dict[str, Any]] = None):
        self.config = scenario_config or {}

    def collect(self) -> SystemReport:
        fw_type = self.config.get("firmware_type", "UEFI")
        is_uefi = (fw_type.upper() == "UEFI")
        fw = FirmwareInfo(firmware_type=fw_type, is_uefi=is_uefi)

        cpu = CpuInfo(
            model=self.config.get("cpu_model", "Intel Pentium Silver N5030"),
            architecture=self.config.get("cpu_arch", "x86_64"),
            cores=self.config.get("cpu_cores", 4),
            logical_processors=self.config.get("cpu_logical", 4)
        )

        mem = MemoryInfo(
            total_ram_gb=self.config.get("total_ram_gb", 3.8),
            available_ram_gb=self.config.get("avail_ram_gb", 2.1)
        )

        disk_size = self.config.get("disk_size_gb", 789.0)
        sys_free = self.config.get("sys_free_gb", 150.0)
        bitlocker_on = self.config.get("bitlocker_enabled", False)

        parts = [
            DiskPartition(
                drive_letter="C:",
                filesystem="NTFS",
                total_gb=round(disk_size - 1.0, 2),
                free_gb=sys_free,
                is_system=True
            )
        ]

        disks = [
            DiskInfo(
                device_id="0",
                model=self.config.get("disk_model", "NVMe INTEL SSDPEKNW512G8"),
                size_gb=disk_size,
                media_type=self.config.get("media_type", "SSD"),
                bus_type=self.config.get("bus_type", "NVMe"),
                partition_style=self.config.get("partition_style", "GPT"),
                partitions=parts
            )
        ]

        bl_status = {}
        if bitlocker_on:
            bl_status["C:"] = "FullyEncrypted (Protection: On)"

        sec = SecurityInfo(
            secure_boot_enabled=self.config.get("secure_boot_enabled", False),
            bitlocker_status=bl_status,
            fast_startup_enabled=self.config.get("fast_startup_enabled", True)
        )

        return SystemReport(
            os_name=self.config.get("os_name", "Windows (Simulated)"),
            os_version=self.config.get("os_version", "10.0.19045"),
            is_windows=True,
            firmware=fw,
            cpu=cpu,
            memory=mem,
            disks=disks,
            security=sec,
            is_simulated=True,
            raw_errors=[]
        )


def get_collector(simulated: bool = False, scenario: Optional[Dict[str, Any]] = None) -> BaseCollector:
    """Factory function to select appropriate collector."""
    if simulated or platform.system() != "Windows":
        return MockCollector(scenario_config=scenario)
    return WindowsCollector()
