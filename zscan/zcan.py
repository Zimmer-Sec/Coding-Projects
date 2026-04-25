#!/usr/bin/env python3
"""
Python CLI utility that helps run Nmap scans with
IDS/IPS evasion techniques in an interactive way.
Python: 3.x
Optional color support degrades gracefully if colorama is unavailable
"""

from __future__ import annotations
import datetime as dt
import ipaddress
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


try:
    from colorama import Fore, Style, init

    init(autoreset=True)
except Exception:  # pragma: no cover - fallback path for environments without colorama
    class _Dummy:  # pylint: disable=too-few-public-methods
        RED = ""
        GREEN = ""
        YELLOW = ""
        CYAN = ""
        MAGENTA = ""
        RESET_ALL = ""

    Fore = Style = _Dummy()


# Configuration (edit these values as needed)

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
TRACKER_FILE = BASE_DIR / "technique_tracker.json"
NMAP_BINARY = "nmap"
DEFAULT_NMAP_ARGS = ["-Pn"]  # skip host discovery for CTF/lab targets


@dataclass
class ScanType:
    """Represents a scan mode shown to the user."""

    key: str
    name: str
    args: List[str]
    description: str


SCAN_TYPES: Dict[str, ScanType] = {
    "1": ScanType("1", "SYN Scan", ["-sS"], "Stealthy half-open TCP scan."),
    "2": ScanType("2", "ACK Scan", ["-sA"], "Firewall rule mapping and filtering analysis."),
    "3": ScanType("3", "UDP Scan", ["-sU"], "Scans UDP services (often slower/noisy)."),
    "4": ScanType("4", "TCP Connect Scan", ["-sT"], "Full TCP handshake scan (no raw packet privileges needed)."),
    "5": ScanType("5", "FIN Scan", ["-sF"], "Useful against some stateless filtering systems."),
    "6": ScanType("6", "NULL Scan", ["-sN"], "Packet with no TCP flags set; niche evasion case."),
    "7": ScanType("7", "XMAS Scan", ["-sX"], "FIN/PSH/URG set; can reveal filtering behavior."),
    "8": ScanType("8", "Version Detection", ["-sV"], "Service version fingerprinting."),
    "9": ScanType("9", "OS Detection", ["-O"], "Attempts remote OS fingerprinting."),
    "10": ScanType("10", "Aggressive", ["-A"], "OS, version, scripts, traceroute (more noisy)."),
}


EVASION_TECHNIQUES = [
    {
        "id": "1",
        "name": "Fragment packets (-f)",
        "description": "Splits probe packets into tiny fragments.",
        "builder": lambda: ["-f"],
    },
    {
        "id": "2",
        "name": "Custom MTU (--mtu)",
        "description": "Set specific packet MTU (must be a multiple of 8).",
        "builder": lambda: ["--mtu", prompt_mtu()],
    },
    {
        "id": "3",
        "name": "Decoy scanning (-D)",
        "description": "Blend your scan among decoy IPs (e.g., RND:5 or 1.1.1.1,ME).",
        "builder": lambda: ["-D", prompt_non_empty("Enter decoy list (e.g., RND:5,ME): ")],
    },
    {
        "id": "4",
        "name": "Source port manipulation (--source-port)",
        "description": "Set source port to mimic trusted traffic.",
        "builder": lambda: ["--source-port", prompt_port("Enter source port (1-65535): ")],
    },
    {
        "id": "5",
        "name": "Timing template (-T0..-T5)",
        "description": "Control scan timing profile from paranoid to insane.",
        "builder": lambda: [prompt_timing_template()],
    },
    {
        "id": "6",
        "name": "Randomize hosts (--randomize-hosts)",
        "description": "Randomizes target host scan order.",
        "builder": lambda: ["--randomize-hosts"],
    },
    {
        "id": "7",
        "name": "Spoof MAC address (--spoof-mac)",
        "description": "Spoof source MAC (value like 0, random, vendor, or full MAC).",
        "builder": lambda: ["--spoof-mac", prompt_non_empty("Enter spoof MAC value (e.g., 0, random, Apple, 00:11:22:33:44:55): ")],
    },
    {
        "id": "8",
        "name": "Bad checksums (--badsum)",
        "description": "Sends packets with invalid TCP/UDP checksums.",
        "builder": lambda: ["--badsum"],
    },
    {
        "id": "9",
        "name": "Append random data (--data-length)",
        "description": "Pad packets with random payload bytes.",
        "builder": lambda: ["--data-length", prompt_positive_int("Enter data length bytes (1+): ")],
    },
    {
        "id": "10",
        "name": "IP options (--ip-options)",
        "description": "Set custom IP options string (advanced evasion).",
        "builder": lambda: ["--ip-options", prompt_non_empty("Enter IP options value: ")],
    },
    {
        "id": "11",
        "name": "TTL manipulation (--ttl)",
        "description": "Set custom packet TTL.",
        "builder": lambda: ["--ttl", prompt_positive_int("Enter TTL value (1+): ")],
    },
    {
        "id": "12",
        "name": "Spoof source IP (-S)",
        "description": "Set forged source IP (advanced; route/interface constraints apply).",
        "builder": lambda: ["-S", prompt_non_empty("Enter spoofed source IP: ")],
    },
    {
        "id": "13",
        "name": "Set scan delay (--scan-delay)",
        "description": "Delay between probes (e.g., 500ms, 1s).",
        "builder": lambda: ["--scan-delay", prompt_non_empty("Enter scan delay (e.g., 500ms, 1s): ")],
    },
    {
        "id": "14",
        "name": "Set max scan delay (--max-scan-delay)",
        "description": "Upper bound for dynamically adjusted delays.",
        "builder": lambda: ["--max-scan-delay", prompt_non_empty("Enter max scan delay (e.g., 2s): ")],
    },
    {
        "id": "15",
        "name": "Set packet send rate (--min-rate/--max-rate)",
        "description": "Control packet send rates for evasion/performance tuning.",
        "builder": lambda: prompt_rate_options(),
    },
    {
        "id": "16",
        "name": "Use specific DNS servers (--dns-servers)",
        "description": "Override resolvers to reduce default DNS fingerprinting.",
        "builder": lambda: ["--dns-servers", prompt_non_empty("Enter DNS server list (comma-separated): ")],
    },
    {
        "id": "17",
        "name": "Defeat RST rate limits (--defeat-rst-ratelimit)",
        "description": "Improve closed/filtered classification when RST limiting exists.",
        "builder": lambda: ["--defeat-rst-ratelimit"],
    },
    {
        "id": "18",
        "name": "Defeat ICMP rate limits (--defeat-icmp-ratelimit)",
        "description": "Improve UDP scan reliability against ICMP limiting.",
        "builder": lambda: ["--defeat-icmp-ratelimit"],
    },
]


def print_banner() -> None:
    """Print a large stylized Z banner."""
    banner = rf"""
{Fore.MAGENTA}
ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ
ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ
ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ
ZZZZZZZ            NMAP IDS/IPS EVASION ENHANCED             ZZZZZZZ
ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ
ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ
ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

{Style.RESET_ALL}
"""
    print(banner)


def ensure_environment() -> None:
    """Create required directories/files and verify nmap binary."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if not TRACKER_FILE.exists():
        default_tracker = {
            "created_at": dt.datetime.now().isoformat(),
            "successful_scans": [],
        }
        TRACKER_FILE.write_text(json.dumps(default_tracker, indent=2), encoding="utf-8")

    if not shutil_which(NMAP_BINARY):
        print(f"{Fore.RED}[!] Nmap binary not found in PATH. Install nmap first.{Style.RESET_ALL}")
        sys.exit(1)


def shutil_which(binary: str) -> str | None:
    """Local helper to avoid importing entire shutil in global scope."""
    import shutil

    return shutil.which(binary)


def prompt_non_empty(message: str) -> str:
    """Prompt until non-empty input is supplied."""
    while True:
        value = input(message).strip()
        if value:
            return value
        print(f"{Fore.YELLOW}[-] Input cannot be empty.{Style.RESET_ALL}")


def prompt_positive_int(message: str) -> str:
    """Prompt for integer > 0 and return as string for CLI args."""
    while True:
        raw = input(message).strip()
        if raw.isdigit() and int(raw) > 0:
            return raw
        print(f"{Fore.YELLOW}[-] Enter a valid positive integer.{Style.RESET_ALL}")


def prompt_port(message: str) -> str:
    """Prompt for valid port number."""
    while True:
        raw = input(message).strip()
        if raw.isdigit() and 1 <= int(raw) <= 65535:
            return raw
        print(f"{Fore.YELLOW}[-] Port must be between 1 and 65535.{Style.RESET_ALL}")


def prompt_mtu() -> str:
    """Prompt for valid MTU value (positive integer divisible by 8)."""
    while True:
        raw = prompt_positive_int("Enter MTU value (multiple of 8): ")
        if int(raw) % 8 == 0:
            return raw
        print(f"{Fore.YELLOW}[-] MTU must be divisible by 8.{Style.RESET_ALL}")


def prompt_timing_template() -> str:
    """Prompt for timing template and return corresponding nmap arg."""
    while True:
        raw = input("Enter timing template (0-5 for T0..T5): ").strip()
        if raw in {"0", "1", "2", "3", "4", "5"}:
            return f"-T{raw}"
        print(f"{Fore.YELLOW}[-] Invalid choice. Enter a number from 0 to 5.{Style.RESET_ALL}")


def prompt_rate_options() -> List[str]:
    """Prompt for min/max packet rates."""
    args: List[str] = []
    print("Configure send rate options:")
    min_rate = input("  Min rate (leave blank to skip): ").strip()
    max_rate = input("  Max rate (leave blank to skip): ").strip()

    if min_rate:
        if min_rate.isdigit() and int(min_rate) > 0:
            args.extend(["--min-rate", min_rate])
        else:
            print(f"{Fore.YELLOW}[-] Ignoring invalid min-rate value.{Style.RESET_ALL}")

    if max_rate:
        if max_rate.isdigit() and int(max_rate) > 0:
            args.extend(["--max-rate", max_rate])
        else:
            print(f"{Fore.YELLOW}[-] Ignoring invalid max-rate value.{Style.RESET_ALL}")

    if not args:
        print(f"{Fore.YELLOW}[-] No valid rate provided; skipping this technique.{Style.RESET_ALL}")

    return args


def parse_targets(raw_targets: str) -> List[str]:
    """Parse and validate one or multiple targets split by comma/space/newline."""
    tokens = [t.strip() for t in re.split(r"[\s,]+", raw_targets.strip()) if t.strip()]
    valid_targets: List[str] = []

    for token in tokens:
        if is_valid_target(token):
            valid_targets.append(token)
        else:
            print(f"{Fore.YELLOW}[-] Skipping invalid target: {token}{Style.RESET_ALL}")

    return valid_targets


def is_valid_target(token: str) -> bool:
    """Validate IPv4/IPv6/CIDR/hostname target values."""
    try:
        ipaddress.ip_address(token)
        return True
    except ValueError:
        pass

    # CIDR network support
    try:
        ipaddress.ip_network(token, strict=False)
        return True
    except ValueError:
        pass

    # Basic hostname/domain pattern
    hostname_regex = re.compile(
        r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
    )
    return bool(hostname_regex.match(token))


def choose_scan_type() -> ScanType:
    """Interactive scan type selection."""
    print(f"\n{Fore.CYAN}Available Scan Types:{Style.RESET_ALL}")
    for key, scan in SCAN_TYPES.items():
        print(f"  [{key}] {scan.name:<20} - {scan.description}")

    while True:
        choice = input("Select scan type: ").strip()
        if choice in SCAN_TYPES:
            return SCAN_TYPES[choice]
        print(f"{Fore.YELLOW}[-] Invalid selection. Try again.{Style.RESET_ALL}")


def choose_evasion_techniques() -> Tuple[List[str], List[str]]:
    """Interactive evasion-technique picker with support for multiple selections."""
    print(f"\n{Fore.CYAN}Evasion Technique Menu:{Style.RESET_ALL}")
    for tech in EVASION_TECHNIQUES:
        print(f"  [{tech['id']}] {tech['name']} - {tech['description']}")
    print("  [0] Finish selection")

    selected_flags: List[str] = []
    selected_names: List[str] = []
    selected_ids = set()

    while True:
        choice = input("Choose technique number (or 0 to finish): ").strip()

        if choice == "0":
            break

        match = next((t for t in EVASION_TECHNIQUES if t["id"] == choice), None)
        if not match:
            print(f"{Fore.YELLOW}[-] Invalid technique number.{Style.RESET_ALL}")
            continue
        if choice in selected_ids:
            print(f"{Fore.YELLOW}[-] Technique already selected; skipping duplicate.{Style.RESET_ALL}")
            continue

        built_flags = match["builder"]()
        if built_flags:
            selected_flags.extend(built_flags)
            selected_names.append(match["name"])
            selected_ids.add(choice)
            print(f"{Fore.GREEN}[+] Added: {match['name']}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[-] Technique not added due to invalid values.{Style.RESET_ALL}")

    return selected_flags, selected_names


def sanitize_filename(value: str) -> str:
    """Convert a target string into a safe filename segment."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", value)


def create_output_base(target: str) -> Path:
    """Create target-specific timestamped output path base."""
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_slug = sanitize_filename(target)
    run_dir = RESULTS_DIR / f"{timestamp}_{target_slug}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir / target_slug


def build_nmap_command(
    target: str,
    scan: ScanType,
    evasion_flags: List[str],
    ports: str,
    extra_flags: str,
    output_base: Path,
) -> List[str]:
    """Build final nmap command list for subprocess execution."""
    cmd = [NMAP_BINARY]
    cmd.extend(scan.args)
    cmd.extend(DEFAULT_NMAP_ARGS)

    if ports:
        cmd.extend(["-p", ports])

    cmd.extend(evasion_flags)

    if extra_flags:
        cmd.extend(shlex.split(extra_flags))

    # Save outputs in normal, XML, and grepable formats
    cmd.extend(["-oN", f"{output_base}.nmap"])
    cmd.extend(["-oX", f"{output_base}.xml"])
    cmd.extend(["-oG", f"{output_base}.gnmap"])

    cmd.append(target)
    return cmd


def execute_scan(command: List[str]) -> Tuple[int, str, str]:
    """Run nmap command and return process info."""
    try:
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 127, "", "nmap binary not found"
    except Exception as exc:  # pragma: no cover - defensive path
        return 1, "", str(exc)


def load_tracker() -> dict:
    """Load tracking JSON file safely."""
    try:
        with TRACKER_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if "successful_scans" not in data:
                data["successful_scans"] = []
            return data
    except (json.JSONDecodeError, OSError):
        return {"created_at": dt.datetime.now().isoformat(), "successful_scans": []}


def save_tracker(data: dict) -> None:
    """Write tracking JSON file."""
    with TRACKER_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def log_successful_scan(
    target: str,
    scan_name: str,
    techniques: List[str],
    command: List[str],
    output_base: Path,
) -> None:
    """Append a successful scan entry to tracker JSON."""
    tracker = load_tracker()
    tracker["successful_scans"].append(
        {
            "timestamp": dt.datetime.now().isoformat(),
            "target": target,
            "scan_type": scan_name,
            "techniques": techniques,
            "command": " ".join(shlex.quote(c) for c in command),
            "outputs": {
                "normal": f"{output_base}.nmap",
                "xml": f"{output_base}.xml",
                "grepable": f"{output_base}.gnmap",
            },
        }
    )
    save_tracker(tracker)


def summarize_tracker() -> None:
    """Display quick summary of tracked successful techniques."""
    data = load_tracker()
    entries = data.get("successful_scans", [])
    print(f"\n{Fore.CYAN}Technique Tracker Summary{Style.RESET_ALL}")
    print(f"Total successful scans: {len(entries)}")
    if not entries:
        return

    counts: Dict[str, int] = {}
    for entry in entries:
        for tech in entry.get("techniques", []):
            counts[tech] = counts.get(tech, 0) + 1

    print("Most used successful techniques:")
    for tech, count in sorted(counts.items(), key=lambda item: item[1], reverse=True):
        print(f"  - {tech}: {count}")


def run_scan_flow() -> None:
    """Run the full interactive scan workflow."""
    print(f"\n{Fore.CYAN}Target Input{Style.RESET_ALL}")
    raw_targets = prompt_non_empty("Enter target IP/domain(s) (comma or space separated): ")
    targets = parse_targets(raw_targets)

    if not targets:
        print(f"{Fore.RED}[!] No valid targets provided. Returning to main menu.{Style.RESET_ALL}")
        return

    scan = choose_scan_type()

    ports = input("Optional port spec (e.g., 22,80,443 or 1-1000). Leave blank for default: ").strip()
    evasion_flags, evasion_names = choose_evasion_techniques()
    extra_flags = input("Any additional nmap flags? (optional): ").strip()

    print(f"\n{Fore.CYAN}Execution Plan{Style.RESET_ALL}")
    print(f"  Targets: {', '.join(targets)}")
    print(f"  Scan Type: {scan.name}")
    print(f"  Techniques: {', '.join(evasion_names) if evasion_names else 'None'}")

    confirm = input("Proceed with scan? (y/n): ").strip().lower()
    if confirm != "y":
        print(f"{Fore.YELLOW}[-] Scan cancelled by user.{Style.RESET_ALL}")
        return

    for target in targets:
        output_base = create_output_base(target)
        command = build_nmap_command(target, scan, evasion_flags, ports, extra_flags, output_base)

        print(f"\n{Fore.MAGENTA}[*] Running command for {target}:{Style.RESET_ALL}")
        print("    " + " ".join(shlex.quote(c) for c in command))

        returncode, stdout, stderr = execute_scan(command)

        if stdout.strip():
            print(f"{Fore.GREEN}{stdout}{Style.RESET_ALL}")
        if stderr.strip():
            print(f"{Fore.YELLOW}{stderr}{Style.RESET_ALL}")

        if returncode == 0:
            print(f"{Fore.GREEN}[+] Scan completed for {target}.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}[!] Scan exited with code {returncode} for {target}.{Style.RESET_ALL}")

        print("Saved outputs:")
        print(f"  - {output_base}.nmap")
        print(f"  - {output_base}.xml")
        print(f"  - {output_base}.gnmap")

        success_mark = input("Mark this scan as successful for technique tracking? (y/n): ").strip().lower()
        if success_mark == "y":
            log_successful_scan(target, scan.name, evasion_names, command, output_base)
            print(f"{Fore.GREEN}[+] Technique success logged.{Style.RESET_ALL}")


def main() -> None:
    """Program entry point."""
    print_banner()
    ensure_environment()

    while True:
        print(f"\n{Fore.CYAN}Main Menu{Style.RESET_ALL}")
        print("  [1] New Evasion Scan")
        print("  [2] View Technique Tracker Summary")
        print("  [3] Exit")

        choice = input("Select option: ").strip()

        if choice == "1":
            run_scan_flow()
        elif choice == "2":
            summarize_tracker()
        elif choice == "3":
            print(f"{Fore.CYAN}Good luck in the lab. Exiting...{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.YELLOW}[-] Invalid option. Try again.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
