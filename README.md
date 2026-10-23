# Tunneling Insights

**A local cybersecurity lab for understanding DNS tunneling behavior and exploring explainable detection.**


Tunneling Insights demonstrates a complete defensive analysis workflow: generate controlled DNS traffic, capture packets, extract behavioral features, compare traffic with a normal baseline, and inspect detection results in an interactive dashboard.

> **Use only in an authorized, isolated lab.** This project is an educational prototype. It is not a production intrusion detection system, and its scores are indicators for investigation rather than proof of malicious activity.

## Project at a glance

- Build a small, controlled DNS message transport using Base32 encoded chunks and a test namespace.
- Run a local DNS receiver that validates and reassembles those chunks.
- Capture normal and simulated tunnel traffic as PCAP files.
- Measure lexical, volume, uniqueness, and timing characteristics of DNS queries.
- Score fixed time windows against a normal DNS baseline.
- Review offline results and live telemetry in a Streamlit dashboard.

This repository contains the complete application, datasets, tests, screenshots, and documentation.

## How it works

```text
Harmless test message
        |
        v
UTF-8 -> Base32 -> payload chunks
        |
        v
DNS queries under tunnel.test
        |
        +--> Local receiver validates and reassembles the message
        |
        v
PCAP capture -> feature extraction -> time windows
        |
        v
Normal traffic baseline -> explainable score and severity
        |
        +--> Offline evaluation
        +--> Streamlit dashboard and live CSV log
```

The example protocol uses this query-name structure:

```text
v1.<session_id>.<chunk_index>.<total_chunks>.<payload>.tunnel.test
```

Base32 is an encoding format, **not encryption**. Example messages are harmless lab text. Do not place sensitive information in test payloads.

## Detection methodology

The offline detector builds a statistical baseline from normal traffic windows. For each input window it compares these features with the baseline:

| Signal | What it describes |
| --- | --- |
| Average entropy | Character diversity in queried names |
| Average label length | Length of the longest label in each queried name, averaged over the window |
| Query rate | DNS queries per second |
| Unique subdomain ratio | Share of distinct queried names in the window |
| Inter-arrival coefficient of variation | Relative variability in the time between queries |
| Burstiness | Whether query timing is clustered or more evenly spaced |

Feature deviations contribute to a weighted score. The dashboard exposes per-signal contributions to make a result easier to inspect. Severity bands are:

| Score | Severity |
| ---: | --- |
| 0-29 | LOW |
| 30-59 | MEDIUM |
| 60-79 | HIGH |
| 80-100 | CRITICAL |

Live detection uses its own configured weights and scoring steps. Its results are written to `data/live_windows.csv`; the dashboard can refresh on demand or at a selected interval.

### Interpreting results

These scores describe deviation from the included baseline. High entropy, long labels, or unusual timing can also appear in legitimate DNS. Review multiple signals and the surrounding context before drawing conclusions. The included datasets are small and controlled, so their outcomes do not represent expected real-world detection accuracy.

## Dashboard

The Streamlit app has three workspaces:

### Overview

- Normal and tunnel sample query counts
- Baseline window count and high-risk tunnel rate
- Severity distribution for normal and tunnel windows
- Side-by-side average traffic profile
- Latest live detection state, when live data exists
- Context for interpreting the sample-level flags

### Investigate

- Filter tunnel windows by severity and minimum score
- Sort and review scores, classifications, and query counts
- Replay a selected window and inspect its feature values
- Compare average signal contributions across the tunnel sample
- Export filtered window details and signal contributions as CSV

### Live monitor

- Latest window status, query count, rate, and score
- Score timeline with severity threshold guides
- Latest window signal contribution chart
- Filterable recent-window table
- On-demand refresh or automatic refresh every 5, 15, or 30 seconds
- Download the live detection log as CSV

## Repository contents

The repository is organized as follows:

```text
Tunneling-Insights/
|-- data/
|   |-- normal_dns.pcap
|   |-- dns_tunnel_realistic.pcap
|   |-- normal_behavioral_features.csv
|   |-- tunnel_behavioral_features.csv
|   |-- normal_window_features.csv
|   |-- tunnel_window_features.csv
|   `-- live_windows.csv
|-- docs/screenshots/
|-- src/
|   |-- __init__.py
|   |-- capture.py
|   |-- capture_tunnel.py
|   |-- config.py
|   |-- dashboard.py
|   |-- dns_records.py
|   |-- dns_server.py
|   |-- evaluate_detector.py
|   |-- features.py
|   |-- live_detector.py
|   |-- normal_workload.py
|   |-- pcap_features.py
|   |-- protocol.py
|   |-- tunnel_workload.py
|   |-- window_detector.py
|   `-- window_features.py
|-- tests/
|   |-- test_features.py
|   |-- test_protocol.py
|   `-- test_window_detector.py
|-- .gitignore
|-- pytest.ini
|-- requirements.txt
`-- README.md
```

The feature CSVs and PCAP files provide ready-to-use sample data. `live_windows.csv` is the output log used by live monitoring; the dashboard shows an empty state when no live records are present.

## Requirements

- Python 3.11 or newer
- Windows for the included packet-capture interface configuration
- Npcap installed for Scapy packet capture; loopback capture support is required for local traffic
- Administrator privileges may be required by the packet-capture driver

The project pins Python dependencies in `requirements.txt`, including Scapy, dnspython, dnslib, pandas, Altair, Streamlit, and pytest.

## Installation

Clone the repository and create a virtual environment:

```powershell
git clone https://github.com/tejas764/Tunneling-Insights.git
cd Tunneling-Insights
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, use the activation instructions for your shell or invoke the environment's Python directly at `.venv\Scripts\python.exe`.

## Run the dashboard

From the repository root:

```powershell
streamlit run src/dashboard.py
```

The dashboard uses the included CSV datasets and opens in your browser.

## Run the analysis pipeline

The repository includes preprocessed sample CSVs. To regenerate them from the included PCAP files, run from the repository root:

```powershell
python src/pcap_features.py
python src/window_features.py
python src/evaluate_detector.py
```

The PCAP processing step writes per-query behavioral features. Window processing groups the queries into time windows and calculates aggregate features. Evaluation compares the tunnel windows with a baseline built from the normal windows and reports a confusion matrix and summary metrics.

Run the automated test suite with:

```powershell
pytest -q
```

## Run a controlled traffic exercise

Use only loopback traffic and harmless test messages. Open separate terminals from the repository root.

1. Start the local receiver:

   ```powershell
   python src/dns_server.py
   ```

2. In another terminal, run either the normal workload or the controlled tunnel workload:

   ```powershell
   python src/normal_workload.py
   ```

   ```powershell
   python src/tunnel_workload.py
   ```

3. To capture traffic, run the relevant capture script while the workload is active:

   ```powershell
   python src/capture.py
   ```

   ```powershell
   python src/capture_tunnel.py
   ```

4. Regenerate features, evaluate the data, or open the dashboard as described above.

The capture and live-detection scripts are configured for the Windows Npcap loopback interface and UDP port 5353. Adjust the interface and capture filter in the source before using a different local setup. Do not point the lab at networks or resolvers without explicit authorization.

## Live detection

Start the live detector from a terminal in the repository:

```powershell
python src/live_detector.py
```

It reads the normal window baseline, listens for DNS queries on the configured loopback interface and UDP port 5353, and appends scored windows to:

```text
data/live_windows.csv
```

Then open the dashboard in another terminal. Select **Live monitor** and enable automatic refresh or use the refresh button to load new windows. Live capture depends on the configured Npcap interface and appropriate OS permissions.

## Project components

| Component | Responsibility |
| --- | --- |
| `protocol.py` | Base32 encoding, chunking, query-name validation, and reassembly |
| `dns_server.py` | Local DNS receiver for the controlled test namespace |
| `normal_workload.py` | Generates ordinary queries to a local resolver |
| `tunnel_workload.py` | Sends harmless encoded test messages as DNS query chunks |
| `capture.py`, `capture_tunnel.py` | Capture DNS packets to PCAP files |
| `pcap_features.py` | Extract per-query lexical and traffic features from PCAP files |
| `window_features.py` | Group queries into windows and calculate aggregate features |
| `window_detector.py` | Build the normal baseline and score offline windows |
| `live_detector.py` | Score live windows and append them to the live CSV log |
| `evaluate_detector.py` | Report offline confusion-matrix metrics |
| `dashboard.py` | Explore sample data, detections, window details, and live results |

## Technology stack

| Technology | Use |
| --- | --- |
| Python | Protocol, feature extraction, scoring, and orchestration |
| Scapy | Packet capture and PCAP reading |
| dnspython | DNS client queries |
| dnslib | Local DNS server |
| pandas | CSV analysis and dashboard tables |
| Altair | Interactive charts |
| Streamlit | Analyst dashboard |
| pytest | Automated tests |
| Wireshark | Optional manual PCAP inspection |

## Limitations

- The bundled traffic is a small laboratory sample, not representative production traffic.
- Thresholds and feature weights are configured for demonstration and require validation for other environments.
- The offline and live detectors use separate scoring logic; their scores should not be compared as if they were calibrated probabilities.
- The detector uses statistical feature deviations, not a trained classifier or domain-reputation service.
- Legitimate services can produce long, high-entropy, or rapidly changing DNS labels.
- Packet capture depends on OS, interface, driver, and permission configuration.
- A score is a triage signal and does not establish intent, data exfiltration, or compromise.

## Responsible use

Use Tunneling Insights for education, authorized defensive research, and isolated lab exercises. Keep generated traffic on loopback or another explicitly authorized environment. Use only non-sensitive sample messages. Do not use this project to transmit data through third-party DNS infrastructure or to test systems without permission.

## License

This project is available under the [MIT License](LICENSE). You may use, modify, and redistribute it, including for educational purposes, provided the copyright and license notices are retained. The MIT License also permits commercial use. See the license text for the full terms.

## Links

- **GitHub:** [tejas764/Tunneling-Insights](https://github.com/tejas764/Tunneling-Insights)
