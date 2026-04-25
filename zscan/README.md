# Z-Scan(ner) 
### My personal interactive Python CLI tool for running Nmap reconnaissance and enumeration scans with built-in IDS/IPS evasion advice.
### Combines: 

- guided target/scan selection,
- evasion technique stacking,
- automatic multi-format result export, and
- persistent technique-success tracking for post-lab analysis.

This tool is noob-friendly, professional, and modular with features for multiple scan profiles, evasion/shaping techniques, input validation, and multi-target support.

This tool supports automatic result exports in the following formats:
Normal output (.nmap)
XML output (.xml)
Grepable output (.gnmap)
Persistent JSON-based success tracker (technique_tracker.json)
Summary dashboard for most-used successful techniques

Prerequisites
- Python 3.x
- Nmap installed and available in PATH
- (Optional) colorama for improved terminal colors

Verify prerequisites
- `python3 --version`
- `nmap --version`

Installation
- `git clone (https://github.com/Zimmer-Sec/Z-Scanner)`
- `cd Z-Scanner`
- `python3 -m venv .venv`
- `source .venv/bin/activate`
- `pip install colorama`
- colorama is optional. The tool runs without it using graceful fallback.

Quick Start
Run the tool:
- `python3 nmap_evasion_tool.py`

You will be guided through:
- Target input
- Scan type selection
- Optional port specification
- Evasion technique selection (multiple allowed)
- Optional additional flags
- Confirmation and execution
- Optional success logging into tracker


Supported Scan Types

1.	SYN Scan	-sS	Stealthy half-open TCP scan
2.	ACK Scan	-sA	Firewall/filter rule analysis
3.	UDP Scan	-sU	UDP service discovery
4.	TCP Connect Scan	-sT	Full TCP handshake scan
5.	FIN Scan	-sF	Stateless filter evasion scenarios
6.	NULL Scan	-sN	No TCP flags set
7.	XMAS Scan	-sX	FIN/PSH/URG probing behavior
8.	Version Detection	-sV	Service version fingerprinting
9.	OS Detection	-O	Remote OS fingerprinting
10.	Aggressive	-A	OS + version + scripts + traceroute

Evasion Techniques Reference

1.	Fragment packets	-f
2.	Custom MTU	--mtu <multiple_of_8>
3.	Decoy scanning	-D <decoy_list>
4.	Source port manipulation	--source-port <port>
5.	Timing template	-T0 to -T5
6.	Randomize hosts	--randomize-hosts
7.	Spoof MAC address	--spoof-mac <value>
8.	Bad checksums	--badsum
9.	Append random data	--data-length <bytes>
10.	IP options	--ip-options <value>
11.	TTL manipulation	--ttl <value>
12.	Spoof source IP	-S <ip>
13.	Scan delay	--scan-delay <time>
14.	Max scan delay	--max-scan-delay <time>
15.	Packet send rate control	--min-rate <n>, --max-rate <n>
16.	Custom DNS servers	--dns-servers <list>
17.	Defeat RST rate limits	--defeat-rst-ratelimit
18.	Defeat ICMP rate limits	--defeat-icmp-ratelimit

Output & Results Format
For each target, the tool generates a timestamped run folder and exports:

- .nmap: human-readable full output
- .xml: machine-readable output for automation/parsers
- .gnmap: grep-friendly format for rapid filtering
- This supports both manual reporting and downstream automation pipelines.

============================ MY NOTES: =========================

Add screenshots:

- Main Menu + Banner: Shows professional CLI interface and options.
- Technique Selection Screen: Demonstrates full evasion menu.
- Execution Plan + Generated Command: Shows transparency and reproducibility.
- Result Files in results/: Validates output artifacts.
- Tracker Summary View: Shows analytics component.

Do not use this tool on networks, hosts, or applications you do not own or lack permission to assess. Unauthorized scanning may violate laws, policies, and ethical standards.

Possible future updates
- Profile presets for common target types (web server, AD, IoT)
- JSON/YAML scan profile import/export
- Report generation (Markdown/PDF) from output + tracker logs
- Plugin architecture for custom evasion techniques
- Optional non-interactive mode (argparse) for CI/lab automation
- Comparative analytics dashboard for technique success trends
- Docker packaging for reproducible deployment

License: considering adding...

MIT License (permissive)
Apache-2.0 (permissive + patent protection)
GPL-3.0 (copyleft)
Until a license file is added, default copyright restrictions apply.
