"""System information collection for comm-release."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field


# ─── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class DistribInfo:
    id: str = "Unknown"
    release: str = "Unknown"
    codename: str = "Unknown"
    description: str = "Unknown Distribution"


@dataclass
class SystemInfo:
    distrib: DistribInfo = field(default_factory=DistribInfo)
    environment: str = "Unknown"
    architecture: str = "Unknown"
    kernel: str = "Unknown"
    cpu: str = "Unknown"
    memory: str = "Unknown"
    uptime: str = "Unknown"
    install_date: str = "Unknown"
    last_update: str = "Unknown"
    repositories: str = "Unknown"
    pending_updates: str = "Unknown"


# ─── Internal helpers ──────────────────────────────────────────────────────────

def _run(cmd: list[str], timeout: int = 15) -> str:
    """Run a command and return stripped stdout; empty string on any failure."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _read(path: str) -> str:
    """Read a file safely; empty string if unreadable."""
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return ""


def _parse_key_value(content: str) -> dict[str, str]:
    """Parse a shell-style key=value file, stripping surrounding quotes."""
    result: dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


# ─── Collectors ────────────────────────────────────────────────────────────────

def collect_distrib() -> DistribInfo:
    """Read distribution identity from the highest-priority config file."""
    info = DistribInfo()

    for path in ("/etc/comm-release", "/etc/lsb-release"):
        if os.path.isfile(path):
            data = _parse_key_value(_read(path))
            info.id          = data.get("DISTRIB_ID",          info.id)
            info.release     = data.get("DISTRIB_RELEASE",     info.release)
            info.codename    = data.get("DISTRIB_CODENAME",    info.codename)
            info.description = data.get("DISTRIB_DESCRIPTION", info.description)
            return info

    if os.path.isfile("/etc/os-release"):
        data = _parse_key_value(_read("/etc/os-release"))
        info.id          = data.get("ID",               info.id)
        info.release     = data.get("VERSION_ID",       info.release)
        info.codename    = data.get("VERSION_CODENAME", info.codename)
        info.description = data.get("PRETTY_NAME",      info.description)

    return info


def collect_environment() -> str:
    """Detect whether the system is bare metal, VM, container, or WSL."""
    if os.environ.get("WSL_DISTRO_NAME") or \
            "microsoft" in _read("/proc/version").lower():
        return "WSL (Windows Subsystem for Linux)"

    if os.path.isfile("/.dockerenv"):
        return "Docker Container"

    if os.path.isfile("/run/.containerenv"):
        return "Podman Container"

    virt = _run(["systemd-detect-virt"])
    if virt and virt != "none":
        virt_map = {
            "kvm":        "KVM Virtual Machine",
            "qemu":       "QEMU Virtual Machine",
            "vmware":     "VMware Virtual Machine",
            "virtualbox": "VirtualBox Virtual Machine",
            "xen":        "Xen Virtual Machine",
            "microsoft":  "Hyper-V Virtual Machine",
        }
        return virt_map.get(virt, f"Virtual Machine ({virt})")

    product = _read("/sys/class/dmi/id/product_name")
    for keyword, label in (
        ("VirtualBox", "VirtualBox Virtual Machine"),
        ("VMware",     "VMware Virtual Machine"),
        ("QEMU",       "QEMU Virtual Machine"),
    ):
        if keyword in product:
            return label

    return "Bare Metal"


def collect_hardware() -> tuple[str, str, str, str, str]:
    """Return (architecture, kernel, cpu, memory, uptime)."""
    architecture = _run(["uname", "-m"]) or "Unknown"
    kernel       = _run(["uname", "-r"]) or "Unknown"

    # CPU
    cpu = "Unknown"
    cpuinfo = _read("/proc/cpuinfo")
    model_match = re.search(r"model name\s*:\s*(.+)", cpuinfo)
    if model_match:
        model = model_match.group(1).strip()
        cores = sum(1 for ln in cpuinfo.splitlines() if ln.startswith("processor"))
        cpu = f"{model} ({cores} core{'s' if cores != 1 else ''})"

    # Memory
    memory = "Unknown"
    mem_match = re.search(r"MemTotal:\s+(\d+)\s+kB", _read("/proc/meminfo"))
    if mem_match:
        kb = int(mem_match.group(1))
        memory = (
            f"{kb / 1024 / 1024:.1f} GB"
            if kb >= 1024 * 1024
            else f"{kb // 1024} MB"
        )

    # Uptime
    uptime = "Unknown"
    uptime_raw = _read("/proc/uptime")
    if uptime_raw:
        total       = int(float(uptime_raw.split()[0]))
        days, rem   = divmod(total, 86400)
        hours, rem  = divmod(rem, 3600)
        minutes     = rem // 60
        if days:
            uptime = f"{days}d {hours}h {minutes}m"
        elif hours:
            uptime = f"{hours}h {minutes}m"
        else:
            uptime = f"{minutes}m"

    return architecture, kernel, cpu, memory, uptime


def collect_install_date() -> str:
    """Estimate install date from the first entry in pacman.log."""
    pacman_log = _read("/var/log/pacman.log")
    if pacman_log:
        first = pacman_log.splitlines()[0]
        match = re.search(r"\[(\d{4}-\d{2}-\d{2})T", first)
        if match:
            return match.group(1)
    return "Unknown"


def collect_last_update() -> str:
    """Return the timestamp of the most recently installed/upgraded package."""
    if shutil.which("expac"):
        out = _run(["expac", "--timefmt=%Y-%m-%d %H:%M:%S", "%l\t%n"])
        if out:
            lines = sorted(out.splitlines())
            if lines:
                return lines[-1].split("\t")[0]

    pacman_log = _read("/var/log/pacman.log")
    if pacman_log:
        for line in reversed(pacman_log.splitlines()[-200:]):
            if "[ALPM]" in line and any(
                op in line for op in ("installed", "upgraded", "removed")
            ):
                match = re.search(
                    r"\[(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})", line
                )
                if match:
                    return f"{match.group(1)} {match.group(2)}"

    return "Unknown"


def collect_repositories() -> str:
    """Count enabled repositories for the detected package manager."""
    if os.path.isfile("/etc/pacman.conf"):
        content = _read("/etc/pacman.conf")
        count = sum(
            1
            for line in content.splitlines()
            if line.startswith("[")
            and "]" in line
            and line.strip() != "[options]"
        )
        return f"{count} Pacman repositories" if count else "Unknown"

    if os.path.isdir("/etc/apt"):
        sources = []
        if os.path.isfile("/etc/apt/sources.list"):
            sources.append("/etc/apt/sources.list")
        apt_d = "/etc/apt/sources.list.d"
        if os.path.isdir(apt_d):
            sources += [
                os.path.join(apt_d, f)
                for f in os.listdir(apt_d)
                if f.endswith(".list")
            ]
        count = sum(
            1
            for path in sources
            for line in _read(path).splitlines()
            if line.startswith("deb ")
        )
        return f"{count} APT repositories" if count else "Unknown"

    return "Unknown"


def collect_pending_updates() -> str:
    """Return number of pending package updates."""
    if shutil.which("checkupdates"):
        out = _run(["checkupdates"])
        lines = [ln for ln in out.splitlines() if ln.strip()]
        return f"{len(lines)} packages" if lines else "None"

    if shutil.which("pacman"):
        out = _run(["pacman", "-Qu"])
        lines = [ln for ln in out.splitlines() if ln.strip()]
        return f"{len(lines)} packages" if lines else "None"

    if shutil.which("apt-get"):
        out = _run(["apt", "list", "--upgradable"])
        count = sum(1 for ln in out.splitlines() if "upgradable" in ln)
        return f"{count} packages" if count else "None"

    return "Unknown"


def collect_all() -> SystemInfo:
    """Collect all system information and return a populated SystemInfo."""
    info = SystemInfo()
    info.distrib = collect_distrib()
    info.environment = collect_environment()
    (
        info.architecture,
        info.kernel,
        info.cpu,
        info.memory,
        info.uptime,
    ) = collect_hardware()
    info.install_date    = collect_install_date()
    info.last_update     = collect_last_update()
    info.repositories    = collect_repositories()
    info.pending_updates = collect_pending_updates()
    return info
