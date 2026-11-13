# Demonstration guide

## Five-minute walkthrough

1. Install `requirements.txt` and run `python -m streamlit run src/dashboard.py`.
2. Use the bundled normal and tunnel CSV samples.
3. Show Overview, then Investigate and filter by severity.
4. Inspect a window and export its details.
5. Explain that high scores are triage indicators. Hosted demos should use offline samples; live capture requires a configured local interface.

## Deployment

Use `Dockerfile.demo`: build with `docker build -f Dockerfile.demo -t project-demo .` and run `docker run --rm -p 8501:8501 project-demo`. Configure a container host to route to port 8501. Data changes inside the container are ephemeral.

## Screenshots and verification

Existing project screenshots: [Overview](docs/screenshots/Overview.png), [Live monitor](docs/screenshots/Live%20Monitoring.png).

Existing screenshots are historical assets, not fresh proof of this build. No new runtime screenshots or deployment success are claimed. Before sharing a demo, run the walkthrough, capture only fictional data, and record the commit SHA beside the images.
