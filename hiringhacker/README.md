### Hiring Dork Tool

Python-based Google dorking utility for **job-posting reconnaissance** during footprinting and OSINT workflows.

It generates region-aware Google dorks from one or more target keywords, executes searches with rate-limiting, and writes both:
- raw search results, and
- structured JSON records for downstream analysis.

---

#### Features

- Multi-keyword target support (`--target` repeated or comma-separated)
- Region/country aware hiring-site mapping (US, UK/Europe, APAC, LATAM, MEA, Global)
- Automated Google dork generation
- Search execution with retry/backoff + delay/jitter controls
- Structured parseable JSON output
- Separate raw and parsed output files
- API integration placeholder framework for paywalled sites
- YAML configuration for community customization
- CLI-first workflow and progress logging

---

#### Project layout

```text
hiring_dork_tool/
├── config/
│   ├── regions.yaml
│   └── api_integrations.example.yaml
├── dork_tool/
│   ├── __init__.py
│   ├── api_framework.py
│   ├── cli.py
│   ├── config_loader.py
│   ├── dork_generator.py
│   ├── models.py
│   ├── output_writer.py
│   ├── parser.py
│   └── search_executor.py
├── output/
│   ├── parsed/
│   └── raw/
├── main.py
├── requirements.txt
└── README.md
```

---

#### Installation

```bash
cd /home/ubuntu/hiring_dork_tool
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

#### Usage examples

##### 1) Basic run (US)

```bash
python3 main.py \
  --target "Acme Corp" \
  --location "US"
```

##### 2) Multi-keyword entity forms + UK/Europe mapping

```bash
python3 main.py \
  --target "Acme Corp" \
  --target "Acme Incorporated,Acme Inc" \
  --location "Germany"
```

`Germany` resolves to `UK_EUROPE` based on `config/regions.yaml`.

##### 3) Adjust anti-block behavior

```bash
python3 main.py \
  --target "Target Name" \
  --location "APAC" \
  --delay 4.0 \
  --jitter 1.2 \
  --max-results-per-query 30
```

##### 4) Dry-run (generate dorks only)

```bash
python3 main.py \
  --target "Target Name" \
  --location "LATAM" \
  --dry-run --verbose
```

---

#### Output format

Two files are created per run:
- `output/raw/raw_results_<timestamp>.json`
- `output/parsed/parsed_results_<timestamp>.json`

Structured records include:
- `originating_site`
- `company_name`
- `position`
- `description`
- `url`
- `date_found`
- `region`

Example parsed record:

```json
{
  "originating_site": "linkedin.com",
  "company_name": "Acme Corp / Acme Inc",
  "position": "Security Engineer",
  "description": "Security Engineer - Acme Corp hiring in London...",
  "url": "https://www.linkedin.com/jobs/view/...",
  "date_found": "2026-04-25T00:00:00+00:00",
  "region": "UK_EUROPE"
}
```

---

#### Customizing hiring sites per region

Edit `config/regions.yaml`:
- Add/remove domains under each region’s `sites`
- Add alias terms under `aliases`
- Extend `country_to_region` mappings

You can keep community-specific forks with region-specific job board lists.

---

#### API integration framework (future extension)

`dork_tool/api_framework.py` + `config/api_integrations.example.yaml` provide scaffolding for:
- premium job APIs,
- authenticated partner feeds,
- registration/paywalled data sources.

Contributors can implement provider adapters that normalize to the same JSON schema.

---

#### Error handling notes

The tool handles:
- transient network failures (retry + backoff)
- basic Google anti-bot page detection
- malformed config files
- unresolved location/region mapping

If Google blocks frequent queries, increase `--delay`/`--jitter`, reduce run size, or switch network profile.

---

#### Legal / ethical note

Use responsibly and comply with:
- target platform terms of service,
- local laws/regulations,
- engagement scope and authorization rules.

This project is intended for defensive security research and authorized reconnaissance.
